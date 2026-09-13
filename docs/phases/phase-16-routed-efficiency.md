# Phase 16 — routed efficiency (existing pipeline)

Ship compute that matches the ask. Keep LangGraph, canned, tools, and RAG.
Do **not** rebuild QUE as a multi-agent system.

Handbook **Phase 16 async workflows** stays **Later**. This file is the
engineering report for routed efficiency on the pipeline we already have.

## Problem

A static how-to such as `"how to published the draft exam"` still paid for:

1. Hybrid RAG (query embed + overlapping publish / lifecycle / CORE chunks)
2. One chat completion on a reasoning model (`nvidia/nemotron-3.5-lightning:free`)
   with thinking left on — LangSmith showed ~1.5k reasoning tokens and ~12s
3. Duplicate format rules (CORE_POLICY + TURN_STATE + howto piece + UI)

Phase 15 already slimmed identity and assemble caps. That was not enough:
CORE.md was still **retrieved** from Chroma, and every knowledge turn called
the reasoning model.

## What we shipped

Cheap first, then proportional generate:

```text
decide_turn
  guardrail / canned / OOS / write-confirm     → Tier 0 (0 LLM)
  high-confidence workflow card               → Tier 0 (0 LLM)
  simple_knowledge                             → RAG 1 unique doc + no reasoning, max_tokens 128
  complex_knowledge                            → RAG 2–3 unique docs + no reasoning, max_tokens 300
  tool_required / agent / multi_step          → existing tools + reasoning allowed
```

Internal routing object (never sent to the LLM as JSON):
`execution_class`, `canonical_intent`, `confidence` on `RequestUnderstanding`.

### Files

| Area | Path |
|---|---|
| Execution class + lexical overlay | `app/orchestration/intent_catalog.py`, `understanding.py` |
| Prototypes (ids **are** canonical intents) | `app/orchestration/intent_prototypes.json` |
| Workflow cards | `knowledge/intents/*.json` |
| Prompt packs | `app/orchestration/prompt_pack.py` |
| Shared query embed | `app/knowledge/query_embed.py` |
| Reasoning / token budgets | `app/core/llm.py` (`extra_body.reasoning`, `LLM_MAX_TOKENS_SIMPLE`) |
| Parent LangSmith run | `pipeline._langsmith_turn` → `que.turn` + `que.route.*` tags |
| Offline harness | `evals/efficiency_cases.json`, `scripts/benchmark_efficiency.py` |

Write tools stay propose-then-confirm. `"Publish this exam"` is still
`tool_required`. `"How do I publish"` is **not** `publish_exam`.

## Before / after (offline harness)

`evals/baselines/efficiency_before.json` is a **reconstructed** Phase-15 snapshot
(routing landed in the same change set as the harness). After numbers are
from `uv run python scripts/benchmark_efficiency.py --write-after`.

| Ask | Before | After (offline) |
|---|---|---|
| `"How do I publish an exam?"` (and grammar/paraphrase siblings) | RAG + 1 LLM, ~2189 prompt chars, reasoning on | `workflow:exam.publish`, **0 LLM**, ~224 chars |
| Simple how-to set (exact/paraphrase/grammar) | 0 / 15 zero-LLM | **15 / 15** zero-LLM |
| All efficiency cases | ~28 / 31 would call LLM | **20 / 31** zero-LLM (cards + canned + OOS) |
| Comparison / troubleshooting | RAG + reasoning | Still LLM, reasoning **off**, 1–3 unique docs |
| `"Publish this exam"` | write-tool | unchanged `tool_required` |

Do **not** claim sub-2s wall time until `--live` is re-run. First process
start still embeds intent prototypes when `QUE_SEMANTIC_ROUTER=true` and a
key exists (cached for later turns).

Keyword retrieval eval **34/34**. Scope **42/42**. Intent **31/31**.
Efficiency zero-LLM rate **20/20** expected skips.

## Retrieval

- CORE.md is listed but `retrieve: false` — not ingested, filtered at query time
- At most one chunk per `doc_id`; `simple_knowledge` top_k=1
- Publish how-to stays in `publishing-and-sharing.md`; lifecycle keeps the
  state machine and points at `exam.publish`
- Keyword fallback uses the matching section, not the whole file

Rebuild the index when embeddings are configured:

```bash
uv run python -m app.knowledge --force
```

Query-time `doc_id != core` covers a stale local Chroma until that rebuild.

## Model tiers

Same `LLM_MODELS` pool. No new model id.

- Non-agent knowledge: `extra_body={"reasoning": {"enabled": false, "effort": "none"}}`
- Agent / `multi_step` / `tool_required`: reasoning allowed
- `LLM_MAX_TOKENS_SIMPLE=128`, howto 128, moderate 300, complex/agent 700

## Remaining bottlenecks

- Comparison and diagnostic asks still assemble ~1.7–2.3k prompt chars (skeleton + packs)
- First turn in a process embeds prototypes (semantic overlay) when a key is set
- Live latency / reasoning-token proof needs `scripts/benchmark_efficiency.py --live`
- No cross-encoder (Phase 6 deferral still holds)

## How to measure

```bash
uv run pytest
uv run python scripts/run_eval_suite.py --offline --fail-on-regression
uv run python scripts/benchmark_efficiency.py
uv run python scripts/benchmark_efficiency.py --live   # needs LLM keys
```

LangSmith project `Que_agent`: parent run `que.turn` tagged
`que.route.deterministic|simple|complex|tool`. How-to cards should **not**
show a generate span.
