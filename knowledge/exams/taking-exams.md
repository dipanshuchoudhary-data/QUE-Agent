---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Taking Exams (Student Experience)

## Overview

This document covers the complete exam experience from the student's
(taker's) perspective — from opening the link to receiving the
submission confirmation. Students access exams through a published link
shared by the teacher. No Quizzer account is required.

Users may call this: sitting an exam, doing a test, answering questions,
taking a quiz, student experience, taker flow.

## Step-by-Step UI Guide: What Students See When Taking an Exam

This is the exact flow a student experiences from start to finish:

Step 1 — Open the link:
The student clicks the exam link shared by the teacher (in an email,
chat message, Classroom, or by scanning a QR code). The link opens in
their web browser and loads the exam start page.

Step 2 — Read the exam info:
The start page shows a card with the exam title at the top, the
duration (for example, "60 minutes"), the total number of questions,
and the exam rules. If webcam monitoring is enabled, a notice says
"This exam requires your camera." The student reads this to understand
what to expect.

Step 3 — Fill the verification form:
Below the exam info, the student sees input fields asking for their
identity. Common fields: Name (text box), Enrollment Number (number
field), Section (dropdown), Semester (dropdown). Required fields have
a red asterisk. The student fills in all required fields.

If an access code is required, there is also an Access Code field.
The student types the code given by the teacher.

Step 4 — Click Start:
At the bottom of the form, a Start Exam button appears (it is disabled
until all required fields are filled). Once filled, the button becomes
active (emerald green). The student clicks it.

Step 5 — Grant permissions:
If fullscreen is required, the browser goes fullscreen. If webcam
monitoring is on, a browser permission popup asks "Allow camera access."
The student clicks Allow. A brief grace period starts (about 10
seconds) before webcam violations begin counting.

Step 6 — Answer questions:
The exam interface loads with:
- The question text in the center of the screen
- For MCQ: clickable option cards (click one to select, it highlights)
- For True/False: two option cards (True and False)
- For Short Answer: a text input field
- For Long Answer: a larger text area
- A question navigator panel on the side showing numbered circles for
  each question (green = answered, gray = unanswered, orange = flagged)
- A countdown timer in the top area showing remaining time
- A small auto-save indicator that briefly shows "Saved" after each
  answer change

The student clicks a question number to jump to it, or uses Next and
Previous buttons. They can answer in any order and change answers
freely.

Step 7 — Handle proctoring warnings:
If the student switches tabs, exits fullscreen, or triggers a webcam
violation, a warning overlay appears on screen. It shows the violation
type and remaining violations allowed. The student should return to
fullscreen and stay focused on the exam tab.

Step 8 — Submit:
When ready (or when done with all questions), the student clicks the
Submit button (usually in the bottom-right area of the exam interface).
A confirmation dialog appears showing how many questions are answered
and how many are unanswered. The student clicks Confirm Submit.

If time runs out, the exam auto-submits with whatever answers were
saved. If the violation limit is reached with auto-submit enabled,
the exam auto-submits immediately.

Step 9 — See confirmation:
After submission, a confirmation page appears showing "Exam Submitted
Successfully" with a timestamp. The student cannot go back or change
answers.

## How Students Access an Exam

The teacher publishes the exam and shares the link (via copy/paste,
email, Google Classroom, or QR code). Students open the link in a web
browser.

Requirements for the link to work:
- The exam must be published (not unpublished or archived)
- The link window must still be open (available_until not expired)
- If access codes are required, the student needs a valid unused code
- The student must not have exceeded the maximum attempts limit

Students do NOT find exams through the Quizzer website, a search, or
a dashboard listing. They ONLY access exams through links shared by
the teacher. Even students with Quizzer accounts cannot discover exams
on their own.

## What Students See: Step by Step

### Step 1: Start Page

When a student opens the exam link, they see a start page with:

- Exam title: the name set by the teacher
- Duration: how long they will have (e.g., "60 minutes")
- Number of questions: total question count
- Exam rules summary: what proctoring features are active (fullscreen
  required, tab switching detected, copy/paste blocked, webcam
  monitoring enabled)
- Instructions: any additional guidance

If the exam requires webcam monitoring, a prominent notice informs
the student that their camera will be used. The student sees what
proctoring measures are active before committing to start.

If the link window has expired, the student sees a message that the
exam is no longer available.

### Step 2: Verification Form

Before starting the attempt, the student fills out the verification
form. This form collects identity fields configured by the teacher:

Common fields: name (almost always required), enrollment number, class,
section, semester, batch, institution type, course, phone, email.

The specific fields depend on the teacher's verification schema
configuration (presets: College, School, Coaching, Minimal).

Required fields must be filled before proceeding. Optional fields can
be left blank.

If access codes are required, the code entry field appears as part of
this step. Each code can only be used once — entering an already-used
code is rejected.

The verification form is how the teacher identifies students in
Results and the Students workspace. The same identity fields determine
whether a student has used their allowed attempts.

Users may call this: identity form, registration, sign-in form,
entering details, student info form.

### Step 3: Starting the Attempt

After completing the verification form, the student clicks Start. At
this point:

- An attempt record is created on the server with a unique attempt
  token
- The exam timer starts counting down from the configured duration
- All questions are loaded with their current content, frozen at this
  moment (if the teacher edits questions after this point, this
  student's attempt uses the version from when they started)
- Answer keys are frozen (correct answers locked for grading purposes)
- If fullscreen is required, the browser enters fullscreen mode
- If webcam monitoring is enabled, the browser requests camera
  permission
- The webcam grace period begins (violations from the webcam do not
  count during this window)
- A heartbeat begins sending periodic signals to the server (this is
  what makes the LIVE badge appear for the teacher)

### Step 4: The Exam Interface

Students see a focused, distraction-free exam layout:

Question display: one question at a time with its text, options (for
MCQ, True/False, Multi-Select), or answer field (for Short Answer,
Long Answer).

Question navigator: a sidebar or panel showing all question numbers.
Students can jump to any question at any time. The navigator shows
status indicators — which questions are answered, which are unanswered,
and which are flagged for review.

Timer: a prominent countdown showing remaining time. Changes color or
shows a warning when time is running low (based on the warning
threshold setting).

Auto-save indicator: answers are saved automatically as the student
types or selects options. A small indicator confirms saves. There is
no manual save button — everything is auto-saved.

Submit button: visible at all times. Submits the entire exam when the
student is ready.

Flag for review: students can flag individual questions they want to
revisit before submitting. Flagged questions are marked in the
navigator.

Progress indicator: shows how many questions are answered out of the
total.

### Step 5: Answering Questions

For Multiple Choice (MCQ): tap or click one option. The selection is
highlighted. Tap a different option to change.

For True/False: tap True or False.

For Multi-Select: tap multiple options. Each tap toggles the selection.
All correct options must be selected for full marks.

For Short Answer: type the answer in a single-line text field.

For Long Answer: type the answer in a multi-line text area with more
space for extended responses.

Students can navigate between questions freely — go forward, go back,
jump to any question number. Answers are auto-saved on every change.
Students can change their answers at any time before submitting.

Unanswered questions: students can skip questions and come back later.
Unanswered questions at submission time score zero (no negative marking
penalty for unanswered, even if negative marking is enabled).

### Step 6: Proctoring During the Exam

Depending on exam settings, the following may be actively monitoring:

Fullscreen enforcement: the browser must stay in fullscreen mode.
Exiting fullscreen (pressing Escape, Alt+Tab, etc.) counts as a
violation. A warning overlay appears asking the student to re-enter
fullscreen.

Tab-switch detection: switching to another browser tab or window is
detected and counted as a violation. The system uses the browser's
visibility API to detect focus changes.

Copy/paste blocking: attempting to copy text, paste text, or use
keyboard shortcuts like Ctrl+C / Ctrl+V is blocked. The action is
prevented and a violation may be recorded.

Webcam monitoring (if enabled):
- Phone detection: the AI model scans the webcam feed for phones or
  remote devices. Detections above the confidence threshold (default
  70%) count as violations.
- Face monitoring (if enabled): checks whether a face is present in
  the frame. No face detected (student left, camera blocked) counts
  as a violation.
- A small webcam preview may be shown so students can verify their
  camera is working.

Violation warnings: when a violation occurs, the student sees a
warning notification. The remaining violation count may be displayed.
Repeated violations show increasingly urgent warnings.

Auto-submit: if auto-submit is enabled and the violation limit is
reached, the exam is submitted immediately and automatically. The
student sees a message that their exam was submitted due to integrity
violations. Grading begins.

If auto-submit is off (the default), violations are recorded but the
student can continue the exam.

### Step 7: Submitting the Exam

Students can submit at any time by clicking the Submit button. Before
final submission, a confirmation dialog appears showing:
- How many questions are answered vs total
- How many are flagged for review
- A confirm/cancel choice

The exam is also submitted automatically when:
- The timer runs out (all saved answers are submitted)
- The violation limit is reached with auto-submit enabled

After submission, answers cannot be changed. The attempt is locked.

### Step 8: After Submission

Students see a submission confirmation page with:
- Confirmation that the exam was submitted successfully
- Submission timestamp
- Attempt summary (number of questions answered)

Students cannot go back, review answers, or retake the exam from this
page. If the teacher allows multiple attempts and the link window is
still open, the student can open the link again to start a fresh
attempt.

Grading happens immediately:
- Objective questions (MCQ, True/False, Multi-Select) are graded
  instantly
- Written questions (Short Answer, Long Answer) go through the
  6-step smart grading pipeline

The teacher can see results in the Results tab and the student appears
in the Monitoring/Results data.

## Resuming an Attempt

If Allow Resume is enabled in the exam settings and a student's
browser closes, crashes, or they navigate away:

- They can return to the exam link
- The system recognizes their identity (from verification fields) and
  offers to resume the existing attempt
- The timer continues from where it was — it does NOT pause when the
  browser is closed
- All previously auto-saved answers are preserved
- The student picks up where they left off

If Allow Resume is off (the default):
- A closed browser may mean the attempt is interrupted
- The student cannot resume that specific attempt
- They may need to start a new attempt (if attempts remain and the
  link window is open)
- The interrupted attempt's auto-saved answers are still recorded,
  and the timer continues until it expires (potentially auto-submitting
  whatever was saved)

## Multiple Attempts

If the teacher set Maximum Attempts to more than 1:

- The student can take the exam multiple times
- Each attempt is fully independent: own timer, own answers, own
  violation record, own frozen answer key
- The student opens the same exam link to start a new attempt
- The system identifies them by their verification fields (name,
  enrollment number, etc.)
- If they have used all allowed attempts, starting a new one is blocked

Multiple attempts are tracked separately in the teacher's Results tab.
Each attempt has its own row.

## Browser Requirements

The exam interface works on modern browsers: Chrome, Firefox, Edge,
Safari. Best experience on desktop Chrome.

Webcam proctoring requires:
- A browser that supports the MediaStream API (webcam access)
- Camera permission granted for the Quizzer domain
- An actual camera connected and working

Fullscreen mode requires a browser that supports the Fullscreen API.

Mobile browsers work for the exam interface but may have limitations
with fullscreen enforcement and webcam features.

## What Students Cannot Do

Students taking an exam CANNOT:
- See other students' answers or scores
- See the correct answers during the exam
- See the teacher's identity or settings
- Access the creator workspace
- Extend their timer
- Pause the exam (the timer is always running)
- Submit after the timer expires (auto-submission happens)
- Take more attempts than allowed
- Reuse an access code

## Common Questions

How do students take the exam?
The teacher shares a published link. Students open it, fill the
verification form with their identity, and start. No account needed.

Do students need a Quizzer account?
No. Students access the exam via the shared link and identify
themselves through the verification form.

Can students go back to previous questions?
Yes. Students can navigate freely between all questions during the
exam using the question navigator.

What happens if a student closes their browser?
If Allow Resume is on, they can reopen the link and continue (timer
does not pause). If off, the attempt may be interrupted. Auto-saved
answers are preserved either way.

What happens when time runs out?
The exam is submitted automatically with whatever answers have been
saved up to that point.

Can students retake the exam?
Only if the teacher set Maximum Attempts to more than 1. Each retake
is a completely fresh attempt.

What happens if the student gets too many violations?
If auto-submit is enabled, the exam is submitted automatically when
the violation limit is reached. If auto-submit is off, violations are
recorded but the student can continue.

Can students see their score after submitting?
The submission confirmation page does not show the score. Students see
confirmation that the exam was submitted. The teacher decides whether
and how to share scores.

What happens if the webcam stops working?
If webcam monitoring is enabled and the camera disconnects or is
covered, it may trigger face monitoring violations (if face monitoring
is on). The student should ensure their camera is working before
starting.

Can students use their phone to take the exam?
Yes, the exam link works on mobile browsers. However, webcam proctoring
and fullscreen enforcement may have limitations on mobile devices.

## Related Features

See also: Exam Settings (proctoring, attempts, duration), Verification
Schema, Publishing and Sharing (link window), Scoring and Grading,
Monitoring and LIVE
