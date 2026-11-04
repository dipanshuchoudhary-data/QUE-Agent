# Judge repeatability: before and after

Frozen rows: r02, s17, r16, s11, p06, s03, r12, s07, p05, m06, a06, t06. Cache off. One pinned model per arm.

| arm | model | rows | repeats | mean range | share of metric ranges > 0.2 | pass/fail flips @0.7 | calls/row |
|---|---|---|---|---|---|---|---|
| claims | gemini-3.5-flash-lite | 12 | 3 | 0.037 | 7% | 1 | 2.0 |
| one_call | gemini-3.5-flash-lite | 12 | 3 | 0.070 | 6% | 0 | 1.0 |
| claims_vote | gemini-3.5-flash-lite | 6 | 2 | 0.024 | 6% | 0 | 4.8 |

## Mean per-row range (max - min across repeats) by metric

| arm | recall | precision | relevancy | faithfulness | answer_relevancy | correctness |
|---|---|---|---|---|---|---|
| claims | 0.057 | 0.000 | 0.042 | 0.029 | 0.069 | 0.024 |
| one_call | 0.088 | 0.167 | 0.067 | 0.025 | 0.000 | 0.075 |
| claims_vote | 0.042 | 0.000 | 0.000 | 0.017 | 0.083 | 0.000 |

## Per-row range of the worst metric

| row | claims | one_call | claims_vote |
|---|---|---|---|
| r02 | 0.25 | 0.00 | 0.25 |
| s17 | 0.17 | 1.00 | 0.00 |
| r16 | 0.50 | 0.10 | 0.50 |
| s11 | 0.17 | 0.50 | 0.00 |
| p06 | 0.25 | 0.10 | 0.00 |
| s03 | 0.10 | 0.20 | 0.10 |
| r12 | 0.00 | 0.20 | - |
| s07 | 0.00 | 0.00 | - |
| p05 | 0.50 | 1.00 | - |
| m06 | 0.07 | 0.00 | - |
| a06 | 0.00 | 0.00 | - |
| t06 | 0.33 | 0.20 | - |

Vote arm: mean pass-1 vs pass-2 label agreement retriever 0.93, generator 0.81.

## Experiment 0: identical prompt, temperature 0, one pinned model

Same prompt sent 5 times to `gemini-3.5-flash-lite` on r16, s03, s17. No row repeated its scores exactly. Mean per-metric range 0.21, largest 1.0 (s17 recall and precision flipped 0 to 1). The endpoint rejects `seed` (HTTP 400), so there is no seed lever. Variance is in the model, not only the prompt.

## Hand check of rows where repeats differed (claims arm)

I read the chunks, reference claims and verdicts for r02, s11, r16, p05, s17, t06 and m06.

| finding | rows | verdict |
|---|---|---|
| Label flips are on genuinely borderline claims (`partial` vs `unsupported`, `partial` vs `contradicted`, chunk `partly` vs `relevant`) | t06, m06, s17, p05 | Fine. A flip moves the score by one claim's share, not by a free number. |
| Stable and correct on clear cases | r16, r12, s07, a06, s11 | s11 answer invents 7 UI steps the chunk never states: all repeats label them unsupported (faithfulness 0). Correct. |
| **Wrong label, repeated**: reference claim "Monitoring is not located in the sidebar" labelled `contradicted` in 2 of 3 repeats, although the chunk says "no top-level Monitoring item in the sidebar" | r02 | Real accuracy error on a negative claim. Majority vote does not fix it (2 of 3 wrong). |
| Large range on r16 comes from answer relevancy: the answer has 2 or 3 statements and one more or less off-topic statement moves the share by 0.5 | r16 | Small-n effect, not a bad verdict. |
| p05 range 0.5 is chunk label `partly` vs `relevant` on the one truncated chunk (700 chars hide the later grading steps) | p05 | Borderline. Also shows the injected chunk is cut before the steps the answer needs. |

## Against the success bar

| bar | result |
|---|---|
| Mean per-row range at or below 0.05 | claims 0.037, claims_vote 0.024 (one_call 0.070). Met. |
| At most 1 pass/fail flip across 12 rows | claims 1, one_call 0, claims_vote 0 (6 rows). Met, but one_call showed 0 flips only because its average hides a 1.0 swing on s17 and p05. |
| No drop in accuracy against the hand check | Not fully met: one repeated negation error (r02). Needs the fix below. |

Worst-case swings fall from 1.0 (one_call, s17 and p05) to 0.5 (claims, r16 and p05).

## Honest limits

- Perfect determinism is not reached and cannot be: the API has no seed and varies at temperature 0.
- Scores still move by one claim's share when a borderline label flips. That is by design: small, bounded, and visible in the verdicts.
- 12 rows and 3 repeats is a small sample. The claims_vote arm ran only 6 rows and 2 repeats.
- Reference claims were extracted by the same judge family and not human reviewed. Review `evals/golden_claims.json`.
- Nothing here is cached. Cached equality is not evidence of determinism.

## Recommendation

Use the 2-call `claims` mode as the default. Use `claims_vote` (about 4.8 calls) only for final reports. Add to the retriever prompt that a claim stating something is absent ("X is not in Y") is supported when the chunk says so, then rerun r02 only.
