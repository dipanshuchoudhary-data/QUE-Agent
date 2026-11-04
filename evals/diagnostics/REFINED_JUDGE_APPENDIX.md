# Refined claim-level judge

## Findings: why t06 flipped (from stored verdicts, `variance_runs.json`)

Row `t06`, query "arena room code". Same frozen chunk, claims and answer; three repeats.

| Item | Repeat labels | Cause |
|---|---|---|
| Reference claim 0 "a six-character room code **and a join URL** are generated" | supported / supported / partial (run pair in the two-run test: partial vs supported) | Compound claim. The chunk has the room and the code, not the URL. Whether the URL counts decides the label. |
| Reference claim 3 "players join by link, join page, or room code plus nickname" | unsupported / unsupported / **partial** | Compound claim, and the flip run cited "mentions players answering questions" (topic overlap, no stated sub-fact). The rubric never said partial needs a stated sub-fact. |
| Coverage claim 1 "code is displayed and can be copied, linked, or scanned" | partial / partial / partial, or conveyed in another pair | Compound claim again. |
| Contextual relevancy of the single Arena overview chunk | 0.5 vs 1.0 | Chunk-level label `partly` vs `relevant`. Only about one sentence helps the question; one run judged by topic. With one chunk, one flip is a 0.5 jump. |
| Answer-claim labels (faithfulness), statement labels | identical in all runs | Stable. |

## Compound-claim audit of the current frozen claims

21 of 53 reference claims contain "and" or a comma (r02, r16, s11, p06, s03, r12, p05 and others). Compound claims make `partial` mean two different things: "one of two facts is present" and "the judge was unsure".

Conclusion: the label flips come first from ambiguous claims and an undefined `partial`, and second from a chunk-level relevancy label that lets topic closeness stand in for usefulness.

## Experiment results (30 rows, frozen chunks, answers and atomic claims; cache off; one pinned model)

Arms: **original** one prompt with free numbers; **current** closed labels, chunk-level relevancy; **refined** quotes, partial rule, unit-level relevancy, borderline adjudication; **refined_first** the refined labels before adjudication (same calls, step skipped).

### Reproducibility

| arm | rows | repeats | mean range | max range | mean SD | metric ranges > 0.2 | pass/fail flips @0.7 |
|---|---|---|---|---|---|---|---|
| original | 30 | 3 | 0.072 | 1.00 | 0.033 | 8% | 0 |
| current | 30 | 3 | 0.036 | 1.00 | 0.016 | 7% | 1 |
| refined | 30 | 3 | 0.057 | 1.00 | 0.027 | 10% | 1 |
| refined_first | 30 | 3 | 0.065 | 1.00 | 0.030 | 13% | 3 |

Mean range by metric (max in brackets):

| arm | recall | precision | relevancy | faithfulness | answer_relevancy | correctness |
|---|---|---|---|---|---|---|
| original | 0.100 (1.00) | 0.100 (1.00) | 0.080 (0.50) | 0.073 (1.00) | 0.007 (0.20) | 0.071 (0.30) |
| current | 0.031 (0.17) | 0.000 (0.00) | 0.042 (0.50) | 0.060 (1.00) | 0.039 (0.50) | 0.046 (0.33) |
| refined | 0.029 (0.17) | 0.050 (1.00) | 0.095 (0.88) | 0.044 (0.33) | 0.023 (0.50) | 0.104 (0.67) |
| refined_first | 0.067 (0.50) | 0.050 (1.00) | 0.095 (0.88) | 0.055 (0.33) | 0.023 (0.50) | 0.099 (0.36) |

Rows where any label flipped in the first 3 repeats (19 rows), all repeats that finished before the daily quota ended:

| arm | rows | repeats (max) | mean range | max range | mean SD |
|---|---|---|---|---|---|
| current (all available repeats) | 19 | 3 | 0.043 | 1.00 | 0.020 |
| refined (all available repeats) | 19 | 5 | 0.082 | 1.00 | 0.036 |

### Label disagreement across repeats (reference-claim and coverage labels)

| arm | items | items where repeats disagree | rate | partial vs supported/conveyed flips | partial vs unsupported/missing flips |
|---|---|---|---|---|---|
| current | 460 | 37 | 8% | 20 | 15 |
| refined_first | 460 | 45 | 10% | 7 | 12 |
| refined | 460 | 30 | 7% | 1 | 3 |

### Accuracy against the reference labels

Reference labels were drafted by the assistant (not an independent human review). Score error is the mean absolute difference from the score computed on the reference labels with the same formulas.

| arm | MAE recall | MAE precision | MAE relevancy | MAE faithfulness | MAE answer_relevancy | MAE correctness |
|---|---|---|---|---|---|---|
| original | 0.242 | 0.072 | 0.307 | 0.108 | 0.042 | 0.152 |
| current | 0.057 | 0.100 | 0.260 | 0.163 | 0.039 | 0.158 |
| refined_first | 0.087 | 0.022 | 0.130 | 0.126 | 0.020 | 0.123 |
| refined | 0.077 | 0.022 | 0.130 | 0.115 | 0.020 | 0.113 |

