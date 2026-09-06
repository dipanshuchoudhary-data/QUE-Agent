---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# LIVE, Monitoring, and Real-Time Exam Tracking

## Overview

Quizzer provides real-time visibility into exam activity through two
complementary features: LIVE badges that appear on the Exams and
Dashboard workspaces, and the Monitoring tab within each exam workspace
that shows detailed attempt and integrity data.

Users may call this: live view, proctoring view, who is taking the exam,
real-time monitoring, exam supervision.

## Step-by-Step UI Guide: Monitoring Live Exams

Step 1 — Check for LIVE activity:
In the left sidebar, click Exams. Look at your exam cards. Exams with
active attempts show a pulsing LIVE badge (a small green dot or "LIVE"
label on the card). You can also see live exams on the Dashboard in the
Live Exams panel.

Step 2 — Open the exam's Monitoring tab:
Click on the exam card with the LIVE badge. In the exam workspace,
click the Monitoring tab (second tab: Questions, Monitoring, Results,
Links, Settings).

Step 3 — View active attempts:
The Monitoring tab shows a table of attempts. Each row shows: student
name (from verification), attempt status (In Progress, Submitted),
violation count, and timing info. In-progress attempts appear at the
top.

Step 4 — View integrity events for a specific attempt:
Click on an attempt row to expand it. The integrity detail panel opens
showing a chronological timeline of all events: session start, tab
switches, fullscreen exits, phone detections, face checks, and
timestamps for each.

For in-progress attempts, this panel can update in real time via a
live connection, so you see violations as they happen.

Step 5 — Check the Dashboard live panel:
For a quick overview across all exams, go to the Dashboard (click
Dashboard in the sidebar). The Live Exams panel shows all exams with
currently active LIVE attempts, so you do not need to check each exam
individually.

## Where to Find It

LIVE badges: appear on exam cards in the Exams workspace and on the
Dashboard's live exams panel. These are at-a-glance indicators.

Monitoring tab: open Exams from the sidebar, open a specific exam, then
select the Monitoring tab. This shows detailed per-attempt data.

There is no top-level Monitoring or LIVE item in the sidebar. The URL
/monitoring redirects to the Exams workspace. Always navigate through
the specific exam.

## LIVE Badge Definition

A LIVE badge appears on an exam card when ALL of these conditions are
true simultaneously:

1. The exam is published and not archived.
2. A student has started an attempt (not just opened the landing page).
3. The attempt has not been submitted yet.
4. The server-side exam timer is still running.
5. The student's browser tab is open with a recent heartbeat signal
   (within approximately 150 seconds).

If any condition is false, the LIVE badge disappears. When a student
closes their browser tab, the heartbeat stops and LIVE drops within
two to three minutes.

Users may call this: active, in progress, currently taking, online,
who is live right now, live status.

## Why LIVE Might Not Appear

The exam is not published: publish the exam first.

The exam is archived: unarchive and republish.

Nobody started an attempt: students may have opened the exam page but
not clicked Start. Share the link again and confirm students know how
to begin.

The student already submitted: once submitted, the attempt is no longer
LIVE. Check Results instead.

The timer expired: if the per-attempt timer ran out, the attempt may
have been auto-submitted. Check Results.

The student closed their tab: LIVE drops within a few minutes of the
tab closing. The attempt may still be open on the server, but without
a heartbeat it does not show as LIVE.

The link window expired: if the available_until deadline has passed,
no new attempts can start. Existing in-progress attempts may also be
blocked.

## The Monitoring Tab

The Monitoring tab shows a table of attempts for the selected exam:

Each row includes:
- Student identity (from verification form)
- Attempt status (in progress, submitted, auto-submitted)
- Violation count
- Integrity event summary
- Timing information

## Integrity Events

The Monitoring tab can show detailed integrity events for each attempt.
Integrity events are the raw signals from the browser-based proctoring
system:

Session start/end: when the proctoring session began and ended.
Webcam status: whether the webcam was enabled, disabled, or
malfunctioned.
Phone detection: AI-detected phone or remote device in the webcam feed,
with confidence score.
Face check: whether a face was detected in the webcam feed.
Escalation: when violation counts crossed thresholds.
Tab switch: when the student left the exam tab.
Fullscreen exit: when the student exited fullscreen mode.

These events are timestamped and show a chronological timeline of
everything that happened during the attempt from a proctoring
perspective.

## Integrity WebSocket

For in-progress attempts, the Monitoring tab can receive real-time
integrity updates via a WebSocket connection. This means the teacher
can see violations as they happen, not just after submission.

This is a polling-list plus on-demand-websocket combination. The list
of attempts refreshes periodically, and clicking into a specific
attempt's integrity detail may open a real-time feed.

## Violation Types

Browser-based violations (detected by the exam interface):
- Tab switch or window blur
- Fullscreen exit
- Copy/paste attempt

AI-detected violations (from webcam, if enabled):
- Phone or remote device detected
- Face not detected (if face monitoring is enabled)
- Webcam blocked, covered, or disconnected

Each violation has a severity level and confidence score (for AI
detections). Violations accumulate toward the violation limit set in
the exam's Settings.

## Auto-Submit on Violations

If Enable Auto-Submit is turned on in the exam settings, the exam is
automatically submitted when the violation count reaches the violation
limit. This triggers grading immediately.

If auto-submit is off (the default), violations are recorded and the
student sees warnings, but they can continue the exam.

## Monitoring vs Results vs Analytics

Monitoring: per-exam, focused on in-progress and recent attempts,
integrity events, real-time violation tracking. Best during the exam.

Results: per-exam, focused on submitted and graded outcomes. Scores,
integrity flags, export options. Best after the exam.

Analytics: cross-exam, focused on aggregate trends over time.
Completion rates, average scores, score distribution, integrity flag
rates. Best for portfolio analysis.

## LIVE on the Dashboard

The Dashboard workspace has a live exams panel showing all exams with
currently active LIVE attempts. This gives teachers a quick overview
without opening each exam individually.

The Dashboard's live exam count uses the same LIVE definition: published,
unsubmitted, timer running, heartbeat active.

## Common Questions

Where is Monitoring?
Monitoring is not in the sidebar. Open Exams, open the specific exam,
then select the Monitoring tab.

Why is LIVE not showing even though students are taking the exam?
All five conditions must be true: published, not archived, attempt
started (not just page opened), not submitted, timer running, tab open
with recent heartbeat. If the student closed their tab, LIVE drops
within a few minutes. Check each condition.

What does LIVE actually mean?
It means a student has an active, in-progress exam attempt with their
browser tab open right now. It is not just "the exam is published."

Can I see violations in real time?
Yes. The Monitoring tab shows integrity events as they happen for
in-progress attempts, using a real-time connection.

What happens after a student submits?
The attempt moves from Monitoring to Results. LIVE disappears. Grading
runs immediately and results appear on the Results tab.

What is the difference between Monitoring and Results?
Monitoring shows in-progress and recent attempts with integrity data
(best during the exam). Results shows graded scores and exports (best
after the exam).

A student says they are taking the exam but I see no LIVE badge. Why?
They may have only opened the exam landing page without clicking Start.
Or their tab may be closed (heartbeat expired). Or the timer may have
already run out. Check each LIVE condition.

Can I see LIVE for all my exams at once?
Yes. The Dashboard has a live exams panel showing all exams with active
LIVE attempts.

## Related Features

See also: Exam Settings (proctoring, violation limit, auto-submit),
Results and Exports, Analytics, Taking Exams, Navigation
