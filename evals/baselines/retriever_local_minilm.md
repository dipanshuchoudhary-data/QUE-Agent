# Retriever eval report

Source: `retriever_local_minilm.json`.

## Averages

| Metric | Mean |
|---|---:|
| Contextual recall | 0.8038 |
| Contextual precision | 0.7587 |
| Contextual relevancy | 0.7948 |
| Average of the three | 0.7858 |
| Abstention | 1/4 |
| Injected characters | 1613.7 |
| Latency p50 / p95 (ms) | 309.7 / 526.0 |

Settings: top-k 2, candidate pool 4, dense floor 0.28.

A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. `below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.

## Every row

| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |
|---|---|---|---:|---:|---:|---:|---|
| r02 |  | Where is Monitoring in the sidebar? | 1 | 1 | 0.85 | 0.95 | live-monitoring |
| r04 |  | What is verification schema before an exam? | 1 | 1 | 1 | 1 | none |
| r05 |  | How do I host an Arena battle with a room code? | 1 | 1 | 1 | 1 | none |
| r06 |  | Connect Google Classroom and push grades | 1 | 1 | 0.8 | 0.9333 | none |
| r08 |  | How does grading work for short answers? | 1 | 1 | 1 | 1 | none |
| r10 |  | What exam settings control time limits? | 0.5 | 0.5 | 0.6 | 0.5333 | none |
| r11 |  | How do students take an exam from a link? | 0.33 | 1 | 1 | 0.7767 | none |
| r12 |  | Question types MCQ and true false | 0.67 | 1 | 0.8 | 0.8233 | none |
| r14 |  | Difference between Monitoring and Analytics | 0 | 0 | 0.5 | 0.1667 | terminology |
| r15 |  | Teacher vs student role permissions | 0.8 | 1 | 1 | 0.9333 | none |
| r16 |  | Students workspace cohort health | 0.67 | 0.5 | 0.8 | 0.6567 | none |
| r17 |  | Schedule exam on Google Calendar | 1 | 0.5 | 1 | 0.8333 | none |
| r18 |  | Import source files from Google Drive | 0.8 | 0.5 | 1 | 0.7667 | none |
| r19 |  | How does onboarding work after signup? | 0.8 | 0.5 | 0.75 | 0.6833 | none |
| r20 |  | Change account settings and profile | 0.9 | 1 | 0.9 | 0.9333 | none |
| r21 |  | How do I send feedback about Quizzer? | 1 | 1 | 0.8 | 0.9333 | none |
| r22 |  | Notification preferences and email | 1 | 1 | 1 | 1 | none |
| r23 |  | What shows on the teacher dashboard? | 1 | 1 | 0.9 | 0.9667 | none |
| r24 |  | Exam lifecycle draft published archived | 1 | 1 | 1 | 1 | none |
| r27 |  | Integrity events and live proctoring | 0.8 | 1 | 1 | 0.9333 | none |
| r29 |  | Negative marking settings | 1 | 0.5 | 0.75 | 0.75 | grading |
| r31 |  | Link window vs exam duration meaning | 0.8 | 1 | 0.5 | 0.7667 | exam-settings |
| r32 |  | Join Arena as a player with code | 0.8 | 0.5 | 0.4 | 0.5667 | none |
| r33 |  | Results tab integrity review | 1 | 0.5 | 0.75 | 0.75 | none |
| p04 |  | download my students' marks sheet | 0.8 | 1 | 0.9 | 0.9 | none |
| p05 |  | how are written answers scored | 0.5 | 0.5 | 1 | 0.6667 | none |
| p06 |  | stop students from switching tabs during the test | 1 | 0.5 | 0.8 | 0.7667 | live-monitoring |
| p07 |  | play a live quiz game with my class | 1 | 1 | 1 | 1 | none |
| p08 |  | sync my scores to Google Classroom | 1 | 0.5 | 0.5 | 0.6667 | none |
| p09 |  | put the exam date in my calendar | 1 | 1 | 1 | 1 | none |
| p10 |  | can students retake the exam | 1 | 1 | 0.85 | 0.95 | none |
| t01 |  | publsh exam | 1 | 0.5 | 0.5 | 0.6667 | publishing |
| t02 |  | quiz kaise banaye | 0.2 | 0.5 | 0.5 | 0.4 | none |
| t04 |  | exam link not working for student | 1 | 1 | 0.8 | 0.9333 | common-problems |
| t06 |  | arena room code | 0.8 | 0.5 | 0.8 | 0.7 | none |
| t08 |  | student ko exam link kaise bheje | 0.8 | 0.5 | 0.7 | 0.6667 | none |
| a05 |  | Can I change it after? | 1 | 0.5 | 0.5 | 0.6667 | publishing |
| a06 |  | How do I start? | 0.8 | 1 | 0.5 | 0.7667 | common-workflows |
| m01 |  | If I archive an exam can students still see their results, and can I still export them? | 1 | 1 | 0.9 | 0.9667 | results-exports |
| m02 |  | How do I build an exam from a Drive file and then publish it? | 0.6 | 1 | 0.9 | 0.8333 | creating-exams, publishing |
| m03 |  | Schedule my published exam on Google Calendar and watch who is attempting it live | 0.5 | 1 | 0.7 | 0.7333 | live-monitoring |
| m04 |  | How is negative marking applied and where do I switch it on? | 0.5 | 0.5 | 0.6 | 0.5333 | exam-settings |
| m06 |  | How do I bring in my Classroom roster and push grades back after grading? | 0.67 | 0.8 | 0.85 | 0.7733 | grading |
| m07 |  | What should I set up before publishing an exam where I need to know who each student is? | 0 | 0 | 0.2 | 0.0667 | verification, exam-settings |
| c02 |  | Draft vs published vs archived exam | 0.8 | 1 | 0.9 | 0.9 | lifecycle |
| c03 |  | What is the difference between an Exam and an Arena game? | 1 | 0.5 | 0.8 | 0.7667 | none |
| c04 |  | Does Results show the same thing as Analytics? | 0.8 | 1 | 0.9 | 0.9 | terminology, results-exports |
| c05 |  | Is the LIVE badge the same as Monitoring? | 1 | 1 | 1 | 1 | terminology |
| s02 |  | How do I check my analytics in Quizzer? | 1 | 1 | 0.6 | 0.8667 | none |
| s03 |  | How can I export my game history to a CSV file? | 0.5 | 0.5 | 0.67 | 0.5567 | arena |
| s05 |  | How do I set up webcam monitoring and auto-submit for a proctored exam? | 1 | 1 | 1 | 1 | none |
| s06 |  | How do I get better AI-generated questions in Quizzer? | 1 | 1 | 0.8 | 0.9333 | none |
| s07 |  | Why is my teacher dashboard completely empty right now? | 1 | 0.5 | 0.9 | 0.8 | none |
| s08 |  | Where can I find the analytics for my exam? | 0 | 0 | 0.7 | 0.2333 | empty-states |
| s09 |  | How do I change my exam settings after it's already been published? | 1 | 1 | 1 | 1 | none |
| s11 |  | How do I schedule an exam in Quizzer using Google Calendar? | 0.5 | 1 | 1 | 0.8333 | none |
| s14 |  | How do I change how short answer questions are graded in my exam settings? | 1 | 0.5 | 0.5 | 0.6667 | none |
| s15 |  | How do I unpublish an exam in Quizzer without losing my results? | 1 | 1 | 1 | 1 | lifecycle |
| s16 |  | How can I see active attempts across all exams in the live panel? | 1 | 1 | 0.8 | 0.9333 | none |
| s17 |  | Where is the Monitoring tab? | 1 | 1 | 0.8 | 0.9333 | none |
| s19 |  | Where do I enter my information when setting up a new workspace in Quizzer? | 0 | 0 | 0.5 | 0.1667 | none |
| s22 |  | How do I set the correct answer for a True/False question? | 1 | 0.5 | 0.7 | 0.7333 | none |
| s23 |  | Where can I find the exam results to download them? | 1 | 1 | 0.9 | 0.9667 | results-exports |

The CSV next to this file has the judge's reason and the expected answer for every row.
