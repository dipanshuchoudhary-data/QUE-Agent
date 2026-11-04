# DeepEval pipeline scores, per query

Rows: 20. Bar: 0.7. Reference answers are provisional. Marked `*` = below the bar.

Retriever: contextual recall, precision, relevancy. Generator: faithfulness, answer relevancy, answer correctness (G-Eval against the reference).

| Query | Recall | Precision | Relevancy | Faithfulness | Answer relevancy | Correctness |
|---|---:|---:|---:|---:|---:|---:|
| r12 Question types MCQ and true false | 0.67* | 1.00 | 0.75 | 1.00 | 1.00 | 0.60* |
| s07 Why is my teacher dashboard completely empty right now? | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| r16 Students workspace cohort health | 0.33* | 1.00 | 1.00 | 1.00 | 1.00 | 0.40* |
| s03 How can I export my game history to a CSV file? | 1.00 | 1.00 | 0.33* | 1.00 | 1.00 | 0.90 |
| p05 how are written answers scored | 0.20* | 0.00* | 1.00 | 1.00 | 1.00 | 0.40* |
| r32 Join Arena as a player with code | 0.75 | 1.00 | 0.80 | 0.83 | 1.00 | 0.80 |
| r02 Where is Monitoring in the sidebar? | 1.00 | 1.00 | 0.67* | 0.00* | 1.00 | 0.00* |
| p07 play a live quiz game with my class | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| m06 How do I bring in my Classroom roster and push grades back a | 0.67* | 1.00 | 0.67* | 1.00 | 1.00 | 0.60* |
| a06 How do I start? | 0.00* | 0.00* | 1.00 | 1.00 | 1.00 | 0.00* |
| p06 stop students from switching tabs during the test | 1.00 | 1.00 | 0.40* | 1.00 | 1.00 | 0.60* |
| r22 Notification preferences and email | 0.67* | 1.00 | 1.00 | 1.00 | 0.56* | 0.40* |
| s11 How do I schedule an exam in Quizzer using Google Calendar? | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.20* |
| r21 How do I send feedback about Quizzer? | 0.00* | 0.00* | 1.00 | 1.00 | 1.00 | 0.00* |
| m04 How is negative marking applied and where do I switch it on? | 0.50* | 1.00 | 0.67* | 1.00 | 1.00 | 0.70 |
| c03 What is the difference between an Exam and an Arena game? | 1.00 | 1.00 | 0.71 | 1.00 | 1.00 | 1.00 |
| t06 arena room code | 0.25* | 1.00 | 0.25* | 1.00 | 1.00 | 0.60* |
| t04 exam link not working for student | 1.00 | 1.00 | 0.62* | 1.00 | 1.00 | 0.70 |
| s17 Where is the Monitoring tab? | 1.00 | 1.00 | 0.80 | 0.67* | 0.67* | 0.20* |
| s06 How do I get better AI-generated questions in Quizzer? | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.90 |
| **Mean** | 0.70 | 0.85 | 0.78 | 0.93 | 0.96 | 0.55 |

## Reasons for scores below the bar

### r12: Question types MCQ and true false
- recall 0.67: The score is 0.67 because sentences 1 and 2 of the expected output are successfully attributed to the 1st node in the retrieval context, while sentence 3 cannot be attributed as the context lacks information regarding question cards, badges, or the Questions tab.
- correctness 0.60: The actual output covers the definitions and grading mechanism for both MCQ and True/False types based on the input, but it completely omits the crucial detail from the expected output regarding how both question types show their question type as a small badge on the Questions tab in the exam workspace.

### r16: Students workspace cohort health
- recall 0.33: The score is 0.33 because sentence 3 in the expected output is supported by the 1st node in retrieval context regarding the cohort health visualization, while sentences 1 and 2 lack any corresponding information in the retrieval context.
- correctness 0.40: The actual output mentions the cohort health visualization and troubleshooting steps, but it completely misses key instructions from the expected output such as accessing the Students workspace via the left sidebar and checking the metrics strip for the 'Cohort count' card.

