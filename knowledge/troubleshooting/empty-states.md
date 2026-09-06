---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Empty States and What to Do

## Overview

Many Quizzer workspaces appear empty when you first visit them because
they require specific prerequisites to populate. This guide explains
what each workspace needs and what to do when things look empty or
missing.

Users may call this: nothing showing, empty page, no data, blank,
where is my data, why is it empty, nothing here.

## The Data Dependency Chain

Almost everything in Quizzer flows from this chain:

Create exam → Add/generate questions → Approve questions → Publish
→ Share link → Student opens link → Student fills verification form
→ Student starts attempt → Student answers questions → Student submits
→ Grading runs → Results appear → Analytics aggregates

Each workspace draws from a different point in this chain. If you are
stuck at an earlier step, later workspaces will be empty.

## Exams Workspace

Shows: your exam library (drafts, published, archived).

Empty when: you have not created any exams yet.

What to do: click Create Exam to start your first exam.

## Questions Tab (inside an exam)

Shows: questions belonging to this exam.

Empty when: no questions have been generated or manually added yet.

What to do: upload source material and run AI generation, or manually
add questions. Generated questions start as Draft — review and approve
them.

## Links Tab (inside an exam)

Shows: the public share link and sharing options.

Empty or disabled when: the exam is not published yet.

What to do: publish the exam first. The Links tab activates after
publishing.

## Results Tab (inside an exam)

Shows: graded scores for submitted attempts.

Empty when: no students have submitted this exam yet. Students may
have opened the page or started an attempt but not submitted.

What to do: check the Monitoring tab for in-progress attempts. If
nobody has started, verify your exam is published and the link has been
shared.

## Monitoring Tab (inside an exam)

Shows: in-progress and recent exam attempts with integrity data.

Empty when: no students have started an attempt on this exam.

What to do: verify the exam is published, the link has been shared,
and the link window has not expired.

## Dashboard — Live Exams Panel

Shows: exams with currently active LIVE attempts.

Empty when: no students are actively taking any exam right now.

What to do: this is normal outside of exam hours. The panel fills
when students are actively in the middle of an attempt with their
browser open.

## Dashboard — New Account

Shows: activation checklist and getting-started guidance.

What to do: follow the checklist steps to create your first exam,
approve questions, and publish.

## Analytics Workspace

Shows: aggregate performance trends across exams.

Empty when: no exams have graded results yet.

What to do: verify the date range filter is not too narrow. Then check
that exams have been published AND students have submitted. Publishing
alone does not populate Analytics.

Common trap: the date range filter is the number one cause of
"Analytics is empty" reports. Widen the date range first.

## Students Workspace

Shows: learner directory with readiness, performance, and trends.

Empty when: no students have attempted exams in the selected scope.

What to do: check the scope bar at the top. It may be filtering to
exams or clusters with no attempts. Widen the scope. Also verify that
students have actually taken (not just been assigned) your exams.

Common trap: importing a Google Classroom roster does NOT fill the
Students workspace. The roster brings in names, but exam attempt data
requires actual exam submissions.

## Arena Workspace

Shows: quiz packs and game history.

Empty when: you have not created any Arena quiz packs or hosted any
games.

What to do: create a quick quiz pack or use an existing quiz to host
your first Arena game.

## Integrations Page

Shows: connected services (Google Classroom, Calendar, Drive).

Empty/disconnected: integrations require explicit connection via OAuth.

What to do: click Connect on the service you want to use. Each
integration has its own OAuth flow.

## Notifications Inbox

Shows: in-app notifications.

Empty when: no events have occurred that generate notifications (no
generation results, no attempt milestones, no exports, etc.).

What to do: this is normal for new accounts. Notifications will appear
as you use features.

## Quick Diagnosis Checklist

If a workspace is empty, run through this checklist in order:

1. Check filters (date range, scope, status) — adjust to widest view.
2. Check exam status — is the exam published?
3. Check link window — has available_until expired?
4. Check for attempts — have students actually started AND submitted?
5. Check grading — for Results/Analytics, grading must have completed.
6. Check integration status — for Drive/Classroom/Calendar features,
   is the service connected?

## Common Questions

Why is everything empty when I just signed up?
You need to create an exam first. Everything downstream depends on
having exams with published content and student submissions.

I published my exam but Analytics is still empty. Why?
Publishing is step 1. Students need to take the exam and submit it.
After grading completes, Analytics will show data. Also check your
date range filter.

I imported my Classroom roster but Students workspace is empty:
Roster import brings names, not attempt data. Students must actually
take exams for scores and readiness to appear.

## Related Features

See also: specific workspace guides for detailed feature information
