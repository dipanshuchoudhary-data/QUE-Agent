---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Results and Exports

## Overview

The Results tab in each exam workspace shows graded outcomes for every
student who submitted that exam. Teachers can view individual scores,
integrity data, violation timelines, and export results in multiple
formats.

Users may call this: scores, grades, marks, outcomes, performance,
exam results.

## Step-by-Step UI Guide: Viewing and Exporting Results

Step 1 — Open the exam:
In the left sidebar, click Exams. Click on the exam card whose results
you want to see.

Step 2 — Go to the Results tab:
At the top of the exam workspace, click the Results tab (third tab:
Questions, Monitoring, Results, Links, Settings). The results table
loads showing all submitted attempts.

Step 3 — Read the results table:
Each row shows one submitted attempt with columns: Student name,
Enrollment number (if collected), Final score, Violation count,
Integrity flag, Status (Graded or Pending Professor Review), and
Submitted timestamp.

Step 4 — View integrity details:
Click on any result row to expand it. The Integrity Review Panel opens
below, showing a violation timeline (chronological list of all
integrity events during that attempt) and violation buckets
(categorized counts).

Step 5 — Export results:
Look for the Export button (usually in the top-right area of the
Results tab, or as a dropdown menu). Click it and choose your format:

CSV — downloads a .csv file to your computer.
Excel — downloads an .xlsx spreadsheet.
Google Sheets — creates a new spreadsheet in your connected Google
Drive (only available if Drive is connected via Integrations).

After clicking, a background job starts. When ready, you get an
in-app notification (bell icon in the top bar) with a download link.

Step 6 — Filter results:
At the top of the Results table, look for filter options: All, Graded,
Pending Professor Review. Click a filter to narrow the view.

## How to Access Results

Results are accessed through each exam's workspace, not the sidebar.
There is no top-level Results item in the sidebar. The URL /results
redirects to the Exams workspace.

For cross-exam aggregate data, use the Analytics workspace instead.

## What the Results Tab Shows

Each row in the results table represents one submitted attempt:

Student name: from the verification form.
Enrollment number: from the verification form (if configured).
Other verification fields: institution type, course, section, semester,
batch (depending on the verification schema).
Final score: the total score after grading, negative marking, and
violation penalties.
Violation count: number of integrity violations during the attempt.
Integrity flag: whether the student had any violations (flagged or
clean).
Status: Graded or Pending Professor Review.
Submitted at: when the exam was submitted.

The integrity flag shows whether the student had any integrity
violations during the exam (such as tab switching, leaving fullscreen,
or phone detection); flagged results have a violation count above zero.
Results only appear after students submit and grading completes. If
there are no results, check the Monitoring tab for in-progress attempts.

## Score Trend

The Results tab may include a score trend visualization showing how
scores are distributed across all attempts for the exam. This helps
teachers quickly identify performance patterns.

## Filtering Results

Results can be filtered by status:
- All: every submitted attempt
- Graded: fully scored attempts
- Pending Professor Review: attempts with written answers awaiting
  manual review

## Integrity Review

Expanding a result row shows the Integrity Review Panel with detailed
violation data for that specific attempt:

Violation timeline: chronological list of all integrity events during
the attempt, including type (tab switch, fullscreen exit, phone
detected, face check, etc.) and timestamp.

Violation buckets: aggregated counts by violation category (browser
violations vs AI-detected violations).

This helps teachers determine whether flagged attempts had legitimate
issues or minor accidental triggers.

## Export Options

Teachers can export results from the Results tab:

CSV export: download results as a CSV file. Includes student identity
fields, scores, violation counts, integrity flags, and timestamps.

Excel export: download results as an Excel spreadsheet with the same
data as CSV.

Google Sheets export: if Google Drive is connected via Integrations,
export results directly to a Google Sheets spreadsheet. The spreadsheet
is created in the teacher's Drive account.

Exports are processed as background tasks. When the export is ready,
the teacher receives an in-app notification with a download link. The
download link is available for a limited time.

Users may call this: download results, export scores, get spreadsheet,
save results, download grades.

## Results Persistence

Results are never deleted by unpublishing or archiving an exam. If
you unpublish or archive an exam, all existing results remain fully
accessible and exportable from the Results tab. Only new attempts are
blocked.

Even if you try to delete an exam that has attempts, the system
archives it instead of deleting, preserving all result history.

Unpublishing or archiving only blocks new attempts; results are never
deleted.

## Pending Professor Review

When written answers (Short Answer, Long Answer) cannot be confidently
scored by the automated grading pipeline, they are marked as Pending
Professor Review.

What it means: the overall score may be incomplete. One or more
answers need manual review by the teacher.

What to do: open the attempt details, review the flagged answers,
and assign appropriate scores manually.

The status changes from Pending Professor Review to Graded once all
answers have been resolved.

## Results vs Analytics

Results: per-exam view. Shows individual scores for each student who
submitted that specific exam. Accessed from the exam workspace.

Analytics: cross-exam view. Shows aggregate trends, completion rates,
average scores, and charts across multiple exams and time periods.
Accessed from the sidebar.

Use Results to check individual performance on one exam. Use Analytics
for portfolio-level trends and comparisons.

## Related Features

See also: Scoring and Grading, Analytics, Monitoring and LIVE, Exam
Settings (violation penalty, proctoring)