### s03: How can I export my game history to a CSV file?
- relevancy 0.33: The score is 0.33 because while the context mentions that 'Game history is accessible from the Arena workspace and can be exported to CSV, JSON, or Google Sheets,' it mostly contains irrelevant details, such as how 'a summary is saved to permanent storage: Winner and top rankings (top 20)' and where arena game history appears in the Analytics workspace, which do not explain how to perform the expo

### p05: how are written answers scored
- recall 0.20: The score is 0.20 because while the 1st node in the retrieval context supports the mention of written answers in sentence 1, it fails to provide information for the remaining sentences detailing the specific grading pipeline steps 1 through 6.
- precision 0.00: The score is 0.00 because the first node in the retrieval contexts discusses exam settings, Answer Grading Styles, and options like 'Balanced', 'Writing and Language', and 'Formulas and STEM', but it does not contain the step-by-step grading pipeline described in the expected output (exact match, fuzzy match, keyword overlap, embedding similarity, AI model, and Pending Professor Review).
- correctness 0.40: The actual output captures the initial grading steps (exact match and fuzzy match) and mentions the layered pipeline, but it misses several key steps defined in the expected output, specifically keyword overlap, embedding similarity, batched AI model scoring, and the final fallback to manual professor review. Due to these significant missing steps, the score is moderately low.

### r02: Where is Monitoring in the sidebar?
- relevancy 0.67: The score is 0.67 because while the context includes relevant statements explaining that the "Monitoring tab is found by opening Exams from the sidebar," it also contains irrelevant information stating that "LIVE badges appear on exam cards."
- faithfulness 0.00: The score is 0.00 because the output incorrectly states there is a top-level Monitoring item in the sidebar, whereas the context clarifies that Monitoring is actually accessed by opening Exams, selecting a specific exam, and then choosing the Monitoring tab.
- correctness 0.00: The actual output completely contradicts the expected output by claiming that Monitoring is in the left sidebar, whereas the expected output states it is not in the sidebar and requires navigating through Exams and a specific exam card.

### m06: How do I bring in my Classroom roster and push grades back after grading?
- recall 0.67: The score is 0.67 because while sentences 2 and 3 of the expected output are supported by the 1st node in the retrieval context, the first sentence regarding the initial Google Classroom connection steps lacks matching information in the nodes in the retrieval context.
- relevancy 0.67: The score is 0.67 because while the context includes relevant statements explaining how to 'Import a roster' and 'Push grades', it also contains irrelevant information about how to 'Assign an exam as coursework'.
- correctness 0.60: The Actual Output captures the primary goals of importing the roster and syncing grades, but it misses several key factual steps outlined in the Expected Output, such as completing the Google OAuth authorization via the Connect button, importing courses from the Integrations section before importing the roster, and the option for a manual grade push.

### a06: How do I start?
- recall 0.00: The score is 0.00 because the 1st node in the retrieval context fails to provide information for any part of the expected output, missing details regarding app access, account creation methods, and the four-step onboarding flow.
- precision 0.00: The score is 0.00 because the first node in the retrieval contexts is irrelevant, as it explains 'How to Start' by creating an exam rather than providing instructions on how to start using the app by signing up, creating an account, or going through the onboarding flow.
- correctness 0.00: The Actual Output completely misses the key steps and facts required by the Expected Output, such as opening the app, signing up with email/Google/Microsoft, and completing the four-step onboarding flow. Instead, it provides instructions on creating an exam, which does not align with the expected onboarding process.

### p06: stop students from switching tabs during the test
- relevancy 0.40: The score is 0.40 because while the context includes relevant information like 'Block Tab Switching detects and reports when a student leaves the exam tab', it also contains significant irrelevant details such as 'Require Fullscreen forces the exam into fullscreen mode', 'Block Copy/Paste prevents copying or pasting text', and 'Violation Limit is the maximum number of integrity violations tolerate
- correctness 0.60: The actual output correctly identifies the main feature ('Block Tab Switching' under Proctoring and Integrity) needed to address the input, but it misses several specific navigational steps provided in the expected output, such as opening Exams from the left sidebar, clicking the exam card, accessing the Settings tab, and noting that settings auto-save.

