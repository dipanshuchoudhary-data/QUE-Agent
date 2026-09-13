# QUE-Agent — architecture & file-by-file guide

This document explains how QUE is structured, how chat connects to Quizzer, and what every important file does.

**Current phase:** LangGraph chat (`prepare → context → tools|agent|knowledge → generate`) + product knowledge packs + UI context + optional insight tools (`QUE_TOOLS_ENABLED`) + bounded multi-tool loop (Phase 7) + LLM gateway (Phase 8) + freshness-gated cache (Phase 9) + input/output guardrails (Phase 10) + unified offline eval suite (Phase 11) + in-process observability/cost (Phase 12) + tested failure matrix (Phase 13) + confirmed write tools + rate limiting + production readiness guards (Phase 14).  
No Quizzer DB access from QUE. Tools call Quizzer internal HTTP APIs only.

---

## Big picture

QUE is an **independently deployable microservice**. It does **not** import Quizzer packages and does **not** talk to Quizzer’s database.

Chat traffic does **not** proxy through Quizzer Backend (that would load Quizzer with every SSE token). Quizzer only mints a short-lived access token after cookie auth; the browser then calls QUE directly.

```text
┌─────────────┐  cookie JWT   ┌──────────────────┐
│ Quizzer UI  │ ────────────► │ Quizzer Backend  │
│ (browser)   │  POST /que/session               │
│             │ ◄──────────── │ mints Que JWT    │
└──────┬──────┘               └────────┬─────────┘
       │                               │
       │  Authorization: Bearer        │  QUE → Quizzer (tools, flag on)
       │  POST /v1/chat/stream         │  X-Que-Service-Key + X-Que-User-Id
       ▼                               │  POST /internal/que/v1/tools/invoke
┌─────────────┐                        │
│  QUE-Agent  │ ───────────────────────┘
│   :8100     │ ────────────────────────► LLM
└─────────────┘
```

| Rule | Why |
|---|---|
| Browser → QUE for chat | Offload Quizzer; lower latency for streaming |
| Quizzer → mint only (`/que/session`) | Proves the user is logged in; light/rare request |
| Shared `QUE_JWT_SECRET` | QUE verifies tokens Quizzer minted |
| `QUE_SERVICE_KEY` never in browser | Server/ops + QUE→Quizzer tools only |
| History sent each turn | QUE is **stateless** (no chat DB; MemorySaver is in-process) |
| `user_id` opaque | From JWT `sub` / request body — Quizzer re-checks ownership on tools |

Deploy shape: `app.quizzer…` (frontend/API) and `que.quizzer…` (this service). Set QUE `CORS_ALLOW_ORIGINS` to the frontend origin(s).

---

## Auth (two credentials)

Full product A→Z (Quizzer workspace + attempt + QUE, expiries, re-login): **[AUTH.md](AUTH.md)**.  
Phased build roadmap (open in browser): **[docs/que-agent-handbook.html](docs/que-agent-handbook.html)**.

Either is enough on `/v1/*`:

1. **`Authorization: Bearer <token>`** — `typ=que_access`, `aud=que-agent`, `iss=quizzer`, signed with `QUE_JWT_SECRET`
2. **`X-Que-Service-Key`** — shared service secret (internal callers; used by Quizzer BFF on `feat/que-agent-wip`)

Token mint (Quizzer, when token-exchange is wired): `create_que_access_token`  
Token verify (QUE): `app/core/tokens.py` → `decode_que_access_token`  
HTTP gate (QUE): `app/core/security.py` → `require_chat_auth`

---

## Request path (one chat turn)

```text
Browser already holds Que access_token (from POST /que/session)

POST /v1/chat  or  POST /v1/chat/stream
        │
        ▼
app/api/chat.py                 # HTTP + require_chat_auth
        │
        ▼
app/services/chat_service.py    # complete vs SSE framing
        │
        ▼
app/orchestration/pipeline.py
  decide_turn → Request Understanding (scope/intent/route)
       ├─ refuse / clarify / canned  → early reply (no LLM)
       └─ dialog → LangGraph
              prepare  → sanitize history + inject identity
              context  → labeled QUIZZER_UI_CONTEXT (Phase 3)
              route    → tools (insight) | knowledge (RAG)
              generate → LLM reply (TOOL_RESULT and/or packs grounded)
        │
        ▼
ChatResponse  or  SSE: meta(+understanding) → token* → done
```

