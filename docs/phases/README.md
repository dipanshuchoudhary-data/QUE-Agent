# QUE phase writeups (interview + codebase guide)

One markdown file per **shipped** handbook phase. Use these to:

1. **Understand the code** — which files belong to which upgrade, and what they do
2. **Explain in interviews** — problem → design choice → what you built → how you measured it
3. **Onboard yourself later** — without re-reading the whole repo

| File | Phase | Status |
|---|---|---|
| [phase-00-foundations.md](phase-00-foundations.md) | 0 Foundations | Done |
| [phase-01-que-core.md](phase-01-que-core.md) | 1 QUE Core + understanding + evals | Done |
| [phase-02-knowledge-rag.md](phase-02-knowledge-rag.md) | 2 Knowledge + dense RAG | Done |
| [phase-03-context-engineering.md](phase-03-context-engineering.md) | 3 UI context | Done |
| [phase-04-tools.md](phase-04-tools.md) | 4 Insight tools + secure execution | Done |
| [phase-05-policy.md](phase-05-policy.md) | 5 Identity + permissions + policy | Done |
| [phase-06-hybrid-retrieval.md](phase-06-hybrid-retrieval.md) | 6 Hybrid BM25 + RRF | Done |
| [phase-07-agent-runtime.md](phase-07-agent-runtime.md) | 7 Bounded agent loop | Done |
| [phase-08-llm-gateway.md](phase-08-llm-gateway.md) | 8 LLM gateway (RR + failover) | Done |
| [phase-09-caching.md](phase-09-caching.md) | 9 Caching + data freshness | Done |
| [phase-10-guardrails.md](phase-10-guardrails.md) | 10 Guardrails + AI security | Done |
| [phase-11-unified-eval.md](phase-11-unified-eval.md) | 11 Unified evaluation platform | Done |
| [phase-12-observability.md](phase-12-observability.md) | 12 Observability + cost | Done |
| [phase-13-reliability.md](phase-13-reliability.md) | 13 Reliability | Done |
| [phase-14-write-tools-and-readiness.md](phase-14-write-tools-and-readiness.md) | 14 Write tools (human-in-the-loop) + rate limits + production readiness | Done |
| [phase-15-context-efficiency.md](phase-15-context-efficiency.md) | 15 Context-efficient routing + slim prompts | Done |
| [phase-16-routed-efficiency.md](phase-16-routed-efficiency.md) | 16 Routed efficiency (cards + no-reasoning how-tos) | Done |

**You are next:** Phase 16 async workflows (job queue) — **Later**. Routed efficiency above is a pipeline upgrade, not the handbook async phase.

Related living docs:

- [`../FAILURE_MATRIX.md`](../FAILURE_MATRIX.md) — Phase 13 degraded-behavior rows
- [`../BUILD_PROGRESS.md`](../BUILD_PROGRESS.md) — short status table
- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — full file-by-file map
- [`../../AGENTS.md`](../../AGENTS.md) — rules for coding agents
- [`../que-agent-handbook.html`](../que-agent-handbook.html) — interactive roadmap
- [`../TOOL_CONTRACTS_V1.md`](../TOOL_CONTRACTS_V1.md) — Phase 4 tool API contracts

## How to use in an interview (30-second frame)

> “I built QUE as a separate microservice for Quizzer. I shipped it in gated phases: foundations and auth first, then scope/understanding, then RAG, then UI context, then read-only insight tools with a kill switch. Each phase had an eval gate so regressions were attributable. I deliberately did **not** jump to ReAct or write tools before ownership checks and deterministic selection were solid.”

Then open the phase file that matches the interviewer’s question (RAG vs tools vs auth).

## System shape after Phase 14

```text
Browser (Quizzer UI)
  → Quizzer BFF /que/chat/stream  (cookie auth, stamps user_id + role)
  → QUE /v1/chat/stream
       input guardrail (Quizzer bait does not waive jailbreak)
       decide_turn (resolve → understand → canned/refuse?)
       LangGraph: prepare → context → tools|agent|knowledge → generate
       knowledge: hybrid (dense + BM25 RRF) when indexed
       agent: bounded multi-tool loop when the ask is multi-intent
       generate/stream: LLM gateway + output guardrail (leaks not cached)
       obs: TurnTrace spans + in-process P50/P95/P99 + token/USD budgets
       cache: static how-tos only; live/tool/critical skip LLM reply cache
       SSE: meta → status* → token* → done
```

QUE never imports Quizzer packages or opens Quizzer’s DB. Live numbers only come through Quizzer’s internal tool HTTP API when `QUE_TOOLS_ENABLED=true`. Offline health: `uv run python scripts/run_eval_suite.py --offline --fail-on-regression`. Ops snapshot: `GET /v1/ops/metrics` with the service key. Failure matrix: [`../FAILURE_MATRIX.md`](../FAILURE_MATRIX.md).
