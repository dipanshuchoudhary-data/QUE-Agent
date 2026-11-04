# Retriever eval report

Source: `retriever_final_nemotron.json`.

## Averages

| Metric | Mean |
|---|---:|
| Contextual recall | 0.8121 |
| Contextual precision | 0.8119 |
| Contextual relevancy | 0.8593 |
| Average of the three | 0.8278 |
| Abstention | 9/12 |
| Injected characters | 1592.8 |
| Latency p50 / p95 (ms) | 2203.1 / 2878.3 |

Settings: top-k 2, candidate pool 4, dense floor 0.28.

A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. `below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.

## Every row

| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |
|---|---|---|---:|---:|---:|---:|---|
| r01 |  | How do I create a quiz? | 0.6 | 1 | 1 | 0.8667 | none |
| r02 |  | Where is Monitoring in the sidebar? | 1 | 1 | 1 | 1 | live-monitoring |
| r03 |  | How do I publish my exam? | 0.67 | 1 | 1 | 0.89 | none |
| r04 |  | What is verification schema before an exam? | 0.9 | 1 | 0.9 | 0.9333 | none |
| r05 |  | How do I host an Arena battle with a room code? | 1 | 1 | 1 | 1 | none |
| r06 |  | Connect Google Classroom and push grades | 1 | 1 | 0.8 | 0.9333 | none |
| r07 |  | Why is Analytics empty with no data? | 1 | 1 | 0.9 | 0.9667 | none |
| r08 |  | How does grading work for short answers? | 1 | 1 | 0.75 | 0.9167 | none |
| r09 |  | Export results to CSV or Excel | 0.8 | 0 | 0.9 | 0.5667 | none |
| r10 |  | What exam settings control time limits? | 0.5 | 0.5 | 0.8 | 0.6 | none |
| r11 |  | How do students take an exam from a link? | 0.2 | 0.5 | 0.8 | 0.5 | none |
| r12 |  | Question types MCQ and true false | 0.67 | 1 | 0.8 | 0.8233 | none |
| r13 |  | What is Quizzer and who is it for? | 0.85 | 1 | 1 | 0.95 | none |
| r14 |  | Difference between Monitoring and Analytics | 1 | 1 | 0.8 | 0.9333 | none |
| r15 |  | Teacher vs student role permissions | 0.8 | 1 | 1 | 0.9333 | none |
| r16 |  | Students workspace cohort health | 0.67 | 1 | 1 | 0.89 | none |
| r17 |  | Schedule exam on Google Calendar | 0.8 | 0.5 | 0.83 | 0.71 | none |
| r18 |  | Import source files from Google Drive | 0.86 | 0.5 | 1 | 0.7867 | none |
| r19 |  | How does onboarding work after signup? | 0.75 | 1 | 1 | 0.9167 | none |
| r20 |  | Change account settings and profile | 0.9 | 1 | 1 | 0.9667 | none |
| r21 |  | How do I send feedback about Quizzer? | 1 | 1 | 1 | 1 | none |
| r22 |  | Notification preferences and email | 1 | 0.5 | 0.8 | 0.7667 | none |
| r23 |  | What shows on the teacher dashboard? | 1 | 1 | 0.9 | 0.9667 | none |
| r24 |  | Exam lifecycle draft published archived | 0.9 | 1 | 1 | 0.9667 | none |
| r25 |  | Common workflow create exam then share link | 1 | 1 | 1 | 1 | common-workflows |
| r26 |  | Generation failed or daily AI quota | 1 | 1 | 1 | 1 | common-problems |
| r27 |  | Integrity events and live proctoring | 0.8 | 0.8 | 0.9 | 0.8333 | none |
| r28 |  | Approve draft questions before publish | 0.83 | 1 | 0.9 | 0.91 | questions |
| r29 |  | Negative marking settings | 0.8 | 1 | 0.7 | 0.8333 | grading |
| r30 |  | Command palette and sidebar navigation | 0.5 | 0.5 | 0.75 | 0.5833 | none |
| r31 |  | Link window vs exam duration meaning | 1 | 1 | 1 | 1 | exam-settings |
| r32 |  | Join Arena as a player with code | 0.33 | 0.5 | 0.6 | 0.4767 | none |
| r33 |  | Results tab integrity review | 1 | 1 | 0.8 | 0.9333 | none |
| r34 |  | Cannot publish questions stuck in draft | 1 | 1 | 1 | 1 | none |
| p01 |  | I want to make a test for my class from my PDF notes | 0.8 | 0.5 | 1 | 0.7667 | none |
| p02 |  | how do I put my quiz online so students can attempt it | 0.5 | 0.5 | 0.8 | 0.6 | none |
| p03 |  | give students the link to the exam | 0.5 | 1 | 1 | 0.8333 | none |
| p04 |  | download my students' marks sheet | 0.85 | 0.9 | 0.8 | 0.85 | none |
| p05 |  | how are written answers scored | 0.8 | 0.5 | 0.9 | 0.7333 | none |
| p06 |  | stop students from switching tabs during the test | 0.8 | 1 | 0.9 | 0.9 | live-monitoring |
| p07 |  | play a live quiz game with my class | 1 | 1 | 1 | 1 | none |
| p08 |  | sync my scores to Google Classroom | 1 | 0.5 | 0.8 | 0.7667 | none |
| p09 |  | put the exam date in my calendar | 1 | 1 | 1 | 1 | none |
| p10 |  | can students retake the exam | 1 | 1 | 0.8 | 0.9333 | exam-settings |
| p11 |  | what happens to my exam when I archive it | 1 | 1 | 0.8 | 0.9333 | none |
| p12 |  | see who is cheating right now | 0.85 | 0.5 | 0.6 | 0.65 | none |
| t01 |  | publsh exam | 0.67 | 1 | 1 | 0.89 | none |
| t02 |  | quiz kaise banaye | 0.2 | 0.5 | 0.8 | 0.5 | creating-exams |
| t03 |  | results? | 0.8 | 1 | 1 | 0.9333 | none |
| t04 |  | exam link not working for student | 0.67 | 1 | 0.5 | 0.7233 | common-problems, publishing |
| t05 |  | negetive marking | 1 | 1 | 0.75 | 0.9167 | exam-settings |
| t06 |  | arena room code | 1 | 1 | 0.8 | 0.9333 | none |
| t07 |  | analytcs empty | 1 | 1 | 1 | 1 | none |
| t08 |  | student ko exam link kaise bheje | 0 | 0 | 0.5 | 0.1667 | publishing |
| a01 |  | Where are my results? | 1 | 1 | 1 | 1 | results-exports, analytics |
| a02 |  | It's not working | 1 | 0.5 | 0.75 | 0.75 | none |
| a06 |  | How do I start? | 0 | 0 | 0 | 0 | onboarding, common-workflows |
| m01 |  | If I archive an exam can students still see their results, and can I still export them? | 1 | 1 | 1 | 1 | lifecycle, results-exports |
| m02 |  | How do I build an exam from a Drive file and then publish it? | 0.85 | 1 | 1 | 0.95 | creating-exams |
| m03 |  | Schedule my published exam on Google Calendar and watch who is attempting it live | 0.5 | 1 | 1 | 0.8333 | live-monitoring |
| m04 |  | How is negative marking applied and where do I switch it on? | 0.5 | 0.5 | 0.5 | 0.5 | exam-settings |
| m06 |  | How do I bring in my Classroom roster and push grades back after grading? | 0.8 | 1 | 1 | 0.9333 | grading |
| m07 |  | What should I set up before publishing an exam where I need to know who each student is? | 1 | 1 | 1 | 1 | exam-settings |
| m10 |  | My Analytics page is empty. Is that a bug or do I need exams first? | 1 | 1 | 1 | 1 | none |
| c02 |  | Draft vs published vs archived exam | 1 | 0.5 | 1 | 0.8333 | none |
| c03 |  | What is the difference between an Exam and an Arena game? | 1 | 1 | 0.8 | 0.9333 | product-overview |
| c04 |  | Does Results show the same thing as Analytics? | 1 | 1 | 0.8 | 0.9333 | terminology |
| c05 |  | Is the LIVE badge the same as Monitoring? | 1 | 1 | 1 | 1 | none |
| s02 |  | How do I check my analytics in Quizzer? | 0 | 0 | 0.5 | 0.1667 | none |
| s03 |  | How can I export my game history to a CSV file? | 1 | 1 | 0.8 | 0.9333 | none |
| s05 |  | How do I set up webcam monitoring and auto-submit for a proctored exam? | 1 | 1 | 1 | 1 | none |
| s06 |  | How do I get better AI-generated questions in Quizzer? | 1 | 1 | 0.5 | 0.8333 | none |
| s07 |  | Why is my teacher dashboard completely empty right now? | 1 | 1 | 0.5 | 0.8333 | none |
| s08 |  | Where can I find the analytics for my exam? | 0 | 0 | 0.8 | 0.2667 | empty-states |
| s09 |  | How do I change my exam settings after it's already been published? | 1 | 1 | 1 | 1 | none |
| s11 |  | How do I schedule an exam in Quizzer using Google Calendar? | 1 | 1 | 1 | 1 | none |
| s14 |  | How do I change how short answer questions are graded in my exam settings? | 1 | 1 | 0.8 | 0.9333 | none |
| s15 |  | How do I unpublish an exam in Quizzer without losing my results? | 1 | 1 | 1 | 1 | none |
| s16 |  | How can I see active attempts across all exams in the live panel? | 1 | 1 | 0.8 | 0.9333 | none |
| s17 |  | Where is the Monitoring tab? | 1 | 1 | 1 | 1 | none |
| s19 |  | Where do I enter my information when setting up a new workspace in Quizzer? | 1 | 0.5 | 0.75 | 0.75 | none |
| s21 |  | How do I publish an exam in Quizzer? | 0 | 0 | 0.5 | 0.1667 | publishing |
| s22 |  | How do I set the correct answer for a True/False question? | 1 | 0.5 | 1 | 0.8333 | none |
| s23 |  | Where can I find the exam results to download them? | 1 | 0.5 | 1 | 0.8333 | none |

The CSV next to this file has the judge's reason and the expected answer for every row.
