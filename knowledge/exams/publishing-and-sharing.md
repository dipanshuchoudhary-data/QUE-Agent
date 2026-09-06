---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Publishing and Sharing

## Overview

Publishing makes an exam available for students to take via a shareable
link. Before students can access an exam, it must be published with all
questions approved. After publishing, you share the link and manage the
link window that controls how long it stays active.

Publishing is the gateway between creation and delivery. Everything
before publishing is preparation; everything after is live.

Users may call this: release, make live, go live, activate, open,
launch, share, send to students.

## Step-by-Step UI Guide: Publishing and Sharing Your Exam

Step 1 — Open your exam:
In the left sidebar, click Exams. Click on your exam card to open the
exam workspace.

Step 2 — Verify all questions are approved:
Click the Questions tab. Look at the status summary at the top. Every
question must show a green Approved badge. If any show Draft (gray) or
Rejected (red), approve them first. You can use the Bulk Approve
action if you have reviewed everything.

Step 3 — Publish the exam:
Look for the Publish button. It appears as a prominent emerald-green
button on the exam card in the Exams workspace, or at the top of the
exam workspace view. Click Publish.

If all requirements are met, the exam publishes immediately. You will
see a success screen with your exam link.

If publishing is blocked, a message tells you exactly what is wrong
(usually unapproved questions). Fix the issue and try again.

Step 4 — Copy the share link:
After publishing, a success screen appears with the exam URL. Click
the Copy Link button (clipboard icon) to copy it. You can also find
the link anytime on the Links tab inside the exam workspace.

Step 5 — Share with students:
You have several sharing options from the Links tab:

Option A — Copy and paste: paste the copied link into any messaging
app, email client, or LMS.

Option B — Share by email: on the Links tab, find the Share by Email
section. Type up to 50 email addresses (comma separated) and click
Send. Quizzer sends an invitation email with the exam link.

Option C — Google Classroom: if Classroom is connected, click the
Assign to Classroom button on the Links tab. Select your course and
the exam is assigned as coursework.

Option D — QR code: on the Links tab, find the QR code option. A
scannable QR code is generated. Students can scan it with their
phone camera.

Step 6 — Check the link window:
On the Links tab, you will see the link window status showing when the
link expires (for example, "Active until Sep 8, 2026"). If you need
more time, click Renew or Extend to push the deadline forward.

## Publish Requirements

All of these must be true to publish:

1. The exam has at least one question.
2. Every question is in Approved status (no Draft or Rejected questions
   remain).
3. The exam is not archived.
4. AI generation is not currently in progress on this exam.
5. The teacher owns the exam.

If any requirement is not met, the Publish action is blocked with a
specific message explaining what needs to be fixed:

Unapproved questions: "All questions must be approved before
publishing." This is the most common blocker. Open the Questions tab
and approve remaining Draft questions, or use bulk approve.

No questions: the exam needs at least one question to be publishable.

Archived exam: "Archived quizzes cannot be published." Unarchive the
exam first, then publish.

Generation in progress: wait for AI generation to complete before
publishing.

In-progress attempts already exist (republish scenario): the system
asks for confirmation because existing in-progress attempts may be
affected by republishing.

## How to Publish

Open your exam from the Exams workspace, then use the Publish action.
The Publish button is available:
- On the exam card in the Exams workspace list
- Inside the exam workspace (top-level action)

On publish, the system:
- Validates all publish requirements
- Generates a unique public link (UUID-based) if this is the first
  publish
- Sets a link window based on your subscription tier
- Makes the exam accessible to students via the link
- Sends a Publish confirmation notification

After publishing, the exam's status changes from Draft to Published.

## The Published Exam Link

Each published exam gets a unique public URL. This URL is what
students open to take the exam. The link:
- Does not require a Quizzer account to access
- Contains a unique identifier for this specific exam
- Leads to the exam attempt interface (not the creator workspace)
- Works on any modern browser (Chrome, Firefox, Edge, Safari)

You can find and copy the link from:
- The Links tab in the exam workspace (primary location)
- The Exams workspace after publishing (quick copy action)
- The post-publish success screen

## Link Window

The link window (available_until) controls how long the published link
accepts new attempt starts. It is a deadline after which students can
no longer begin the exam.

Default link windows by subscription tier:
- Explorer: 24 hours from publish time
- Professional: 1 week from publish time
- Elite: 1 week default, extendable to custom dates

During the public beta, link window caps may be relaxed so every user
gets longer windows.

When the link window expires:
- The exam remains published (status does not change)
- Students who open the link see that it is no longer available
- In-progress attempts that started before expiry may also be affected
- The teacher can renew/extend the link window at any time

Link window and duration are different things:
- Link window: how long the link accepts new starts (hours/days)
- Duration: how long each student has once they start (minutes)

Users may call this: deadline, expiry, availability, when does the
link close, how long is the link active, available until.

## Renewing or Extending the Link Window

If the link window has expired or is about to expire:

From the Links tab: click the Renew or Extend link window option.
You can extend by a preset duration (24 hours, 1 week) or set a
specific end date and time (on eligible tiers).

From the Exams workspace: the exam card shows link window status.
Use the renew action directly from the card.

