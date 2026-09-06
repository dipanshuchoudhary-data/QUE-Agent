---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Common Problems and Solutions

## Overview

This guide covers the most frequently encountered issues when using
Quizzer, along with their root causes and step-by-step solutions. If
you are experiencing a problem, find the symptom below and follow the
resolution steps.

Users may call this: help, troubleshooting, something is wrong, not
working, fix, error, issue, bug, problem.

## Exam Creation Problems

I cannot create an exam (button is disabled or missing):
Check that you have a Teacher role. Student accounts cannot create
exams. The Create Exam button appears on the Exams workspace sidebar
or the Dashboard quick actions.

AI generation is not starting:
Verify you have uploaded or pasted source content. The system needs
material to generate questions from. Also check your daily generation
quota — if you have exhausted it, wait until the next day. The quota
resets daily.

AI generation failed:
Check the notification for error details. Common causes: the source
document was too short, the content could not be extracted (corrupted
PDF, image-only PDF), or a temporary AI service error. Try again with
different source content, or split a large document into smaller
sections.

Questions are not appearing after generation:
Questions are created with Draft status. Check the Questions tab and
look at all statuses, not just Approved. Review and approve the
generated questions.

I cannot upload a file:
Supported formats: PDF, DOCX, DOC, TXT, text content pasted directly.
Maximum file size: 10 MB. Check that the file is not corrupted and is
in a supported format.

## Publishing Problems

I cannot publish my exam (Publish is disabled):
Publish requires at least one Approved question. Check the Questions
tab — you need to review generated questions and approve them. Draft
or Rejected questions do not count.

I published but students cannot access the exam:
Check the link window. If available_until is set to a past time, the
link has expired. Extend or remove the deadline. Also verify you shared
the correct link from the Links tab.

The exam link expired:
The available_until time has passed. Open the exam Settings, extend
the available_until time, and share the new link.

## Student Access Problems

Students say the link does not work:
First check: is the exam published? Unpublished or archived exams
cannot be accessed. Second check: has the link window expired
(available_until passed)? Third check: are they using the correct
link from the Links tab?

Students say they cannot start the exam:
If the exam requires a verification form, students must fill in all
required fields before starting. Check your verification schema
settings. Also, if max attempts is set and they have already used all
attempts, they cannot start again.

A student's exam was auto-submitted unexpectedly:
Three possible causes: (1) the timer ran out, (2) the violation limit
was reached with auto-submit enabled, or (3) the browser lost
connection for too long. Check the Monitoring tab for the specific
attempt to see what happened.

## Scoring and Results Problems

Some scores show "Pending Professor Review":
The automated grading pipeline could not confidently score one or more
written answers. Open the attempt, review the flagged answers, and
assign scores manually.

Scores seem wrong or lower than expected:
Check for negative marking (wrong answers deduct marks) and violation
penalty (integrity violations deduct marks). Both are configurable in
the exam Settings.

Results are not showing:
Results only appear after students submit and grading completes. Check
Monitoring for in-progress attempts. If students have not submitted
yet, there are no results.

I changed a question's correct answer but scores did not update:
Answer keys are frozen when a student starts an attempt. Changes to
correct answers only affect future attempts, not existing ones.

## LIVE and Monitoring Problems

LIVE badge is not showing:
All five conditions must be true simultaneously: (1) exam is published,
(2) not archived, (3) a student started an attempt (not just opened
the page), (4) not submitted, (5) browser tab open with recent
heartbeat. Check each condition.

LIVE disappeared suddenly:
The student may have closed their tab (heartbeat stops), submitted,
or the timer expired causing auto-submit. Check Results for a recently
submitted attempt.

I cannot find the Monitoring tab:
Monitoring is inside each exam workspace, not in the sidebar. Open
Exams, open the specific exam, then select the Monitoring tab.

## Analytics Problems

Analytics is empty:
Check date range filters first (the most common cause). Then verify
that you have exams with submitted, graded attempts. Publishing alone
does not populate Analytics.

Numbers look different from what I expected:
Verify your filters: date range, quiz selection, and status. A narrow
date range or specific quiz filter can exclude data.

## Students Workspace Problems

Students workspace is empty:
Check the scope bar at the top. It may be filtering to exams with no
attempts. Also verify that students have actually taken your exams —
simply publishing is not enough.

Classroom roster imported but no data:
Importing a Classroom roster brings in names but not exam attempt data.
Students must actually take exams to show scores and readiness labels.

## Integration Problems

Google Classroom says "not connected":
Go to Integrations and connect Google Classroom. The connection uses a
separate OAuth flow from Google Sign-In.

Import from Google Drive button is missing:
Connect Google Drive from Integrations first. The button appears in the
exam creation wizard only after Drive is connected.

Google Sheets export is not available:
Connect Google Drive from Integrations. The Sheets export option
appears in the Results tab after Drive is connected.

## Arena Problems

I cannot host an Arena game:
Verify all questions in your pack are Approved. Draft or Rejected
questions prevent hosting.

Nobody can join my Arena room:
Confirm you shared the correct room code. Codes are six characters
and case-sensitive. Also check if the room timed out (rooms close
after 15 minutes of existence or after 7 minutes with zero players).

The Arena room closed unexpectedly:
Rooms have idle timeouts. If the lobby is empty for 5 minutes, a
warning appears. After 2 more minutes, the room closes. Also, rooms
have a 15-minute maximum lifetime and will close if the host
disconnects for more than 5 minutes.

## Account and Login Problems

I cannot log in:
Check your email and password. For email+password accounts, verify your
email was confirmed (check your inbox for the verification email). For
Google or Microsoft sign-in, ensure you are using the correct account.

I forgot my password:
Use the password reset flow on the login page. An email will be sent
to reset your password.

I chose the wrong persona during onboarding:
The persona affects greeting text and detail questions but not
features, unless you chose Student (which limits your workspace). To
change from Student to Teacher role, contact support.

## Browser and Performance Problems

The page is loading slowly:
Try a hard refresh (Ctrl+Shift+R or Cmd+Shift+R). Clear your browser
cache. Ensure you have a stable internet connection. Quizzer works
best on modern browsers (Chrome, Firefox, Edge, Safari).

Webcam proctoring is not working:
The browser must have camera permission granted for the Quizzer domain.
Check browser settings. Also, webcam proctoring requires a modern
browser with MediaStream API support.

I see a blank or error page:
Try refreshing. If the issue persists, check your internet connection,
clear browser cache, or try a different browser. Report persistent
errors with **Send feedback** (sidebar ACCOUNT section).

## How to Report a Bug

1. In the left sidebar ACCOUNT section, click **Send feedback**.
2. Choose category **Bug report** (or the **Found a bug** quick pill).
3. Describe what went wrong and the steps to reproduce.
4. Submit the form.

Do not open the avatar menu for Feedback — that menu is only Log out.

## Common Questions

Where do I get help?
Open **Help & Support** in the sidebar ACCOUNT section for tours and
guides. To contact the team about a bug or idea, use **Send feedback**.

My problem is not listed here:
Try checking the specific feature guide for the area you are having
trouble with (e.g., Exam Settings, Publishing, Arena). If still stuck,
use **Send feedback** in the sidebar.

## Related Features

See also: all feature-specific guides for detailed information on each
area of Quizzer
