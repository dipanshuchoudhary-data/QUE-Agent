---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# QUE Core Product Knowledge

Always inject this pack. Treat as ground truth for Quizzer UI and flows.
Do not invent live counts, scores, or who is taking an exam.
Prefer product words below. If unsure of a label, describe the place.

---

## What Quizzer Is

AI assessment platform: Create Exam (add sources, AI generates questions)
then review/approve questions then Publish then students take exam then
Monitoring / Results then Students / Analytics.

Arena is a separate live competition loop (speed-based scoring, room
codes, team mode), not the same as graded exams. Arena has its own
history and its own section in Analytics.

Quizzer is in public beta. Every plan is free. Four tiers exist
(Explorer, Professional, Elite, Enterprise) with different feature
limits, but pricing is not set yet.

## Two Runtimes (never mix)

Creator workspace: teachers and creators. Sidebar apps, Create Exam,
exam workspace tabs. Cookie-based JWT login.

Exam attempt: takers. Focused exam interface via published link.
Attempt token, no account required. Students identify themselves
through a verification form.

These are completely separate interfaces sharing no UI.

## Teacher Sidebar

Grouped sections on the left rail:

ASSISTANT: Ask QUE (opens the QUE chat panel).

WORKSPACE: Dashboard, Exams, Arena, Students, Analytics, Integrations.
Create Exam remains a primary action (command palette / quick action).

ACCOUNT: Upgrade, Settings, Send feedback, Help & Support.

Bottom of the sidebar: your avatar shows name/email. Clicking it opens
a small menu for profile / **Log out** only — not Feedback or Settings.

Not in the sidebar: Monitoring, Results, Settings for one exam, Links.
Those live on the exam workspace: open Exams, open exam, then tabs.
Top-level /monitoring and /results URLs redirect to Exams.

## Student Sidebar

Dashboard (student version) and Help only. No exam creation, no Arena
hosting, no Students, no Analytics, no Integrations.

Students enter exams via shared links, not the sidebar.

## Exam Workspace Tabs

Questions, Monitoring, Results, Links, Settings.

Questions: view, approve, reject, edit, regenerate, bulk actions.
Monitoring: live attempts, integrity events, violation data.
Results: graded scores, exports (CSV, Excel, Sheets), integrity review.
Links: published URL, link window, sharing (copy, email, Classroom,
Calendar).
Settings: timing, proctoring, scoring, attempts, access codes,
verification schema.

## Question Types

Multiple Choice (MCQ): one correct answer from options.
True/False: binary choice.
Short Answer: typed response, auto-graded with smart 6-step pipeline.
Long Answer: typed response, may need teacher review.
Multi-Select: multiple correct answers from options.

Arena adds: One Word Answer (fuzzy-matched short answer) and Guess It
(short answer with image).

## Question Review Statuses

Draft: initial, needs review. Approved: ready for publishing. Rejected:
excluded. All questions must be Approved before publishing.

## Key Settings (per exam)

Duration: whole-exam timer in minutes (default 60, minimum 5).
Proctoring: fullscreen, tab-switch, copy-paste blocking (all on by
default). Webcam monitoring off by default. Phone detection on when
webcam enabled. Face monitoring off by default.
Attempts: maximum per student (default 1). Allow Resume off by default.
Scoring: negative marking off by default. Grading style for written
questions (Balanced by default). Violation penalty (default 0).
Access Code: optional single-use codes for extra access control.
Verification Schema: identity form before exam. Preset contexts:
College, School, Coaching, Minimal.

## Dependency Chain

Create exam then Approve all questions then Publish then Share link
(link window open) then Students start attempts then LIVE / Monitoring
useful then Submit then Grade then Results rows then Students list and
Analytics charts fill.

An exam on Exams is not enough for Students/Analytics. Need submitted,
graded attempts. If any workspace is empty, check which upstream step
is missing.

## Link Window vs Duration

Link window (available_until): how long the published link accepts
new attempt starts. Tier-dependent defaults (Explorer 24h, Pro 1wk,
Elite custom). Renew via Links tab or Exams card.

Duration: per-attempt timer once the student starts (minutes).

These are different. A 60-minute exam with a 24-hour link window means
students have 24 hours to start, and 60 minutes once they begin.

## Exam Lifecycle States

Draft: being prepared, not accessible to students.
Published: live, students can take it via the share link.
Archived: retired, no new attempts, all results preserved.

Unpublishing or archiving never deletes results. Deleting an exam with
attempts archives instead of deleting. Results are permanent.

## Grading

Objective questions (MCQ, True/False, Multi-Select): graded instantly
by comparing to the correct answer.

Written questions (Short Answer, Long Answer): graded through a
6-step pipeline: exact match, fuzzy match, keyword overlap, embedding
similarity, AI evaluation, then Pending Professor Review if confidence
is low.

Grading style (Balanced, Writing and Language, Formulas and STEM,
Ideas and Concepts, Key Terms) only affects written question evaluation.

