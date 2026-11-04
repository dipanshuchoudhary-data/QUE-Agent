# DeepEval pipeline scores, per query

Rows: 20. Bar: 0.7. Reference answers are provisional. Marked `*` = below the bar.

Retriever: contextual recall, precision, relevancy. Generator: faithfulness, answer relevancy, answer correctness (G-Eval against the reference).

| Query | Recall | Precision | Relevancy | Faithfulness | Answer relevancy | Correctness |
|---|---:|---:|---:|---:|---:|---:|
| r12 Question types MCQ and true false | 0.67* | 1.00 | 0.80 | 1.00 | 1.00 | 0.80 |
| s07 Why is my teacher dashboard completely empty right now? | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| r16 Students workspace cohort health | 0.50* | 1.00 | 1.00 | 0.50* | 0.80 | 0.50* |
| s03 How can I export my game history to a CSV file? | 1.00 | 1.00 | 1.00 | 0.40* | 1.00 | 0.50* |
| p05 how are written answers scored | 0.00* | 0.00* | 0.30* | 0.00* | 1.00 | 0.40* |
| r32 Join Arena as a player with code | 0.80 | 1.00 | 1.00 | 0.80 | 1.00 | 0.90 |
| r02 Where is Monitoring in the sidebar? | 0.00* | 1.00 | 1.00 | 0.00* | 1.00 | 0.00* |
| p07 play a live quiz game with my class | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| m06 How do I bring in my Classroom roster and push grades back a | 0.80 | 1.00 | 1.00 | 1.00 | 1.00 | 0.90 |
| a06 How do I start? | 0.00* | 1.00 | 1.00 | 1.00 | 1.00 | 0.00* |
| p06 stop students from switching tabs during the test | 0.20* | 1.00 | 0.80 | 1.00 | 1.00 | 0.40* |
| r22 Notification preferences and email | 0.50* | 1.00 | 1.00 | 1.00 | 0.80 | 0.60* |
| s11 How do I schedule an exam in Quizzer using Google Calendar? | 0.00* | 1.00 | 1.00 | 0.00* | 1.00 | 0.00* |
| r21 How do I send feedback about Quizzer? | 0.00* | 0.00* | 1.00 | 0.00* | 1.00 | 0.00* |
| m04 How is negative marking applied and where do I switch it on? | 0.80 | 1.00 | 1.00 | 1.00 | 1.00 | 0.80 |
| c03 What is the difference between an Exam and an Arena game? | 0.90 | 1.00 | 0.80 | 1.00 | 1.00 | 0.95 |
| t06 arena room code | 0.30* | 1.00 | 1.00 | 0.80 | 1.00 | 0.50* |
| t04 exam link not working for student | 1.00 | 1.00 | 0.90 | 1.00 | 1.00 | 1.00 |
| s17 Where is the Monitoring tab? | 0.00* | 1.00 | 1.00 | 0.00* | 1.00 | 0.00* |
| s06 How do I get better AI-generated questions in Quizzer? | 1.00 | 1.00 | 1.00 | 0.33* | 1.00 | 0.50* |
| **Mean** | 0.52 | 0.90 | 0.93 | 0.64 | 0.98 | 0.54 |

## Reasons for scores below the bar

### r12: Question types MCQ and true false
- recall 0.67: The chunks contain the facts for MCQ and True/False definitions, but omit the badge detail.

### r16: Students workspace cohort health
- recall 0.50: The chunks contain the cohort health visualization details but miss the instructions to open the Students workspace and check the cohort count.
- faithfulness 0.50: The claim about checking if exams are published and grading is complete is not supported by the chunks.
- correctness 0.50: It mentions the visualization correctly but misses navigation steps and adds unsupported troubleshooting details.

### s03: How can I export my game history to a CSV file?
- faithfulness 0.40: The chunks mention exporting to CSV from the Arena workspace, but do not support the specific UI steps for clicking an Export button or confirming.
- correctness 0.50: The answer mentions the correct workspace but includes unsupported steps not found in the reference or chunks.

### p05: how are written answers scored
- recall 0.00: The retrieved chunks do not contain the facts from the reference answer about the grading pipeline.
- precision 0.00: The chunks do not contain the facts needed to answer the question.
- relevancy 0.30: The retrieved text discusses exam settings and scoring styles rather than how written answers are scored.
- faithfulness 0.00: The generated claims are not supported by the retrieved chunks.
- correctness 0.40: The answer matches some steps in the reference, but misses later pipeline steps and includes unverified details not present in the chunks.

### r02: Where is Monitoring in the sidebar?
- recall 0.00: The retrieved chunks contain the facts that Monitoring is not in the sidebar, but the answer misses them completely.
- faithfulness 0.00: The answer claims Monitoring is in the sidebar, which is directly contradicted by the chunks.
- correctness 0.00: The answer contradicts both the reference answer and the chunks by stating Monitoring is in the sidebar.

### a06: How do I start?
- recall 0.00: The retrieved chunks do not contain any of the facts needed for the reference answer about signing up and onboarding.
- correctness 0.00: The answer misses all key steps and facts from the reference answer regarding account creation and onboarding.

### p06: stop students from switching tabs during the test
- recall 0.20: The chunks contain information about the Block Tab Switching setting but lack the navigation steps.
- correctness 0.40: The answer misses the specific navigation steps found in the reference answer.

### r22: Notification preferences and email
- recall 0.50: The chunks contain notification toggle facts but miss email usage details.
- correctness 0.60: The answer covers notification settings accurately but misses the facts about email usage.

### s11: How do I schedule an exam in Quizzer using Google Calendar?
- recall 0.00: The chunks do not contain the specific 'Schedule exam' feature details mentioned in the reference.
- faithfulness 0.00: The answer includes integration steps not supported by the provided chunks.
- correctness 0.00: The answer provides steps not found in the reference answer or chunks.

### r21: How do I send feedback about Quizzer?
- recall 0.00: The retrieved chunks do not contain any of the steps or facts from the reference answer.
- precision 0.00: No chunks contain the facts needed to answer the question.
- faithfulness 0.00: The answer mentions steps involving the 'Teacher sidebar' and 'Ask QUE' that are not supported by the retrieved chunks.
- correctness 0.00: The answer provides completely different steps than the reference answer.

### t06: arena room code
- recall 0.30: The chunks contain facts about the six-character room code and room creation, but miss join URL and student steps.
- correctness 0.50: The answer provides logical steps for getting the code, but misses several details from the reference like the join URL and QR code.

### s17: Where is the Monitoring tab?
- recall 0.00: The retrieved chunks do not contain the reference answer facts.
- faithfulness 0.00: The answer claims the tab is in the top navigation bar, which contradicts the chunks.
- correctness 0.00: The answer misses the correct steps and provides contradictory information compared to the reference.

### s06: How do I get better AI-generated questions in Quizzer?
- faithfulness 0.33: Parts of the answer mention features like review and approve or document uploads not found in the chunks.
- correctness 0.50: It includes the reference point on source material but adds extra steps not present in the reference answer.
