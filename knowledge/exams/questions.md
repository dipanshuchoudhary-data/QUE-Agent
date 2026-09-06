---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Questions

## Overview

Questions are the individual assessment items within an exam. After AI
generation or manual creation, questions must be reviewed and approved
before the exam can be published. The Questions tab in each exam
workspace is where you manage all questions for that exam.

Users may call this: items, problems, prompts, tasks, exam content,
question bank.

## How to Access

Open an exam from the Exams workspace, then select the Questions tab.
This shows all questions with their status, type, marks, and content.

## Step-by-Step UI Guide: Reviewing and Approving Questions

Follow these exact steps to review questions after AI generation:

Step 1 — Open your exam:
In the left sidebar, click Exams. You will see your exam list. Find
your exam (it may show a "Draft" badge). Click on the exam card to
open the exam workspace.

Step 2 — Go to the Questions tab:
At the top of the exam workspace, you will see a row of tabs:
Questions, Monitoring, Results, Links, Settings. Click the Questions
tab (it is usually the first or leftmost tab).

Step 3 — See the question list:
You now see all questions organized by section. Each question card
shows:
- The question text
- The question type (MCQ, True/False, Short Answer, etc.) as a small
  badge
- The current status: a colored badge showing Draft (gray/yellow),
  Approved (green), or Rejected (red)
- The marks value

Step 4 — Review a question:
Read the question carefully. Check that the text is clear, the options
make sense, and the correct answer is right.

Step 5 — Approve, reject, or edit:
On each question card you will see action buttons:

Click the Approve button (checkmark icon or green action) to mark the
question as ready. The status badge changes to Approved (green).

Click the Reject button (X icon or red action) to exclude the
question. The status badge changes to Rejected (red).

Click the Edit button (pencil icon) to modify the question text,
options, correct answer, or marks. Make your changes and save.

Click Regenerate (refresh icon) to ask the AI for a new version of
this question. The new version replaces the old one and starts as
Draft again.

Step 6 — Bulk approve (optional shortcut):
If you have reviewed all questions visually and want to approve
everything at once, look for the Bulk Approve action (usually a
button at the top of the questions list or in the toolbar). Click it
to change all remaining Draft questions to Approved in one action.

Step 7 — Check the publish readiness:
Look at the question count summary at the top of the Questions tab.
It shows how many are Approved, Draft, and Rejected. All questions
must be Approved before you can publish. If any show Draft, approve or
reject them.

## Question Types

Quizzer supports five question types for graded exams:

Multiple Choice (MCQ): presents a set of answer options where exactly
one is correct. The student selects one answer. Graded instantly by
comparing to the correct option.

True/False: a binary choice question. The student selects True or
False. Graded instantly by comparing to the correct answer.

Short Answer: the student types a text response. Graded automatically
through a 6-step smart matching pipeline: exact match (normalized),
fuzzy match (for typos), keyword overlap, embedding similarity, AI
evaluation, and Pending Professor Review if needed. One or more accepted
answers can be configured. The pipeline handles minor variations in
spelling, casing, and phrasing.

Long Answer: the student types a longer text response. Evaluated by
the AI grading system using the grading style setting. May result in
Pending Professor Review if AI confidence is too low for automatic
scoring. Best for essay-type or explanation questions.

Multi-Select: presents a set of answer options where multiple answers
can be correct. The student selects all that apply. Graded by comparing
the selected set to the correct set — all correct options must be
selected and no incorrect options for full marks.

Arena-specific question types (not available in graded exams):
One Word Answer: short typed response with fuzzy matching (Arena only).
Guess It: short answer with an image prompt (Arena only).

Users may call this: question format, item type, MCQ, TF, essay,
fill-in-the-blank, multiple answer.

## Question Review Workflow

Every question has a review status that determines its eligibility:

Draft: the initial status after AI generation or manual creation. Draft
questions have not been reviewed and are not included when publishing.
They need teacher review.

Approved: the teacher has confirmed the question is correct, well-
formed, and ready for students. Only Approved questions are included
in the published exam. At least one Approved question is required to
publish.

Rejected: the teacher has marked the question as not suitable. Rejected
questions are excluded from the exam. They remain visible on the
Questions tab for reference but are not shown to students.

The workflow is: Draft → review (edit if needed) → Approved or Rejected.

All questions must be in Approved status before the exam can be
published. Draft or Rejected questions block publishing. This is the
primary publish gate — if publishing is disabled, check for unapproved
questions first.

## How to Review Questions

Open the exam from Exams, then select the Questions tab. You see all
questions organized by section with their current status.

For each question you can:

Approve: mark it as ready for students. The question turns green or
gets an approved indicator. Cannot approve if the question is missing
a valid correct answer (MCQ, True/False, Multi-Select must have
correct answers set).

Reject: mark it as not suitable. The question is excluded but not
deleted. You can un-reject later if you change your mind.

Edit: change any part of the question — the question text, answer
options (for MCQ, True/False, Multi-Select), correct answer(s), marks
value, or even the question type. Editing is free-form; you can
modify AI-generated questions extensively.

Regenerate: ask the AI to create a new version of this question based
on the same source material. The original question is replaced with
the new version. The new question starts as Draft. Regenerating
individual questions does not count against your daily generation quota.

Duplicate: create a copy of the question within the same section. The
copy starts as Draft. Useful when you want variations of a question.

Delete: permanently remove the question from the exam. This cannot be
undone.