Quizzer Backend is **not** on the chat SSE path after the session mint.
When `QUE_TOOLS_ENABLED=true`, QUE may call Quizzer `/internal/que/v1/tools/*` mid-turn.

Golden scope eval: `evals/scope_golden.json` · `uv run python scripts/run_scope_eval.py`  
Tool selection eval: `evals/tool_cases.json` · `uv run python scripts/run_tool_eval.py`  
Build tracker: [`docs/BUILD_PROGRESS.md`](docs/BUILD_PROGRESS.md) · handbook: [`docs/que-agent-handbook.html`](docs/que-agent-handbook.html)
Contracts: [`docs/TOOL_CONTRACTS_V1.md`](docs/TOOL_CONTRACTS_V1.md)

---

## Repo tree

```text
Que-Agent/
├── AGENTS.md                 # Short rules for coding agents
├── ARCHITECTURE.md           # This file
├── README.md                 # Quick start & endpoints
├── pyproject.toml            # Package + deps + ruff/pytest
├── uv.lock                   # Locked deps (CI uses --frozen)
├── Dockerfile                # Production image
├── .env.example              # Config template
├── .github/workflows/ci.yml  # Secret scan + lint + audit + tests
├── scripts/start.sh          # gunicorn + uvicorn workers
├── app/                      # Python service
│   ├── run.py                # Local entry: python -m app.run
│   ├── main.py               # FastAPI app factory
│   ├── api/                  # HTTP routers
│   ├── core/                 # Config, auth, LLM, errors
│   ├── schemas/              # Request/response models
│   ├── services/             # Thin HTTP service layer
│   ├── orchestration/        # Pipeline + history helpers
│   ├── graphs/               # LangGraph agent
│   ├── identity/             # Thin persona (who QUE is)
│   └── knowledge/            # Pack selection code
├── knowledge/                # Markdown product brain (data)
│   ├── CORE.md
│   ├── manifest.json
│   ├── README.md
│   └── guides/*.md
└── tests/                    # pytest
```

---

## Layer map (who owns what)

| Layer | Folder | Responsibility |
|---|---|---|
| HTTP | `app/api/` | Routes, status codes, SSE response headers |
| Service | `app/services/` | SSE framing, call pipeline |
| Orchestration | `app/orchestration/` | Map request ↔ graph; history sanitize |
| Agent | `app/graphs/` | `prepare → context → tools\|agent\|knowledge → generate` |
| Tools | `app/tools/` | Registry, selector, executor, Quizzer client |
| Policy | `app/policy/` | Fail-closed role gate (Phase 5) |
| Guardrails | `app/guardrails/` | Input/output scans (Phase 10); not a policy replacement |
| Observability | `app/obs/` | Spans, cost, in-process percentiles, budgets (Phase 12) |
| Rate limiting | `app/core/ratelimit.py` | In-process token bucket per user/IP (Phase 14) |
| Evals | `app/evals/` | Groundedness heuristic, suite scoring, online sampler |
| Identity | `app/identity/` | Short system prompt / persona metadata |
| Knowledge code | `app/knowledge/` | Select which markdown packs to inject |
| Knowledge data | `knowledge/` | Product guides (not Python) |
| Core | `app/core/` | Settings, service-key auth, LLM factory, public errors |
| Schemas | `app/schemas/` | Pydantic contracts for chat |

---

## File-by-file — application (`app/`)

### Entrypoints

#### `app/run.py`
Local/dev launcher. Loads settings and starts **uvicorn** on `HOST`/`PORT` (default `8100`), with reload in local env.

```bash
uv run python -m app.run
```

#### `app/main.py`
FastAPI factory (`create_app`):

- Lifespan logging (env, version, model, insecure-auth flag)
- CORS for Quizzer frontend origins (`CORS_ALLOW_ORIGINS`) so browser → QUE works
- Mounts `health` + `chat` + `ops` routers
- Docs (`/docs`) only when `APP_ENV` is local/dev

Exports module-level `app` for gunicorn/uvicorn.

---

### HTTP API — `app/api/`

#### `app/api/health.py`
- `GET /health` — no auth  
- Returns `{ status, service, version, env }`  
- Used by Docker `HEALTHCHECK` and load balancers

#### `app/api/ops.py`
- `GET /v1/ops/metrics` — **service key only** (a Que JWT is 401)
- In-process P50/P95/P99, cost, `alerts[]`. Not Grafana.

#### `app/api/chat.py`
All routes under `/v1` require `require_chat_auth` (Bearer Que JWT **or** service key).  
JWT `sub` is copied into `user_id` when the client omits it.

