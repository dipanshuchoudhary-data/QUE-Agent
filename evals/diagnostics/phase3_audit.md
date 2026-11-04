# Retrieval audit

Rows with any metric under 0.7: 45. Retrieval settings match the scored run (top-k 3, candidate pool 5, rerank on). Causes below are heuristic suggestions.

Suggested causes: EVIDENCE_MISS 20, CONTEXT_NOISE 18, AMBIGUOUS_QUERY 4, RANKING_FAILURE 1, LANGUAGE_MISMATCH / DOC_MISS 1, DOC_MISS 1

Production would serve these rows by: workflow_card 18, retrieval 16, tool 7, refuse 4

Rerank during this diagnostic: failed 44, skipped 1

## r01 — How do I create a quiz?

Scores: recall 0.9, precision 0.8, relevancy 0.67. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.create). Rerank: failed.
Expected docs: creating-exams. Fused doc order: arena, product-overview, creating-exams, onboarding, common-workflows, empty-states. Final: arena / Common Questions, product-overview / Quick Start: Your First Exam in 5 Minutes, creating-exams / Step-by-Step UI Guide: Creating Your First Exam.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To create a quiz, go to the Dashboard in the sidebar and click the Create Exam quick actio | creating-exams / Step-by-Step UI Guide: Creating Your First Exam | 0.94 | 3 | None | 3 | yes |
| Next, enter your exam title, add your source content by pasting text, uploading files, or  | creating-exams / Common Questions | 0.62 | 16 | 6 | 3 | no |
| Finally, click the Generate button at the bottom of the wizard to produce your questions | common-workflows / Create and Publish Your First Exam | 0.71 | 5 | None | 5 | no |

## r03 — How do I publish my exam?

Scores: recall 0.67, precision 0.67, relevancy 0.75. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: publishing. Fused doc order: publishing, account-settings, common-workflows, google-classroom, navigation, onboarding. Final: publishing / How to Publish, account-settings / Common Questions, common-workflows / Create and Publish Your First Exam.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To publish your exam, first ensure every question shows a green Approved badge on the Ques | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.91 | 3 | None | 1 | no |
| Next, click Exams in the left sidebar and open your exam workspace by clicking your exam c | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.75 | 3 | None | 1 | no |
| Finally, click the prominent emerald-green Publish button located on the exam card or at t | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.83 | 3 | None | 1 | no |

## r08 — How does grading work for short answers?

Scores: recall 0.6, precision 1.0, relevancy 0.5. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: grading. Fused doc order: grading, exam-settings. Final: grading / Written Question Grading, exam-settings / Scoring.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Short answer questions go through a layered smart grading pipeline that combines exact mat | grading / Overview | 0.94 | 8 | 3 | 1 | no |
| Each layer attempts to resolve the answer before escalating to the next step, and if confi | grading / Written Question Grading | 0.56 | 4 | 4 | 1 | no |

## r09 — Export results to CSV or Excel

Scores: recall 0.8, precision 0.67, relevancy 0.8. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.export_results). Rerank: failed.
Expected docs: results-exports. Fused doc order: results-exports, common-workflows, students-workspace, lifecycle, google-drive. Final: results-exports / Step-by-Step UI Guide: Viewing and Exporting Results, common-workflows / Export Results for Record-Keeping, students-workspace / CSV Export.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| In the left sidebar, click Exams and select the exam card, then click the Results tab at t | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.9 | 10 | None | 1 | no |
| Click the Export button (or dropdown menu) in the top-right area of the Results tab and ch | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 1.0 | 1 | 4 | 1 | yes |
| A background job starts, and you will receive an in-app notification with a download link  | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.8 | 1 | 4 | 1 | yes |

## r10 — What exam settings control time limits?

Scores: recall 0.5, precision 0.5, relevancy 0.67. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.settings). Rerank: failed.
Expected docs: exam-settings. Fused doc order: exam-settings, product-overview, lifecycle. Final: exam-settings / Overview, product-overview / What You Can Do, lifecycle / Lifecycle States.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To set exam time limits, go to Exams (sidebar), open the exam, and select the Settings tab | product-overview / What You Can Do | 0.78 | 10 | 1 | 2 | yes |
| Near the top of the Settings page, find the Duration field to change how long each student | exam-settings / Step-by-Step UI Guide: Configuring Exam Settings | 1.0 | 4 | None | 1 | no |

## r11 — How do students take an exam from a link?

