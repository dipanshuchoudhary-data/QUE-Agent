---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Notifications

## Overview

Quizzer sends in-app notifications to keep teachers informed about
important events like exam generation results, student activity, and
export readiness. Notifications appear in the notification inbox
accessible from the top navigation bar.

Users may call this: alerts, messages, updates, notification bell,
inbox.

## How to Access

Click the notification bell icon in the top navigation bar (top-right
area of the screen). This opens the notification inbox panel showing
recent notifications and an unread count badge.

## Step-by-Step UI Guide: Using Notifications

Step 1 — Check for new notifications:
Look at the top-right corner of the screen. The bell icon shows a
number badge if you have unread notifications (for example, a red
circle with "3").

Step 2 — Open the inbox:
Click the bell icon. A dropdown panel opens showing your recent
notifications in chronological order. Each notification shows a title,
a brief description, and a timestamp.

Step 3 — Click a notification:
Click on any notification to see its details and navigate to the
relevant page. For example, clicking "Generation complete" takes you
to the exam. Clicking "Export ready" shows the download link.

Step 4 — Mark as read:
Click a notification to mark it as read (the unread indicator
disappears). You can also use the Mark All Read action at the top of
the inbox to clear all unread badges at once.

Step 5 — Configure preferences:
To change which notifications you receive, go to Account Settings
(sidebar ACCOUNT → **Settings**). Click
the Notifications tab. Toggle switches on or off for each notification
category.

## Notification Types

Generation complete: sent when AI exam generation finishes successfully.
Includes a link to the exam.

Generation failed: sent when AI exam generation fails. Includes error
context.

Exam published: sent when you publish an exam. Confirms the publish
action.

Attempt started (milestones): sent when student attempt counts reach
milestones (1, 5, 10, 25, 50, 100 attempts on a specific exam). Helps
teachers track engagement without constant monitoring.

Integrity alert: sent when a student's violation count reaches or
exceeds the exam's violation limit during an attempt. Alerts teachers
to potential issues requiring attention.

Export ready: sent when a result export (CSV, Excel, Sheets) is ready
for download. Includes a download link.

Exam reminder: generated when you check your inbox, based on upcoming
calendar-scheduled exams. A lazy reminder, not a push notification.

Arena results ready: sent when an Arena game ends with final results.

Arena battle reminder: sent approximately 15 minutes before a scheduled
Arena battle.

System announcement: broadcast to all users by staff. Used for product
updates, maintenance notices, or important announcements.

## Notification Categories

Update: informational events (generation complete, exam published,
attempt milestones, export ready, Arena results).

Alert: events requiring attention (generation failed, integrity alert).

Announcement: system-wide messages from the Quizzer team.

## In-App Only

Most notifications are in-app only. Quizzer does NOT send email
notifications for:
- Exam generation (complete or failed)
- Student attempts
- Integrity alerts
- Export readiness
- Arena events
- Exam reminders

Email is only used for three things:
1. Signup email verification (handled by Supabase Auth)
2. Password reset for Google-linked accounts with local passwords
3. Exam share invitations (when you share by email from the Links tab)

The notification preferences page in Account Settings mentions email
alerts, but the backend only writes in-app notifications. No email
is dispatched for the event types listed above.

## Managing Notifications

Mark as read: click on a notification or use the mark-all-read action.

Dismiss: remove individual notifications.

Clear all: remove all notifications at once.

Unread count: shown as a badge on the notification bell icon.

## Notification Preferences

In Account Settings, Notifications tab, you can toggle:

Attempt notifications: milestone attempt counts.
Integrity alerts: violation limit exceeded.
Generation complete: AI generation finished.
Export complete: export ready for download.

Always visible (cannot be turned off): exam published, system
announcements.

These toggles filter the in-app inbox, not email delivery (since email
is not sent for these events).

## Deduplication

Notifications use deduplication to avoid flooding the inbox. For
example, multiple integrity alerts for the same student on the same
exam are deduplicated so you see one notification rather than many.

## Action Links

Most notifications include an action link that takes you directly to
the relevant page. For example, a generation-complete notification
links to the exam, and an integrity alert links to the exam's
Monitoring tab.

## Common Questions

Where do I see my notifications?
Click the bell icon in the top navigation bar.

Does Quizzer send email notifications?
Not for most events. Notifications for generation, attempts, integrity,
exports, and Arena are in-app only. Email is only used for signup
verification, password reset, and exam share invitations.

How do I turn off certain notifications?
Go to Account Settings, Notifications tab, and toggle the categories
you want to disable.

What triggers an integrity alert notification?
When a student's violation count reaches or exceeds the violation limit
set in the exam's Settings during an active attempt.

When do I get attempt notifications?
At milestone counts: 1, 5, 10, 25, 50, and 100 attempts on a specific
exam. Not on every single attempt.

## Related Features

See also: Account Settings, Monitoring and LIVE, Exam Settings
(violation limit), Results and Exports