## Bulk Actions

Bulk Approve: approve all remaining Draft questions at once. Useful
when you have reviewed the full set visually and want to publish
quickly. Available as a single action that changes all Draft questions
to Approved.

Bulk Marks Update: change the marks value for multiple questions at
once. Select the questions and apply a new marks value.

Bulk actions save time when managing exams with many questions.

## Sections

Questions are organized into sections. Each section has:

Title: the name of the section (e.g., "Part A: Fundamentals").
Questions: the items within the section, in order.
Total marks: automatically calculated from the marks of individual
questions in the section.

Sections are created automatically during AI generation (based on the
blueprint in Guided mode, or the AI's own structure in Source-first
mode). You can also create sections manually.

You can:
- Add new sections
- Rename sections
- Reorder sections (drag and drop or move actions)
- Move questions between sections
- Delete empty sections

Sections help structure longer exams into logical parts. Students see
section titles during the exam.

## Marks

Each question has a marks value that determines how many points it is
worth:

Default value: set by the exam's Default Marks setting in the
Workspace tab of Account Settings (default is 1). Individual questions
inherit this default but can be overridden.

Override per question: change the marks on any individual question.
Range: 1 to 100 marks per question.

Marks affect scoring: the student earns the full marks value for a
correct answer (objective questions) or a portion of the marks based
on the grading result (written questions).

Negative marking (if enabled): the configured penalty is deducted per
wrong answer, regardless of the question's marks value.

## Correct Answers

MCQ: exactly one option must be marked as correct. The question cannot
be approved without a valid correct answer.

True/False: one of True or False must be marked as correct. Same
approval requirement.

Short Answer: one or more accepted answers can be set. The grading
pipeline uses smart matching, so minor variations (spelling differences,
extra spaces, case changes) may still match even if not explicitly
listed as accepted answers.

Long Answer: there is no single "correct answer" field. Grading uses
AI evaluation against the question context, the source material, and
the grading style setting. Teachers may set reference answers or key
points to guide the AI evaluator.

Multi-Select: one or more options must be marked as correct. All
correct options must be identified. The student must select exactly
the correct set for full marks.

## Adding Questions Manually

From the Questions tab, you can add new questions without AI generation:

1. Click the add question action.
2. Select the question type.
3. Enter the question text.
4. Add options (for MCQ, True/False, Multi-Select).
5. Set the correct answer(s).
6. Set marks.
7. Save.

The new question starts as Draft and needs to be approved.

## Editing AI-Generated Questions

AI-generated questions can be freely edited after generation. You can
change:
- Question text (rewrite, clarify, expand)
- Answer options (add, remove, reword)
- Correct answer (change which option is correct)
- Marks value (increase or decrease)
- Question type (change from MCQ to True/False, etc.)

Editing does not reset the question status to Draft. If you approved
a question and then edit it, it remains Approved. This gives you
flexibility to make minor corrections without re-approving.

## Question Regeneration

If an AI-generated question is not satisfactory, you can regenerate it:

1. Click the regenerate action on the specific question.
2. The AI creates a new version based on the same source material.
3. The original question is replaced with the new version.
4. The new question starts with Draft status (needs re-approval).

Regeneration does not count against your daily generation quota.

## Answer Key Freezing

When a student starts an attempt, the correct answers for all questions
are frozen at that moment. If you edit a question's correct answer
after a student has started, their attempt is graded against the
original answers, not the updated ones.

This means you can safely edit questions on a published exam without
retroactively affecting in-progress or completed attempts. Changes
only affect future attempts.

## Option Limits

MCQ questions can have 2 to 6 answer options.
Multi-Select questions can have 2 to 8 answer options.
True/False is always exactly 2 options (True and False).

## Question Count Visibility

The Questions tab shows the total question count, broken down by
status (Draft, Approved, Rejected) and by section. This helps you
quickly see what still needs review.

## Common Questions

What question types does Quizzer support?
Multiple Choice (MCQ), True/False, Short Answer, Long Answer, and
Multi-Select for graded exams. Arena also has One Word Answer and
Guess It.

How do I approve questions?
Open the exam, go to the Questions tab, and click Approve on each
question. You can also use the bulk approve action to approve all
remaining drafts at once.

Can I edit AI-generated questions?
Yes. You can change any part of an AI-generated question including the
text, options, correct answer, type, and marks.

Why can I not publish my exam?
All questions must be in Approved status. Check the Questions tab for
any remaining Draft or Rejected questions and approve them. At least
one Approved question is required.

How do I add a question manually?
On the Questions tab, use the add question action. Select the type,
fill in the content, set the correct answer, and save.

Can I change marks per question?
Yes. Each question has its own marks value. The default comes from the
exam's Default Marks setting but can be overridden individually.

What happens if a question has no correct answer?
MCQ, True/False, and Multi-Select questions cannot be approved without
a valid correct answer. The approve action will be disabled with a
message explaining what is missing.

Does editing a question after approval reset it to Draft?
No. Editing does not change the approval status. The question remains
Approved after edits.

What does Regenerate do?
It asks the AI to create a new version of the question from the same
source material. The original is replaced, and the new question starts
as Draft. Does not count against your daily quota.

Can I move questions between sections?
Yes. You can drag questions to different sections or use move actions
to reorganize.

## Related Features

See also: Creating Exams, Exam Settings (Default Marks, Grading Style),
Scoring and Grading, Publishing and Sharing
