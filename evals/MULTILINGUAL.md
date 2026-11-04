# Hinglish and informal-query reliability

Status: provisional. The case set (`evals/multilingual_cases.json`, 41 cases, review sheet
`evals/multilingual_cases_review.csv`) is my reading of the knowledge base, not human verified.
Existing English goldens were not edited.

## Root causes (original query: `mujhe bato apne baccho ke marks kese badye`)

1. **Accidental routing.** The word "marks" set `topic=scoring`, so the turn became a knowledge turn
   without any Quizzer intent being understood.
2. **Retrieval miss.** On local MiniLM (English-only) the query scored below the 0.28 floor, so `no_answer`.
3. **The decline was left to the generator.** The "do not answer" instruction is soft text. The weak free model
   ignored it and invented a "Release Scores" flow. Faithfulness and the other metrics were 0.
4. **Guidance form was English-only.** "kese kru" was not read as a how-to, so `exam publish kese kru`
   ran as a live tool call instead of guidance. This is separate from the embedding model.
5. **Embedding model matters.** Same cases on `text-embedding-3-large`: cross-language consistency 0.417 -> 0.667,
   evidence hit 0.56 -> 0.65 (before any code change).
6. **The provisional golden forced one reading** of an ambiguous ask. Ambiguous cases now list the acceptable
   behaviours instead of one answer.

## Changes (each behind a flag, measured, then kept)

| | change | flag | default |
|---|---|---|---|
| E1 | Retrieval miss on a turn nothing else can ground: fixed honest reply, no LLM (`app/orchestration/clarify.py::no_answer_reply`, `knowledge_node`) | `QUE_NOANSWER_DETERMINISTIC` | on |
| E2 | On a miss only: one small structured LLM call (`app/knowledge/interpret.py`, cached) rewrites the ask into an English search query for ONE retry, or asks a clarifying question when readings lead to different actions. Fails safe to E1. Runs before generation in both the graph and the streaming path (`resolve_knowledge_miss`). | `QUE_INTERPRET_ON_MISS` | on |
| E3 | `is_guidance_ask` and the how-to check in `classify_request` also read the text through the existing retrieval glossary ("kese kru" -> "how to"). No new word list. | none | n/a |

Not done on purpose: no new router, no per-request translation, no keyword lists, no embedding / chunk / top-k change,
no LLM call on every request. A turn that retrieves successfully pays nothing extra. Not fixed: `ye kaam nahi kar raha`
is refused as `no_quizzer_signal`. Fixing it would put an LLM call on every out-of-scope refusal, for one measured case.

## Before / after (deterministic, no LLM: routing + retrieval, 41 cases, N/A excluded)

| index | | routing ok | evidence hit | cross-language | ambiguity ok |
|---|---|---|---|---|---|
| local MiniLM | before | 0.780 | 0.560 | 0.417 | 0.800 |
| local MiniLM | after | 0.829 | 0.640 | 0.417 | 0.800 |
| API `text-embedding-3-large` (`data/chroma_bench/api_nofaq`) | before | 0.854 | 0.654 | 0.667 | 0.800 |
| API | after | 0.902 | 0.731 | 0.667 | 0.800 |

By kind, local: hinglish routing 0.692 -> 0.769, shorthand 0.5 -> 1.0, English anchors unchanged (0.909 / 0.667).
Rows changed by E3: `Students ki performance kaise improve kru?`, `exam publish kese kru`, `exam publish krna h kaise`
(tool -> guidance; the last two now retrieve `publishing`). E1/E2 do not change routing or retrieval for retrieved turns,
so they do not move this table.

## Regression

- Per-row snapshot of 267 existing eval queries (route, execution class, canonical intent, retrieved chunk ids,
  no-answer flag) before vs after: **0 rows changed** (`evals/baselines/ml_baseline_routes.json`,
  `ml_after_routes.json`, `scripts/snapshot_routes.py --compare`). The snapshot is deterministic (re-run = 0 diffs).
  Because retrieval is untouched, the judged retriever metrics are unchanged by construction; they were not re-judged.