| Endpoint | What it does |
|---|---|
| `GET /v1/identity` | Persona metadata (no LLM) |
| `POST /v1/chat` | Full reply via `chat_service.chat_complete` |
| `POST /v1/chat/stream` | SSE stream via `chat_service.chat_stream_events` |

Maps `ValueError` → 400, `LLMError` → 503 (not configured) or 502 (upstream fail).

---

### Schemas — `app/schemas/`

#### `app/schemas/chat.py`
Pydantic contracts:

- `ChatMessage` — `role` ∈ `system|user|assistant`, content 1–32k chars (stripped)
- `QueUiContext` — structured page/entity/role (Phase 3 UX hint; not auth)
- `ChatRequest` — `messages` (1–100), optional `conversation_id`, optional opaque `user_id`, optional `context`
- `ChatResponse` — assistant `message` + `conversation_id` + `model`

Client-sent `system` messages are **dropped** later in `sanitize_history` so callers cannot override identity.

#### Context precedence (Phase 3)

Highest first:

1. Explicit user wording (named exam/id in the message)
2. Conversational resolve (`resolved_query` / topic)
3. Structured `QueUiContext` (page / entity / server-stamped role)
4. Retrieved knowledge packs

UI context is injected as a labeled `SystemMessage` (`QUIZZER_UI_CONTEXT`), never concatenated into the user message. Quizzer BFF overwrites `user_role` from the authenticated User before QUE sees it.

---

### Core — `app/core/`

#### `app/core/config.py`
`pydantic-settings` `Settings` from env / `.env`:

- App: `APP_ENV`, name, version, CORS (frontend origins for browser → QUE)
- Auth: `QUE_JWT_SECRET` (+ algo/aud/iss), `QUE_SERVICE_KEY`, `ALLOW_INSECURE_LOCAL_NO_AUTH`
- LLM: `LLM_API_KEY` / `LLM_API_KEY_N`, `LLM_MODELS` (or `LLM_MODEL`), gateway retry/backoff, temperature
- LLM gateway (Phase 8): `LLM_GATEWAY_RR`, `LLM_MAX_ATTEMPTS`, `LLM_RETRY_BASE_MS`, `LLM_RETRY_CAP_MS`
- Cache (Phase 9): `QUE_CACHE_*` TTLs including `QUE_CACHE_RETRIEVAL_TTL_SECONDS`; freshness policy skips live/tool replies
- Memory: `QUE_MEMORY_ENABLED`, `QUE_MEMORY_MAX_TURNS` (LangGraph MemorySaver)
- Tools (Phase 4): `QUE_TOOLS_ENABLED`, `QUIZZER_INTERNAL_BASE_URL`, tool timeouts/circuit
- Agent loop (Phase 7): `QUE_AGENT_MAX_STEPS`, `QUE_AGENT_MAX_EXECUTION_MS`, `QUE_AGENT_MAX_TOOL_CHARS`
- Guardrails (Phase 10): `QUE_GUARDRAILS_ENABLED` (default true)
- Online eval sample (Phase 11): `QUE_EVAL_ONLINE_SAMPLE`, `QUE_EVAL_ONLINE_RATE`, `QUE_EVAL_ONLINE_PATH`
- Observability (Phase 12): `QUE_OBS_*`, `QUE_BUDGET_*`, `QUE_ALERT_*`
- Reliability (Phase 13): `QUE_LLM_CIRCUIT_FAILURES`, `QUE_LLM_CIRCUIT_TTL_SECONDS`
- Server: host, port, log level

**Production guards:** insecure no-auth forbidden outside local; weak JWT/service secrets rejected.  
`get_settings()` is `@lru_cache`’d.

#### `app/core/tokens.py`
Decode/verify Quizzer-minted Que access JWTs (`typ=que_access`, audience/issuer checks).

#### `app/core/security.py`
`require_chat_auth`:

1. Prefer `Authorization: Bearer` → `decode_que_access_token`
2. Else `X-Que-Service-Key` (constant-time compare)
3. Local escape hatch: `ALLOW_INSECURE_LOCAL_NO_AUTH=true` only when `is_local`

Browser never receives the service key.

`require_service_key_only`: ops metrics — service key only; a valid Que JWT is still 401.

