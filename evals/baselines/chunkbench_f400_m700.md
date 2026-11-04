# Retriever eval report

Source: `chunkbench_f400_m700.json`.

## Averages

| Metric | Mean |
|---|---:|
| Contextual recall | 0.7824 |
| Contextual precision | 0.8413 |
| Contextual relevancy | 0.8643 |
| Average of the three | 0.8293 |
| Abstention | 1/4 |
| Injected characters | 1187.2 |
| Latency p50 / p95 (ms) | 4006.9 / 5395.5 |

Settings: top-k 2, candidate pool 4, dense floor 0.28.

A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. `below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.

## Every row

| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |
|---|---|---|---:|---:|---:|---:|---|
| r02 |  | Where is Monitoring in the sidebar? | 1 | 1 | 1 | 1 | live-monitoring |
| r04 |  | What is verification schema before an exam? | 0.8 | 1 | 1 | 0.9333 | none |
| r05 |  | How do I host an Arena battle with a room code? | 1 | 1 | 1 | 1 | none |
| r06 |  | Connect Google Classroom and push grades | 1 | 1 | 1 | 1 | none |
| r08 |  | How does grading work for short answers? | 1 | 0.5 | 1 | 0.8333 | none |
| r10 |  | What exam settings control time limits? | 0.5 | 0.5 | 0.75 | 0.5833 | none |
| r11 |  | How do students take an exam from a link? | 0.5 | 1 | 1 | 0.8333 | none |
| r12 |  | Question types MCQ and true false | 0.5 | 1 | 0.8 | 0.7667 | none |
| r14 |  | Difference between Monitoring and Analytics | 0.5 | 1 | 0.8 | 0.7667 | terminology |
| r15 |  | Teacher vs student role permissions | 0.2 | 0.5 | 1 | 0.5667 | none |
| r16 |  | Students workspace cohort health | 0.5 | 1 | 1 | 0.8333 | none |
| r17 |  | Schedule exam on Google Calendar | 1 | 1 | 1 | 1 | none |
| r18 |  | Import source files from Google Drive | 0.8 | 1 | 1 | 0.9333 | none |
| r19 |  | How does onboarding work after signup? | 0.8 | 1 | 1 | 0.9333 | none |
| r20 |  | Change account settings and profile | 0.8 | 1 | 1 | 0.9333 | none |
| r21 |  | How do I send feedback about Quizzer? | 0 | 0 | 0.5 | 0.1667 | none |
| r22 |  | Notification preferences and email | 1 | 1 | 1 | 1 | none |
| r23 |  | What shows on the teacher dashboard? | 1 | 1 | 0.5 | 0.8333 | none |
| r24 |  | Exam lifecycle draft published archived | 0.67 | 0.5 | 1 | 0.7233 | none |
| r27 |  | Integrity events and live proctoring | 0.8 | 1 | 1 | 0.9333 | none |
| r29 |  | Negative marking settings | 1 | 1 | 1 | 1 | none |
| r31 |  | Link window vs exam duration meaning | 1 | 1 | 1 | 1 | exam-settings |
| r32 |  | Join Arena as a player with code | 0.8 | 1 | 0.8 | 0.8667 | none |
| r33 |  | Results tab integrity review | 1 | 0.5 | 0.8 | 0.7667 | none |
| p04 |  | download my students' marks sheet | 0.8 | 0.5 | 1 | 0.7667 | none |
| p05 |  | how are written answers scored | 0.5 | 1 | 1 | 0.8333 | none |
| p06 |  | stop students from switching tabs during the test | 0.5 | 1 | 1 | 0.8333 | live-monitoring |
| p07 |  | play a live quiz game with my class | 0.9 | 1 | 1 | 0.9667 | none |
| p08 |  | sync my scores to Google Classroom | 1 | 1 | 0.8 | 0.9333 | none |
| p09 |  | put the exam date in my calendar | 1 | 1 | 1 | 1 | none |
| p10 |  | can students retake the exam | 1 | 1 | 0.85 | 0.95 | none |
| t01 |  | publsh exam | 0.75 | 1 | 1 | 0.9167 | none |
| t02 |  | quiz kaise banaye | 0 | 0 | 0.5 | 0.1667 | creating-exams |
| t04 |  | exam link not working for student | 1 | 1 | 1 | 1 | publishing |
| t06 |  | arena room code | 0.8 | 1 | 0.8 | 0.8667 | none |
| t08 |  | student ko exam link kaise bheje | 0.8 | 1 | 1 | 0.9333 | none |
| a05 |  | Can I change it after? | 1 | 1 | 0.5 | 0.8333 | publishing |
| a06 |  | How do I start? | 0 | 0 | 0.2 | 0.0667 | onboarding, common-workflows |
| m01 |  | If I archive an exam can students still see their results, and can I still export them? | 1 | 1 | 0.8 | 0.9333 | lifecycle |
| m02 |  | How do I build an exam from a Drive file and then publish it? | 0.67 | 1 | 1 | 0.89 | creating-exams, publishing |
| m03 |  | Schedule my published exam on Google Calendar and watch who is attempting it live | 0.5 | 1 | 1 | 0.8333 | live-monitoring |
| m04 |  | How is negative marking applied and where do I switch it on? | 0.5 | 0.5 | 1 | 0.6667 | none |
| m06 |  | How do I bring in my Classroom roster and push grades back after grading? | 0.6 | 0.5 | 1 | 0.7 | grading |
| m07 |  | What should I set up before publishing an exam where I need to know who each student is? | 1 | 1 | 0.5 | 0.8333 | verification, exam-settings, publishing |
| c02 |  | Draft vs published vs archived exam | 1 | 1 | 1 | 1 | none |
| c03 |  | What is the difference between an Exam and an Arena game? | 0.8 | 1 | 0.8 | 0.8667 | none |
| c04 |  | Does Results show the same thing as Analytics? | 1 | 1 | 1 | 1 | terminology |
| c05 |  | Is the LIVE badge the same as Monitoring? | 1 | 1 | 0.8 | 0.9333 | none |
| s02 |  | How do I check my analytics in Quizzer? | 0 | 0 | 1 | 0.3333 | none |
| s03 |  | How can I export my game history to a CSV file? | 1 | 1 | 0.5 | 0.8333 | none |
| s05 |  | How do I set up webcam monitoring and auto-submit for a proctored exam? | 1 | 1 | 1 | 1 | none |
| s06 |  | How do I get better AI-generated questions in Quizzer? | 1 | 0.5 | 0.5 | 0.6667 | none |
| s07 |  | Why is my teacher dashboard completely empty right now? | 1 | 1 | 1 | 1 | none |
| s08 |  | Where can I find the analytics for my exam? | 1 | 0.5 | 1 | 0.8333 | empty-states |
| s09 |  | How do I change my exam settings after it's already been published? | 1 | 1 | 0.85 | 0.95 | none |
| s11 |  | How do I schedule an exam in Quizzer using Google Calendar? | 1 | 1 | 1 | 1 | none |
| s14 |  | How do I change how short answer questions are graded in my exam settings? | 1 | 1 | 1 | 1 | none |
| s15 |  | How do I unpublish an exam in Quizzer without losing my results? | 1 | 1 | 0.8 | 0.9333 | lifecycle |
| s16 |  | How can I see active attempts across all exams in the live panel? | 1 | 1 | 0.8 | 0.9333 | none |
| s17 |  | Where is the Monitoring tab? | 1 | 1 | 1 | 1 | navigation |
| s19 |  | Where do I enter my information when setting up a new workspace in Quizzer? | 0 | 0 | 0 | 0 | none |
| s22 |  | How do I set the correct answer for a True/False question? | 1 | 1 | 0.5 | 0.8333 | none |
| s23 |  | Where can I find the exam results to download them? | 1 | 1 | 1 | 1 | none |

The CSV next to this file has the judge's reason and the expected answer for every row.
