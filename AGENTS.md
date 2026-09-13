# Agent notes — QUE-Agent

- Phase writeups (what shipped, files, interview notes): `docs/phases/README.md`
- Separate from Quizzer. No Quizzer DB access. No importing Quizzer packages.
- Deploy as its own microservice. Browser chats QUE **directly** after Quizzer
  mints a short-lived Que access JWT (`POST /que/session`). Do **not** proxy
  chat/SSE through Quizzer Backend.
- Auth: `Authorization: Bearer <que_access>` (browser) **or** `X-Que-Service-Key`
  (server/ops). Never put the service key in the browser. Shared mint secret:
  `QUE_JWT_SECRET` on both services.
- Agent flow is LangGraph (`app/graphs/`): `prepare → context → tools|agent|knowledge → generate`.
  Runtime mode (`app/orchestration/runtime_mode.py`): most live asks are a **workflow**
  (one tool). Multi-intent asks enter a **bounded agent loop** (`agent_loop.py`) with
  step/call/time/char limits — not LLM ReAct. Partial answers on limit, never a hang.
- Insight tools (Phase 4): deterministic selector in `app/tools/` (not ReAct). Calls Quizzer
  `POST /internal/que/v1/tools/invoke` with `X-Que-Service-Key` + `X-Que-User-Id`.
  Kill switch: `QUE_TOOLS_ENABLED` (default false) + `QUIZZER_INTERNAL_BASE_URL`.
  Named-exam asks (`see my exam titled X`) use `lookup_my_exam` (title, not UUID).
  Contracts: `docs/TOOL_CONTRACTS_V1.md`. Tool JSON is labeled `TOOL_RESULT` for the LLM.
- Policy (Phase 5): `app/policy/` fail-closed role gate; Quizzer re-checks `User.role` on invoke.
  Matrix: `docs/CAPABILITY_MATRIX_V1.md`. UI context role is not authorization.
- Guardrails (Phase 10): `app/guardrails/` input scan at `decide_turn` (Quizzer bait does not
  waive injection) + output scan on generate/stream. Kill switch `QUE_GUARDRAILS_ENABLED`
  (default true). Retrieved/tool/UI blocks are untrusted data — never instructions.
  Red-team: `evals/injection_cases.json`.
- Unified evals (Phase 11): `evals/catalog.json` + `scripts/run_eval_suite.py --offline`.
  CI runs the suite with `--fail-on-regression` vs `evals/baselines/offline.json`.
  Per-category scores only. Heuristic groundedness in `app/evals/groundedness.py` — no
  LLM-as-judge. Optional sampled online JSONL (`QUE_EVAL_ONLINE_SAMPLE`) hashes user/query.
- Observability (Phase 12): `app/obs/` spans + in-process P50/P95/P99. `GET /v1/ops/metrics`
  is **service key only**. Token/USD budgets (`QUE_BUDGET_*`) skip LLM with a capacity reply.
  Never log raw query, emails, or exam answers. Script: `scripts/summarize_obs.py`.
  Optional LangSmith (dual-control): `LANGSMITH_TRACING` + `ALLOW_LANGSMITH_IN_PROD` in
  non-local; project **`Que_agent`**. Instrumented in `app/core/llm.py` (`@traceable`).
  Exports prompts when enabled — see `docs/RUNBOOK.md`.
  Context efficiency (Phase 15): canned meta/capabilities, slim CORE_POLICY, selective UI,
  paid-first failover, optional `QUE_SEMANTIC_ROUTER` — see
  `docs/phases/phase-15-context-efficiency.md`.
  Routed efficiency (Phase 16): execution_class + workflow cards for stable how-tos
  (0 LLM), CORE not retrieved, reasoning off on non-agent turns — see
  `docs/phases/phase-16-routed-efficiency.md`.
- Reliability (Phase 13): do **not** retry LLM 401/403/400. LLM circuit
  `QUE_LLM_CIRCUIT_*` (tools already have a breaker). Matrix: `docs/FAILURE_MATRIX.md`.
- Write tools (Phase 14): `publish_exam` / `notify_students` / `delete_draft_exam` are
  `risk_tier="write"` — always propose-then-confirm, never LLM-decided. Propose stores a
  `PendingAction` (`app/orchestration/pending_actions.py`, 5-min TTL, keyed like memory's
  thread id). A tight yes/no on the *next* turn (`pipeline.resolve_write_confirmation`,
  runs outside the graph/LLM) is the only thing that calls
  `app/tools/executor.execute_confirmed_write_action`. Deterministic success/cancel text,
  never LLM-paraphrased. Never chained in the bounded agent loop (`WRITE_TOOL_NAMES`
  excluded everywhere). Separate hourly cap `QUE_BUDGET_WRITE_ACTIONS_PER_HOUR`.
  Quizzer re-validates ownership/role and dedupes on `idempotency_key`.
