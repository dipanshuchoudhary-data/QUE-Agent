---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Students Workspace

## Overview

The Students workspace is a teacher-facing command center for managing
and understanding the learners who have attempted your exams. It shows
a directory of all students, their readiness status, performance trends,
support needs, and cohort health. This is NOT the student-role
dashboard — it is a teacher tool for learner management.

Users may call this: student list, learner directory, class roster,
who took my exams, student performance, student management.

## How to Access

Click Students in the sidebar. This is a top-level workspace.

## Who Can Use It

Teacher-role accounts only. Student accounts cannot access the Students
workspace.

## Step-by-Step UI Guide: Using the Students Workspace

Step 1 — Open Students:
In the left sidebar, click Students (it has a people icon). The
Students workspace loads.

Step 2 — Set the scope:
At the top, find the scope bar. It controls which students are shown.
Click the dropdown to choose:
All in cluster — see all students across your exams.
Custom scope — pick specific exams to filter by.
If you imported Google Classroom courses, those appear as cluster
options too.

Step 3 — Read the metrics strip:
Below the scope bar, a row of metric cards shows: Total students,
Active, Completed attempts, Average score, Support count, Cohort count.

Step 4 — Browse the student directory:
The main table shows all students with columns: Name, Attempt count,
Average score, Violation count, Readiness label, and Trend. Click
column headers to sort.

Step 5 — Filter by category:
Above the table, click filter tabs: All, Live (currently taking),
Support (needs attention), Integrity (flagged), Strong (top performers).

Step 6 — View a student profile:
Click on any student row. A detail modal opens showing their complete
profile: all attempts across exams, scores over time, violation
history, and readiness assessment.

Step 7 — Export data:
Look for the Export CSV button (usually in the top-right area). Click
it to download a spreadsheet with all student data.

## Scope Controls

The Students workspace has a scope bar at the top that controls which
students are shown:

Custom scope: select specific exams to see only students who attempted
those exams.

All in cluster: see all students across a group. Clusters include your
local exam library and any imported Google Classroom courses.

Deep links: the URL can include query parameters to pre-filter by a
Classroom course or a specific student.

If the Students workspace appears empty, the scope bar is the first
thing to check. It may be filtering to exams that have no attempts.

## Metrics Strip

At the top of the workspace, a metrics strip shows key numbers:

Total students: unique learners across the scoped exams.
Active: students with recent activity.
Completed attempts: total submitted attempts.
Average score: mean score across the scoped data.
Support count: students flagged as needing support.
Cohort count: number of distinct cohorts or groups.

## Student Directory

The main panel is a searchable, sortable table of students with:

Student name and verification details (enrollment number, institution,
etc.).
Attempt count: how many exams they have attempted.
Average score: their mean score across attempts.
Violation count: total integrity violations.
Readiness label: an auto-generated assessment of the student's status.
Trend: whether their performance is improving, stable, or declining.

## Filter Options

The directory can be filtered by:

All: every student.
Live: students currently with LIVE (active) attempts.
Support: students flagged as needing attention.
Integrity: students with integrity flags or violations.
Strong: top-performing students.

## Readiness Labels

Each student gets an auto-generated readiness label based on their
activity and performance:

Live now: the student has an active, in-progress attempt right now.
Not started: the student has not attempted any exam in the scope.
Strong learner: consistently high performance.
Needs coaching: scores indicate room for improvement.
Needs check-in: inactive for a while or declining performance.

These labels help teachers quickly identify who needs attention without
reviewing every score manually.

## Support Queue

The support queue highlights students who might need help — those with
low scores, declining trends, or many integrity violations. This helps
teachers prioritize outreach.

## Cohort Health

A cohort health visualization shows the distribution of readiness
across the student population. This gives a snapshot of how the class
or group is performing overall.

## Recent Attempts

A panel showing the most recent attempts across the scoped exams,
giving teachers a quick view of latest activity.

## Top Performers

A section highlighting the highest-performing students in the current
scope.

## Insights

Auto-generated text summaries providing quick observations about the
student population, such as engagement patterns, common difficulties,
or notable trends.

## Learner Modal

Clicking on a student opens a detailed profile modal showing:

Preview card: quick summary of the student's key metrics.
Full profile: complete attempt history across exams, scores over time,
violation history, and readiness assessment.

## CSV Export

Teachers can export the Students data to CSV. The export includes:
student name, verification fields, attempt count, scores, violations,
readiness label, and trend.

This is a client-side export (generated in the browser, not a server
background task like Results export).

## Google Classroom Roster

If Google Classroom is connected, the Students workspace can show
students imported from a Classroom roster when that cluster is selected.

Important distinction: the Classroom roster and exam attempt starters
are different data sources. A student appearing in the Classroom roster
does not mean they have attempted any exam. The roster comes from Google
Classroom enrollment. The attempt data comes from actual exam
submissions.

Importing a Classroom roster does NOT populate the Students workspace
with attempt data. Students must actually take and submit exams to
appear with scores and readiness labels.

## What Makes Students Empty

The Students workspace requires exam attempts. The dependency chain:

Create exam, then publish, then students take the exam, then they appear
in the Students workspace.

If empty:
- Scope bar may be filtering to exams with no attempts
- No exams have been published
- Exams are published but nobody has started
- Students started but have not submitted (may still appear as Live now)
- Classroom roster imported but no exam attempts from those students

## Students Workspace vs Student Accounts

The Students sidebar item is a teacher tool showing learner data from
exam attempts.

A student account is a logged-in Quizzer user with a student role who
has a limited interface (Dashboard + Help only).

These are different things. The Students workspace shows anyone who
took your exams (they do not need Quizzer accounts), while a student
account is a specific type of Quizzer login.

## Common Questions

How do I see my students?
Click Students in the sidebar. Use the scope bar to select which exams
or clusters to include.

Why is the Students workspace empty?
Check the scope bar first. Then verify that students have actually
started exams. Publishing alone is not enough — students need to take
the exam. Classroom roster import is also not enough.

What do the readiness labels mean?
They are auto-generated assessments: Live now (active attempt), Strong
learner (high scores), Needs coaching (low scores), Needs check-in
(inactive or declining). They help you quickly identify who needs
attention.

Can I export student data?
Yes. Use the CSV export option to download a spreadsheet with names,
scores, violations, readiness, and trends.

What is the difference between the Students workspace and Analytics?
Students is a people-centric view (who are your learners, how are they
doing individually). Analytics is a data-centric view (aggregate trends
across exams). Both need exam attempts to show data.

Does importing a Classroom roster fill the Students workspace?
No. Classroom roster import brings in student names and enrollment from
Google Classroom, but it does not create exam attempt data. Students
must actually take exams to appear with scores and readiness labels.

## Related Features

See also: Analytics, Results and Exports, Monitoring and LIVE, Google
Classroom Integration, Roles
