---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Google Calendar Integration

## Overview

Quizzer integrates with Google Calendar to let teachers schedule exams
as calendar events. When you schedule an exam, a calendar event is
created in your Google Calendar with the exam details and link.

Users may call this: calendar scheduling, schedule exam, add to
calendar, exam calendar.

## Step-by-Step UI Guide: Scheduling an Exam on Google Calendar

Step 1 — Connect Calendar:
In the left sidebar, click Integrations. Find the Google Calendar card.
Click Connect. Authorize Quizzer in the Google popup. The card shows
"Connected" (green status).

Step 2 — Publish your exam first:
Calendar scheduling requires a published exam. Go to Exams, open your
exam, and make sure it is published (green Published badge on the
card).

Step 3 — Schedule the exam:
You can schedule from two places:

Option A — From the post-publish screen: right after publishing, a
success screen shows schedule options. Click Schedule on Calendar.

Option B — From the Integrations page: go to Integrations, find the
Calendar section, and click Schedule Exam. Select the published exam
from the dropdown.

Step 4 — Set the event details:
Choose the date and time for the exam. The event title is auto-filled
from the exam name. Click Schedule. A calendar event is created on your
primary Google Calendar with the exam link.

## How to Connect

Go to Integrations in the sidebar, find Google Calendar, and click
Connect. This starts a Google OAuth flow where you grant Quizzer
permission to access your Calendar (read and create events).

Google Calendar uses separate credentials from Google Sign-In and may
use separate credentials from Google Classroom (though they can share
the same set depending on configuration).

## Available Features

Schedule exam: create a Google Calendar event for a published exam.
The event includes the exam title, link, and timing information. The
event is created on your primary Google Calendar.

Manage events: view upcoming scheduled exam events, update event
details, or cancel scheduled events.

Calendar insights: view scheduling overview from the Calendar
integration dashboard section.

## How Scheduling Works

Scheduling is teacher-initiated, not automatic. Publishing an exam
does NOT automatically create a calendar event. The teacher must
explicitly use the Calendar section or the post-publish success screen
to schedule it.

When you schedule an exam:
1. A calendar event is created on your primary Google Calendar.
2. The event is tagged as a Quizzer exam event.
3. A record is saved in Quizzer to track the event.

You can update or cancel the event later. Changes in Quizzer are
reflected in your Google Calendar.

## Plan Availability

Explorer tier: Calendar integration is locked. Available on
Professional and Elite tiers. During the public beta, this restriction
may be relaxed.

## Limitations

Calendar scheduling is one-way: Quizzer creates and manages events in
your Google Calendar. It does not read your existing calendar events
or block conflicting time slots.

There is no push notification from Google Calendar back to Quizzer.
Exam reminders are generated lazily when you check your notification
inbox, based on upcoming scheduled events.

Scheduling does not affect the exam's link window or availability.
The calendar event is informational — it does not automatically
open or close the exam link.

## Common Questions

How do I schedule an exam on Google Calendar?
Connect Google Calendar from Integrations first. Then, after publishing
an exam, use the Calendar section to schedule it. A calendar event will
be created with the exam link.

Does publishing automatically create a calendar event?
No. Scheduling is a separate action. You must explicitly schedule it
after publishing.

Does the calendar event control when students can access the exam?
No. The calendar event is informational. The link window
(available_until) controls when students can start. These are
independent.

Can I cancel a scheduled event?
Yes. From the Calendar section in Integrations, you can cancel or
update scheduled exam events.

Can students see the calendar event?
If you share your Google Calendar or send the calendar invite, students
can see the event. Quizzer creates the event on YOUR primary calendar —
it does not automatically invite students.

## Related Features

See also: Publishing and Sharing (link window), Integrations overview,
Notifications (exam reminders)