- Rate limiting (Phase 14): lenient in-process token bucket per user/IP on
  `/v1/chat[/stream]` (`app/core/ratelimit.py`, `QUE_RATE_LIMIT_*`). Service-key callers
  are exempt (not end users).
- Production readiness (Phase 14): `enforce_production_guards` also requires
  `LLM_API_KEY*` + `CORS_ALLOW_ORIGINS` outside local/dev. `GET /ready` checks real
  dependencies (LLM key, knowledge index, Quizzer tools reachability); `GET /health`
  stays pure liveness. Runbook: `docs/RUNBOOK.md`.
- LLM access goes through `app/core/llm.py` (`get_chat_model` / `ainvoke_chat` /
  `astream_chat`). Chat round-robins `LLM_MODELS` + `LLM_API_KEY` / `LLM_API_KEY_N`
  with capped failover. Agent / `multi_step` turns try `LLM_MODEL` first
  when that id is in `LLM_MODELS`. Set both in `.env` — do not hardcode model ids.
  Embeddings stay on the first key. Logs use `model` + `key_index` — never raw keys.
- Identity lives only in `app/identity/` (thin persona). Product knowledge lives in `knowledge/`
  (domain folders + `manifest.json`). Runtime selection is hybrid RAG when enabled
  (`app/knowledge/` → Chroma dense + BM25 RRF at `QUE_CHROMA_PATH`) with keyword fallback
  in `retrieve.py`. Build/update index: `uv run python -m app.knowledge`. **`knowledge/` is committed and
  copied into the Docker image** — without it, deployed QUE has no product brain.
- Knowledge rules: answer-oriented guides with click paths, decision trees, SAY/NEVER —
  not tab FAQ dumps or thin template stubs. See `knowledge/README.md`.
- Knowledge injects a tiny CORE skeleton (or skips it when ≥2 RAG hits) plus dense/hybrid
  top-K chunks (or up to 2 keyword guides). Full CORE.md is **not retrieved** (`retrieve: false`).
  Below `QUE_RAG_MIN_SCORE` → honest no-answer (dense-gated even in hybrid).
  Frontmatter stripped. Hybrid: `QUE_RAG_HYBRID` (default true) + `bm25_corpus.json` from ingest.
  High-confidence static workflows use `knowledge/intents/*.json` cards (no RAG/LLM).
  `QUE_SEMANTIC_ROUTER` defaults on when an embedding key exists; fail-open to heuristics.
- UI context (Phase 3): Quizzer sends structured `context` (page/entity/role hint) each turn.
  Quizzer BFF overwrites `user_role` from the authenticated user. QUE injects it as a labeled
  system block — never concatenated into the user message. Precedence: explicit user wording
  → conversational resolve → UI context → RAG. Context is a UX hint, not authorization.
- Common chit-chat / meta FAQs (hello, what can you do, what is Quizzer, …) use
  varied canned replies in `app/orchestration/canned.py` — do not call the LLM.
- Request Understanding (`app/orchestration/understanding.py`) classifies scope /
  intent / route **after** conversational resolve (`app/orchestration/resolve.py`).
  Hard out-of-scope (weather/coding/…) always refuses. Active Quizzer threads
  continue without requiring Quizzer keywords on every follow-up.
- QUE owns its own in-process TTL/LRU cache (`app/core/que_cache.py`) for FAQ
  intents, canned-variant rotation, static how-to LLM replies, and retrieval.
  Freshness (`app/orchestration/cache_policy.py`) gates it: live/tool/critical
  turns never reuse an LLM reply. Keys for personalized replies always include
  `user_id` (or `anon`). Never Quizzer Redis.
- Short-term memory: LangGraph `MemorySaver` on `dialog` turns, keyed by
  `conversation_id` (+ optional `user_id`). New chat = new `conversation_id`.
- Live account numbers require tools (when enabled), not markdown invention.
  With tools off / Quizzer unreachable: honest “not available yet” (no invented counts).
- Use `uv` + Python 3.11. Prefer `uv sync --frozen` in CI/deploy.
