---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Google Classroom Integration

## Overview

Quizzer integrates with Google Classroom to let teachers import class
rosters, assign exams as coursework, automatically push grades back to
Classroom, and post announcements. This connects your Quizzer exams
with your existing Google Classroom courses.

Users may call this: Classroom connection, Google integration, link
my class, import students, sync grades.

## Step-by-Step UI Guide: Connecting and Using Google Classroom

Step 1 — Open Integrations:
In the left sidebar, click Integrations (plug icon). The Integrations
hub loads showing available services.

Step 2 — Connect Classroom:
Find the Google Classroom card. Click the Connect button on the card.
A Google sign-in popup opens. Select your Google account and grant
Quizzer permission to access your Classroom courses, rosters, and
coursework. After authorizing, the popup closes and the card shows
"Connected" (green status).

Step 3 — Import courses:
In the Classroom section (now expanded after connecting), click Import
Courses. Your Google Classroom course list loads. Select the courses
you want to import by clicking their checkboxes. Click Import. The
selected courses are now available in Quizzer.

Step 4 — Import a roster:
Click on an imported course. Click Import Roster. Student names and
enrollment info from Google Classroom are pulled into Quizzer. These
appear in the Students workspace when you filter by this Classroom
cluster.

Step 5 — Assign an exam as coursework:
After publishing an exam, go to the exam's Links tab. Find the Assign
to Classroom option. Click it, select the Classroom course from the
dropdown, and click Assign. Students see the assignment in their
Google Classroom with a link to the exam.

Step 6 — Push grades:
After students take the exam and grading completes, scores are
automatically synced back to the Classroom coursework entry. You can
also trigger a manual push from the Classroom section in Integrations.

## How to Connect

Go to Integrations in the sidebar, find Google Classroom, and click
Connect. This starts a Google OAuth flow where you grant Quizzer
permission to access your Classroom data (courses, rosters,
coursework, announcements).

Quizzer uses separate Google credentials for Classroom than for
Google Sign-In. Connecting Classroom does NOT sign you into Quizzer
with Google, and signing in with Google does NOT connect Classroom.

## Available Features

Import courses: pull your Google Classroom course list into Quizzer.
You select which courses to import. Imported courses appear as
clusters in the Students workspace.

Sync courses: refresh already-imported courses with the latest data
from Google Classroom. This updates existing courses, not imports new
ones.

Import roster: pull the student roster for a specific imported course.
This brings in student names and enrollment info from Classroom
enrollment. The roster appears in the Students workspace when you
filter by that Classroom cluster.

Assign exam as coursework: create a coursework entry in your Classroom
course that links to your Quizzer exam. Students see the assignment
in their Google Classroom with a link to the exam.

Push grades: send graded scores from Quizzer back to Google Classroom.
This updates the coursework entry with each student's score.

Grade sync happens in two ways:
- Automatic: after a student submits and grading completes, scores are
  automatically synced back to Classroom.
- Manual: teachers can also trigger a manual grade push.

Post announcement: post exam results or other messages as Classroom
announcements.

Share material: share the exam link as a Classroom courseWork material.

Insights: view engagement statistics for Classroom-linked exams
(class-level insights, roster insights, activity).

## Important Distinction: Roster vs Attempts

Importing a Classroom roster brings in student identities from Google
Classroom. This does NOT mean those students have taken any Quizzer
exam. The roster and exam attempt data are separate.

A student appearing in an imported roster will only show scores,
readiness labels, and other metrics in the Students workspace after
they actually take and submit a Quizzer exam.

## Disconnecting

You can disconnect Google Classroom from the Integrations page. This
removes Quizzer's access to your Classroom data but does not delete
any exam results or attempt history already recorded in Quizzer.

## Plan Availability

Explorer tier: Classroom integration is locked. Available on
Professional and Elite tiers. During the public beta, this restriction
may be relaxed.

## Common Questions

How do I connect Google Classroom?
Go to Integrations in the sidebar, find Google Classroom, and click
Connect. Complete the Google OAuth authorization.

How do I import my class roster?
After connecting, go to the Classroom section in Integrations, import
your courses, then import the roster for a specific course.

How do I assign an exam to my Classroom students?
Publish your exam first, then use the Classroom section to create a
coursework entry linking to your exam. Students see it in their
Google Classroom.

Are grades synced automatically?
Yes. After a student submits and grading completes, scores are
automatically pushed to Classroom. You can also trigger a manual push.

Does importing the roster mean students have taken the exam?
No. Roster import brings in names from Google Classroom enrollment.
Students must actually open the exam link and take the exam for
attempt data and scores to appear.

Can I use Classroom sign-in to connect?
No. Classroom uses a separate OAuth connection from Google Sign-In.
You connect Classroom through the Integrations page, not through
your login.

What happens if I disconnect Classroom?
Quizzer loses access to your Classroom data. Existing exam results
and attempt history in Quizzer are not affected.

## Related Features

See also: Students Workspace (Classroom clusters), Publishing and
Sharing (Classroom assignment), Results and Exports (grade push),
Arena (Classroom roster join)
