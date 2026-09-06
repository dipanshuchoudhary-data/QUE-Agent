---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Analytics

## Overview

The Analytics workspace provides aggregate performance data across all
your exams over time. Unlike the Results tab (which shows individual
scores for one exam), Analytics shows trends, distributions, and
comparisons across your entire exam portfolio.

Users may call this: reports, statistics, insights, performance data,
dashboard, charts, exam analytics.

## How to Access

Click Analytics in the sidebar. This is a top-level workspace, not
inside a specific exam.

## Who Can Use It

Teacher-role accounts only. Student accounts cannot access Analytics.

## Step-by-Step UI Guide: Using Analytics

Step 1 — Open Analytics:
In the left sidebar, click Analytics (it has a chart icon). The
Analytics workspace loads showing your aggregate data.

Step 2 — Check the date range:
At the top of the Analytics page, find the date range filter. It may
be set to a specific period (like "Last 7 days"). Click the date
picker to widen or narrow the range. This is the most common reason
Analytics appears empty — the date range might not include your data.

Step 3 — Read the summary metrics:
At the top, you will see metric cards showing: Total attempts,
Completion rate, Average score, Score spread, and Integrity flags.
Each card shows the current value and a comparison to the previous
period (an up or down arrow with a percentage change).

Step 4 — Browse the charts:
Scroll down to see visualizations: score distribution chart, completion
trend over time, violations by quiz, and attempts mix. These help you
spot patterns.

Step 5 — Filter by quiz:
Use the Quiz filter dropdown to focus on a specific exam, or select
All to see everything.

Step 6 — Filter by status:
Use the Status filter to show only completed, in-progress, or flagged
(integrity issues) attempts.

Step 7 — Check Arena analytics:
Scroll to the Arena section (separate from graded exam analytics).
This shows data from Arena game history.

## Key Metrics

The Analytics workspace shows these primary metrics:

Total attempts: how many exam attempts have been made across all
filtered exams in the selected date range.

Completion rate: the percentage of started attempts that were actually
submitted. Helps identify drop-off.

Average score: the mean final score across all graded attempts in the
filtered set.

Score spread: the range between the highest and lowest scores (high
and low markers).

Integrity flags: the count of attempts that had integrity violations.

Period-over-period deltas: each metric shows a comparison to the
previous equivalent time period (for example, this week vs last week),
indicating whether the number went up or down.

## Filters

Analytics data can be filtered by:

Date range: select a start and end date to focus on a specific time
period. Widening or narrowing the date range changes which attempts
are included.

Quiz filter: focus on a specific exam or view all exams together.

Status filter: filter by attempt status — all, completed, in progress,
or flagged (integrity issues).

If Analytics appears empty, the first thing to check is whether the
filters (especially date range) are too narrow.

## Charts and Visualizations

Score distribution: a chart showing how scores are distributed across
all attempts. Helps identify whether most students clustered around
a certain score.

Completion trend: a chart showing how completion rates change over
time. Useful for spotting patterns in student engagement.

Violations by quiz: shows which exams have the most integrity
violations, helping identify problematic assessments.

Attempts mix: breakdown of attempt statuses across the portfolio.

Performance table: a detailed table with per-exam rows showing attempt
count, average score, completion rate, and other metrics. Clicking a
row can open a detail panel for that exam.

## At-a-Glance Cards

Analytics includes summary cards for quick insights:

Top exam: the exam with the most attempts or best performance.

Completion: overall completion rate across the portfolio.

Integrity: overall integrity flag rate.

## Arena Analytics Section

Analytics has a separate section for Arena (live quiz battle) data.
This shows metrics from Arena game history, which is tracked separately
from graded exam results.

Arena analytics and graded exam analytics can differ because they draw
from different data sources. An empty graded exam section can still
have Arena data, and vice versa.

## What Makes Analytics Empty

Analytics requires graded attempts. The dependency chain is:

Create exam, then publish, then students take the exam, then students
submit, then grading completes, then Analytics has data to show.

If Analytics is empty:
- No exams have been created yet
- Exams are created but not published
- Exams are published but nobody has started an attempt
- Students started but have not submitted yet
- Date range filter excludes the relevant attempts
- Quiz filter is set to a specific exam that has no attempts

Publishing alone does not populate Analytics. Graded results are needed.

## Analytics vs Results

Analytics: cross-exam aggregate view. Shows trends and distributions
across many exams and time periods. Accessed from the sidebar.

Results: per-exam detail view. Shows individual scores for each student
who submitted a specific exam. Accessed from inside that exam's
workspace.

Use Analytics for the big picture. Use Results for individual student
performance on a specific exam.

## Common Questions

Where is Analytics?
In the sidebar. Click Analytics. It is a top-level workspace, not
inside a specific exam.

Why is Analytics empty?
Check your date range filters first (the most common cause). Then
verify that you have exams with submitted and graded attempts. Simply
publishing an exam does not populate Analytics — students need to take
and submit it.

What is the difference between Analytics and Results?
Analytics shows aggregate trends across exams. Results shows individual
scores for one exam. Use Analytics for the portfolio view, Results for
per-student details.

Can I see Arena data in Analytics?
Yes. Analytics has a separate section for Arena game history. It is
separate from graded exam data.

How do I narrow down the data?
Use the date range, quiz, and status filters at the top of the
Analytics workspace.

Why do the numbers look different from what I expected?
Check your filters. Date range, quiz selection, and status filters all
affect which attempts are included. A narrow date range may exclude
recent or older data.

## Related Features

See also: Results and Exports (per-exam scores), Students Workspace
(people view), Dashboard (overview metrics), Arena