Scores: recall 0.2, precision 0.5, relevancy 0.4. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: workflow_card (deterministic, exam.share). Rerank: failed.
Expected docs: taking-exams. Fused doc order: google-classroom, taking-exams, product-overview, arena, publishing, dashboard. Final: google-classroom / Common Questions, taking-exams / How Students Access an Exam, product-overview / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Students click the published exam link shared by the teacher to open the start page in the | taking-exams / Step-by-Step UI Guide: What Students See When Taking an | 0.88 | 2 | None | 2 | no |
| Next, they read the exam info, fill out the identity verification form (and enter an acces | taking-exams / Step-by-Step UI Guide: What Students See When Taking an | 0.86 | 5 | None | 2 | no |
| After granting any necessary browser permissions for fullscreen or webcam access, they ans | taking-exams / Step-by-Step UI Guide: What Students See When Taking an | 0.83 | 9 | None | 2 | no |
| Finally, when ready, they click the Submit button and confirm to complete the exam | taking-exams / Step-by-Step UI Guide: What Students See When Taking an | 0.71 | 7 | None | 2 | no |

## r14 — Difference between Monitoring and Analytics

Scores: recall 1.0, precision 1.0, relevancy 0.67. Category confusable. Suggested cause: **RANKING_FAILURE (doc found, cut before final)**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: terminology. Fused doc order: live-monitoring, analytics, students-workspace, results-exports, product-overview, terminology. Final: live-monitoring / Monitoring vs Results vs Analytics, analytics / Analytics vs Results, students-workspace / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Monitoring is a tab located inside each individual exam workspace that shows real-time dat | terminology / Monitoring | 0.77 | 5 | None | 6 | no |
| In contrast, Analytics is a sidebar workspace that shows aggregate performance data, trend | results-exports / Results vs Analytics | 0.83 | 3 | None | 4 | no |

## r15 — Teacher vs student role permissions

Scores: recall 0.5, precision 0.5, relevancy 1.0. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (complex_knowledge). Rerank: failed.
Expected docs: roles. Fused doc order: roles, students-workspace. Final: roles / Teacher Role, students-workspace / Students Workspace vs Student Accounts.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Teachers have full access to the sidebar workspaces (Dashboard, Exams, Arena, Students, An | roles / Permission Summary Table | 0.68 | 4 | None | 1 | no |
| In contrast, students who select the Student persona during onboarding receive a deliberat | roles / Student Role | 0.82 | 3 | 3 | 1 | no |
| Students enter exams exclusively through shared links, while exam takers without an accoun | product-overview / Two Separate Experiences | 0.65 | None | None | None | no |

## r16 — Students workspace cohort health

Scores: recall 0.67, precision 0.5, relevancy 1.0. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: students-workspace. Fused doc order: students-workspace, terminology, navigation. Final: students-workspace / Cohort Health, terminology / Cohort, navigation / Teacher Sidebar.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To access information about cohort health, open the Students workspace by clicking Student | google-classroom / Step-by-Step UI Guide: Connecting and Using Google  | 0.44 | None | None | None | no |
| Below the scope bar, check the metrics strip, which includes a "Cohort count" card showing | students-workspace / Metrics Strip | 0.53 | 3 | 7 | 1 | no |
| Additionally, a cohort health visualization displays the distribution of readiness across  | students-workspace / Cohort Health | 0.69 | 1 | 1 | 1 | yes |

## r21 — How do I send feedback about Quizzer?

Scores: recall 0.0, precision 0.0, relevancy 0.33. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: feedback. Fused doc order: feedback, common-problems, product-overview, navigation. Final: feedback / Overview, common-problems / Common Questions, product-overview / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| On desktop, scroll to the **ACCOUNT** section in the left sidebar and click **Send feedbac | feedback / How to Open Feedback (current UI) | 1.0 | 20 | 3 | 1 | no |
| On mobile, open the account or more menu from the bottom navigation and tap **Send feedbac | feedback / How to Open Feedback (current UI) | 1.0 | 20 | 3 | 1 | no |

## r25 — Common workflow create exam then share link

Scores: recall 1.0, precision 0.5, relevancy 1.0. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: common-workflows. Fused doc order: lifecycle, publishing, common-workflows, product-overview, google-calendar. Final: lifecycle / Typical Teacher Workflow (with UI steps), publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam, common-workflows / Create and Publish Your First Exam.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To create an exam and share the link, open Create Exam from the Dashboard or press Ctrl+K  | common-workflows / Create and Publish Your First Exam | 0.86 | 2 | None | 3 | no |
| Review and approve the questions in the Questions tab, configure your preferences in the S | lifecycle / Typical Teacher Workflow (with UI steps) | 0.91 | 5 | 2 | 1 | yes |
| Finally, click Copy Link on the success screen or find the URL on the Links tab to send it | common-workflows / Create and Publish Your First Exam | 0.9 | 1 | None | 3 | yes |

## r28 — Approve draft questions before publish

Scores: recall 0.5, precision 0.33, relevancy 0.75. Category multi_doc. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: questions, publishing. Fused doc order: questions, publishing, terminology, lifecycle, creating-exams. Final: questions / Step-by-Step UI Guide: Reviewing and Approving Questions, publishing / Publish Requirements, terminology / Draft / Approved / Rejected.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To approve draft questions before publishing, open your exam from the Exams workspace in t | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.83 | None | 11 | 2 | no |
| Review each question card and click the **Approve** button (checkmark icon or green action | questions / Step-by-Step UI Guide: Reviewing and Approving Questions | 1.0 | 4 | 13 | 1 | no |
| All questions must be in Approved status before you can publish the exam | questions / Question Review Workflow | 1.0 | 3 | 8 | 1 | no |

## r30 — Command palette and sidebar navigation

Scores: recall 0.5, precision 1.0, relevancy 1.0. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: refuse (out_of_scope). Rerank: skipped.
Expected docs: navigation. Fused doc order: navigation. Final: navigation / Command Palette.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Press Ctrl+K (Windows) or Cmd+K (Mac) to open the command palette, a search overlay used t | navigation / Step-by-Step UI Guide: Finding Your Way Around | 1.0 | 3 | 4 | 1 | no |
| To navigate the sidebar, click Exams on the left side of the screen to view your exam libr | navigation / Step-by-Step UI Guide: Finding Your Way Around | 0.75 | 3 | 4 | 1 | no |
| At the top of the exam workspace, a tab row appears allowing you to switch between Questio | navigation / Step-by-Step UI Guide: Finding Your Way Around | 0.93 | 3 | 4 | 1 | no |

## p01 — I want to make a test for my class from my PDF notes

Scores: recall 0.5, precision 0.33, relevancy 0.4. Category paraphrase. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: refuse (out_of_scope). Rerank: failed.
Expected docs: creating-exams. Fused doc order: common-workflows, onboarding, creating-exams, google-classroom, account-settings, product-overview. Final: common-workflows / Create and Publish Your First Exam, onboarding / Common Questions, creating-exams / Step-by-Step UI Guide: Creating Your First Exam.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To create a test from your PDF notes, go to the Dashboard in the sidebar and click the Cre | creating-exams / Step-by-Step UI Guide: Creating Your First Exam | 0.86 | 9 | None | 3 | no |
| Enter your exam title, then upload your PDF file in the source content panel by dragging a | creating-exams / Step-by-Step UI Guide: Creating Your First Exam | 0.58 | 2 | 13 | 3 | yes |
| Choose an AI generation mode (such as Source-first or Guided) and click the Generate butto | creating-exams / Step 3: AI Generation Mode | 0.88 | None | None | 3 | no |
| Finally, open the exam from the Exams list, review your questions under the Questions tab, | creating-exams / Step-by-Step UI Guide: Creating Your First Exam | 0.78 | None | None | 3 | no |

## p02 — how do I put my quiz online so students can attempt it

Scores: recall 0.8, precision 0.67, relevancy 0.67. Category paraphrase. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: publishing. Fused doc order: publishing, common-workflows, account-settings, product-overview, google-classroom, empty-states. Final: publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam, common-workflows / Create and Publish Your First Exam, account-settings / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To put your quiz online, first open your exam workspace by clicking "Exams" in the left si | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.58 | None | None | 1 | no |
| Go to the Questions tab to verify that every question shows a green "Approved" badge, appr | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.83 | None | None | 1 | no |
| Next, click the prominent emerald-green "Publish" button located on the exam card or at th | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.82 | None | None | 1 | no |
| Finally, copy the generated exam URL from the success screen or the Links tab to share the | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.91 | 3 | None | 1 | yes |

## p04 — download my students' marks sheet

Scores: recall 1.0, precision 0.67, relevancy 0.8. Category paraphrase. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge, results.export). Rerank: failed.
Expected docs: results-exports. Fused doc order: students-workspace, results-exports, common-workflows, account-settings, terminology. Final: students-workspace / CSV Export, results-exports / Export Options, common-workflows / Export Results for Record-Keeping.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To download your students' marks, click Exams in the left sidebar and select the specific  | common-problems / LIVE and Monitoring Problems | 0.62 | None | None | None | no |
| At the top of the exam workspace, click the Results tab, then click the Export button (usu | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.8 | 3 | None | 2 | no |
| Choose your format—CSV, Excel, or Google Sheets—to start a background job | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.89 | 3 | None | 2 | no |
| Once ready, you will receive an in-app notification via the bell icon in the top bar conta | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.75 | 3 | None | 2 | no |

## p05 — how are written answers scored

Scores: recall 0.5, precision 0.5, relevancy 0.6. Category paraphrase. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: grading. Fused doc order: grading, exam-settings, results-exports. Final: grading / Written Question Grading, exam-settings / Scoring, results-exports / Filtering Results.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Written answers (Short Answer and Long Answer) go through a layered grading pipeline | grading / Written Question Grading | 1.0 | 1 | 16 | 1 | yes |
| Step 1 is exact match after normalization, awarding full marks immediately if correct | grading / Written Question Grading | 0.8 | 1 | 16 | 1 | yes |
| Step 2 uses fuzzy match for short strings to catch minor typos | grading / Written Question Grading | 0.78 | 1 | 16 | 1 | yes |
| Step 3 checks keyword overlap for essential concepts, and Step 4 applies embedding similar | grading / Written Question Grading | 0.55 | 1 | 16 | 1 | yes |
| Step 5 uses a batched AI model if previous steps cannot score it, and Step 6 marks it as " | grading / Written Question Grading | 0.82 | 4 | 5 | 1 | no |

## p06 — stop students from switching tabs during the test

Scores: recall 0.5, precision 0.5, relevancy 0.67. Category paraphrase. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: exam-settings, live-monitoring. Fused doc order: taking-exams, exam-settings, results-exports, product-overview. Final: taking-exams / Proctoring During the Exam (Step 7), exam-settings / Proctoring and Integrity, results-exports / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To stop students from switching tabs during a test, open Exams from the left sidebar and c | questions / Step-by-Step UI Guide: Reviewing and Approving Questions | 0.64 | None | None | None | no |
| Click the Settings tab at the top of the workspace, and scroll down to the Proctoring and  | common-workflows / Run a Proctored Exam | 0.88 | None | 18 | None | no |
| Ensure the "Block Tab Switching" toggle switch is turned on, as it is enabled by default t | exam-settings / Step-by-Step UI Guide: Configuring Exam Settings | 0.75 | 3 | 14 | 2 | no |
| Settings auto-save as you make changes | verification / Step-by-Step UI Guide: Setting Up Verification Schema | 0.8 | None | None | None | no |

## p08 — sync my scores to Google Classroom

Scores: recall 0.5, precision 0.5, relevancy 1.0. Category paraphrase. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: workflow_card (deterministic, exam.export_results). Rerank: failed.
Expected docs: google-classroom. Fused doc order: google-classroom, common-workflows, arena. Final: google-classroom / Overview, common-workflows / Share Results with Students via Classroom, arena / Google Classroom Integration.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Scores are automatically synced back to the Google Classroom coursework entry after studen | google-classroom / Step-by-Step UI Guide: Connecting and Using Google  | 1.0 | 5 | 7 | 1 | no |
| Teachers can also trigger a manual grade push from the Classroom section in Integrations | google-classroom / Step-by-Step UI Guide: Connecting and Using Google  | 0.86 | 5 | 7 | 1 | no |

## p09 — put the exam date in my calendar

Scores: recall 1.0, precision 0.5, relevancy 0.67. Category paraphrase. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: google-calendar. Fused doc order: google-calendar, common-workflows, empty-states. Final: google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google Calendar, common-workflows / Schedule an Exam with Google Calendar, empty-states / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To put the exam date in your calendar, first make sure your exam is published and your Goo | google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google  | 0.85 | 3 | 9 | 1 | no |
| Then, schedule the exam either by clicking "Schedule on Calendar" from the post-publish su | google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google  | 0.67 | 3 | 9 | 1 | no |
| Finally, choose the date and time for the event and click "Schedule" to create the calenda | google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google  | 0.8 | 1 | 1 | 1 | yes |

## p11 — what happens to my exam when I archive it

Scores: recall 0.8, precision 0.8, relevancy 0.5. Category paraphrase. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: lifecycle. Fused doc order: lifecycle, publishing, onboarding, empty-states. Final: lifecycle / Typical Teacher Workflow (with UI steps), publishing / Common Questions, onboarding / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| When you archive an exam, it is retired so that students cannot start new attempts, and it | lifecycle / State Transitions | 1.0 | 12 | None | 1 | no |
| All existing results are preserved and remain accessible in the Results tab | lifecycle / Common Questions | 0.83 | 8 | 2 | 1 | no |
| Additionally, archived exams can later be unarchived | lifecycle / Lifecycle States | 0.6 | 11 | None | 1 | no |

## p12 — see who is cheating right now

Scores: recall 0.8, precision 0.67, relevancy 0.67. Category paraphrase. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: refuse (out_of_scope). Rerank: failed.
Expected docs: live-monitoring. Fused doc order: live-monitoring, students-workspace, common-workflows, terminology, dashboard. Final: live-monitoring / Step-by-Step UI Guide: Monitoring Live Exams, students-workspace / Readiness Labels, common-workflows / Run a Proctored Exam.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To see who is cheating or taking an exam right now, click **Exams** in the left sidebar an | dashboard / Step-by-Step UI Guide: Using the Dashboard | 0.92 | None | 9 | 5 | no |
| Alternatively, you can view the **Live Exams panel** on the Dashboard for a quick overview | live-monitoring / Step-by-Step UI Guide: Monitoring Live Exams | 0.89 | 1 | None | 1 | yes |
| Click on an active exam card and select the **Monitoring tab**, where you will see a table | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.67 | None | None | None | no |
| Click on a specific attempt row to expand the integrity detail panel and view a real-time, | live-monitoring / Step-by-Step UI Guide: Monitoring Live Exams | 0.95 | 1 | None | 1 | yes |

## t01 — publsh exam

Scores: recall 0.75, precision 0.67, relevancy 0.67. Category typo_short_hinglish. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: publishing. Fused doc order: publishing, lifecycle, terminology, navigation, common-workflows, empty-states. Final: publishing / How to Publish, lifecycle / Delete Behavior, terminology / Publish.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To publish an exam, first ensure that all questions are approved by checking the Questions | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.78 | 4 | 15 | 1 | no |
| Next, click the emerald-green Publish button located either on the exam card in the Exams  | publishing / Step-by-Step UI Guide: Publishing and Sharing Your Exam | 0.77 | 4 | 15 | 1 | no |
| Once published, a success screen will appear providing the unique shareable exam link | publishing / The Published Exam Link | 0.6 | 17 | 5 | 1 | no |

## t02 — quiz kaise banaye

Scores: recall 0.0, precision 0.0, relevancy 0.0. Category typo_short_hinglish. Suggested cause: **LANGUAGE_MISMATCH / DOC_MISS**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: creating-exams. Fused doc order: arena, product-overview, empty-states, terminology. Final: arena / Creating an Arena Quiz Pack, product-overview / Who Quizzer is For, empty-states / Arena Workspace.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To create a quiz or exam in Quizzer, go to the Dashboard in the sidebar and click the Crea | creating-exams / Step-by-Step UI Guide: Creating Your First Exam | 0.93 | 17 | None | None | no |
| Enter an exam title, add your source content by pasting text, uploading files, providing a | common-workflows / Create and Publish Your First Exam | 0.67 | 16 | None | None | no |
| Finally, click the Generate button at the bottom to produce your questions | creating-exams / Step-by-Step UI Guide: Creating Your First Exam | 0.67 | None | None | None | no |

## t06 — arena room code

Scores: recall 0.5, precision 1.0, relevancy 1.0. Category typo_short_hinglish. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: arena. Fused doc order: arena, common-problems, terminology. Final: arena / Overview, common-problems / Arena Problems, terminology / Arena.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| When a teacher creates an Arena room, Quizzer generates a six-character room code and a jo | arena / Step-by-Step UI Guide: Hosting an Arena Live Quiz Battle | 0.9 | 4 | 1 | 1 | no |
| The room screen prominently displays this code, which can be shared by clicking copy code, | arena / Step-by-Step UI Guide: Hosting an Arena Live Quiz Battle | 0.64 | 4 | 1 | 1 | no |
| Teachers should project this screen on a classroom display so students can see the code | arena / Step-by-Step UI Guide: Hosting an Arena Live Quiz Battle | 0.83 | 4 | 1 | 1 | no |
| Players then join the game by opening the join link or going to the Arena join page to ent | arena / Joining a Game (Players) | 0.79 | 6 | 8 | 1 | no |

## a01 — Where are my results?

Scores: recall 1.0, precision 0.67, relevancy 1.0. Category ambiguous. Suggested cause: **AMBIGUOUS_QUERY**.
Production route: workflow_card (deterministic, exam.export_results). Rerank: failed.
Expected docs: results-exports, navigation, analytics. Fused doc order: results-exports, empty-states, navigation, common-problems, terminology. Final: results-exports / How to Access Results, empty-states / Results Tab (inside an exam), navigation / Critical Navigation Rule.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To see your results, open Exams from the sidebar, click on the specific exam card, and sel | navigation / Step-by-Step UI Guide: Finding Your Way Around | 0.9 | None | None | 3 | no |

## a02 — It's not working

Scores: recall 0.5, precision 0.67, relevancy 0.67. Category ambiguous. Suggested cause: **AMBIGUOUS_QUERY**.
Production route: refuse (out_of_scope). Rerank: failed.
Expected docs: common-problems. Fused doc order: common-problems, taking-exams, empty-states, google-calendar. Final: common-problems / Browser and Performance Problems, taking-exams / Common Questions, empty-states / Quick Diagnosis Checklist.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| If you are experiencing problems, find your symptom in the common-problems guide and follo | common-problems / Overview | 1.0 | 2 | 2 | 1 | no |
| Users call this issue help, troubleshooting, something is wrong, not working, fix, error,  | common-problems / Overview | 1.0 | 2 | 2 | 1 | no |
| If your specific problem is not listed, try checking the feature-specific guide or use **S | common-problems / Common Questions | 1.0 | 5 | None | 1 | no |

## a05 — Can I change it after?

Scores: recall 1.0, precision 0.5, relevancy 0.67. Category ambiguous. Suggested cause: **AMBIGUOUS_QUERY**.
Production route: workflow_card (deterministic, exam.settings). Rerank: failed.
Expected docs: exam-settings, publishing. Fused doc order: questions, exam-settings, onboarding, lifecycle, account-settings, grading. Final: questions / Editing AI-Generated Questions, exam-settings / Settings After Publishing, onboarding / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Yes, most exam settings can be changed at any time, including after publishing | exam-settings / Overview | 0.88 | None | None | 2 | no |
| Changes affect future attempts only, and do not affect in-progress ones | exam-settings / Overview | 1.0 | None | None | 2 | no |

## a06 — How do I start?

Scores: recall 0.0, precision 0.0, relevancy 0.33. Category ambiguous. Suggested cause: **AMBIGUOUS_QUERY**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: onboarding, common-workflows. Fused doc order: account-settings, creating-exams, empty-states, publishing, exam-settings, product-overview. Final: account-settings / Common Questions, creating-exams / How to Start, empty-states / Dashboard — New Account.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To start using Quizzer, open the app in your browser and click the Sign Up link on the log | onboarding / Step-by-Step UI Guide: Signing Up and Onboarding | 0.75 | 8 | None | 7 | no |
| You can create your account using your email and password, or choose Google or Microsoft S | onboarding / Step-by-Step UI Guide: Signing Up and Onboarding | 1.0 | 8 | None | 7 | no |
| After signing in, you will go through a four-step onboarding flow where you enter your dis | onboarding / Step-by-Step UI Guide: Signing Up and Onboarding | 0.61 | 11 | None | 7 | no |

## m02 — How do I build an exam from a Drive file and then publish it?

Scores: recall 1.0, precision 0.67, relevancy 1.0. Category multi_doc. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: google-drive, creating-exams, publishing. Fused doc order: google-drive, publishing, common-workflows, google-classroom. Final: google-drive / Step-by-Step UI Guide: Using Google Drive with Quizzer, publishing / How to Publish, common-workflows / Create and Publish Your First Exam.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To build an exam from a Drive file, go to Dashboard and click Create Exam, add source cont | common-workflows / Create and Publish Your First Exam | 0.79 | 1 | None | 3 | yes |
| Once generation is complete, go to the Questions tab to approve all questions | product-overview / Quick Start: Your First Exam in 5 Minutes | 1.0 | 19 | None | None | no |
| Finally, click the Publish action from the exam card or the exam workspace | publishing / Common Questions | 0.83 | 7 | 4 | 2 | no |

## m03 — Schedule my published exam on Google Calendar and watch who is attempting it live

Scores: recall 0.5, precision 1.0, relevancy 1.0. Category multi_doc. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: google-calendar, live-monitoring. Fused doc order: common-workflows, google-calendar. Final: common-workflows / Schedule an Exam with Google Calendar, google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google Calendar.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To schedule your published exam on Google Calendar, go to Integrations in the sidebar, fin | google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google  | 1.0 | 2 | 1 | 2 | yes |
| Choose the date and time, and click Schedule to create an event on your primary Google Cal | google-calendar / Step-by-Step UI Guide: Scheduling an Exam on Google  | 0.85 | 4 | 7 | 2 | no |
| To watch who is attempting it live, click Exams in the sidebar, open the exam showing a pu | terminology / Monitoring | 0.79 | None | None | None | no |
| Alternatively, you can check the Live Exams panel on the Dashboard for a quick overview ac | live-monitoring / Step-by-Step UI Guide: Monitoring Live Exams | 0.89 | None | None | None | no |

## m04 — How is negative marking applied and where do I switch it on?

Scores: recall 0.5, precision 0.5, relevancy 0.67. Category multi_doc. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: grading, exam-settings. Fused doc order: grading, navigation, terminology, exam-settings, google-drive, questions. Final: grading / Negative Marking, navigation / Overview, terminology / Negative Marking.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To switch on negative marking, open your exam from the Exams workspace, go to the Settings | navigation / Exam Workspace | 0.67 | None | None | 2 | no |
| Once enabled, a Penalty field appears where you can set the specific deduction amount per  | exam-settings / Step-by-Step UI Guide: Configuring Exam Settings | 0.82 | 6 | None | 4 | no |

## m06 — How do I bring in my Classroom roster and push grades back after grading?

Scores: recall 0.86, precision 0.67, relevancy 0.67. Category multi_doc. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: retrieval (simple_knowledge, student.view). Rerank: failed.
Expected docs: google-classroom, grading. Fused doc order: google-classroom, common-workflows, empty-states, students-workspace. Final: google-classroom / Step-by-Step UI Guide: Connecting and Using Google Classroom, common-workflows / Share Results with Students via Classroom, empty-states / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To bring in your Google Classroom roster and push grades back, go to the Integrations page | google-classroom / Common Questions | 0.73 | 2 | 1 | 1 | no |
| After connecting, go to the Classroom section in Integrations to import your courses, and  | google-classroom / Common Questions | 0.86 | 2 | 1 | 1 | no |
| Once students take the exam and grading completes, scores are automatically synced back to | google-classroom / Step-by-Step UI Guide: Connecting and Using Google  | 0.89 | 1 | 2 | 1 | yes |

## m07 — What should I set up before publishing an exam where I need to know who each student is?

Scores: recall 0.0, precision 0.0, relevancy 0.33. Category multi_doc. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: verification, exam-settings, publishing. Fused doc order: empty-states, common-workflows, exam-settings, verification, product-overview, roles. Final: empty-states / Common Questions, common-workflows / Create and Publish Your First Exam, exam-settings / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Before publishing an exam where you need to identify each student, you should set up the V | verification / Common Questions | 0.68 | None | 2 | 4 | no |

## c05 — Is the LIVE badge the same as Monitoring?

Scores: recall 0.5, precision 0.0, relevancy 0.67. Category confusable. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: terminology, live-monitoring. Fused doc order: live-monitoring, terminology, dashboard, common-problems. Final: live-monitoring / LIVE Badge Definition, terminology / LIVE, dashboard / Teacher Dashboard.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| No, the LIVE badge is not the same as Monitoring | terminology / Common Confusions | 1.0 | 16 | 4 | 2 | no |
| The LIVE badge is an at-a-glance indicator on exam workspace cards and the Dashboard that  | terminology / LIVE | 0.86 | 5 | 19 | 2 | yes |
| In contrast, Monitoring is a specific tab within each exam workspace that provides detaile | live-monitoring / Overview | 0.83 | 3 | 12 | 1 | no |

## s02 — How do I check my analytics in Quizzer?

Scores: recall 0.0, precision 0.0, relevancy 0.33. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: analytics. Fused doc order: account-settings, analytics, empty-states, terminology, navigation, publishing. Final: account-settings / Common Questions, analytics / Step-by-Step UI Guide: Using Analytics, empty-states / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Click Analytics (chart icon) in the left sidebar to open the Analytics workspace | analytics / Step-by-Step UI Guide: Using Analytics | 1.0 | 3 | None | 2 | no |

## s06 — How do I get better AI-generated questions in Quizzer?

Scores: recall 1.0, precision 0.5, relevancy 0.33. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: creating-exams. Fused doc order: questions, creating-exams, notifications, product-overview, empty-states, account-settings. Final: questions / Common Questions, creating-exams / Tips for Better AI Generation, notifications / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Provide clear, well-structured source content with organized material, clear topics, and c | creating-exams / Tips for Better AI Generation | 1.0 | 2 | 2 | 2 | yes |

## s08 — Where can I find the analytics for my exam?

Scores: recall 0.0, precision 0.0, relevancy 0.67. Category basic. Suggested cause: **DOC_MISS**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: empty-states. Fused doc order: analytics, navigation, dashboard, results-exports, empty-states. Final: analytics / How to Access, navigation / Common Questions, dashboard / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Analytics will show data after students take and submit the exam, grading completes, and t | empty-states / Common Questions | 0.86 | None | 5 | 5 | no |

## s09 — How do I change my exam settings after it's already been published?

Scores: recall 1.0, precision 1.0, relevancy 0.67. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: exam-settings. Fused doc order: exam-settings, account-settings, lifecycle, onboarding, grading, navigation. Final: exam-settings / Settings After Publishing, account-settings / Common Questions, lifecycle / Settings Changes After Publishing.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Most settings can be changed on a published exam, but they generally only affect future at | exam-settings / Settings After Publishing | 0.85 | 1 | 6 | 1 | yes |
| Finalize settings before publishing when possible, as changes only impact students who sta | exam-settings / Settings After Publishing | 0.83 | 1 | 6 | 1 | yes |

## s14 — How do I change how short answer questions are graded in my exam settings?

Scores: recall 1.0, precision 1.0, relevancy 0.67. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: workflow_card (deterministic, exam.settings). Rerank: failed.
Expected docs: grading. Fused doc order: grading, exam-settings, account-settings, questions, navigation. Final: grading / Common Questions, exam-settings / Scoring, account-settings / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Use the Answer Grading Style setting on the exam's Settings tab to control how written ans | grading / Grading Style | 0.91 | 4 | None | 1 | no |

## s15 — How do I unpublish an exam in Quizzer without losing my results?

Scores: recall 1.0, precision 1.0, relevancy 0.67. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.unpublish). Rerank: failed.
Expected docs: lifecycle. Fused doc order: publishing, lifecycle, account-settings, navigation, results-exports, notifications. Final: publishing / What Happens to Results, lifecycle / What Happens to Results, account-settings / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Simply unpublish the exam | publishing / State Transitions | 0.67 | None | None | 1 | no |
| Results stay and remain accessible in the Results tab | publishing / What Happens to Results | 1.0 | 1 | 4 | 1 | yes |

## s19 — Where do I enter my information when setting up a new workspace in Quizzer?

Scores: recall 0.0, precision 0.0, relevancy 0.33. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: retrieval (simple_knowledge). Rerank: failed.
Expected docs: onboarding. Fused doc order: onboarding, navigation, product-overview, account-settings, verification, notifications. Final: onboarding / The Four Onboarding Screens (inside Steps 3-6 above), navigation / Common Questions, product-overview / Two Separate Experiences.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Enter your optional details (such as Institution, Subject Area, and Courses Taught based o | onboarding / Step-by-Step UI Guide: Signing Up and Onboarding | 0.86 | 4 | None | 1 | no |

## s21 — How do I publish an exam in Quizzer?

Scores: recall 1.0, precision 1.0, relevancy 0.67. Category basic. Suggested cause: **CONTEXT_NOISE (off-topic docs in final set)**.
Production route: workflow_card (deterministic, exam.publish). Rerank: failed.
Expected docs: publishing. Fused doc order: publishing, common-workflows, google-classroom, questions, terminology, notifications. Final: publishing / How to Publish, common-workflows / Create and Publish Your First Exam, google-classroom / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Open your exam from the Exams workspace, then use the Publish action found on the exam car | publishing / How to Publish | 0.88 | 3 | None | 1 | yes |

## s22 — How do I set the correct answer for a True/False question?

Scores: recall 1.0, precision 1.0, relevancy 0.33. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: workflow_card (deterministic, exam.settings). Rerank: failed.
Expected docs: questions. Fused doc order: questions, taking-exams, terminology, grading. Final: questions / Correct Answers, taking-exams / Answering Questions (Step 6), terminology / Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| Mark one of True or False as correct | grading / Common Questions | 1.0 | 7 | None | 4 | no |

## s23 — Where can I find the exam results to download them?

Scores: recall 0.5, precision 0.33, relevancy 0.75. Category basic. Suggested cause: **EVIDENCE_MISS (right doc, supporting chunk not selected)**.
Production route: tool (tool_required). Rerank: failed.
Expected docs: results-exports. Fused doc order: results-exports, common-workflows, navigation, google-drive. Final: results-exports / How to Access Results, common-workflows / Export Results for Record-Keeping, navigation / Common Questions.

| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |
|---|---|---:|---:|---:|---:|---|
| To find the exam results to download, go to the Results tab at the top of the exam workspa | results-exports / Step-by-Step UI Guide: Viewing and Exporting Results | 0.8 | 5 | None | 1 | no |
