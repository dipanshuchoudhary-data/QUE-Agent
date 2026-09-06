---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Scoring and Grading

## Overview

When a student submits an exam, Quizzer grades it automatically. The
grading process differs by question type: objective questions (Multiple
Choice, True/False, Multi-Select) are scored instantly, while written
questions (Short Answer, Long Answer) go through a multi-step smart
grading pipeline that combines exact matching, fuzzy matching, keyword
analysis, embedding similarity, and AI evaluation.

Users may call this: scoring, marking, auto-grading, how marks are
calculated, how answers are checked.

## Who Can Use It

Grading is automatic. Teachers see the results after grading completes.
Students see the submitted confirmation but not individual question
scores unless the teacher shares results.

## Step-by-Step UI Guide: How Grading Works and Where to See It

Step 1 — Student submits:
When a student clicks the Submit button in the exam interface (or time
runs out, or auto-submit triggers), grading starts automatically. No
teacher action is needed to trigger grading.

Step 2 — View graded results:
In the left sidebar, click Exams. Click on your exam card. Click the
Results tab (third tab in the row: Questions, Monitoring, Results,
Links, Settings). You will see a table of submitted attempts with
scores.

Step 3 — Check for Pending Professor Review:
In the Results table, look at the Status column. If any row shows
"Pending Professor Review" (usually an orange or yellow badge), that
means the AI could not confidently score one or more written answers.

Step 4 — Manually review (if needed):
Click on the Pending Professor Review row to expand it. You will see
the flagged answers with the student's response and the question
context. Read the answer and assign a score manually using the score
input field. Click Save or Confirm. Once all flagged answers are
resolved, the status changes to Graded (green badge).

Step 5 — Configure grading style (before students take the exam):
To change how written answers are evaluated, go to the Settings tab
for your exam. Scroll to the Scoring section. Find the Answer Grading
Style dropdown (only visible if your exam has Short Answer or Long
Answer questions). Click the dropdown and choose: Balanced, Writing
and Language, Formulas and STEM, Ideas and Concepts, or Key Terms.

## Objective Question Grading

Multiple Choice (MCQ): the student's selected option is compared to the
correct answer. Exact match scores full marks, otherwise zero.

True/False: same as MCQ. The student's choice is compared to the
correct answer.

Multi-Select: all correct options must be selected. The comparison
checks whether the student selected exactly the right set of options.

Objective grading happens instantly on submission. No AI or external
service is involved.

## Written Question Grading

Short Answer and Long Answer questions go through a layered grading
pipeline. Each layer tries to resolve the answer before escalating to
the next, more expensive step:

Step 1 — Exact match: the student's answer is compared to the accepted
answer(s) after normalization (lowercasing, trimming whitespace,
stripping punctuation). If it matches exactly, full marks are awarded
immediately.

Step 2 — Fuzzy match: for short strings, the system checks if the
answer is close enough using character-level distance. Minor typos or
spelling variations may still match. This step is especially useful for
one-word or short-phrase answers.

Step 3 — Keyword overlap: the system checks whether key terms from the
accepted answer appear in the student's response. This catches answers
that use different phrasing but contain the essential concepts.

Step 4 — Embedding similarity: the student's answer and the accepted
answer are converted to numerical representations (embeddings) and
compared for semantic similarity. This catches answers that express the
same idea in completely different words.

Step 5 — AI evaluation (batched LLM): if the previous steps could not
confidently score the answer, it is sent to an AI model for evaluation.
Multiple answers from different students may be batched together for
efficiency. The AI considers the question context, accepted answers, and
the grading style setting.

Step 6 — Pending Professor Review: if the AI confidence is too low, or
if the answer cannot be reliably scored by any automated method, the
answer is marked as Pending Professor Review. The teacher can then
review and manually score it.

Users may call this: how short answers are graded, AI grading, smart
grading, automatic marking, answer checking.

## Grading Style

The Answer Grading Style setting on the exam's Settings tab controls
how written answers are evaluated. It only appears when the exam has
Short Answer or Long Answer questions.

Balanced: standard evaluation considering correctness, completeness,
and clarity. Good for most subjects.

