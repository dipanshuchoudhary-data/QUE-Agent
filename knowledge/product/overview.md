---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# What is Quizzer

## Overview

Quizzer is an AI-powered assessment platform for creating, delivering,
monitoring, and analyzing exams. It serves anyone who needs to build
assessments — from students practicing for their own exams to
institutions running large-scale evaluations.

The core idea: upload your content (text, PDFs, YouTube videos, web
pages), let AI generate exam questions from it, review and approve
them, publish a link, and let students take the exam. Quizzer handles
the rest — real-time monitoring, automatic grading, integrity
detection, and analytics.

Users may call this: the app, the platform, the website, Quizzer,
assessment tool, exam platform, quiz maker, test builder.

## Who Quizzer is For

Students studying on their own: create practice exams from your study
material, take them yourself, and track your growth over time. The
self-study flow uses the same powerful AI generation as the teacher
flow.

Solo teachers and tutors: build exams from your course content with
AI, share them with students via a simple link, monitor attempts in
real time, review results, and analyze performance across exams.

Trainers and freelancers: run skills assessments for clients or
corporate teams. Create assessments from training material, use
proctoring for integrity, and export results for reporting.

Teams and startups: conduct hiring quizzes, onboarding knowledge
checks, or internal certification tests. Multiple exam types and
scoring options support different assessment needs.

Coaching institutes: manage exams across batches and cohorts.
Verification schemas collect student identity fields like enrollment
numbers, sections, and batches. The Students workspace tracks learner
readiness and support needs.

Schools and universities: build exams with AI from course content,
enable webcam proctoring for integrity, push grades to Google
Classroom, and schedule exams via Google Calendar. The verification
schema can be configured for school-specific fields.

HR professionals: create hiring assessments, compliance tests, or
skills evaluations. Access codes provide controlled exam distribution.

Content creators: build and publish educational quizzes from any
source material.

## What You Can Do

Create exams from any content: paste text directly, upload documents
(PDF, DOCX, PPTX, TXT, images), provide a YouTube video URL for
transcript extraction, supply a web page URL for content scraping, or
import files from Google Drive. Combine multiple sources on a single
exam.

AI question generation: choose from three modes — Source-first (AI
extracts questions from your content), Guided (you specify exact
counts, types, and structure), or Custom (manual creation). Five
question types are supported: Multiple Choice, True/False, Short
Answer, Long Answer, and Multi-Select.

Review and approve: AI-generated questions start as drafts. Review
each one — approve, reject, edit, or regenerate. Bulk approve when
you are confident. All questions must be approved before publishing.

Configure exam settings: set time limits (5 minutes to unlimited),
choose proctoring options (fullscreen enforcement, tab-switch
detection, copy/paste blocking, webcam monitoring with AI phone
detection), control attempt limits, enable negative marking, choose
grading styles for written answers, and configure verification schemas
for student identity.

Publish and share: publish your exam to generate a shareable link.
Control how long the link stays active with a link window. Share via
copy/paste, email (up to 50 recipients from the Links tab), Google
Classroom assignment, or Google Calendar event.

Monitor in real time: see LIVE badges on exams with active attempts.
The Monitoring tab shows per-attempt integrity events as they happen
via real-time connections. Track tab switches, fullscreen exits, phone
detections, and face checks.

Automatic grading: objective questions (MCQ, True/False, Multi-Select)
are graded instantly on submission. Written questions (Short Answer,
Long Answer) go through a six-step smart grading pipeline: exact
match, fuzzy match, keyword overlap, embedding similarity, AI
evaluation, and if needed, Pending Professor Review for teacher
manual scoring. Five grading styles let you tune the AI evaluation
emphasis.

Analyze results: view per-exam scores in the Results tab with
integrity flags, violation timelines, and export options (CSV, Excel,
Google Sheets). Use the Analytics workspace for cross-exam aggregate
trends, score distributions, completion rates, and integrity flag
rates over time.

Manage learners: the Students workspace shows a directory of all
exam takers with readiness labels (Strong learner, Needs coaching,
Needs check-in, Live now), a support queue, cohort health
visualization, and CSV export.

Run live quiz battles: Arena mode lets you host real-time competitions
where students join with a six-character room code and answer
questions for speed-based points with streak multipliers. Supports
team mode, spectator view, and game history export. Completely
separate from graded exams — different scoring, different history,
different analytics section.

Connect integrations: link Google Classroom to import rosters, assign
exams as coursework, and auto-push grades. Link Google Calendar to
schedule exams as events. Link Google Drive to import source files
during creation and export results to Google Sheets.

## Quick Start: Your First Exam in 5 Minutes

1. Open Create Exam from the Dashboard quick actions or press Ctrl+K
   and type "Create Exam."
