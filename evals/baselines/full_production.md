# Retriever eval report

Source: `full_production.json`.

## Averages

| Metric | Mean |
|---|---:|
| Contextual recall | 0.6074 |
| Contextual precision | 0.8158 |
| Contextual relevancy | 0.8724 |
| Average of the three | 0.7652 |
| Abstention | 1/4 |
| Injected characters | 670.2 |
| Latency p50 / p95 (ms) | 2063.6 / 3525.8 |

Settings: top-k 2, candidate pool 4, dense floor 0.28.

A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. `below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.

## Every row

| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |
|---|---|---|---:|---:|---:|---:|---|
| r02 |  | Where is Monitoring in the sidebar? | 1 | 1 | 1 | 1 | navigation |
| r04 |  | What is verification schema before an exam? | 0.8 | 1 | 1 | 0.9333 | none |
| r05 |  | How do I host an Arena battle with a room code? | 0.85 | 1 | 1 | 0.95 | none |
| r06 |  | Connect Google Classroom and push grades | 0.5 | 1 | 1 | 0.8333 | google-classroom |
| r08 |  | How does grading work for short answers? | 0.5 | 1 | 1 | 0.8333 | none |
| r12 |  | Question types MCQ and true false | 0.8 | 1 | 0.8 | 0.8667 | none |
| r15 |  | Teacher vs student role permissions | 0.5 | 1 | 1 | 0.8333 | none |
| r16 |  | Students workspace cohort health | 0.5 | 1 | 1 | 0.8333 | none |
| r17 |  | Schedule exam on Google Calendar | 0.8 | 1 | 1 | 0.9333 | google-calendar |
| r18 |  | Import source files from Google Drive | 0.6 | 1 | 1 | 0.8667 | none |
| r19 |  | How does onboarding work after signup? | 0.6 | 1 | 1 | 0.8667 | none |
| r21 |  | How do I send feedback about Quizzer? | 0 | 0 | 1 | 0.3333 | none |
| r22 |  | Notification preferences and email | 0.5 | 1 | 1 | 0.8333 | none |
| r23 |  | What shows on the teacher dashboard? | 1 | 1 | 1 | 1 | none |
| r31 |  | Link window vs exam duration meaning | 1 | 1 | 1 | 1 | exam-settings |
| r32 |  | Join Arena as a player with code | 0.8 | 1 | 0.9 | 0.9 | none |
| p04 |  | download my students' marks sheet | 0.8 | 1 | 1 | 0.9333 | none |
| p05 |  | how are written answers scored | 0.33 | 1 | 1 | 0.7767 | none |
| p06 |  | stop students from switching tabs during the test | 0.2 | 1 | 1 | 0.7333 | exam-settings, live-monitoring |
| p07 |  | play a live quiz game with my class | 1 | 1 | 1 | 1 | arena |
| p10 |  | can students retake the exam | 0 | 0 | 0.5 | 0.1667 | exam-settings |
| t01 |  | publsh exam | 0 | 0 | 0 | 0 | publishing |
| t02 |  | quiz kaise banaye | 0 | 0 | 0.5 | 0.1667 | creating-exams |
| t04 |  | exam link not working for student | 1 | 0.5 | 0.75 | 0.75 | none |
| t06 |  | arena room code | 0.2 | 1 | 1 | 0.7333 | none |
| a06 |  | How do I start? | 0 | 0 | 0.2 | 0.0667 | onboarding, common-workflows |
| m04 |  | How is negative marking applied and where do I switch it on? | 0.5 | 1 | 1 | 0.8333 | exam-settings |
| m06 |  | How do I bring in my Classroom roster and push grades back after grading? | 0.8 | 1 | 1 | 0.9333 | grading |
| c02 |  | Draft vs published vs archived exam | 1 | 1 | 1 | 1 | none |
| c03 |  | What is the difference between an Exam and an Arena game? | 1 | 1 | 0.5 | 0.8333 | product-overview |
| c05 |  | Is the LIVE badge the same as Monitoring? | 0.5 | 1 | 1 | 0.8333 | terminology |
| s03 |  | How can I export my game history to a CSV file? | 1 | 1 | 1 | 1 | none |
| s05 |  | How do I set up webcam monitoring and auto-submit for a proctored exam? | 1 | 0.5 | 1 | 0.8333 | none |
| s06 |  | How do I get better AI-generated questions in Quizzer? | 0 | 0 | 0 | 0 | creating-exams |
| s07 |  | Why is my teacher dashboard completely empty right now? | 1 | 1 | 1 | 1 | none |
| s11 |  | How do I schedule an exam in Quizzer using Google Calendar? | 0.5 | 1 | 1 | 0.8333 | none |
| s17 |  | Where is the Monitoring tab? | 1 | 1 | 1 | 1 | none |
| s19 |  | Where do I enter my information when setting up a new workspace in Quizzer? | 0.5 | 1 | 1 | 0.8333 | none |

The CSV next to this file has the judge's reason and the expected answer for every row.
