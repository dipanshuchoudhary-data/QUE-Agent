# Retrieval audit: results of the controlled plan

All goldens are still `human_verified: false`. Nothing here edits a golden. Scores are provisional.

## Blocker found on the way (read first)

The free OpenRouter models hit their **daily cap of 50 requests** (`free-models-per-day`, resets 2026-10-08 00:00 UTC).
- Rerank (`nvidia/llama-nemotron-rerank-vl-1b-v2:free`) failed open on most rows in the rerun: 59 of 85 answered rows failed, 23 ok, 3 skipped.
- The chat LLMs (`nvidia/nemotron-*:free`) also return 429, so generator answers for retrieval rows could not be produced.
- So the earlier "large embeddings + rerank" jump (average 0.739 to 0.811) cannot be attributed: rerank was available then and mostly not now, and the same system re-judged gives 0.773.
- Fix kept in code: a daily-cap 429 now fails fast (no retries) and cools down for 10 minutes. Judged runs record `rerank_status` and `rerank_fail_open_rate`.
- Fix on your side: add 10 credits on OpenRouter (raises the free cap to 1000/day) or wait for the reset, then rerun the rerank-dependent items below.

## Phase 0: where the 47 weak rows fail

`evals/diagnostics/retrieval_audit.md`. Suggested causes (heuristic): CONTEXT_NOISE 19, EVIDENCE_MISS 19, AMBIGUOUS_QUERY 4, EVAL_ERROR 4, LANGUAGE_MISMATCH 1.
Production serves only 46 of 104 rows through retrieval (31 workflow cards, 14 refusals, 12 tools, 1 conversational), so the retrieval eval covers under half of real traffic.

## Phase 1: eval fidelity

- `--mode production` judges the injected 700-char text, passes production `execution_class`, and buckets card/tool/refuse rows.
- Seven "NOT IN GUIDE" goldens are set aside for a person (`a03 a04 m05 m08 m09 c01 c06`); the old run scored them about 1.0.
- Same system, same 85 rows, judged twice: averages moved 0.02-0.04 and 14-17 rows moved by more than 0.2. **Judge noise is about 0.03.**

## Phase 2: KB fixes (only the two files changed)

`taking-exams.md` now has one canonical Step 1-9 order with a short answer on top; the second list is "Details Behind Each Step". `onboarding.md` no longer numbers the same steps twice. 15 touched rows: recall 0.687 to 0.729, precision 0.687 to 0.711, relevancy 0.637 to 0.659 (near noise; rerank was failing in both runs). `r11` stays weak because production routes it to the teacher share card.

## Phase 3: reclassification after Phase 2

`evals/diagnostics/retrieval_audit_after_phase2.md` (45 rows): EVIDENCE_MISS 20, CONTEXT_NOISE 18, AMBIGUOUS_QUERY 4, RANKING_FAILURE 1, DOC_MISS 1, LANGUAGE_MISMATCH 1. KB gaps are not the main cause. The right document is found; the section holding the steps often is not selected, and the one-chunk-per-document rule fills other slots with other guides.

## Phases 4 and 6: judge-free ablations (`ablations.md`, 67 rows, rerank effectively off)

Coverage is a word-overlap proxy for recall, not the judge.

| Variant | Coverage | Rows fully covered | Doc hit | Noise | Chars |
|---|---:|---:|---:|---:|---:|
| base (k3, pool 5) | 0.632 | 28 | 0.94 | 0.602 | 1746 |
| neighbor expand 1 | 0.646 | 30 | 0.94 | 0.592 | 1874 |
| pool 8 | 0.654 | 28 | 0.97 | 0.617 | 1775 |
| k2, pool 4 (current default) | 0.572 | 26 | 0.851 | 0.515 | 1195 |
| k4, pool 8 | 0.723 | 36 | 0.97 | 0.695 | 2358 |
| query normalize (Phase 5) | 0.637 | 28 | 0.94 | 0.602 | 1744 |
| embeddings small, k3 | 0.571 | 26 | 0.896 | 0.609 | 1711 |
| embeddings small, k2 | 0.511 | 22 | 0.821 | 0.515 | 1183 |

- Neighbor expansion: small gain, small cost. Worth keeping as an option (`QUE_RAG_NEIGHBOR_EXPAND`), off by default.
- Bigger K buys coverage and noise together. No default change without judged precision.
- Current default (k2, pool 4) is the weakest here; the earlier "only set top-k to 2" cost coverage.
- Embeddings large vs small, one variable, no rerank: coverage 0.571 to 0.632, doc hit 0.896 to 0.94. Large helps; this is deterministic, so it is not noise.
- Dynamic final K (`QUE_RAG_DYNAMIC_K_RATIO`) needs rerank scores, so the run was a no-op. Inconclusive.
- Rerank on vs off: not measurable today (quota). Rerun `scripts/ablate_retrieval.py --variants base,rerank_off` after the reset.

## Phase 5: query normalization and clarify

`app/knowledge/query_normalize.py`: a small typo/Hinglish glossary applied to the retrieval string only (`QUE_RAG_QUERY_NORMALIZE`, off). Effect: +0.005 coverage. Not worth enabling. `should_clarify` flags 4 of the 4 vague single-pronoun rows (`a02 a04 a05 a06`) with no false positives on the golden set; it is not wired into production routing.

## Phase 7: generator and full pipeline (16-row fixed sample, `evals/baselines/generator_check.json`)

- Retrieval rows: blocked by the LLM daily cap (9 of 16 errored).
- Workflow-card rows (7, no LLM): completeness 0.27, relevancy 0.51 on average. Several are the **wrong card**: `p09` and `m03` (Google Calendar scheduling) got the publish card, `r20` (account settings) and `r29` (negative marking) got the exam settings card. Low-confidence lexical intent matches (0.26-0.55) are being served as deterministic cards.

## Recommended next steps (not applied)

1. Raise the OpenRouter free cap or wait for the reset, then rerun judged eval in `--mode production` and the rerank ablation.
2. Raise the confidence threshold for serving a workflow card, and fix the `r11` student-link routing.
3. Have a person verify goldens, starting with the 7 quarantined rows.
4. Try same-document neighbor expansion with the judge before enabling it.

## Rerun after the quota reset (2026-10-09)

Rerank now rotates across all configured keys and eval runs cache rerank results on disk (`evals/rerank_cache.py`).

- Full raw judged run (top-k 3, pool 5, 97 answered rows, rerank ok 82 / failed 12 / skipped 3): recall 0.800, precision 0.819, relevancy 0.823, average 0.814. File: `evals/baselines/full_raw_k3_c5.json`. Seven NOT-IN-GUIDE rows still held for human review.
- Ablation with rerank (67 rows; rerank ok on 53, failed open on 11, so the rerank gain is understated): coverage rerank off 0.623, on 0.646 (rows fully covered 29 to 32). Neighbor expansion 1 on top: 0.667, 34 rows, noise 0.567 (best). Dynamic K 0.6 / 0.8 cut coverage to 0.533 / 0.511 (rejected). Query normalization 0.641 (no gain).
- Production-mode judged run: rerank failed open on 64% of rows (quota spent again), so its scores (recall about 0.61, precision 0.82, relevancy 0.87 on the rows that reach retrieval) are not clean. Rerun after the next reset or after adding credits.
- Full pipeline, 66 rows (`evals/baselines/generator_full.json`, 7 errors): retrieval rows completeness 0.63, contradiction 0.22, relevancy 0.87; workflow-card rows completeness 0.43, contradiction 0.31, relevancy 0.61. Cards are the weaker path.