### r22: Notification preferences and email
- recall 0.67: The score is 0.67 because sentences 1 and 2 of the expected output are supported by node(s) in retrieval context 1, while sentence 3 lacks information regarding exclusive email uses in the context.
- answer_relevancy 0.56: The score is 0.56 because while it partially addresses the input regarding notification preferences and email, it includes several irrelevant statements about milestone attempt counts, integrity alerts, AI generation status, and export completion status.
- correctness 0.40: The actual output covers the notification toggles and clarifies that they only apply to the in-app inbox, but it completely misses the specific instructions on how to navigate to the settings (sidebar ACCOUNT, select Settings) and fails to state the specific purposes for which email is used (signup verification, password resets, and exam share invitations) as outlined in the expected output.

### s11: How do I schedule an exam in Quizzer using Google Calendar?
- correctness 0.20: The Actual Output is cut off at the end ("The exam will now appear as an"), and it describes a multi-step integration process via the Teacher sidebar that contradicts the Expected Output's description of using a direct 'Schedule exam' feature to create a Google Calendar event. Critical facts and steps from the Expected Output regarding the primary calendar event details (title, link, and timing) a

### r21: How do I send feedback about Quizzer?
- recall 0.00: The score is 0.00 because the entire expected output detailing desktop and mobile navigation steps for the ACCOUNT section cannot be attributed to anything in the 1st node in the retrieval context, which only provides a general feature overview without any instructions.
- precision 0.00: The score is 0.00 because the only retrieval context provided is irrelevant. Specifically, the first node in the retrieval contexts is deemed unhelpful as it lacks any instructions on how to actually access or send feedback on desktop or mobile, noting only that 'Submissions go to the Quizzer support inbox'.
- correctness 0.00: The Actual Output completely misses the steps and facts provided in the Expected Output. Instead of describing how to scroll to the ACCOUNT section in the left sidebar on desktop or using the bottom navigation on mobile to access the /feedback page, the Actual Output instructs the user to open the Teacher sidebar and click Ask QUE, which contradicts the expected instructions.

### m04: How is negative marking applied and where do I switch it on?
- recall 0.50: The score is 0.50 because sentence 1 in the expected output cannot be attributed to any information in the 1st node in the retrieval context, whereas sentence 2 is successfully attributed to the same node.
- relevancy 0.67: The score is 0.67 because while it correctly explains how the penalty is set via the 'Penalty for Wrong Answer setting' and applied, it also includes irrelevant information regarding alternative terminology such as 'penalty for wrong answers, mark deduction, minus marking, negative scoring' which does not address how to switch it on.

### t06: arena room code
- recall 0.25: The score is 0.25 because only the 1st sentence of the expected output is supported by the 1st node in the retrieval context, while the remaining sentences regarding the room screen display, sharing options, classroom projection, and player join details lack corresponding information in the node(s) in retrieval context.
- relevancy 0.25: The score is 0.25 because while the context mentions how a teacher 'shares a six-character room code', it is mostly filled with irrelevant details such as 'The host runs the game live while players answer questions for speed-based points' and descriptions of how 'Arena is completely separate from the graded exam flow'.
- correctness 0.60: The actual output correctly identifies the generation of a six-character room code and its purpose. However, it misses several key details provided in the expected output, specifically the mention of the join URL, the QR code, the copy code functionality, and the instruction for teachers to project the screen for students.

### t04: exam link not working for student
- relevancy 0.62: The score is 0.62 because while the context provides actionable troubleshooting steps like checking if the "exam is published" or if the "link window expired," it also includes irrelevant information regarding "auto-submitted" exams and general platform navigation that does not address the specific issue of a broken link.

### s17: Where is the Monitoring tab?
- faithfulness 0.67: The score is 0.67 because the actual output incorrectly places the Monitoring tab in the top navigation bar of the Quizzer dashboard, whereas the context specifies it is located within each individual exam workspace.
- answer_relevancy 0.67: The score is 0.67 because while the response addresses the location of the tab, it includes unnecessary troubleshooting advice that is irrelevant to the user's specific question.
- correctness 0.20: The actual output fails to provide the necessary navigation steps required by the expected output. It incorrectly suggests the tab is in the top navigation bar of the dashboard, whereas the expected output specifies that the user must first open Exams and select a specific exam before the Monitoring tab becomes accessible.
