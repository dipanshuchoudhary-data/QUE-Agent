---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Navigation and UI Map

## Overview

Quizzer's interface is organized around a sidebar for main workspaces,
tabs within each exam for detailed management, and utility overlays
(command palette, search, notifications). Understanding where things
live prevents confusion between features that share similar names.

Users may call this: where is, how do I find, where do I go, sidebar,
menu, navigation, UI.

## Step-by-Step UI Guide: Finding Your Way Around

Step 1 — The sidebar:
On the left side of the screen, you will see the sidebar. It has a
dark background with the Quizzer logo at the top. Items are grouped:

ASSISTANT: Ask QUE.
WORKSPACE: Dashboard, Exams, Arena, Students, Analytics, Integrations.
ACCOUNT: Upgrade, Settings, Send feedback, Help & Support.

Step 2 — Create Exam:
Use Create Exam from quick actions / command palette (Ctrl+K or Cmd+K),
or the create entry points on Dashboard / Exams. It starts a new exam.

Step 3 — Account links vs avatar:
ACCOUNT items (Upgrade, Settings, Send feedback, Help & Support) are
visible in the sidebar — click them directly. The avatar at the bottom
only opens a small menu for your identity and **Log out**. Do not tell
users to open the avatar to find Feedback or Settings.

Step 4 — Opening an exam workspace:
Click Exams in the sidebar. You see your exam library as cards. Click
on any exam card to open its workspace. At the top of the workspace,
a tab row appears: Questions, Monitoring, Results, Links, Settings.
Click any tab to switch between views.

Step 5 — The notification bell:
In the top navigation bar (at the very top of the screen), look for
the bell icon on the right side. A number badge shows unread count.
Click it to open the notification inbox with recent alerts.

Step 6 — The command palette:
Press Ctrl+K (Windows) or Cmd+K (Mac) to open the command palette — a
search overlay that lets you quickly jump to any workspace, search
exams, or trigger actions. Type what you are looking for and select
from the results.

Step 7 — Collapsing the sidebar:
If you want more screen space, click the collapse button on the
sidebar header. The sidebar shrinks to a narrow icon-only rail. Click
again to expand it back.

## Teacher Sidebar

The sidebar (desktop left rail) or bottom navigation (mobile) shows
these items for teacher accounts, grouped:

ASSISTANT:
- Ask QUE: opens the QUE chat assistant

WORKSPACE:
- Dashboard: overview of exam activity, live exams panel, summary
  metrics, quick actions, and activation checklist (for new accounts).
- Exams: list of all your exams with status indicators (Draft, Published,
  Archived), LIVE badges, link window status, and management actions.
  This is the entry point to individual exam workspaces.
- Arena: live quiz battle hub. Quiz pack library, quick-create flow,
  scheduled battles, and game history.
- Students: learner directory with readiness labels, support queue,
  cohort health, and scope controls. Filters by exams or Classroom
  courses.
- Analytics: cross-exam aggregate trends. Charts for score distribution,
  completion rates, integrity flags, and an Arena analytics section.
- Integrations: connect and manage Google Classroom, Google Calendar,
  and Google Drive.

ACCOUNT:
- Upgrade: opens the plans / subscription page
- Settings: full account settings (Profile, Preferences, Workspace,
  Security, Notifications) at /account/settings
- Send feedback: opens /feedback to report bugs, UI issues, or ideas
- Help & Support: guides, tours, Explore Quizzer at /help

Avatar footer (bottom of sidebar):
Shows your name and email. Clicking the avatar opens a small menu for
identity and **Log out** only. Settings and Send feedback are NOT in
this menu anymore.

## Student Sidebar

Student-role accounts see a limited sidebar:

Dashboard: student version with welcome message and guidance cards.
Help: feature tours.

No Exams, Arena, Students, Analytics, or Integrations items. No Create
Exam action. Students access exams only through shared links.

## Exam Workspace

Opening any exam from the Exams list reveals the exam workspace — a
multi-tabbed interface for managing that specific exam. The tabs are:

Questions: view, edit, approve, reject, regenerate, duplicate, delete,
and bulk-manage questions. Shows question status (Draft, Approved,
Rejected), sections, marks, and correct answers. Includes bulk approve
and bulk marks update actions.

Monitoring: in-progress and recent attempts with integrity event data.
Shows per-attempt violation timeline, webcam events, tab switches,
fullscreen exits, phone detections. Real-time updates via WebSocket
for active attempts. LIVE badge logic visible here.

Results: graded outcomes for all submitted attempts. Per-student scores,
violation counts, integrity flags, and result status (Graded or Pending
Professor Review). Expand rows for integrity review panels with
violation timelines. Export to CSV, Excel, or Google Sheets.

Links: the published exam URL, link window status (active, expired,
renew), sharing options (copy link, share by email, assign via
Classroom, schedule via Calendar). QR code generation available.

Settings: all configurable exam settings organized into sections —
Timing (duration), Question Order (shuffle), Proctoring (fullscreen,
tab switch, copy/paste, webcam, phone detection, face monitoring,
violation limit, auto-submit), Scoring (default marks, negative
marking, violation penalty, grading style), Attempts (max attempts,
allow resume, prevent duplicate), Access Control (access codes), and
Verification Schema.

These tabs are INSIDE each exam, not in the sidebar. There is no
top-level Monitoring, Results, Settings, or Links item in the sidebar.

## Critical Navigation Rule

Top-level /monitoring and /results URLs redirect to the Exams
workspace. There is no standalone Monitoring or Results page. Always
navigate through the specific exam:

Exams (sidebar) → open the exam → select the tab (Monitoring, Results,
Links, Settings, Questions).

