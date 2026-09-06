---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Quizzer Terminology

## Exam

The primary assessment unit in Quizzer. A teacher creates an exam, adds
questions (via AI or manually), configures settings, and publishes it so
students can take it. In the UI, the sidebar says Exams and the creation
action says Create Exam.

Exams have three lifecycle states: Draft (being prepared), Published
(live and accessible), and Archived (retired, results preserved).

Users may call this: quiz, test, assessment, paper, evaluation.

## Attempt

One sitting of an exam by a student. Each attempt has its own timer,
its own set of answers, its own violation record, and its own frozen
copy of the answer key. A student is identified by their verification
fields (such as name and enrollment number), not by a Quizzer account.

Multiple attempts are allowed if the teacher sets Maximum Attempts
greater than 1. Each attempt is independent.

Users may call this: try, sitting, submission, take, retake, session.

## Questions

Individual items within an exam. Quizzer supports five question types:

Multiple Choice (MCQ): one correct answer from a set of options.
True/False: binary choice between true and false.
Short Answer: typed text response, graded automatically with a smart
multi-step matching pipeline.
Long Answer: typed text response, may need teacher review if AI
confidence is low.
Multi-Select: multiple correct answers from a set of options.

Questions have a review status (Draft, Approved, Rejected) and a marks
value.

Users may call this: items, problems, prompts, tasks.

## Section

A grouping of questions within an exam. Sections have a title and can
contain questions of any type. The AI generation blueprint organizes
questions into sections. Sections help structure exams into logical
parts (e.g., "Part A: Multiple Choice" and "Part B: Short Answer").

You can reorder sections, move questions between them, and set marks
per section.

## Draft / Approved / Rejected

Question review statuses that form the review workflow:

Draft: the initial status after AI generation or manual creation.
Questions need review before publishing.

Approved: the teacher has confirmed the question is correct, well-
formed, and ready for students. Required for publishing.

Rejected: the teacher has marked the question as unsuitable. Rejected
questions are excluded from the exam.

The workflow is: Draft, then review (edit if needed), then Approved.
All questions must be Approved before the exam can be published. This
is the primary publish gate.

Users may call this: review status, question status, approval status.

## Publish

Making an exam available for students via a shareable link. Publishing
requires at least one question, all questions Approved, the exam not
archived, and AI generation not in progress. Publishing generates a
unique public link and sets a link window.

Users may call this: release, make live, activate, open, go live,
launch.

## Link Window

The time period during which the published exam link allows new
attempts to start. Set automatically on publish based on subscription
tier (Explorer: 24 hours, Professional: 1 week, Elite: custom dates).
Teachers can extend or renew the link window from the Links tab or
Exams workspace.

When the link window expires, the exam remains published but students
can no longer start new attempts. Existing in-progress attempts may
continue.

Users may call this: deadline, expiry, availability, link expiration,
how long the link works, when does it close, available until.

## Duration

The per-attempt timer in minutes. Once a student starts an attempt,
they have this many minutes to complete it. Default: 60 minutes.
Minimum: 5 minutes.

Users may call this: time limit, exam length, how long they have,
timer.

## Link Window vs Duration

These are different and commonly confused:

Link window: how long the published link accepts new starts (hours
or days). Controls WHEN students can begin.

Duration: how long each student has once they start (minutes). Controls
HOW LONG students can work.

A 60-minute exam with a 24-hour link window means students have 24
hours to start, and 60 minutes once they begin.

## Verification Schema

The identity form students fill out before starting an exam. Collects
fields like name, enrollment number, class, section, batch. Configured
per exam in the Settings tab, with an optional account-wide default.

Verification Schema determines how the teacher identifies students in
Results and the Students workspace. It also controls attempt
deduplication (same identity fields cannot exceed the Maximum Attempts
limit).

Not related to answer grading. Not answer keys or scoring rules.

Users may call this: student identity form, registration fields,
enrollment form, identity verification, student info, before-exam form.