Label level (reference-claim and coverage items; all repeats pooled). FP = judge gives more credit than the reference, FN = less credit.

| arm | items | exact match | FP | FN | false contradictions | missed contradictions |
|---|---|---|---|---|---|---|
| current | 1380 | 84% | 74 (5%) | 149 (11%) | 6 | 0 |
| refined_first | 1380 | 83% | 66 (5%) | 171 (12%) | 3 | 1 |
| refined | 1380 | 83% | 61 (4%) | 174 (13%) | 4 | 1 |

Faithfulness at answer-unit level (judge claims matched to units by text similarity; units with no matching claim are excluded):

| arm | units compared | exact | FP (judge says supported, reference not) | FN | unmatched |
|---|---|---|---|---|---|
| current | 368 | 93% | 17 | 10 | 61 |
| refined_first | 401 | 94% | 8 | 16 | 28 |
| refined | 401 | 95% | 5 | 16 | 28 |

### Cost per row

| arm | judge calls | retries | seconds | prompt tokens | completion tokens |
|---|---|---|---|---|---|
| original | 1.0 | 0.10 | 3.1 | 790 | 235 |
| current | 2.1 | 0.20 | 7.5 | 1963 | 1230 |
| refined | 2.6 | 0.12 | 9.4 | 3351 | 1856 |