This is the single most common navigation confusion. If someone asks
"where is Monitoring" or "where are my Results," direct them to open
the specific exam first.

## Where to Find Things — Quick Reference

To list, search, or manage exams:
Exams in the sidebar.

To create a new exam:
Create Exam from Dashboard quick actions or command palette (Ctrl+K).

To approve or edit questions:
Exams → open exam → Questions tab.

To watch live attempts or check integrity events:
Exams → open exam → Monitoring tab.

To see scores for one exam:
Exams → open exam → Results tab.

To export results:
Exams → open exam → Results tab → export action.

To share the exam URL or check link window status:
Exams → open exam → Links tab.

To change exam duration, proctoring, scoring, or attempts:
Exams → open exam → Settings tab.

To configure the verification form for one exam:
Exams → open exam → Settings tab → Verification Schema section.

To set default verification fields for all future exams:
Account Settings → Workspace tab.

To see who took your exams (people view):
Students in the sidebar. Use the scope bar to filter.

To see cross-exam performance charts:
Analytics in the sidebar. Adjust date range and quiz filters.

To host a live quiz battle:
Arena in the sidebar.

To connect Google Classroom, Calendar, or Drive:
Integrations in the sidebar.

To change theme, density, or motion settings:
Account Settings → Preferences tab.

To change password or sign out everywhere:
Account Settings → Security tab.

To configure notification preferences:
Account Settings → Notifications tab.

To learn about features with video walkthroughs:
Help & Support (sidebar ACCOUNT section) → Explore Quizzer.

## Command Palette

Teachers can open the command palette with a keyboard shortcut (Ctrl+K
or Cmd+K) to quickly navigate to any workspace, search exams, or
trigger actions like Create Exam.

The command palette reads from the same navigation configuration as the
sidebar. It provides fuzzy search across workspace names, exam titles,
and action labels.

Users may call this: quick search, keyboard shortcut, command bar,
Ctrl+K, search bar.

## Global Search

The search overlay lets teachers search across exams and navigation
items from any page. It is accessible from the top navigation bar or
the command palette.

## Notification Bell

The notification bell icon in the top navigation bar opens the
notification inbox. Shows an unread count badge when there are new
notifications. Click to see recent notifications with action links.

## Feature Tours (Explore Quizzer)

Under Help & Support in the sidebar ACCOUNT section, the Explore
Quizzer section provides video walkthroughs for major features:

- Arena: how to host live quiz battles
- Student Exam: what taking an exam feels like and how integrity works
- Monitoring & Results: watching the exam live, then reviewing scores
- Analytics: exam-wide attempts, scores, trends, and integrity totals
- Students: the roster of who is active and who needs support
- Security enforcement: violation limit, fullscreen, tab switch, and
  paste controls per exam
- Publish readiness: review and approval status gate publish eligibility

These tours help new users understand the product without trial and
error.

## Mobile Navigation

On smaller screens, the sidebar collapses into a bottom navigation
bar. The same workspaces are accessible, but the layout is optimized
for touch interaction. Some features may have a simplified layout on
mobile.

## URL Patterns

Creator workspace URLs follow patterns like /dashboard, /exams,
/arena, /students, /analytics, /integrations, /settings.

Individual exam workspace URLs include the exam ID in the path.

Exam attempt URLs (what students see) use a completely different route
pattern with the exam's public ID. These are NOT part of the creator
workspace URL structure.

## Sidebar Collapse

The sidebar can be collapsed to save horizontal space. Toggle via the
sidebar header or the Sidebar collapsed preference in Account Settings.
When collapsed, only icons are shown.

## Common Navigation Mistakes

Monitoring is not in the sidebar: open Exams, open the specific exam,
then the Monitoring tab.

Results for one exam: same path — Exams, open the exam, Results tab.
The portfolio view is Analytics (in the sidebar).

Create Exam is a quick action, not inside Monitoring or Results.

Verification Schema is under the exam's Settings tab, not Questions.

Top-level /monitoring and /results URLs redirect to Exams. Always open
the specific exam first.

Do not send exam takers to the creator workspace URL. They use the
published exam link, which is a completely separate interface.

Account Settings is under ACCOUNT → **Settings** in the left sidebar
(`/account/settings`). It is not inside the avatar dropdown.

Where do I report a bug or send feedback?
Click **Send feedback** in the left sidebar ACCOUNT section. Choose
**Bug report** (or Found a bug), describe the issue, and submit. Do
not open the avatar menu for Feedback — that menu is only for Log out.

## Common Questions

Where is Monitoring?
Not in the sidebar. Open Exams, open the specific exam, then select
the Monitoring tab.

Where are my Results?
Not in the sidebar. Open Exams, open the specific exam, then select
the Results tab. For cross-exam trends, use Analytics in the sidebar.

How do I find a specific exam?
Use the Exams workspace in the sidebar. You can search, filter by
status (Draft, Published, Archived), or browse the list.

Where do I change exam settings?
Open the exam from Exams, then select the Settings tab.

Where is the Create Exam button?
In the sidebar as a quick action button, or on the Dashboard quick
actions panel.

How do I open the command palette?
Press Ctrl+K (Windows) or Cmd+K (Mac) from any page.

Where are my notifications?
Click the bell icon in the top navigation bar.

Why does /monitoring redirect to Exams?
There is no standalone Monitoring page. Monitoring lives inside each
exam's workspace. Open the specific exam first, then select the
Monitoring tab.

## Related Features

See also: Roles (teacher vs student sidebar), Exam Settings,
Terminology, Dashboard, Account Settings
