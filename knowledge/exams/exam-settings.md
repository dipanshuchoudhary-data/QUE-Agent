---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Exam Settings

## Overview

Every exam has configurable settings that control timing, question
presentation, proctoring and integrity, scoring, attempt limits, access
control, and student identity collection. Settings are accessed by
opening an exam from the Exams workspace and selecting the Settings tab.

Settings can be changed at any time, including after publishing. Some
changes may prompt a confirmation if students have in-progress attempts.
Changes to most settings affect future attempts only, not in-progress
ones.

Users may call this: exam configuration, exam options, how to set up,
exam properties, exam rules.

## How to Access

Exams (sidebar) → open the exam → Settings tab.

For account-wide defaults (marks, duration, verification): Account
Settings → Workspace tab.

## Step-by-Step UI Guide: Configuring Exam Settings

Follow these steps to set up your exam's timing, proctoring, and
scoring before publishing:

Step 1 — Open the exam:
In the left sidebar, click Exams. Click on your exam card to open the
exam workspace.

Step 2 — Go to the Settings tab:
At the top of the exam workspace, click the Settings tab (the
rightmost tab in the tab row: Questions, Monitoring, Results, Links,
Settings).

Step 3 — Set the duration:
Near the top of the Settings page, find the Duration field. It shows
a number (default 60 minutes). Click the field and type a new value
or use the picker to change how long each student has. Minimum is 5
minutes.

Step 4 — Configure question shuffle:
Look for Shuffle Questions and Shuffle Options toggles. Click the
toggle switch to turn them on (the switch slides right and turns
emerald green when active). Shuffle randomizes the order for each
student.

Step 5 — Set up proctoring:
Scroll to the Proctoring and Integrity section. You will see toggle
switches for:

Require Fullscreen — toggle is on by default (green). Leave it on to
force students into fullscreen mode.

Block Tab Switching — toggle is on by default. Leave it on to detect
when students leave the exam tab.

Block Copy/Paste — toggle is on by default.

Violation Limit — a number field showing the maximum violations (default
3). Click to change it.

Step 6 — Enable webcam proctoring (optional):
Find the Enable Webcam Monitoring toggle. Click it to turn it on (it
turns emerald green). Once enabled, additional webcam settings appear
below:

Enable Phone Detection — already on by default when webcam is enabled.
Phone Confidence Threshold — a slider or number field (default 70%).
Enable Face Monitoring — off by default. Toggle on if you want to
detect when students leave the camera frame.
Enable Auto-Submit — off by default. Toggle on if you want the exam to
auto-submit when the violation limit is reached.

Step 7 — Set scoring options:
Scroll to the Scoring section.

Default Marks — change the default point value for questions (default 1).
Negative Marking — toggle on to deduct marks for wrong answers. When
enabled, a Penalty field appears where you set the deduction amount.
Answer Grading Style — a dropdown that only appears if your exam has
Short Answer or Long Answer questions. Click the dropdown and select
from Balanced, Writing and Language, Formulas and STEM, Ideas and
Concepts, or Key Terms.

Step 8 — Set attempt limits:
Find Maximum Attempts (default 1). Change to a higher number if you
want students to retake the exam.
Allow Resume — toggle on if you want students to resume after a
browser close.

Step 9 — Configure access codes (optional):
Find Require Access Code and toggle it on. A Generate Codes button
appears. Click it, set the quantity (1 to 200), and click Generate.
Download or copy the codes to distribute to students.

Step 10 — Save:
Settings auto-save as you change them. You will see a small save
confirmation (a brief toast notification in the top-right corner).

## Timing

Duration: how long each attempt lasts, in minutes. This is the whole-
exam timer that starts when a student begins their attempt.
Default: 60 minutes. Minimum: 5 minutes. No explicit maximum.

The duration is per-attempt, not per-question. Arena battles have
per-question timers; graded exams do not.

Warning threshold: can be configured to show a timer warning when a
certain number of minutes remain. This alerts students that time is
running low.

When time runs out, the exam auto-submits with whatever answers have
been saved. Students cannot extend the timer.

Users may call this: time limit, exam length, how long they have,
timer, countdown.

## Question Order

Shuffle Questions: randomize the order of questions for each attempt.
Each student sees questions in a different order.
Default: Off.

Shuffle Options: randomize the order of answer choices within each
MCQ, True/False, and Multi-Select question. Each student sees options
in a different order.
Default: Off.

Both shuffle settings help prevent answer sharing between students
taking the exam at similar times. They are independent — you can
shuffle questions without shuffling options, or vice versa.

