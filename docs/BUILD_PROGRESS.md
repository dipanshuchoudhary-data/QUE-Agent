# QUE build progress (handbook-aligned)

Open the interactive tracker: [`que-agent-handbook.html`](que-agent-handbook.html)
(**Progress tracker** section — Done / Now / Next / Later, You Are Here, **Mark baseline**).

**Phase deep-dives (interview + code map):** [`phases/README.md`](phases/README.md)
— one MD per shipped phase (0–16): what changed, which files, how it works.

## Current focus: Phase 16 routed-efficiency done (async still Later)

| Phase | Status | Notes |
|---|---|---|
| 0 Foundations | **Done** | Separate microservice, JWT/service-key auth, Docker |
| 1 QUE Core + understanding + evals | **Done** | Request Understanding + golden scope eval + canned + memory |
| 2 Knowledge + RAG | **Done** | Dense Chroma RAG + keyword fallback; eval recall@5 ≈ 0.91 |
| 3 Context Engineering | **Done** | Structured UI context end-to-end; role stamped by Quizzer BFF |
| 4 Tools + secure execution | **Done** | Insight tools + `summarize_my_exams`; kill switch; status SSE |
| 5 Policy + permissions | **Done** | Role gate QUE + Quizzer; capability matrix; adversarial eval |
| 6 Hybrid retrieval | **Done** | BM25 + dense RRF; recall@5 **0.9265** (+0.015 vs dense); CE deferred |
| 7 Agent runtime | **Done** | Explicit workflow vs bounded loop; mode eval **7/7**; no ReAct |
| 8 LLM gateway | **Done** | RR 3 OpenRouter models + numbered keys; mini-first on agent; capped failover |
| 9 Caching + freshness | **Done** | Freshness gates LLM/retrieval cache; user isolation; no tool-result cache |
| 10 Guardrails | **Done** | Input/output layers; injection **14/14**; FP **26/26** in-scope |
| 11 Unified evals | **Done** | Catalog + offline suite + CI `--fail-on-regression`; no LLM-as-judge |
| 12 Observability / cost | **Done** | Spans, `/v1/ops/metrics` P50/P95/P99, token/USD budgets |
| 13 Reliability | **Done** | 401/403 not retried; LLM circuit; [`FAILURE_MATRIX.md`](FAILURE_MATRIX.md) |
| 14 Write tools + rate limits + readiness | **Done** | Confirmed publish/notify/delete; rate limiter; real `/ready`; `RUNBOOK.md` |
| 15 Context efficiency | **Done** | Canned meta, slim CORE_POLICY, paid-first failover, optional semantic router |
| 16 Routed efficiency | **Done** | Execution class + workflow cards; CORE not retrieved; reasoning off on how-tos |
| 16 Async workflows | **Later** | Job queue — not this drop |

Deep dive: [`phases/phase-16-routed-efficiency.md`](phases/phase-16-routed-efficiency.md) · [`phases/phase-15-context-efficiency.md`](phases/phase-15-context-efficiency.md) · [`phases/phase-14-write-tools-and-readiness.md`](phases/phase-14-write-tools-and-readiness.md)

## Phase 16 — what landed

- `execution_class` + `canonical_intent` on Request Understanding; lexical/semantic overlay
- High-confidence how-tos (`exam.publish`, share, archive, settings, …) render JSON
  workflow cards in `decide_turn` — 0 LLM, never `publish_exam`
- CORE.md skipped at ingest/query; unique-doc hybrid; publish vs lifecycle deduped
- OpenRouter `reasoning.enabled: false` on non-agent turns; `LLM_MAX_TOKENS_SIMPLE=128`
- Parent LangSmith `que.turn` + `que.route.*` tags; eval categories `intent` + `efficiency`
- Harness: `scripts/benchmark_efficiency.py` (offline default)

## Phase 15 — what landed

- Canned meta/capabilities; slim `CORE_POLICY`; selective UI; paid-first failover
- Optional `QUE_SEMANTIC_ROUTER`; assemble caps 4k/700; howto `max_tokens` 400
- Details: [`phases/phase-15-context-efficiency.md`](phases/phase-15-context-efficiency.md)

## Phase 14 — what landed

- Write tools `publish_exam` / `notify_students` / `delete_draft_exam` — propose (stores a
  `PendingAction`) then a tight yes/no on the next turn executes deterministically, outside
  the LLM/graph (`app/orchestration/pending_actions.py`, `app/tools/executor.py`)
- Excluded from the bounded agent loop everywhere; separate hourly write-action budget
- `ungrounded_number` output guard for every role (not just student cross-role)
- Lenient in-process rate limiter (`app/core/ratelimit.py`) on `/v1/chat[/stream]`
- `enforce_production_guards` also requires `LLM_API_KEY*` + `CORS_ALLOW_ORIGINS`
- Real `GET /ready` (LLM key, knowledge index, Quizzer tools reachability); `Dockerfile`
  healthcheck now hits it
- `docs/RUNBOOK.md` + `.env.staging.example`

## Phase 13 — what landed

- `_is_retryable` skips 400/401/403/404/422; keeps 408/429/5xx/timeouts
- LLM circuit `QUE_LLM_CIRCUIT_FAILURES` / `QUE_LLM_CIRCUIT_TTL_SECONDS`
- Failure matrix documented + `tests/test_reliability.py`