Writing and Language: emphasizes grammar, structure, expression, and
language quality. Best for language arts, literature, and writing exams.

Formulas and STEM: emphasizes mathematical notation, formulas, units,
and scientific accuracy. Best for math, physics, chemistry, and
engineering exams.

Ideas and Concepts: emphasizes conceptual understanding and reasoning
over exact wording. Best for social sciences, philosophy, and
discussion-based exams.

Key Terms: emphasizes the presence of specific technical terms and
vocabulary. Best for exams where using correct terminology matters
(medical, legal, technical fields).

Users may call this: scoring mode, marking style, evaluation method,
how to change grading.

## Negative Marking

When negative marking is enabled in the exam settings:

Correct answer: full marks for the question.
Wrong answer: the configured penalty is deducted.
Unanswered: no marks gained, no penalty.

The penalty amount is set per exam via the Penalty for Wrong Answer
setting. Negative marking applies to all question types.

Users may call this: penalty for wrong answers, mark deduction, minus
marking, negative scoring.

## Violation Penalty

If the Violation Penalty setting is configured (default is 0), marks
are deducted during grading based on the number of integrity violations
the student accumulated during the exam. This is separate from
negative marking for wrong answers.

The formula is: violation_count divided by 2 (rounded down) as the
base penalty factor.

## Score Calculation

For each question: marks are awarded based on whether the answer is
correct (objective) or the grading result (written).

Total score: sum of all question scores, minus any negative marking
penalties, minus any violation penalty.

The final score is stored on both the attempt record and the result
record. It cannot go below zero.

## Integrity Flag

After grading, each result is tagged with an integrity flag if the
student had any violations during the exam. This flag appears in the
Results tab so teachers can identify potentially compromised attempts.

## Result Statuses

After grading, results can have these statuses:

Graded: all questions have been scored. The result is final.

Pending Professor Review: one or more written answers could not be
confidently scored by the automated pipeline. The teacher needs to
review them manually. The overall score may be incomplete until review
is finished.

Users may call this: review needed, needs manual grading, incomplete
score, why is the score pending.

## When Grading Happens

Grading runs immediately when:
- A student clicks Submit
- The exam timer expires (auto-submit)
- The violation limit is reached with auto-submit enabled

Grading does not run on draft or in-progress attempts. It only triggers
on submission.

## Answer Key Freezing

When a student starts an attempt, the correct answers for all questions
are frozen at that moment. If the teacher edits a question's correct
answer after a student has started, the student's attempt is graded
against the original answers, not the updated ones. This prevents
unfair grading due to mid-exam changes.

## Common Questions

How does scoring work?
Multiple choice and true/false are graded instantly by comparing to
the correct answer. Short answers go through a multi-step pipeline
(exact match, fuzzy match, keywords, embedding similarity, AI
evaluation). Long answers may need teacher review if the AI is not
confident enough.

What is negative marking?
When enabled, wrong answers cause a mark deduction. The penalty amount
is configurable per exam. Unanswered questions are not penalized.

How are short answers graded?
Through a layered pipeline: exact match first, then fuzzy matching for
typos, keyword overlap, embedding similarity, and finally AI evaluation.
Only answers the pipeline cannot resolve go to Pending Professor Review.

What does Pending Professor Review mean?
It means the automated grading could not confidently score one or more
written answers. The teacher should review these manually. The score
may be incomplete until review is done.

Can I change how written answers are graded?
Yes. The Answer Grading Style setting (in exam Settings) controls the
evaluation emphasis. Choose Balanced for general use, or a specialized
style for STEM, writing, concepts, or key terms.

Why does this setting not appear?
Answer Grading Style only shows when the exam has Short Answer or Long
Answer questions. Exams with only MCQ or True/False do not show it.

Does grading happen for in-progress attempts?
No. Grading only runs when the exam is submitted (manually, by timer
expiry, or by auto-submit on violation limit).

What happens if I change a question's answer after students started?
Students who already started are graded against the answers that were
frozen when they began their attempt. Changes only affect future
attempts.

## Related Features

See also: Exam Settings (negative marking, violation penalty, grading
style), Results and Exports, Questions (correct answers, marks),
Taking Exams (submission)