Users may call this: randomize, random order, mix up, scramble.

## Proctoring and Integrity

These settings control browser-based integrity monitoring during the
exam. They detect and report suspicious behavior.

Require Fullscreen: forces the exam into fullscreen mode when the
student starts. Exiting fullscreen counts as a violation.
Default: On.

Block Tab Switching: detects and reports when a student leaves the
exam tab (switching to another browser tab or window). Each tab switch
counts as a violation.
Default: On.

Block Copy/Paste: prevents copying or pasting text during the exam.
Attempts to copy or paste are blocked and counted as violations.
Default: On.

Violation Limit: the maximum number of integrity violations tolerated
before an escalation action (such as auto-submit if enabled, or a
final warning). The count includes all violation types combined
(browser and webcam).
Default: 3. Minimum: 1. Maximum: configurable.

Users may call this: cheating prevention, proctoring, anti-cheating,
exam security, integrity settings.

## Webcam Proctoring

These settings control camera-based monitoring. They only apply when
webcam monitoring is enabled. Webcam features do not appear in the
student's exam unless Enable Webcam Monitoring is turned on.

All webcam analysis runs entirely in the student's browser using a
client-side machine learning model (TensorFlow.js with COCO-SSD). No
video frames or images are uploaded to any server. Only violation
event metadata (type, timestamp, confidence score) is sent to the
backend.

Enable Webcam Monitoring: activate the webcam during the exam. The
student is asked for camera permission when starting.
Default: Off.

Enable Phone Detection: AI-based detection of phones or remote devices
in the webcam feed. When a phone is detected with sufficient
confidence, it counts as a violation.
Default: On (but only active when webcam monitoring is enabled).

Phone Confidence Threshold: the minimum confidence percentage the AI
model must reach before reporting a phone detection as a violation.
Higher values reduce false positives but may miss some detections.
Default: 70%. Range: 0% to 100%.

Phone Detection Cooldown: minimum seconds between phone detection
reports. Prevents rapid-fire violation counting from continuous phone
presence.
Default: 30 seconds. Minimum: 5 seconds.

Enable Face Monitoring: monitors whether a face is present in the
webcam feed. If no face is detected, it counts as a violation (student
may have left the frame or covered the camera).
Default: Off.

Webcam Grace Period: seconds before webcam violations start counting
after the exam begins. Gives students time to position their camera
and settle in.
Default: 10 seconds. Minimum: 3 seconds.

Max Webcam Violations: how many webcam-related violations are tolerated
before escalation. This is a subset threshold within the overall
violation limit.
Default: 3.

Max Phone Violations: how many phone detection events are tolerated
before escalation.
Default: 3.

Enable Auto-Submit: automatically submit the exam when the violation
limit is reached. Without auto-submit, violations are recorded and
the student sees warnings, but they can continue the exam.
Default: Off.

Users may call this: camera monitoring, webcam settings, phone
detection, face detection, AI proctoring.

## Scoring

Default Marks: the default point value assigned to each new question.
Individual questions can override this value. This setting also exists
as an account-wide default in Account Settings → Workspace tab.
Default: 1 mark.

Negative Marking: when enabled, wrong answers on objective questions
(MCQ, True/False, Multi-Select) cause a mark deduction. Unanswered
questions are not penalized.
Default: Off.

Penalty for Wrong Answer: the number of marks deducted per wrong
answer when negative marking is enabled. Applies uniformly to all
question types.
Default: 0 (effectively no penalty even if negative marking is toggled).

Violation Penalty: marks deducted during grading based on the number
of integrity violations the student accumulated. Separate from negative
marking for wrong answers. The formula uses the violation count to
calculate a penalty amount.
Default: 0 (no violation-based penalty).

Answer Grading Style: controls how written answers (Short Answer, Long
Answer) are evaluated by the AI grading system. This setting ONLY
appears when the exam contains at least one written question. If the
exam has only MCQ, True/False, or Multi-Select questions, this setting
is hidden.
Default: Balanced.

Options:
- Balanced: standard evaluation considering correctness, completeness,
  and clarity. Good for most subjects.
- Writing and Language: emphasizes grammar, structure, expression, and
  language quality. Best for language arts, literature, writing.
- Formulas and STEM: emphasizes mathematical notation, formulas, units,
  and scientific accuracy. Best for math, physics, chemistry.
- Ideas and Concepts: emphasizes conceptual understanding and reasoning
  over exact wording. Best for social sciences, philosophy.
- Key Terms: emphasizes the presence of specific technical terms and
  vocabulary. Best for medical, legal, technical fields.