#### `app/core/llm.py`
- `LLMError` — normalized failure type
- `get_chat_model()` — builds LangChain `ChatOpenAI` for one gateway lane (OpenRouter by default)
- `ainvoke_chat()` / `astream_chat()` — round-robin keys + models, capped failover with backoff
- **Not retryable:** 400/401/403/404/422. Retryable: 408/429/5xx/timeouts
- LLM circuit (`QUE_LLM_CIRCUIT_FAILURES` / `QUE_LLM_CIRCUIT_TTL_SECONDS`); open → `LLMError` → public try-again
- Records `usage_metadata` (prompt/completion tokens) for Phase 12 cost
- Agent / `complexity=multi_step` prefers `LLM_MODEL` first (when it is in `LLM_MODELS`), then the rest of the pool
- Logs `model`, `key_index`, `attempt`, `fallback` — never the API key
- Embeddings (`app/knowledge/embeddings.py`) stay on the first configured key

Call sites: `generate_node` and `stream_turn_events`. Do not construct `ChatOpenAI` elsewhere.

#### `app/core/que_cache.py`
In-process TTL/LRU (not Quizzer Redis): FAQ intents, canned variants, static how-to LLM replies, product retrieval. Phase 9 policy (`app/orchestration/cache_policy.py`) skips LLM/retrieval cache on live/tool/critical turns. LLM keys always include `user_id` or `anon`.

#### `app/core/errors.py`
Maps exceptions to **stable public codes** (no provider stack traces):

| Code | Meaning |
|---|---|
| `llm_not_configured` | Missing `LLM_API_KEY` |
| `llm_empty_response` | Model returned empty |
| `llm_unavailable` | Generic upstream failure |
| `bad_request` | Validation / empty history |

---

### Services — `app/services/`

#### `app/services/chat_service.py`
Thin HTTP-facing layer over the pipeline:

- `chat_complete` → `pipeline.complete`
- `chat_stream_events` → SSE JSON events:
  1. `meta` (conversation_id, model, identity)
  2. `token` chunks from `stream_tokens`
  3. `done`
  - If stream yields zero tokens / fails → **one** fallback to non-stream `complete`, then fake-chunk the text so the UI still “streams”
  - On total failure → `error` event with public code/message

---

### Orchestration — `app/orchestration/`

#### `app/orchestration/history.py`
`sanitize_history`:

1. Keep only `user` / `assistant` (strip client `system`)
2. Cap to last ~16 messages
3. Cap ~10k characters from the end (preserve recent turns)
4. Guarantee at least one user message remains

Protects latency/cost and identity integrity.

#### `app/orchestration/runtime_mode.py` / `agent_loop.py`
Phase 7 — explicit `knowledge|workflow|agent` routing and a bounded multi-tool loop
(`QUE_AGENT_MAX_STEPS`, `QUE_TOOL_MAX_CALLS`, wall clock, TOOL_RESULT char cap).

#### `app/guardrails/`
Phase 10 — layered checks on top of Phase 5 policy (not a replacement). `input.py` runs at the start of `decide_turn`; Quizzer wording does not waive a jailbreak. `output.py` scans the finished reply in `generate_node` and after stream join (leaked text is not cached). `sanitize.py` drops injection lines from retrieved/tool payloads only.

#### `app/orchestration/pipeline.py`
Bridge between HTTP schemas and LangGraph:

| Function | Role |
|---|---|
| `_request_to_input` | Build initial `QueGraphState` |
| `prepare_turn` | Run prepare→context→(tools\|agent\|knowledge) without LLM (tests) |
| `complete` | `graph.ainvoke` → extract last AI text → `ChatResponse` |
| `stream_tokens` | Same prepare path as graph, then `model.astream` |

Streaming reuses the same prepare/context/tools-or-agent-or-knowledge path as non-stream, then streams tokens directly (not the compiled `generate` node).

---

### LangGraph agent — `app/graphs/`

#### `app/graphs/state.py`
`QueGraphState` TypedDict shared across nodes:

| Field | Purpose |
|---|---|
| `input_messages` | Raw role/content from HTTP |
| `dialog` | Short-term user/assistant turns (checkpointed) |
| `messages` | Ephemeral prompt for this turn (identity + context + tools/knowledge + dialog) |
| `sources_used` | Audit tags (`identity`, `memory`, `context`, `tools`, `knowledge`, `llm`, …) |
| `conversation_id` / `user_id` | Thread key for MemorySaver (`user_id:conversation_id`) |
| `identity_version` | Bumped with persona changes |
| `knowledge_packs` | Pack ids injected this turn |
| `memory_turns` | Length of `dialog` after merge/append |
| `model_name` | From generate |
| `ui_context` | Phase 3 structured page/entity/role |
| `tool_name` / tool meta | Phase 4 last tool call audit |