## LIVE

A badge on Exams workspace cards and the Dashboard live panel
indicating a student has an active, in-progress attempt. All five
conditions must be true simultaneously:

1. Exam is published and not archived
2. A student started an attempt (not just opened the page)
3. The attempt has not been submitted
4. The server-side exam timer is still running
5. The student's browser tab is open with a recent heartbeat (within
   approximately 150 seconds)

LIVE drops within two to three minutes of a student closing their tab
(heartbeat stops).

Users may call this: active, in progress, currently taking, online,
who is taking the exam right now.

## Monitoring

A tab within each exam workspace showing in-progress and completed
attempts with detailed integrity and violation data. Not a sidebar
item. Access it by opening an exam from Exams, then selecting the
Monitoring tab.

Shows real-time integrity events via WebSocket for active attempts.

Users may call this: proctoring view, live view, watch students,
supervision, real-time tracking.

## Results

A tab within each exam workspace showing graded outcomes with scores,
violation counts, integrity flags, and export options per student.
Results are per-exam — each exam has its own Results tab.

Separate from Analytics, which shows aggregate trends across multiple
exams.

Users may call this: scores, grades, outcomes, marks, performance,
exam results.

## Analytics

A sidebar workspace showing aggregate performance data across all
exams and time periods. Includes charts for score distribution,
completion trends, and integrity flag rates. Has a separate section
for Arena game analytics.

Requires date range, quiz, and status filters. Empty when no graded
results exist or filters are too narrow.

Users may call this: reports, statistics, dashboard, performance data,
insights, charts.

## Students (Workspace)

A sidebar workspace (teacher view) showing all learners who have
attempted exams. Includes a searchable directory, readiness labels
(Strong learner, Needs coaching, Needs check-in, Live now, Not started),
support queue, cohort health visualization, and CSV export.

Scope can be filtered by specific exams or Google Classroom courses
via the scope bar.

Not the same as student-role accounts. The Students workspace shows
anyone who took your exams (no account needed), while a student
account is a specific Quizzer login type.

Users may call this: learners, roster, class list, student directory,
my students, who took my exams.

## Dashboard

The landing page after login. For teachers: overview metrics, live
exams panel, quick actions, activation checklist (for new accounts).
For students: welcome message with guidance cards.

Users may call this: home, main page, landing page, overview.

## Arena

A separate live quiz battle mode. A teacher (host) creates a room,
shares a six-character code, and players join to answer questions in
real time with speed-based scoring (1000 base + speed bonus ×
streak multiplier up to 1.5x). Supports team mode (Red, Blue, Green,
Gold), leaderboard, spectator tickets, and game history.

Completely separate from graded exams — different scoring system,
different history, different analytics section.

Users may call this: live quiz, battle, game, competition, Kahoot-style,
quiz game, live quiz battle.

## Blueprint

The structure specification for AI exam generation in Guided mode:
how many sections, which question types per section, number of
questions per section, and marks allocation. Limits: 20 sections max,
50 questions per section, 100 total questions, marks 1-100.

Users may call this: exam structure, generation template, question
plan.

## Source-first / Guided / Custom

The three AI generation modes when creating an exam:

Source-first (Recommended): AI reads uploaded content and extracts
questions directly from it. Best when you want the AI to decide
structure and types.

Guided: you specify an exact blueprint (count, type, topic per
section). AI follows your specification using source material as
context. Best when you need precise control.

Custom: create questions manually without AI. Best when you have
specific questions in mind.

Users may call this: generation mode, how to create questions, AI mode,
auto-generate.

## Grading Style

A per-exam setting controlling how written answers (Short Answer, Long
Answer) are evaluated by the AI grading system. Only appears in
Settings when the exam has written questions.

Balanced: standard evaluation. Good for most subjects.
Writing and Language: emphasizes grammar, structure, expression.
Formulas and STEM: emphasizes notation, formulas, units, accuracy.
Ideas and Concepts: emphasizes conceptual understanding over wording.
Key Terms: emphasizes specific technical vocabulary.

