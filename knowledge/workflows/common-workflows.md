---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Common Workflows

## Overview

This guide walks through common end-to-end workflows that span multiple
features. Use these as step-by-step recipes for common tasks.

Users may call this: how to, step by step, walkthrough, tutorial,
guide, help me with.

## Create and Publish Your First Exam

Goal: go from zero to a live exam that students can take.

1. Open Create Exam from the Dashboard quick actions or press Ctrl+K
   and type "Create Exam." The creation wizard opens.
2. Type an exam title in the title field at the top. Add an optional
   description below it.
3. Add source content in the content area below: paste text into the
   editor, or drag files onto the upload zone (PDF, DOCX, TXT), or
   paste a YouTube/web URL, or click Import from Google Drive if
   connected.
4. Select a generation mode: click Source-first (recommended, green
   badge) for AI to decide structure, or Guided to specify exact
   counts and types using the blueprint editor.
5. Click the emerald-green Generate button at the bottom. A processing
   indicator appears. Wait for the notification (bell icon in the top
   bar) confirming completion.
6. Go to Exams in the sidebar. Click your new exam card. Click the
   Questions tab. Review each question: click Approve (checkmark) on
   good ones, Reject (X) on bad ones, Edit (pencil) to fix, or use
   Bulk Approve at the top to approve all at once.
7. Click the Settings tab. Set Duration (timer), toggle proctoring
   switches, set Maximum Attempts, and configure Verification Schema.
8. Click the Publish button (emerald-green). A success screen shows
   your exam link.
9. Click Copy Link to copy the URL. Find it anytime on the Links tab.
10. Send the link to students via email, chat, Google Classroom
    (Assign to Classroom button on Links tab), or project the QR code.

## Run a Proctored Exam

Goal: use Quizzer's integrity and proctoring features for a supervised
assessment.

1. Create an exam and generate questions (see workflow above).
2. Click the Settings tab in the exam workspace. Scroll to the
   Proctoring section.
3. Verify these toggles are on (green): Require Fullscreen, Block Tab
   Switching, Block Copy/Paste. They are on by default.
4. Toggle on Enable Webcam Monitoring. Additional webcam settings
   appear below: Phone Detection (on by default), Face Monitoring
   (toggle on if you want face presence checks).
5. Set the Violation Limit field (default 3) to your desired threshold.
6. Toggle on Enable Auto-Submit if you want the exam to end
   automatically when the limit is reached.
7. Set Duration to the appropriate time for your exam.
8. Expand Verification Schema and configure identity fields (name,
   enrollment number, etc.) using a preset or custom fields.
9. Click Publish (emerald-green button).
10. Share the link. During the exam, click Exams in the sidebar, open
    the exam, and click the Monitoring tab to watch integrity events
    in real time.
11. After students submit, click the Results tab. Look for the
    integrity flag column and expand flagged rows to see violation
    timelines.

## Share Results with Students via Classroom

Goal: push exam scores back to Google Classroom.

1. Connect Google Classroom from the Integrations page.
2. Import your Classroom course.
3. When publishing the exam, assign it as coursework to the Classroom
   course. Students see the assignment in their Google Classroom.
4. After students take the exam and grading completes, scores are
   automatically synced back to Google Classroom.
5. Check the Classroom integration dashboard for sync status.

## Host a Live Arena Battle

Goal: run a live, real-time quiz competition with your class.

1. Go to Arena in the sidebar.
2. Create a quiz pack: either quick-create with new questions, or use
   an existing quiz with Approved questions.
3. Review and approve all questions in the pack.
4. Configure battle settings: timer per question, scoring options,
   team mode, negative marking, randomization.
5. Create the room. Copy the room code or share the join URL.
6. Wait in the lobby for players to join (share the code via
   projector, chat, etc.).
7. Click Start when enough players have joined.
8. Control the game: reveal answers, advance questions, skip, pause
   as needed.
9. At the end, the leaderboard shows. Export game history if desired.

## Export Results for Record-Keeping

Goal: download exam results for external use.

1. Open the exam workspace and go to the Results tab.
2. Click the export option.
3. Choose format: CSV, Excel, or Google Sheets (if Drive is connected).
4. Wait for the notification that the export is ready.
5. Download the file or open the Google Sheet.

## Review and Improve Low-Performing Exams

Goal: use Analytics and Results to identify and fix issues.

1. Go to Analytics and review score distribution.
2. Identify exams with unusually low average scores or high drop-off.
3. Open the specific exam's Results tab.
4. Look for patterns: are specific questions causing most wrong
   answers? Are many students timing out?
5. Check the exam Settings: is the timer too short? Is negative
   marking too harsh?
6. If needed, unpublish the exam, adjust questions or settings, then
   re-publish.
7. Note: changes only affect future attempts. Existing results are
   preserved with the original settings.

## Set Up Default Verification for All Exams

Goal: configure a standard identity form that applies to all new exams.

1. Go to Account Settings, Workspace tab.
2. Find Default Verification Schema.
3. Configure the fields you want (name, enrollment number, institution
   type, course, section, semester, batch).
4. Set which fields are required vs optional.
5. Save. All new exams will use this schema by default.
6. Individual exams can still override the default in their Settings.

## Monitor Student Progress Across Exams

Goal: track how your students are doing across all your assessments.

1. Go to the Students workspace in the sidebar.
2. Set the scope bar to include the exams or clusters you want.
3. Review the metrics strip: total students, active, completion rate,
   average score.
4. Use filters (All, Live, Support, Integrity, Strong) to focus on
   specific groups.
5. Click on individual students for detailed profiles.
6. Check readiness labels: Live now, Strong learner, Needs coaching,
   Needs check-in.
7. Use the support queue to prioritize outreach to struggling students.

## Schedule an Exam with Google Calendar

Goal: create a calendar event for an upcoming exam.

1. Connect Google Calendar from the Integrations page.
2. Create and publish your exam.
3. After publishing, use the Calendar section in Integrations or the
   post-publish screen to schedule the exam.
4. A calendar event is created on your Google Calendar with the exam
   link.
5. Optionally share the calendar event or invite students directly
   through Google Calendar.

## Handle Pending Professor Review

Goal: resolve written answers that need manual grading.

1. Go to the Results tab for the exam.
2. Filter by Pending Professor Review status.
3. Open each flagged attempt.
4. Review the answers that the AI could not confidently score.
5. Assign a score manually based on your evaluation.
6. Once all flagged answers are resolved, the status changes to
   Graded and the final score is updated.

## Common Questions

What is the fastest way to create an exam?
Paste text content or upload a PDF, configure the blueprint, click
Generate, approve questions, and publish. The AI handles question
creation.

Can I reuse questions across exams?
Questions belong to their exam. You cannot currently share questions
between exams, but you can create similar content using the same source
material.

How do I know if students are struggling?
Check the Students workspace for readiness labels (Needs coaching,
Needs check-in) and the support queue. Use Analytics for score
distribution trends.

## Related Features

See also: all feature-specific guides for detailed information on each
workflow step
