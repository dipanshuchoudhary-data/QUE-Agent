# QUE-Agent runbook

Operational reference for running, degrading gracefully, and rolling back
QUE-Agent. Pairs with [`FAILURE_MATRIX.md`](FAILURE_MATRIX.md) (expected
degraded behavior per failure mode) and
[`phases/phase-12-observability.md`](phases/phase-12-observability.md) /
[`phases/phase-13-reliability.md`](phases/phase-13-reliability.md).

## Health endpoints

| Endpoint | Purpose | Auth |
|---|---|---|
| `GET /health` | Pure liveness — process is up | none |
| `GET /ready` | Real dependency check (LLM key, knowledge index, Quizzer tools reachability) — use for load-balancer / orchestrator readiness gates | none |
| `GET /v1/ops/metrics` | In-process latency/cost/error snapshot | `X-Que-Service-Key` |

`GET /ready` returns `503` with a `checks` breakdown when anything is
unhealthy — check the response body first, it tells you exactly which
dependency is failing before you touch logs.

## Common incidents

### Chat returns 503 / `llm_not_configured`

Cause: no `LLM_API_KEY*` set, or it was rotated without redeploying.
`enforce_production_guards` (Phase 14) should have refused to boot without a
key in non-local environments — if you're seeing this in prod, the
deployment somehow started without hitting that guard (check `APP_ENV`).

Fix: set `LLM_API_KEY` (or `LLM_API_KEY_1..8`), redeploy. No data loss risk —
this fails closed before any request is processed.

### Chat is slow / P95 latency alert

1. `GET /v1/ops/metrics` (service key) → check `spans.llm.p95` vs
   `spans.tool.p95` vs `spans.retrieve.p95` to isolate the layer.
2. If `spans.llm` is slow: check `QUE_LLM_CIRCUIT_*` — the gateway may be
   failing over between keys/models already (see `que_llm_fail` logs).
3. If `spans.tool` is slow: check Quizzer's own health / `tools_health`
   snapshot and `QUE_TOOL_CIRCUIT_*`.

### Tool circuit / LLM circuit stuck open

Both breakers auto-heal after `QUE_TOOL_CIRCUIT_TTL_SECONDS` /
`QUE_LLM_CIRCUIT_TTL_SECONDS`. To force-clear without waiting (rare — only
if you've already fixed the upstream issue and don't want to wait out the
TTL), restart the QUE process — breaker state is in-process, not persisted.

### A write action (publish/notify/delete) misbehaved

- Check `que_write_action_proposed` / `que_write_action_resolved` /
  `que_write_action_ok` / `que_write_action_error` logs for the
  `request_id`.
- Every confirmed write call carries an `idempotency_key`; Quizzer dedupes
  on it for 10 minutes (`backend/api/que_internal_tools.py`), so a retried
  HTTP call cannot double-execute.
- `QUE_BUDGET_WRITE_ACTIONS_PER_HOUR` (default 20/user/hour) is a hard stop
  if something is looping — raise it only after confirming it's a false
  positive, not a bug.
- Nothing executes without a human "yes" in chat first — if a mutation
  happened that a teacher didn't expect, check the conversation transcript
  for the confirmation turn before assuming a code bug.

### Rate limiting is too aggressive / not aggressive enough

`QUE_RATE_LIMIT_PER_MINUTE` / `QUE_RATE_LIMIT_BURST` in `.env`. Set
`QUE_RATE_LIMIT_ENABLED=false` to disable entirely as a stopgap (not
recommended in prod for more than a few minutes).

## LangSmith (AI failure capture)

QUE chat LLM failover is instrumented with `@traceable` / `trace`
(`app/core/llm.py`). Failed lanes still appear as child runs when a later
key/model succeeds. Meta/capabilities asks should be **canned** (no LLM) —
if LangSmith shows a 120s `generate` on "what can you help me with", the
deploy is missing Wave 1 context-efficiency fixes (see
`docs/phases/phase-15-context-efficiency.md`). How-tos such as
`"How do I publish an exam?"` should be a parent `que.turn` tagged
`que.route.deterministic` **without** a generate child (Phase 16 cards).

| Var | Value |
|---|---|
| `LANGSMITH_PROJECT` | `Que_agent` (keep distinct from Quizzer) |
| `LANGSMITH_TRACING` | `true` to enable |
| `ALLOW_LANGSMITH_IN_PROD` | **required** when `APP_ENV` is not local/dev |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` |
| `LANGSMITH_API_KEY` | LangSmith personal/org key for the Que project |
| `LLM_PREFER_PAID_FIRST` | `true` — paid models before `:free` |
| `LLM_MAX_ATTEMPTS_NON_AGENT` | `2` — fail faster on knowledge/workflow |
| `QUE_SEMANTIC_ROUTER` | default **true** when embeddings are configured; fail-open to heuristics |

Exports prompts to LangSmith — treat as third-party data sharing. Never commit
keys; set them on Render / local `.env` only.

## Rollback

QUE-Agent is stateless per request (short-term memory is in-process
`MemorySaver`, not durable — a rollback loses in-flight conversation
continuity but nothing persistent). Rollback is a standard container
redeploy:

1. Identify the last known-good image tag / git SHA
   (`docs/BUILD_PROGRESS.md` and phase docs map features to shipped
   commits).
2. Redeploy that image with the **same** `.env` (do not roll back env vars
   unless the new variables listed in this phase's `.env.example` diff are
   the actual cause — most new knobs default to safe values, so a rollback
   of code alone is usually sufficient).
3. Confirm `GET /ready` returns `200` before routing traffic.
4. If the incident involved `QUE_CHROMA_PATH` (dense index), verify the
   mounted volume/image still has the expected index — a rollback to an
   older image with a newer index format can break dense retrieval
   (`select_dense` returns `None`; keyword fallback still works when
   `QUE_RAG_FALLBACK_KEYWORD=true`).
5. Post-rollback: re-run `uv run python scripts/run_eval_suite.py --offline`
   against the rolled-back version to confirm no regression before
   declaring the incident resolved.

### `/ready` stuck 503 on `knowledge_index` after a fresh deploy

`scripts/start.sh` builds the Chroma index automatically before gunicorn
starts (incremental, needs `LLM_API_KEY*` for embeddings) — this should be
self-healing within the container's first boot. If it stays unhealthy:

1. Check container logs for `warn: knowledge index build failed` — usually
   means `LLM_API_KEY*` wasn't set yet at boot, or the embeddings provider
   was unreachable.
2. Confirm `QUE_CHROMA_PATH` points at a writable, ideally persistent, disk
   — without a persistent volume every restart re-embeds the whole corpus
   from scratch (slow, costs tokens, but not incorrect).
3. Manual rebuild: exec into the running container (or a one-off shell) and
   run `python -m app.knowledge --force`.
4. `QUE_RAG_FALLBACK_KEYWORD=true` (default) means chat still answers
   product questions via keyword search while the index is down — this is
   a degraded-but-safe state, not an outage.

## Staging config

See [`.env.staging.example`](../.env.staging.example) — same shape as
`.env.example` but with staging-appropriate defaults (guardrails/rate limits
on, tools likely off until Quizzer staging internal URL is confirmed).