Users may call this: scoring mode, marking style, evaluation method.

## Negative Marking

A scoring option that deducts marks for wrong answers. Configurable
penalty amount per exam. Unanswered questions are not penalized.

Users may call this: penalty for wrong answers, mark deduction, minus
marking, negative scoring.

## Proctoring / Integrity

Browser-based monitoring during an exam. Includes fullscreen
enforcement, tab-switch detection, copy/paste blocking, and optional
webcam monitoring with AI phone detection and face monitoring.

Webcam proctoring runs entirely in the student's browser (TensorFlow.js
+ COCO-SSD). No video is uploaded to servers.

Violations are counted and can trigger auto-submit when the limit is
reached.

Users may call this: cheating prevention, monitoring, supervision,
anti-cheating, exam security, integrity settings.

## Violation

An integrity event detected during an exam attempt. Types include
tab switch, fullscreen exit, copy/paste attempt (browser-based), and
phone detected, face not detected (AI webcam-based). Each violation
increments the student's violation count toward the violation limit.

## Pending Professor Review

A result status indicating the automated grading pipeline could not
confidently score one or more written answers. The teacher needs to
manually review and score those answers. The overall score may be
incomplete until resolved.

Users may call this: needs review, manual grading needed, incomplete
score, why is the score pending.

## Subscription Tier

The user's plan level. Four tiers: Explorer (free/basic), Professional,
Elite, and Enterprise (contact only). Controls features like link
window duration, AI model selection, daily generation quota, Arena
quiz pack limits, and integration availability.

Quizzer is currently in public beta with every plan free.

Users may call this: plan, subscription, account level, pricing tier,
upgrade.

## Access Code

A single-use code generated by the teacher that students must enter
before starting an exam. Generated in batches of 1 to 200 from the
Settings tab. Provides an extra layer of access control beyond the
published link.

Users may call this: exam code, entry code, start code, passcode.

## Readiness Label

Auto-generated assessment of a student in the Students workspace:

Live now: actively taking an exam right now.
Strong learner: consistently high performance.
Needs coaching: low scores, room for improvement.
Needs check-in: inactive or declining performance.
Not started: has not attempted any exam in the current scope.

## Cohort

A group of students, typically from the same class, batch, or imported
Google Classroom course. Used in the Students workspace scope bar.

## Spectator

A read-only Arena role. Can see the live question, timer, and
leaderboard but cannot answer or control the game. Useful for
projecting the game on a screen. Access via a spectator ticket (valid
4 hours).

## Common Confusions

Exam vs Quiz: In Quizzer, these mean the same thing. The UI uses Exam.

Monitoring vs Analytics: Monitoring is per-exam (inside the exam
workspace, real-time). Analytics is cross-exam (sidebar, aggregate).

Results vs Analytics: Results shows individual scores for one exam.
Analytics shows aggregate trends across exams.

LIVE vs Monitoring: LIVE is a badge indicating active attempts.
Monitoring is a tab with detailed attempt and integrity data.

Link Window vs Duration: Link window is how long the published link
accepts new starts. Duration is how long each student has once they
start.

Students workspace vs Student accounts: The Students sidebar item is
a teacher tool showing learners from exam attempts. A student account
is a logged-in Quizzer user with a student role and limited interface.

Verification Schema vs Grading: Verification Schema is the identity
form before the exam. Grading is how answers are scored after
submission.

Arena vs Exams: Arena is a live, synchronous game with speed scoring.
Exams are asynchronous, individually timed assessments with detailed
grading.

Notifications vs Email: Most notifications are in-app only. Quizzer
does not email about generation, attempts, integrity, or exports.
Email is only for signup verification, password reset, and exam share
invitations.

Draft (exam) vs Draft (question): An exam in Draft state means it is
unpublished. A question in Draft status means it has not been reviewed
yet. Different concepts sharing the same word.