Answer keys are frozen when a student starts. Changes to correct
answers only affect future attempts.

## LIVE Badge

All 5 conditions must be true: exam published and not archived,
attempt started (not just page opened), not submitted, timer running,
browser tab open with recent heartbeat (within ~150 seconds). LIVE
drops within 2-3 minutes of tab closing.

## Notifications

Most notifications are in-app only. Quizzer does NOT email about:
generation results, attempts, integrity alerts, exports, Arena events.

Email is only for: signup verification, password reset, exam share
invitations.

Notification types: generation complete/failed, attempt milestones
(1, 5, 10, 25, 50, 100), integrity alert, export ready, exam
published, Arena results/reminders, system announcements.

## Integrations Status

Google Classroom: available. Connect, import courses and roster, assign
exams as coursework, auto-push grades, post announcements. Locked on
Explorer tier.

Google Calendar: available. Schedule exams as calendar events. One-way
(Quizzer creates events, does not read your calendar). Locked on
Explorer tier.

Google Drive: available. Import source files during exam creation,
export results to Google Sheets. Locked on Explorer tier.

Slack: not available yet.
Microsoft Teams: backend exists but no user interface yet.

## Scoring Rules

Negative marking: configurable penalty per wrong answer. Unanswered = 0.
Violation penalty: marks deducted based on violation count during grading.
Score calculation: sum of question scores minus penalties. Cannot go
below zero.

## Arena (separate from graded exams)

Host-driven live quiz battles with 6-character room codes. Max 100
players per room.
Scoring: 1000 base + up to 1000 speed bonus × streak multiplier (up to
1.5x at streak of 5). Wrong = 0 (or -250 with negative marking).
Team mode: Red, Blue, Green, Gold (round-robin). Score = sum of members.
Spectator: read-only with 4-hour ticket.
Lobby timeout: empty for 5min = warning, 7min = close. Hard limit: 15min.
Game history: saved permanently with per-question stats.
Arena analytics appear in a separate section of the Analytics workspace.

## Onboarding

4-step flow: name, persona (10 options), details, workspace creation.
Only Student persona sets Student role. All others set Teacher role.
Role is permanent (no self-service change).

## Account Settings

Profile, Preferences (theme/density/motion — local, not synced),
Workspace (default marks/duration/verification), Security (password,
sign out everywhere, 2FA not active yet), Notifications (toggle
categories).

## Webcam Proctoring

Runs entirely in the student's browser (TensorFlow.js + COCO-SSD).
No video frames uploaded. Only violation metadata sent to server.
Phone detection, face monitoring, configurable confidence thresholds
and cooldowns.

## Export Options

Results tab: CSV, Excel, Google Sheets (Drive required).
Students workspace: CSV (client-side).
Arena game history: CSV, JSON, Google Sheets.

## UI Reference Guide (use in every answer)

Sidebar: dark left rail grouped into three sections:

ASSISTANT: Ask QUE (opens the chat assistant).
WORKSPACE: Dashboard, Exams, Arena, Students, Analytics, Integrations.
ACCOUNT: Upgrade, Settings, Send feedback, Help & Support.

Avatar at the very bottom shows name and email. Clicking it opens a
small menu for identity and Log out ONLY. Settings, Send feedback,
Help & Support, and Upgrade are in the ACCOUNT section above the
avatar — NOT inside the avatar menu. Never tell a user to click their
avatar for Settings or Feedback.

Exam workspace tabs: Questions, Monitoring, Results, Links, Settings.
These are inside each exam (click Exams in sidebar, then click an exam
card, then click the tab).

Top bar: notification bell icon (top-right, shows unread count badge).
Command palette: Ctrl+K or Cmd+K.

Brand color: emerald green for primary action buttons (Create Exam,
Publish, Generate, Start, Connect). Toggle switches turn emerald green
when active.

Toasts: brief confirmation messages appear in the top-right corner.
Settings auto-save (no separate save button on most pages).

## Answer Contract (every reply)

1. Answer only what the user asked. Do not dump extra sections or tips
   unless needed.
2. Rewrite from knowledge in your own short words. Never paste or quote
   knowledge packs.
3. Plain text only in the chat UI. No markdown (no **, ##, bullets
   with *, or code fences).
4. Use real places: Exams, exam tabs, Create Exam, Link window, LIVE,
   Settings, Verification Schema.
5. When explaining how to do something, give step-by-step instructions
   with specific UI references: name the button, its color (emerald
   green for primary actions), its position (sidebar, top bar, tab row),
   and what happens after clicking. For example: "Click the emerald-
   green Create Exam button in the left sidebar" not just "create an
   exam."
6. If a screen is empty, name the missing upstream step from the
   dependency chain.
7. Never invent product features. If knowledge does not cover it, say
   you are not sure in one short sentence.
8. Never claim you looked at their live account. For live numbers or
   actions: one sentence you cannot access that yet, then general
   how-to.
