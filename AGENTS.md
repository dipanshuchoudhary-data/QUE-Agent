# Agent notes — QUE-Agent

- Separate from Quizzer. No Quizzer DB access. No importing Quizzer packages.
- Deploy as its own microservice. Browser chats QUE **directly** after Quizzer
  mints a short-lived Que access JWT (`POST /que/session`). Do **not** proxy
  chat/SSE through Quizzer Backend.
- Auth: `Authorization: Bearer <que_access>` (browser) **or** `X-Que-Service-Key`
  (server/ops). Never put the service key in the browser. Shared mint secret:
  `QUE_JWT_SECRET` on both services.
- Agent flow is LangGraph (`app/graphs/`): `prepare → knowledge → generate`.
- LLM access goes through `app/core/llm.py` (`ChatOpenAI` / LangChain).
- Identity lives only in `app/identity/` (thin persona). Product knowledge lives in `knowledge/`
  (domain folders + `manifest.json`) and is selected by `app/knowledge/retrieve.py`.
  **`knowledge/` is committed and copied into the Docker image** — without it, deployed QUE
  has no product brain. Update packs in git and redeploy to ship better answers.
- Knowledge rules: answer-oriented guides with click paths, decision trees, SAY/NEVER —
  not tab FAQ dumps or thin template stubs. See `knowledge/README.md`.
- CORE.md is always injected; up to `max_guides` (3) keyword-matched docs are added per turn
  (no embeddings yet). Frontmatter is stripped before injection.
- Common chit-chat / meta FAQs (hello, what can you do, what is Quizzer, …) use
  varied canned replies in `app/orchestration/canned.py` — do not call the LLM.
- Request Understanding (`app/orchestration/understanding.py`) classifies scope /
  intent / route **after** conversational resolve (`app/orchestration/resolve.py`).
  Hard out-of-scope (weather/coding/…) always refuses. Active Quizzer threads
  continue without requiring Quizzer keywords on every follow-up.
- QUE owns its own in-process TTL/LRU cache (`app/core/que_cache.py`) for FAQ
  intents, canned-variant rotation, and repeated LLM answers — never Quizzer Redis.
- Short-term memory: LangGraph `MemorySaver` on `dialog` turns, keyed by
  `conversation_id` (+ optional `user_id`). New chat = new `conversation_id`.
- Live account numbers require future tools, not markdown. Until tools exist,
  live-data routes return an honest “not available yet” reply (no invented counts).
- Use `uv` + Python 3.11. Prefer `uv sync --frozen` in CI/deploy.