## Phase 12 — what landed

- `TurnTrace` spans (`app/obs/`); hashed `user_id`; no raw query in traces
- `GET /v1/ops/metrics` service-key only; `scripts/summarize_obs.py`
- Token usage + static USD table; `QUE_BUDGET_*` skip LLM with a capacity reply
- In-process `que_alert` windows (error-rate / USD-per-minute)

## Phase 11 — what landed

- Catalog `evals/catalog.json` (pointers, not a mega-JSON)
- `scripts/run_eval_suite.py --offline` prints **per-category** scores
- Baseline `evals/baselines/offline.json`; CI after pytest
- Heuristic groundedness (`app/evals/groundedness.py`)
- Sampled online JSONL (hashed user/query; default off)

## Phase 10 — what landed

- `app/guardrails/` input at `decide_turn`; Quizzer bait does not waive
- Retrieved chunks fenced as `RETRIEVED_DOCUMENT`; injection lines stripped from untrusted payloads
- Output scan on generate + after stream join; leaks not cached
- Red-team `evals/injection_cases.json` — **14/14**
- Kill switch `QUE_GUARDRAILS_ENABLED` (default true)

## Phase 9 — what landed

- Policy: `allow_llm_reply_cache` / `allow_retrieval_cache` (`app/orchestration/cache_policy.py`)
- LLM fingerprint always includes `uid:` (or `anon`); live/critical/tool turns skip reply cache
- Retrieval TTL map for product RAG (`QUE_CACHE_RETRIEVAL_TTL_SECONDS`)
- Isolation tests: User A vs B; anon vs named; critical bypass

## Phase 8 — what landed

- Config: `LLM_MODELS` + `LLM_API_KEY` / `LLM_API_KEY_N`; retry cap / backoff
- `ainvoke_chat` / `astream_chat` — one call site; logs `model` + `key_index` only
- Agent / `multi_step` prefers `openai/gpt-4o-mini` first, then the ring
- Stream failover only before the first token (no mixed-model SSE)
- Embeddings stay on the first configured key

## Phase 7 — what landed

- `runtime_mode`: knowledge | workflow | agent (`app/orchestration/runtime_mode.py`)
- Bounded loop: `QUE_AGENT_MAX_STEPS` / `QUE_TOOL_MAX_CALLS` / time / char cap
- Graph: `prepare → context → tools|agent|knowledge → generate`
- Partial answer + `AGENT_PARTIAL` on step/call/timeout/token stop
- Eval: `evals/agent_cases.json` + `scripts/run_agent_eval.py` — **7/7**

## Phase 6 — what landed

- Sparse corpus `bm25_corpus.json` written beside Chroma on ingest
- `app/knowledge/sparse.py` + `hybrid.py` (RRF); shared `assemble.py`
- Kill / tune: `QUE_RAG_HYBRID`, `QUE_RAG_CANDIDATE_K`, `QUE_RAG_RRF_K`
- Eval: `scripts/run_retrieval_eval.py --mode hybrid --latency`
- Neural cross-encoder **not** shipped (P95 / evidence)

## Phase 5 — what landed

Deep dive: [`phases/phase-05-policy.md`](phases/phase-05-policy.md) · matrix: [`CAPABILITY_MATRIX_V1.md`](CAPABILITY_MATRIX_V1.md)

## Phase 4 — what landed

- Contracts: [`TOOL_CONTRACTS_V1.md`](TOOL_CONTRACTS_V1.md)
- Quizzer: `POST /internal/que/v1/tools/invoke` (+ health) — service key + `X-Que-User-Id`, ownership checks
- QUE: `app/tools/` registry, deterministic selector, executor, Quizzer HTTP client
- LangGraph: `prepare → context → tools|knowledge → generate`
- Tool JSON injected as labeled `TOOL_RESULT` (untrusted for the LLM)
- Kill switch: `QUE_TOOLS_ENABLED` (default **false**); needs `QUIZZER_INTERNAL_BASE_URL`
- Eval: `evals/tool_cases.json` + `scripts/run_tool_eval.py` — selection accuracy **16/16**
- Unit: `tests/test_tool_select.py`; Quizzer auth: `backend/tests/test_que_internal_tools.py`
- Deep dive: [`phases/phase-04-tools.md`](phases/phase-04-tools.md)

### Enable locally

```
QUE_TOOLS_ENABLED=true
QUIZZER_INTERNAL_BASE_URL=http://127.0.0.1:8000
QUE_SERVICE_KEY=<same as Quizzer>
```

## Phase 3 — what landed

- `QueUiContext` on QUE `ChatRequest` + Quizzer `QueChatRequest`
- Frontend `buildQueUiContext(pathname)` attached on every SSE turn
- BFF `_upstream_payload` overwrites `user_role` from authenticated `User`
- Context injected as labeled `SystemMessage` JSON (never into user text)
- Precedence: explicit user wording → resolve → UI context → RAG / tools

## Phase 2 RAG (complete)

- Chunk → embed → Chroma at `QUE_CHROMA_PATH`
- CLI: `uv run python -m app.knowledge --force`
- Eval: `evals/retrieval_cases.json` + `scripts/run_retrieval_eval.py`
- Hybrid BM25 + RRF shipped in Phase 6 (cross-encoder still deferred)