2. Paste your study material or upload a PDF in the source content area.
3. Click Source-first (recommended) then click the green Generate button.
4. Wait for the notification (bell icon, top-right) confirming generation.
5. Open the exam from Exams in the sidebar. Click the Questions tab.
6. Click Bulk Approve to approve all questions at once (or review each).
7. Click the Settings tab to set duration and proctoring options.
8. Click Publish (emerald-green button). Copy the link from the success screen.
9. Share the link with your students. They open it, fill the identity form, and start.

That is the complete flow. Each step below explains the details.

## The Core Loop

The typical workflow follows this chain:

Create Exam (add source content, run AI generation)
then Review and approve questions (Draft to Approved)
then Configure settings (timing, proctoring, scoring, attempts,
verification)
then Publish (generates a shareable student link)
then Share the link with students
then Students take the exam (via the published link)
then Automatic grading runs on submission
then Teacher reviews Results, checks Monitoring data
then Students workspace shows learner readiness
then Analytics aggregates trends across exams

Each stage unlocks the next. An exam with no approved questions cannot
be published. An unpublished exam cannot be taken. Results only appear
after students submit and grading completes. Analytics only shows data
when graded results exist.

If any workspace or tab appears empty, it usually means an earlier
step in this chain has not been completed yet.

## Two Separate Experiences

Quizzer has two completely distinct interfaces that never overlap:

Creator workspace: what teachers and creators see after logging in.
Includes the full sidebar with Dashboard, Exams, Arena, Students,
Analytics, and Integrations. Each exam has its own workspace with
Questions, Monitoring, Results, Links, and Settings tabs. Accessed
via email/password, Google Sign-In, or Microsoft Sign-In. Uses
cookie-based JWT authentication.

Exam attempt interface: what students and takers see when taking an
exam. A focused, distraction-free exam interface with questions, a
timer, a question navigator, and a submit button. Accessed via the
published exam link. No Quizzer account required. Students identify
themselves through a verification form (name, enrollment number, etc.)
and receive an attempt token for their session. Uses token-based
authentication.

A teacher managing exams in the workspace and a student taking an
exam are on completely separate interfaces. They never share the same
screen or navigation.

## Current Status

Quizzer is in public beta. Every plan is free while the team gathers
feedback and iterates on features.

Four subscription tiers exist with different feature limits:

Explorer: the free/basic tier. Limited daily AI generations (1/day),
shorter link windows (24 hours), basic AI model selection. Google
integrations are locked.

Professional: higher limits. 3 AI generations/day, 1-week link
windows, more Arena quiz packs. Google integrations available.

Elite: premium tier. 10 AI generations/day, custom link window dates,
maximum Arena limits, advanced model selection.

Enterprise: contact-only tier for organizations.

During beta, these tier limits may be relaxed so all users can
explore features freely. Pricing has not been set yet — the limits
shown on the Plans page represent what each tier will include when
beta ends.

An Upgrade action is available in the sidebar for changing tiers.

## Privacy and Data

Exam data, questions, and results belong to the teacher who created
the exam. Students do not have access to each other's results.

Webcam proctoring runs entirely in the student's browser using a
client-side machine learning model (TensorFlow.js with COCO-SSD for
phone detection). Webcam frames are analyzed locally and not uploaded
to any server. Only violation event metadata (type, timestamp,
confidence) is sent to the server.

## Common Questions

What is Quizzer?
Quizzer is an AI assessment platform. You upload content, AI generates
exam questions, you review and publish, students take the exam via a
shared link, and results are graded automatically.

Is Quizzer free?
Quizzer is currently in public beta and every plan is free. Pricing
starts when beta ends.

Do students need an account?
No. Students access exams via a shared link and identify themselves
through a verification form. They do not need a Quizzer account to
take an exam.

Can I use Quizzer for self-study?
Yes. You can create exams from your own study material, take them
yourself, and track your performance over time.

What file types can I upload?
PDF, DOCX, PPTX, TXT, and images (PNG, JPG). You can also paste text
directly, provide a YouTube video URL, or a web page URL.

Is webcam data uploaded to a server?
No. Webcam analysis runs entirely in the student's browser. Only
violation event metadata is sent to the server, not video frames.

What is the difference between Arena and regular exams?
Arena is a live, synchronous quiz battle (like Kahoot) with speed-based
scoring. Regular exams are asynchronous, individually timed assessments
with detailed proctoring and grading. They have separate scoring
systems and separate analytics sections.

How many exams can I create?
There is no limit on the number of exams. The daily generation quota
limits how many AI generations you can run per day (varies by tier).

Can I use Quizzer with Google Classroom?
Yes. Connect Google Classroom from Integrations to import courses,
sync rosters, assign exams as coursework, and auto-push grades.

## Related Features

See also: Exam Lifecycle, Creating Exams, Terminology, Roles,
Dashboard, Onboarding