After renewing, the link becomes active again immediately. No new URL
is generated — the same link works.

## Sharing the Link

After publishing, you have multiple ways to distribute the exam link:

Copy URL: copy the link to your clipboard and share it through any
channel — email, messaging apps, LMS, social media, printed QR codes,
etc.

Share by email: from the Links tab, enter up to 50 recipient email
addresses separated by commas. Quizzer sends an invitation email with
the exam title and link. The exam must be published with an active
link window. These invitation emails are one of the few cases where
Quizzer sends real emails.

Google Classroom: if connected via Integrations, you can assign the
exam as coursework in a linked Classroom course. Students see the
assignment in their Google Classroom stream with a direct link.

Google Calendar: if connected via Integrations, you can schedule the
exam as a calendar event. The event includes the exam link and timing.

QR code: the Links tab can generate a QR code for the exam link.
Students scan it with their phone camera to open the exam. Useful for
in-person distribution (project on screen, print on handout).

## Draft vs Published vs Archived

Draft (unpublished): the exam exists in your Exams list but students
cannot access it. The link is inactive. You can edit questions,
settings, and source content freely.

Published: the link is active and students can start attempts (subject
to link window, access codes, and attempt limits). You can still edit
settings and questions after publishing — changes affect future
attempts.

Archived: the exam is retired. The link is deactivated. No new
attempts can start. All existing results are preserved permanently.
You can unarchive an exam, but unarchiving does not automatically
republish it — you must publish again separately.

## State Transitions

Draft → Published: the Publish action. Requires all questions Approved.

Published → Draft: the Unpublish action. Deactivates the link.
Students cannot start new attempts. In-progress attempts may be
affected.

Published → Archived: the Archive action. Deactivates the link and
retires the exam.

Archived → Draft: the Unarchive action. Returns to Draft state.
Does NOT automatically republish.

Draft → Archived: possible but atypical.

## What Happens to Results

Unpublishing or archiving NEVER deletes existing scores, results,
attempt data, or analytics. All data remains fully accessible and
exportable.

Unpublish: results stay in the Results tab. Analytics still includes
the data. The exam just stops accepting new attempts.

Archive: same as unpublish regarding data. The exam moves to an
archived view.

Delete (with attempts): the system archives instead of deleting. This
protects result history from accidental deletion. You cannot lose
student results by deleting.

Delete (without attempts): the exam is permanently deleted. No data
to lose.

Re-publish after unpublish: results from previous publish cycles
remain. New attempts are added alongside existing results.

## What Happens to In-Progress Attempts

When you unpublish while students are mid-attempt:
- The system asks for confirmation before proceeding
- Students currently in the exam may be blocked from continuing
- The timer may still count down, but submission or resumption may
  fail
- Best practice: check the Monitoring tab for active attempts before
  unpublishing

## Republishing

If you unpublished an exam and want to make it available again:

1. Ensure all questions are still Approved (settings may have changed).
2. Publish again using the same Publish action.
3. The same public link is reused (no new URL needed).
4. The link window is refreshed based on your tier.
5. Share the link again (or inform students the link is active again).

If in-progress attempts from the previous cycle exist, the system asks
for confirmation.

## Post-Publish Actions

After publishing, several follow-up actions are available:

Copy link: immediately copy the share URL.
Share by email: send invitations to students.
Assign to Classroom: link to a Google Classroom course.
Schedule on Calendar: create a Google Calendar event.

These actions are shown on the post-publish success screen and are
always available from the Links tab.

## Common Questions

How do I publish my exam?
Make sure all questions are approved on the Questions tab, then click
the Publish action from the Exams workspace or the exam card.

Why can I not publish?
Check for unapproved questions (the most common cause). Open the
Questions tab and approve all remaining Draft questions. Also check
for archived status or in-progress generation.

How do I share the exam with students?
After publishing, copy the link from the Links tab and share it. You
can also share by email (up to 50 recipients), assign via Google
Classroom, or schedule via Google Calendar.

Students say the link does not work. What should I check?
First: is the exam still published (not unpublished or archived)?
Second: has the link window expired? If so, renew it from the Links
tab. Third: is the correct link being used?

What is the difference between the link window and the exam duration?
The link window is how long the published link accepts new starts
(hours or days). The duration is how long each student has once they
start (minutes). A 60-minute exam with a 24-hour link window means
students have 24 hours to start, and 60 minutes once they begin.

Does unpublishing delete my results?
No. Unpublishing blocks new attempts but all existing results remain
visible, exportable, and included in Analytics.

Can students see the exam before I publish?
No. The exam link only works after publishing.

How do I extend the link window?
Go to the Links tab and use the Renew/Extend option. You can add
preset durations or set a specific end date (tier-dependent).

Can I share the exam with specific students only?
Use access codes (Settings → Require Access Code) to control who can
start. Generate unique codes and distribute them only to intended
students.

Does archiving delete the exam?
No. Archiving retires the exam and preserves all results. You can
unarchive and republish later.

## Related Features

See also: Exam Settings (link window), Creating Exams, Taking Exams,
Exam Lifecycle, Google Classroom Integration, Google Calendar
Integration, Notifications (publish confirmation)
