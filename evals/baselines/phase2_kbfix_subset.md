# Retriever eval report

Source: `phase2_kbfix_subset.json`.

## Averages

| Metric | Mean |
|---|---:|
| Contextual recall | 0.7287 |
| Contextual precision | 0.7113 |
| Contextual relevancy | 0.6593 |
| Average of the three | 0.6998 |
| Abstention | 0/0 |
| Injected characters | 2248.3 |
| Latency p50 / p95 (ms) | 9929.0 / 10180.2 |

Settings: top-k 3, candidate pool 5, dense floor 0.28.

A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. `below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.

## Every row

| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |
|---|---|---|---:|---:|---:|---:|---|
| r11 |  | How do students take an exam from a link? | 0.33 | 0.33 | 0.4 | 0.3533 | none |
| r19 |  | How does onboarding work after signup? | 0.8 | 1 | 1 | 0.9333 | none |
| p01 |  | I want to make a test for my class from my PDF notes | 0.5 | 0.33 | 0.67 | 0.5 | none |
| p03 |  | give students the link to the exam | 1 | 0.67 | 0.67 | 0.78 | none |
| p06 |  | stop students from switching tabs during the test | 0.5 | 0.5 | 0.67 | 0.5567 | live-monitoring |
| p10 |  | can students retake the exam | 1 | 1 | 0.85 | 0.95 | none |
| p11 |  | what happens to my exam when I archive it | 0.8 | 0.67 | 0.55 | 0.6733 | none |
| t04 |  | exam link not working for student | 1 | 1 | 0.9 | 0.9667 | none |
| t08 |  | student ko exam link kaise bheje | 1 | 1 | 0.85 | 0.95 | none |
| a02 |  | It's not working | 0.5 | 0.67 | 0.67 | 0.6133 | none |
| a05 |  | Can I change it after? | 1 | 0.5 | 0.67 | 0.7233 | publishing |
| a06 |  | How do I start? | 0 | 0 | 0.33 | 0.11 | onboarding, common-workflows |
| s05 |  | How do I set up webcam monitoring and auto-submit for a proctored exam? | 1 | 1 | 1 | 1 | none |
| s19 |  | Where do I enter my information when setting up a new workspace in Quizzer? | 0.5 | 1 | 0.33 | 0.61 | none |
| s22 |  | How do I set the correct answer for a True/False question? | 1 | 1 | 0.33 | 0.7767 | none |

The CSV next to this file has the judge's reason and the expected answer for every row.