- Offline suite (`run_eval_suite.py --offline --fail-on-regression`): all 10 categories at 1.0000 before and after.
- Unit tests: 429 passed, 2 skipped. New: `tests/test_noanswer_deterministic.py`, `tests/test_hinglish_routing.py`.
- English effect of E1: of 182 English queries only 4 are retrieval misses (2 correct declines, `Dashbaord`,
  `reduce cheating on this`). The last two now get the fixed "tell me which part" reply instead of a model reply.

## Generation-level result (LLM + judge) and its limits

Paired run, same 28 rows completed in all arms (13 of 41 hit provider 429/404 on the free models in some arm; the
runner retries 4 times, so those are infra noise, not system results). Judge: `evals/diagnostics/ml_judge_cache.json`,
one call per row; judge variability is documented in `evals/diagnostics/VARIANCE_RESULTS.md` and a difference under
about 0.1 on 28 rows is not evidence.

| arm | grounded | intent preserved | LLM calls | prompt tokens | latency ms |
|---|---|---|---|---|---|
| base (E1, E2 off) | 0.739 | 0.821 | 28 | 630 | 2299 |
| E1 | 0.826 | 0.857 | 25 | 611 | 2426 |
| E1 + E2 | 0.783 | 0.821 | 26 | 580 | 2123 |

Row evidence that matters more than the means:

- `mujhe bato apne baccho ke marks kese badye`: base invented "Release Scores" (grounded 0, intent 0). E1: honest decline
  (1 / 1). E1+E2, when the provider answered: **"Do you want to view marks after an exam is graded, or export/change
  recorded scores?"** (1 / 1). When the provider failed, it fell back to the E1 reply (checked live).
- `marks badhane hain`, `baccho ka result improve krna h`: clarifying questions ("Do you want to increase recorded
  scores or raise the actual marks?"). The model answered in English for these; it did answer in Hinglish for
  `ye kaam nahi kar raha` in a direct probe, so reply language follows the model, not a rule.
- `how to pubish my exm`: miss on local MiniLM; rewritten to "How to publish my exam" it retrieves `publishing` x2.
  `naya quiz kaise banaye` is a different failure: a confident wrong hit (`arena`), so E2 does not trigger.
- Latency/tokens: E1 removes the LLM call on a miss (about 1.6 s vs 9.7 s on those rows). E2 adds one call of about
  430 tokens and 0.6 to 6 s, only on a miss, cached per query. On this set 3 of 41 turns paid it.

E2 is on by default because it fails safe and costs nothing on hits, but its generation-level gain is supported by
rows, not by a clean paired mean. Re-run `scripts/run_multilingual_eval.py --generate` when provider quota is available.

## Remaining limitations

- Expected docs and acceptable behaviours are provisional until reviewed (`evals/multilingual_cases_review.csv`).
- Confident wrong hits (`naya quiz kaise banaye` -> `arena`) are not rescued; they need a better embedding model
  (the API index fixes several), not more rules. The live index `data/chroma` was not rebuilt.
- `ye kaam nahi kar raha` is still refused instead of clarified.
- Grading: no teacher score-edit endpoint was found in Quizzer's `backend/api` (only AI short-answer grading and
  question-mark edits), yet `knowledge/scoring/*.md` says teachers can assign scores manually. Cases `m04`-`m06`
  are scored against that unverified claim. The guide needs a check against the product before it is trusted.
- Workflow-card answers have no retrieved evidence, so grounding is N/A for them (not 0).
- Free-model quota limits the generation-level sample; the sample is small.

## Reproduce

```
$env:APP_ENV="local"; $env:EMBEDDING_PROVIDER="local"; $env:RERANKER_PROVIDER="local"
uv run python scripts/snapshot_routes.py --out evals/baselines/ml_after_routes.json --compare evals/baselines/ml_baseline_routes.json
uv run python scripts/run_multilingual_eval.py --out evals/baselines/ml_stageA_local_after.json
uv run python scripts/run_multilingual_eval.py --generate --out evals/baselines/ml_full_e1e2.json
uv run python scripts/compare_multilingual.py base=evals/baselines/ml_full_base.json e1e2=evals/baselines/ml_full_e1e2.json
```