Users may call this: scoring rules, marking scheme, how answers are
graded, grading mode, evaluation style.

## Attempts

Maximum Attempts: how many times a student (identified by verification
fields) can take the exam. Each attempt is independent with its own
timer and answers.
Default: 1. Minimum: 1. No explicit maximum.

If set to 1, students get one chance. If set higher, they can retake
the exam up to that many times.

Users may call this: retries, retakes, number of tries, how many times,
can I retake, multiple attempts.

Allow Resume: whether a student can resume an interrupted attempt
(browser closed, connection lost) instead of starting a new attempt.
When enabled, returning to the exam link resumes the same attempt
with the timer continuing from where it was (the timer does not pause).
Default: Off.

When Allow Resume is off, a closed browser may mean the attempt is
abandoned. The student would need to start a new attempt if attempts
remain and the link window is still open.

Prevent Duplicate: block the same identity (based on verification
fields) from starting multiple overlapping attempts simultaneously.
Prevents a student from opening the exam in multiple browser tabs.
Default: On.

## Access Control

Require Access Code: require a single-use, teacher-generated access
code that students must enter before starting the exam. Provides an
extra layer of access control beyond the published link.
Default: Off.

When enabled:
- Generate codes in batches of 1 to 200 from the Settings tab.
- Each code is a unique string that can only be used once.
- Students enter the code on the verification form before starting.
- Used codes are marked and cannot be reused.
- You can generate additional batches as needed.

This is useful for controlled distribution: give each student a unique
code to prevent unauthorized access even if the link is shared widely.

Users may call this: exam code, entry code, start code, passcode,
PIN, access key.

## Verification Schema

The identity fields students fill before starting the exam. Configured
by expanding the Verification Schema section on the Settings tab.

See the Verification Schema document for full details on field
configuration, presets (College, School, Coaching, Minimal), field
types, and the account-wide default.

Quick summary: the verification form collects student identity (name,
enrollment number, class, section, batch, etc.) for identification in
Results and the Students workspace. It also determines attempt
deduplication — the same identity fields cannot exceed the Maximum
Attempts limit.

## Settings After Publishing

Most settings can be changed on a published exam. Key considerations:

Timer changes: affect future attempts only, not in-progress ones.
Students who already started keep their original timer.

Proctoring changes: affect future attempts. In-progress attempts use
the proctoring settings from when they started.

Question changes: correct answer edits do not affect frozen answer
keys in existing attempts. New questions appear in future attempts.

Attempt limit changes: may allow or restrict additional attempts for
students who have already taken the exam.

Shuffle changes: affect future attempts only.

Verification schema changes: affect future attempts. Already-submitted
verification data is not modified.

Best practice: finalize settings before publishing. If changes are
needed on a live exam, be aware that they only affect students who
start a new attempt after the change.

## Common Questions

How do I set a time limit?
Open Exams, open your exam, go to Settings, and change the Duration
field.

How do I allow students to retake the exam?
Change Maximum Attempts to a number greater than 1 in Settings.

How do I enable webcam monitoring?
Open Settings and turn on Enable Webcam Monitoring. The other webcam
settings (phone detection, face monitoring) become active once this
is on.

What is the difference between Violation Limit and Auto-Submit?
Violation Limit sets how many violations are tolerated. Auto-Submit,
when enabled, automatically submits the exam once the violation limit
is reached. Without Auto-Submit, violations are recorded but the
student can continue.

Why do I not see the Answer Grading Style setting?
It only appears when your exam has at least one written question (Short
Answer or Long Answer). If you only have MCQ, True/False, or Multi-
Select questions, this setting is hidden.

Can I require an access code for the exam?
Yes. Turn on Require Access Code in Settings, then generate codes in
batches. Students enter a code before starting. Each code is single-use.

How do I set default settings for all my exams?
Go to Account Settings, then the Workspace tab. You can set default
marks, default duration, and a default verification schema that apply
to all new exams.

Is webcam video uploaded to a server?
No. All webcam analysis runs in the student's browser. Only violation
event metadata (type, timestamp, confidence) is sent to the server.
No video frames or images are transmitted.

Can I change settings after publishing?
Yes. Most settings can be changed at any time. Changes affect future
attempts, not in-progress ones.

What does Prevent Duplicate do?
It blocks the same student (by verification identity) from starting
multiple simultaneous attempts (like opening the exam in two tabs).

## Related Features

See also: Verification Schema, Questions (marks per question), Scoring
and Grading, Publishing and Sharing, Taking Exams (student experience),
Account Settings (workspace defaults)