#### `app/graphs/memory.py`
In-process LangGraph `MemorySaver` helpers: thread ids, dialog merge/trim, enable flag
(`QUE_MEMORY_ENABLED`, `QUE_MEMORY_MAX_TURNS`). Memory is per worker process — not shared
across replicas (swap checkpointer for Postgres/Redis later if needed).

#### `app/graphs/que_graph.py`
Builds and compiles:

```text
START → prepare → context → tools|agent|knowledge → generate → END
```

Conditional after `context`: `runtime_mode` is `knowledge` | `workflow` | `agent`. Workflow is one tool; agent is a bounded multi-tool loop.

`get_que_graph()` is process-cached (`@lru_cache`) and compiled **with** `MemorySaver` when
memory is enabled. Pass `config={"configurable": {"thread_id": ...}}` so `dialog` persists.

#### `app/graphs/nodes.py`
Nodes (one job each):

1. **`prepare_node`** (sync)  
   Merge checkpoint `dialog` with incoming turn → build prompt from memory → prepend identity.

2. **`context_node`** (sync)  
   If `ui_context` present → insert labeled `QUIZZER_UI_CONTEXT` system message.

3. **`tools_node`** (async, Phase 4)  
   Deterministic select → execute via Quizzer internal API → inject labeled `TOOL_RESULT` (or clarify / soft-fail).

4. **`knowledge_node`** (sync)  
   Dense RAG (+ keyword fallback) → insert knowledge system message → record pack ids.

5. **`generate_node`** (async)  
   Budget gate → `ainvoke_chat(...)` → append `AIMessage` to `dialog` + prompt → record the lane's `model`. Capacity reply if the turn token/call/USD budget would be exceeded.

---

### Observability — `app/obs/` (Phase 12)

| Module | Role |
|---|---|
| `trace.py` | `TurnTrace` spans; hashed `user_id` |
| `metrics.py` | In-process ring, P50/P95/P99, `que_alert` windows |
| `cost.py` | Token usage extract + static USD table |
| `budget.py` | Skip LLM when turn/user caps trip |
| `context.py` | Bind `request_id` + current trace |

Failure matrix (Phase 13): [`docs/FAILURE_MATRIX.md`](docs/FAILURE_MATRIX.md).

---

### Tools — `app/tools/` (Phase 4)

| Module | Role |
|---|---|
| `registry.py` | Read-only insight tool specs (including title lookup) |
| `select.py` | Deterministic keyword + page selector (not LLM tool-calling) |
| `executor.py` | Timeout, MAX_TOOL_CALLS, circuit, kill switch |
| `quizzer_client.py` | HTTP to Quizzer `/internal/que/v1/tools` |

Eval gate: selection accuracy ≥ 85% (`scripts/run_tool_eval.py`).

Phase 7: `exclude_tools` on the selector; `invoke_tool_selection` for a single HTTP call; `QUE_TOOL_MAX_CALLS` enforced.

---

### Identity — `app/identity/`

#### `app/identity/persona.py`
Thin persona — **not** product docs:

- `IDENTITY_VERSION` — bump when identity text changes meaningfully
- `build_system_prompt()` — short rules: who QUE is, use packs privately, plain text, ground on TOOL_RESULT when present
- `identity_metadata()` — `{ name, product, identity_version, phase }` for clients/logs

#### `app/identity/__init__.py`
Re-exports persona helpers.

---

### Knowledge selection — `app/knowledge/`

#### `app/knowledge/retrieve.py`
Runtime selection: **hybrid** (dense + BM25 RRF) when `QUE_RAG_HYBRID` and
`bm25_corpus.json` exist; else dense Chroma; else keyword fallback on `manifest.json`.
CORE.md is listed but not retrieved (`retrieve: false`); a tiny skeleton is used only when RAG is thin. Below `QUE_RAG_MIN_SCORE` → honest no-answer (dense-gated).

#### `app/knowledge/hybrid.py` / `sparse.py` / `assemble.py`
Phase 6 — BM25 sidecar, reciprocal rank fusion, shared CORE+chunk assembly.

#### `app/knowledge/dense.py` / `ingest.py` / `store.py`
Phase 2 — embed, Chroma upsert/query; ingest also writes `bm25_corpus.json`.

#### `app/knowledge/__init__.py`
Exports `select_knowledge`, `KnowledgeSelection`, `clear_knowledge_caches`.

---

## File-by-file — knowledge data (`knowledge/`)

