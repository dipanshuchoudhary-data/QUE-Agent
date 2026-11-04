# Retriever eval report

Source: `retriever_local_nofaq_fix.json`.

## Averages

| Metric | Mean |
|---|---:|
| Contextual recall | 0.3 |
| Contextual precision | 0.25 |
| Contextual relevancy | 0.5833 |
| Average of the three | 0.3778 |
| Abstention | 0/0 |
| Injected characters | 1666.7 |
| Latency p50 / p95 (ms) | 313.9 / 13484.4 |

Settings: top-k 2, candidate pool 4, dense floor 0.28.

A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. `below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.

## Every row

| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |
|---|---|---|---:|---:|---:|---:|---|
| r15 |  | Teacher vs student role permissions | 0.2 | 0.5 | 1 | 0.5667 | none |
| r27 |  | Integrity events and live proctoring | 0.8 | 0.5 | 0.9 | 0.7333 | none |
| p04 |  | download my students' marks sheet | 0.8 | 0.5 | 0.6 | 0.6333 | none |
| t02 |  | quiz kaise banaye | 0 | 0 | 0.5 | 0.1667 | none |
| t08 |  | student ko exam link kaise bheje | 0 | 0 | 0.5 | 0.1667 | publishing |
| a05 |  | Can I change it after? | 0 | 0 | 0 | 0 | exam-settings, publishing |

The CSV next to this file has the judge's reason and the expected answer for every row.
