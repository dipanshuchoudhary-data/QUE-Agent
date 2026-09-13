# QUE context-efficiency — Wave 1–4 measurement notes

## Baseline problem (LangSmith)

Ask: "What can you help me with in Quizzer?"
Path before fix: knowledge → generate ~120s on free-tier failover
(3 × ~45s timeouts), large CORE + UI + identity stack.

## Wave 1 fixes

- Capabilities canned + meta regex covers `help me with` / `in Quizzer`
- Classifier `canned_eligible` fallthrough → canned (no LLM)
- Meta/chitchat skip CORE+RAG
- Non-agent `LLM_MAX_ATTEMPTS_NON_AGENT=2`, paid models first
- Removed duplicate pre-graph `select_knowledge`

## Wave 2

- Slim CORE_POLICY identity (~v2.0.0)
- Compact TURN_STATE; no duplicate follow-up HumanMessage
- Selective compact UI context
- Shorter knowledge preamble; CORE cap 4.5k
- Tighter history for standalone asks; task `max_tokens` tiers

## Wave 3

- `intent_prototypes.json` + `semantic_router.py` (embedding cosine)
- Flag: `QUE_SEMANTIC_ROUTER` (default false until embeddings configured)
- Compact state fields: active_topic, previous_intent, …

## Wave 4 ops

LangSmith metadata on generate spans: route, runtime_mode, input_chars,
knowledge_used, ui_injected, fallback. Local/staging stay **free-only**
(`LLM_MODELS` Nemotron `:free`). Do not pin paid models.

## Wave 5 — token/latency (local)

- `QUE_CHROMA_PATH=data/chroma` (not `/app/data/chroma`); rebuild index locally
- Keyword / `dense_unavailable_keyword` go through `assemble_selection` (≤4k chars)
- Identity 2.2.0: tiny `CORE_POLICY` + conditional pieces (howto/knowledge/tools/…)
- Skip embed when index missing; `QUE_RAG_TOP_K` default 2
- Dedupe latest user turn vs TURN_STATE when older history remains

Local measure for `"How do I publish an exam?"` after Wave 5:

| Field | Before | After |
|---|---|---|
| knowledge mode | `dense_unavailable_keyword` | `hybrid` |
| knowledge chars | ~14,219 | ~1,585 |
| `prepare_turn` chars | ~15,634 | ~2,189 (~550 tok) |

## How to measure

1. Offline: `uv run python scripts/run_eval_suite.py --offline --fail-on-regression`
2. Manual: ask "What can you help me with in Quizzer?" → expect `model=canned`, sub-second
3. LangSmith project `Que_agent`: meta asks should not show 120s generate parents
4. Compare obs: `GET /v1/ops/metrics` p50/p95 `spans.llm` before/after deploy

## Target direction

| Metric | Direction |
|--------|-----------|
| LLM calls / meta ask | → 0 |
| Input chars / how-to | ↓ substantially |
| p95 generate latency | ↓ substantially |
| Routing accuracy (scope eval) | hold ≥ threshold |