Runs that failed on malformed judge output (not counted in any score above): refined 11 (s05: answer_units: unit ids do not match the units given, r06: answer_units: unit ids do not match the units given, p07: reference_coverage: expected 0..16 once each, got [0, 1, 2, ); current 1 (p07: Judge did not return JSON for _RetrieverVerdict: '```json { ); original 0

Token prices for the pinned model were not verified, so no USD figure is given. The free tier has no per-token charge.

### Adjudication

- Runs where adjudication triggered: 44 of 90.
- Reference/coverage items adjudicated: 90; label changed on 66.
- Agreement with reference on those items: first label 33/90, after adjudication 35/90.

### Claim extraction stability (12 rows, 2 re-extractions each)

Mean share of frozen claims with a close match in a re-extraction: 0.96. Claim counts per row (frozen vs repeats): r02 4 vs [4, 4]; s17 3 vs [3, 3]; r16 7 vs [7, 7]; s11 6 vs [5, 6]; p06 8 vs [8, 12]; s03 3 vs [3, 3]; r12 7 vs [8, 10]; s07 4 vs [4, 4]; p05 8 vs [8, 8]; m06 7 vs [14, 13]; a06 11 vs [12, 11]; t06 10 vs [10, 9].

## Planted-defect probes

Each probe is a frozen answer with one defect (or unchanged). Base = mean score of the same row over its repeats in that arm. Detected = the expected score moved by at least 0.10 in the right direction (controls: both faithfulness and correctness moved by less than 0.10). For contradiction probes the refined arm must also report a contradicted answer claim.

| probe | defect | row | expected | original | current | refined |
|---|---|---|---|---|---|---|
| x01 | invented_fact | r12 | faithfulness_down | yes (faith +0.50, corr +0.20) | yes (faith +0.20, corr +0.00) | yes (faith +0.14, corr +0.00) |
| x02 | contradiction | r22 | faithfulness_down_contradiction | yes (faith +0.50, corr +0.10) | yes (faith +0.33, corr -0.06) | yes (faith +0.33, corr -0.25) |
| x03 | contradiction | r32 | faithfulness_down_contradiction | yes (faith +0.20, corr +0.17) | yes (faith +0.17, corr +0.25) | yes (faith +0.11, corr +0.25) |
| x04 | omission | c03 | correctness_down | yes (faith +0.00, corr +0.42) | yes (faith +0.00, corr +0.58) | yes (faith +0.00, corr +0.58) |
| x05 | invented_fact | s07 | faithfulness_down | yes (faith +0.50, corr +0.33) | NO (faith +0.00, corr +0.00) | yes (faith +0.17, corr +0.00) |
| x06 | omission | t04 | correctness_down | yes (faith -0.03, corr +0.60) | yes (faith +0.08, corr +0.31) | yes (faith +0.23, corr +0.25) |
| x07 | contradiction | m06 | faithfulness_down_contradiction | yes (faith +0.50, corr +0.48) | yes (faith +0.25, corr +0.29) | yes (faith +0.28, corr +0.29) |
| x08 | contradiction | p06 | faithfulness_down_contradiction | yes (faith +0.33, corr +0.20) | yes (faith +0.25, corr +0.25) | yes (faith +0.25, corr +0.15) |
| x09 | omission | r32 | correctness_down | yes (faith -0.20, corr +0.47) | yes (faith -0.17, corr +0.62) | yes (faith -0.14, corr +0.62) |
| x10 | invented_fact | r19 | faithfulness_down | yes (faith +0.18, corr +0.07) | NO (faith +0.00, corr +0.02) | NO (faith -0.07, corr +0.06) |
| x11 | control | r12 | no_change | yes (faith +0.00, corr +0.00) | yes (faith +0.00, corr +0.00) | yes (faith +0.00, corr +0.00) |
| x12 | control | r22 | no_change | yes (faith +0.00, corr +0.10) | yes (faith +0.00, corr -0.06) | yes (faith +0.00, corr +0.08) |

Detected: original 12/12, current 10/12, refined 11/12.

## Verdict against the plan's success criteria

| Criterion | Result |
|---|---|
| Refined has no more FP and FN than current against the reference labels | Not met. FP 61 vs 74 (better), FN 174 vs 149 (worse). Refined is stricter: exact label match 83% vs 84%. |
| Catches every planted defect the current judge catches | Met. Refined 11/12, current 10/12, original 12/12. Both claim judges miss the invented "30 seconds and a short quiz" sentence (x10). Current also misses x05. |
| `partial` vs `supported` flips drop clearly | Met. 20 to 1 (and `partial` vs `unsupported`/`missing` 15 to 3). |
| t06 no longer swings by 0.5 | Met. Relevancy 0.2, 0.2, 0.2 (current 1.0, 0.5, 0.5). Recall 0.1 in all repeats. |
| Adjudication adds under 0.5 calls per row | Barely. Triggered in 44 of 90 runs (0.49 per row). Total refined calls 2.6 vs 2.1 for current. |
| Reproducibility improves without losing accuracy | Mixed, see below. |

## What the numbers say

- **Label stability improved, score stability did not.** Items where repeats disagree: 8% (current), 10% (refined before adjudication), 7% (refined). But mean score range is 0.036 for current and 0.057 for refined. The unit-level relevancy score has a small denominator on short chunks, so one unit flip moves it a lot (mean range 0.095, max 0.88 vs 0.042 for current). Correctness also moved more (0.104).
- **Accuracy against reference labels improved on three metrics.** Mean absolute score error: relevancy 0.13 vs 0.26 (current) and 0.31 (original); precision 0.02 vs 0.10; correctness 0.113 vs 0.158. Recall error is worse than current (0.077 vs 0.057), because refined gives less partial credit.
- **Hallucination handling.** Faithfulness at unit level: refined has fewer false "supported" (5 vs 17 for current), more false "unsupported" (16 vs 10).
- **Adjudication did not help accuracy.** It changed 66 of 90 adjudicated items, but agreement with the reference moved only from 33/90 to 35/90. The triggered items are the hard ones, and the element-by-element check is not clearly better than the first verdict. It does cut label disagreement (45 to 30 items) and `partial` flips (7 to 1). A second LLM call did not automatically improve correctness.
- **Cost.** Refined: 2.6 calls, about 9.4 s and about 5,200 tokens per row. Current: 2.1 calls, 7.5 s, about 3,200 tokens. Original: 1 call, 3.1 s, about 1,000 tokens.
- **Reliability.** Refined had 11 failed-run events from malformed judge output, mostly answer unit ids that did not match (fixed partway by aligning by order when the count is right); current had 1. Failed runs are excluded from all scores.

## Recommendation

Do not replace the current judge with the refined judge as a whole. Keep these parts, which clearly help:
1. Frozen atomic reference claims (stability of claim extraction was 0.96 on re-extraction).
2. Quote verification and the `partial` rule (the `partial`/`supported` flip drop).
3. Unit-level relevancy for accuracy, but only with a fix for the small-denominator instability (for example, require at least a minimum number of units, or report the unit counts with the score).

Do not keep the adjudication step as built: it costs about half a call per row and showed no accuracy gain. Keep the original one-call judge only as a cheap smoke check; it catches every planted defect but its free numbers are the least reproducible and least accurate on recall and relevancy.

## Limits of this experiment

- 30 rows, one pinned model (`gemini-3.5-flash-lite`), 3 repeats per arm on all rows. The 5-repeat extension reached 4 to 5 repeats for the refined arm and stayed at 3 for current and original because the daily free quota (500 requests) ran out. Headline tables use the first 3 repeats for every arm.
- Reference labels were drafted by the assistant from the frozen chunks, not by an independent human. FP/FN and error figures are only as good as those labels, which should be reviewed. `evals/label_reference.json`.
- The 12 frozen rows were also used to design the refined prompt, so they are not a clean holdout.
- Frozen answers for some rows have damaged characters from an earlier encoding problem.
- Probe x09 was rebuilt on row r32 because the first base row's correctness was already near zero, and probe x03 was rebuilt because its first mutation never applied. Both were rerun before the numbers above.
