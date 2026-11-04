# Judge repeatability: summary

Full tables, the t06 diagnosis and all limits are in [REFINED_JUDGE_APPENDIX.md](REFINED_JUDGE_APPENDIX.md).

## Goal

Make the LLM judge give (almost) the same score when the same question is judged twice, without replacing semantic judgment by keyword rules.

## Setup

30 questions, each judged 3 times, cache off, one pinned model (`gemini-3.5-flash-lite`). Same frozen chunks, answers and reference claims for every judge.

| Judge | How it works |
|---|---|
| Original | The LLM writes the six scores itself (free numbers). 1 call. |
| Current | The LLM picks a label per claim, code computes the scores. 2 calls. |
| Refined | Current plus stricter rules: atomic claims, a quote for every label, per-sentence relevancy, and an extra checking call on borderline items. About 2.6 calls. |

## Results

| | Original | Current | Refined |
|---|---|---|---|
| Average score change between runs (lower is better) | 0.07 | **0.04** | 0.06 |
| `partial` vs `supported` label flips | n/a | 20 | **1** |
| Matches my reference labels exactly | n/a | **84%** | 83% |
| Score error on relevancy (lower is better) | 0.31 | 0.26 | **0.13** |
| Planted defects caught (12 tests) | **12** | 10 | 10 |
| Judge calls per question | **1.0** | 2.1 | 2.6 |

## What it means

1. The t06 flips came from compound claims and an undefined `partial` label. The refined rules fix that: the label flips dropped from 20 to 1.
2. The refined judge is more accurate on relevancy, precision and correctness, but its scores still wobble more than current's. Per-sentence relevancy has few sentences, so one flip moves the score a lot.
3. The extra checking call did not improve accuracy (33 of 90 correct before it, 35 of 90 after). Drop it.
4. The original judge is the least reliable on recall and relevancy, though it catches every planted defect.

## Recommendation

Use the **current** judge as the default. Add from the refined judge only: the frozen atomic claims, the quote check and the `partial` rule. Do not adopt the adjudication step.

## Caveats

- The reference labels (`evals/label_reference.json`) were written by me, not by a person. Please review them. All accuracy numbers depend on them.
- Only 30 questions and one model. Three repeats for every judge. The daily free quota cut the 5-repeat extension short.
- The refined judge had 11 failed runs from malformed output, against 1 for current.