This folder is the **product brain**. Code in `app/knowledge/` only selects and injects it.

| File | Role |
|---|---|
| `knowledge/README.md` | How to write guides (SAY/NEVER, click paths) |
| `knowledge/CORE.md` | Product map — **not retrieved**; skeleton only if RAG is thin |
| `knowledge/manifest.json` | Pack index: paths, `always`, keywords, `max_guides` |
| `knowledge/guides/navigation.md` | Sidebar vs exam tabs / where things live |
| `knowledge/guides/publish-share.md` | Create → approve → publish → link window |
| `knowledge/guides/empty-data.md` | Empty Students / Analytics / Dashboard |
| `knowledge/guides/live-monitoring.md` | LIVE, Monitoring, Results |
| `knowledge/guides/lifecycle.md` | End-to-end graded loop (also keyword fallback) |
| `knowledge/guides/verification.md` | Pre-exam identity form (not grading) |
| `knowledge/guides/arena.md` | Arena ≠ graded exam |

Guide style: teacher question → click path → decision tree → **SAY** / **NEVER**.  
Live counts (“how many students…”) must wait for future tools — guides must not invent them.

---

## File-by-file — tests (`tests/`)

| File | Covers |
|---|---|
| `tests/conftest.py` | Env defaults, clear settings/graph caches, `TestClient` |
| `tests/test_health.py` | `/health` |
| `tests/test_chat.py` | Service-key + Que JWT auth, validation, stream without LLM key |
| `tests/test_graph.py` | Graph topology / nodes |
| `tests/test_pipeline.py` | prepare/complete/stream wiring |
| `tests/test_knowledge.py` | Keyword selection, manifest health, caches |

Tests avoid live LLM calls where possible; CI runs with empty `LLM_API_KEY` / `LLM_API_KEY_N`.

---

## File-by-file — ops & tooling

| File | Role |
|---|---|
| `pyproject.toml` | Package metadata, runtime deps (FastAPI, LangGraph, LangChain…), ruff, pytest |
| `uv.lock` | Locked dependency graph — deploy/CI: `uv sync --frozen` |
| `.env.example` | Documented env vars (copy to `.env`) |
| `Dockerfile` | Multi-stage: uv sync → non-root `que` user → gunicorn via `start.sh` |
| `scripts/start.sh` | `gunicorn app.main:app` + `UvicornWorker`, `WEB_CONCURRENCY` workers |
| `.github/workflows/ci.yml` | gitleaks → `uv sync --frozen` → ruff → pip-audit → pytest |
| `.gitleaks.toml` | Secret-scan config |
| `AGENTS.md` | Short agent rules (separate from Quizzer, graph shape, knowledge rules) |
| `README.md` | Human quick start + integration sketch |

---

## Auth & config cheat sheet

| Concern | Mechanism |
|---|---|
| Quizzer user → Quizzer Backend | Cookie JWT |
| Quizzer Backend → mint Que token | `POST /que/session` + shared `QUE_JWT_SECRET` |
| Browser → QUE chat | `Authorization: Bearer <que_access>` + CORS origins |
| Server/ops → QUE | `X-Que-Service-Key` |
| QUE → Quizzer tools | `X-Que-Service-Key` + `X-Que-User-Id` → `/internal/que/v1/tools` |
| Local docs without key | `ALLOW_INSECURE_LOCAL_NO_AUTH=true` + local env only |
| LLM | `LLM_API_KEY` / `LLM_API_KEY_N` + OpenAI-compatible `LLM_BASE_URL`; chat pool `LLM_MODELS` |
| Insight tools kill switch | `QUE_TOOLS_ENABLED` + `QUIZZER_INTERNAL_BASE_URL` |

---

## What is intentionally out of scope (for now)

- Quizzer DB / ORM imports inside QUE
- Durable multi-worker conversation store (current MemorySaver is in-process / per worker)
- Write / mutate Quizzer tools (V1 is read-only insight only)
- LLM ReAct / planning loops / multi-agent (Phase 17)
- Proxying chat/SSE through Quizzer Backend (avoided on purpose)

Those land later as new graph nodes / tools, without collapsing identity and knowledge into one blob.

---

## Mental model (one sentence)

**Quizzer proves the user once and mints a Que JWT; the browser streams chat straight to QUE; each turn runs LangGraph with short-term `dialog` memory, injects persona + UI context + either insight TOOL_RESULT (workflow or bounded agent loop) or RAG packs, and asks the LLM for a plain-text answer.**
