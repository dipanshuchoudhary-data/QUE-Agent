# DeepEval pipeline scores, per query

Rows: 13. Bar: 0.7. Reference answers are provisional. Marked `*` = below the bar.

Retriever: contextual recall, precision, relevancy. Generator: faithfulness, answer relevancy, answer correctness (G-Eval against the reference).

| Query | Recall | Precision | Relevancy | Faithfulness | Answer relevancy | Correctness |
|---|---:|---:|---:|---:|---:|---:|
| c03 What is the difference between an Exam and an Arena game? | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| a05 Can I change it after? | 0.00* | 0.00* | 0.10* | 1.00 | 1.00 | 0.00* |
| r19 How does onboarding work after signup? | 0.80 | 1.00 | 1.00 | 0.60* | 1.00 | 0.70 |
| c05 Is the LIVE badge the same as Monitoring? | 1.00 | 1.00 | 1.00 | 0.00* | 0.00* | 0.00* |
| s16 How can I see active attempts across all exams in the live p | 1.00 | 1.00 | 0.50* | 1.00 | 1.00 | 1.00 |
| s22 How do I set the correct answer for a True/False question? | 1.00 | 1.00 | 0.80 | 0.60* | 1.00 | 0.50* |
| p09 put the exam date in my calendar | 0.20* | 1.00 | 1.00 | 0.50* | 1.00 | 0.40* |
| r12 Question types MCQ and true false | 0.67* | 1.00 | 0.85 | 1.00 | 1.00 | 0.80 |
| m06 How do I bring in my Classroom roster and push grades back a | 0.50* | 1.00 | 1.00 | 0.50* | 1.00 | 0.60* |
| r02 Where is Monitoring in the sidebar? | 1.00 | 1.00 | 1.00 | 0.67* | 1.00 | 0.75 |
| s19 Where do I enter my information when setting up a new worksp | 0.00* | 0.00* | 1.00 | 0.80 | 1.00 | 0.30* |
| r23 What shows on the teacher dashboard? | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| p04 download my students' marks sheet | 0.80 | 1.00 | 1.00 | 1.00 | 1.00 | 0.85 |
| **Mean** | 0.69 | 0.85 | 0.86 | 0.74 | 0.92 | 0.61 |

## Reasons for scores below the bar

### a05: Can I change it after?
- recall 0.00: The retrieved chunks do not contain any facts about changing exam settings.
- precision 0.00: The retrieved chunks are irrelevant to the user's question about changing exam settings.
- relevancy 0.10: Most of the retrieved text discusses onboarding and personas rather than what was asked.
- correctness 0.00: The answer discusses changing personas instead of exam settings due to mismatched context.

### r19: How does onboarding work after signup?
- faithfulness 0.60: The generator context supports the first part, but does not mention dashboard creation details or skipping steps.

### c05: Is the LIVE badge the same as Monitoring?
- faithfulness 0.00: The generator received no context and made unsupported claims about account roles.
- answer_relevancy 0.00: The answer refuses to address the question and talks about account roles.
- correctness 0.00: The answer fails to provide the facts given in the reference answer.

### s16: How can I see active attempts across all exams in the live panel?
- relevancy 0.50: The retrieved text includes extra information about viewing integrity events for a specific attempt.

### s22: How do I set the correct answer for a True/False question?
- faithfulness 0.60: The answer includes UI navigation steps (opening Exam tab, clicking Edit) that are not supported by the context.
- correctness 0.50: While it mentions selecting True or False, it misses the directness of the reference answer by adding unsupported UI steps.

### p09: put the exam date in my calendar
- recall 0.20: The retrieved chunks only contain details about Step 4 of scheduling the exam.
- faithfulness 0.50: The generator context supports setting the date, time, and clicking schedule, but not the specific UI instructions about the Exams or Links tabs.
- correctness 0.40: The answer misses the requirement to connect Google Calendar under Integrations and includes unsupported UI steps like the Links tab.

### r12: Question types MCQ and true false
- recall 0.67: The chunks contain facts about MCQ and True/False definitions and grading, but omit the badge detail.

### m06: How do I bring in my Classroom roster and push grades back after grading?
- recall 0.50: The chunks contain information about importing rosters and pushing grades, but miss the initial OAuth connection steps.
- faithfulness 0.50: The answer claims you go to the Students workspace to click Import Roster, whereas the context states to click on an imported course.
- correctness 0.60: The answer correctly describes automatic grade syncing but gives incorrect UI steps for importing the roster compared to the reference.

### r02: Where is Monitoring in the sidebar?
- faithfulness 0.67: The context does not mention clicking Dashboard in step 1.

### s19: Where do I enter my information when setting up a new workspace in Quizzer?
- recall 0.00: The retrieved chunks contain information about onboarding screens, but do not contain the specific reference facts about Step 5.
- precision 0.00: Since the chunks do not contain the reference facts, precision cannot be evaluated positively.
- correctness 0.30: The answer misses the specific reference steps and details, incorrectly attributing information across four generic screens instead of Step 5.
