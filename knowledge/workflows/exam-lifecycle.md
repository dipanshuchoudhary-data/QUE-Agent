---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Exam Lifecycle

## Overview

Every exam in Quizzer goes through a defined lifecycle from creation
to archival. Understanding this lifecycle helps you know what is
possible at each stage and what happens when you transition between
states.

Users may call this: exam states, exam status, draft vs published,
what happens when I publish, unpublish, archive.

## Lifecycle States

An exam exists in one of three states at any time:

Draft: the exam is being prepared. You can edit questions, change
settings, upload source content, and configure everything. Students
cannot access a draft exam.

Published: the exam is live and accessible to students via the share
link. Students can view the landing page, fill the verification form,
and start attempts (subject to link window and attempt limits).

Archived: the exam is retired. Students cannot start new attempts.
All existing results remain accessible and exportable. Archived exams
can be unarchived.

## State Transitions

Draft → Published (Publish):
Requirements: at least one Approved question.
Effect: generates a public share link, exam becomes accessible to
students.
Reversible: yes, by unpublishing.

Published → Draft (Unpublish):
Effect: the share link is deactivated. No new attempts can start.
All existing results are preserved — they are NOT deleted.
In-progress attempts may be affected (students cannot resume if the
link is deactivated).
Question editing is unlocked again.

Published → Archived (Archive):
Effect: exam is retired. No new attempts. Results preserved.
Link is deactivated.

Archived → Published (Unarchive + Publish):
Effect: exam comes back to life. A new share link may be generated.
Previous results remain.

Draft → Archived:
Not typical, but possible. Usually exams are published before being
archived.

Archived → Draft (Unarchive):
Effect: exam goes back to draft state for editing. No share link.
Results preserved.

## Delete Behavior

When you try to delete an exam:

If the exam has zero attempts: the exam is permanently deleted.
If the exam has any attempts: the exam is archived instead of deleted.
This protects student result data from accidental deletion.

This means you cannot lose student results by deleting an exam.

## What Happens to Results

Results are never lost during state transitions:

Unpublish: results stay. Accessible in the Results tab.
Archive: results stay. Accessible in the Results tab.
Delete (with attempts): archives instead, results stay.
Re-publish after unpublish: results stay. New attempts can be added.

The only way to lose results is if an exam with zero attempts is
deleted (there are no results to lose in that case).

## What Happens to the Share Link

Publish: generates a public share link. The link includes a UUID
that uniquely identifies this exam.

Unpublish: the link is deactivated. Anyone clicking it sees an error
or inaccessible state.

Re-publish: a new link may be generated, or the previous link may be
reactivated (depending on implementation). Always re-share the link
from the Links tab after re-publishing.

Archive: the link is deactivated.

## Link Window (available_until)

The link window is orthogonal to the lifecycle state. Even a Published
exam can be effectively inaccessible if available_until is in the past.

Published + active link window: students can access the exam.
Published + expired link window: exam is technically published, but
students cannot start new attempts because the window closed.

To reactivate: extend available_until to a future time in Settings.

## Settings Changes After Publishing

Most settings can be changed on a published exam, but some changes have
important implications:

Timer changes: affect future attempts only, not in-progress ones.
Question edits: changes to correct answers do not affect frozen answer
keys in existing attempts.
Adding questions: new questions appear in future attempts.
Removing questions: may affect scoring for future attempts.
Proctoring settings: affect future attempts.

Best practice: finalize settings before publishing. If changes are
needed on a live exam, be aware of the impact on students who are
mid-attempt.

## Typical Teacher Workflow (with UI steps)

1. Open Create Exam from the Dashboard quick actions or press Ctrl+K
   and type "Create Exam." Enter a title and add source content. Click
   Generate. (Exam is now Draft.)
2. Go to Exams in the sidebar. Open your exam. Click the Questions
   tab. Review each question and click Approve (checkmark) or Reject
   (X). Use Bulk Approve for speed.
3. Click the Settings tab. Set Duration, toggle proctoring switches,
   set Maximum Attempts, configure Verification Schema.
4. Click the Publish button (emerald-green). The exam is now Published.
   A success screen shows the link.
5. Copy the link from the Links tab. Share it with students via email,
   chat, Classroom assignment, or QR code.
6. While students take the exam, click the Monitoring tab to watch
   live attempts and integrity events.
7. After students submit, click the Results tab. View scores, expand
   rows for integrity review panels, and export (CSV, Excel, Sheets).
8. When the exam period is over, click the Archive action on the exam
   card in the Exams workspace. The exam moves to Archived. All
   results are preserved.

## Parallel Exams

Teachers can have multiple exams in different states simultaneously.
There is no limit on the number of draft, published, or archived exams.

## Common Questions

What are the exam states?
Draft (being prepared, not accessible), Published (live, students can
take it), and Archived (retired, no new attempts, results preserved).

Can I unpublish a live exam?
Yes. Unpublishing deactivates the link. No new attempts can start.
Existing results are preserved.

What happens to results if I unpublish or archive?
Nothing. Results are never deleted by state changes. They remain
accessible and exportable.

Can I delete an exam that has results?
No. If the exam has any attempts, deleting archives it instead. Results
are protected.

Can I re-publish an archived exam?
Yes. Unarchive it, then publish again. Previous results remain.

I changed the timer on a published exam. Does it affect current takers?
No. Timer changes affect future attempts only. In-progress attempts use
the timer from when they started.

## Related Features

See also: Publishing and Sharing, Exam Settings, Results and Exports,
Questions, Creating Exams
