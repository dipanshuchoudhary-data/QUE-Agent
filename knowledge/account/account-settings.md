---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Account Settings

## Overview

Account Settings lets you manage your profile information, appearance
preferences, workspace defaults, and security options. It is organized
into tabbed sections: Profile, Preferences, Workspace, Security, and
Notifications.

Users may call this: settings, my account, profile, preferences,
configuration, account management.

## How to Access

In the left sidebar, open the **ACCOUNT** section and click **Settings**
(goes to `/account/settings`). You can also use the command palette
(Ctrl+K / Cmd+K) and search for Settings.

Do **not** look for Settings inside the avatar menu. The avatar at the
bottom of the sidebar is for identity and **Log out** only.

## Step-by-Step UI Guide: Changing Common Settings

To change your theme to dark mode:
Click **Settings** in the sidebar ACCOUNT section. Click the Preferences
tab. Find the Theme option. Click the dropdown and select Dark. The
change applies immediately.

To change your password:
Click **Settings** in the sidebar ACCOUNT section. Click the Security
tab. Find Change Password. Enter your current password, then your new
password twice. Click Save.

To set default exam settings:
Click **Settings** in the sidebar ACCOUNT section. Click the Workspace
tab. Here you
can change Default Marks (the default point value for new questions),
Default Quiz Duration (default timer for new exams), and Default
Verification Schema (the identity form for all new exams). Changes
apply to exams you create after saving.

To sign out of all devices:
Click **Settings** in the sidebar ACCOUNT section. Click the Security tab. Find Sign
Out Everywhere Else. Click it. All other sessions are revoked.

To configure notification preferences:
Click **Settings** in the sidebar ACCOUNT section. Click the Notifications tab. Toggle
switches on or off for: Attempt notifications, Integrity alerts,
Generation complete, Export complete.

## Profile Tab

Display name: the name shown across your workspace and to others.

Email: your account email. Cannot be changed directly from this page —
use the email change flow if available.

Phone number: optional contact number.

Institution: your school, university, company, or organization name.

Country: your country.

Timezone: your timezone, used for date/time display across the app.

Subject area: the subject you teach or focus on.

Courses taught: specific courses you offer.

Teaching experience: your level of experience.

Professional title: your job title or role description.

Avatar: upload a profile picture. Supported image formats. The avatar
appears in the sidebar and account areas.

## Preferences Tab

Theme: choose Light, Dark, or System (follows your device setting).
Default: System.

Density: Comfortable (more spacing) or Compact (denser layout).
Default: Comfortable.

Motion: System (follows device accessibility setting), Reduce (minimal
animations), or Allow (full animations). Default: System.

Time format: 12-hour or 24-hour clock. Default: 12-hour.

Live data refresh: control whether live data (like LIVE badges and
monitoring) refreshes automatically. Default: on.

Sidebar collapsed: whether the sidebar starts collapsed. Default: off.

Students scope default: the default scope mode for the Students
workspace — All in cluster or Pick exams. Default: varies.

Highlight integrity risks: whether to visually emphasize integrity-
flagged items. Default: on.

Preferences are saved locally in your browser (localStorage). They do
not sync across devices.

## Workspace Tab

Default marks: the default marks value for new questions when creating
exams. Default: 1.

Default quiz duration: the default duration in minutes for new exams.
Default: 60.

Default warning threshold: minutes before end when a timer warning
appears. Default: varies.

Default verification schema: set the default identity form fields
(name, enrollment number, etc.) that apply to all new exams. Each
exam can override this.

Strict publish checks: enable stricter validation before publishing.
Local preference only, not enforced on the server.

AI safety mode: additional safeguards for AI-generated content. Local
preference.

Autosave review: whether the review screen auto-saves changes. Local
preference.

## Security Tab

Change password: change your current password. Requires entering your
current password first.

Sign out everywhere else: revoke all other sessions, keeping only your
current one active. Useful if you suspect unauthorized access.

Two-factor authentication: shown as a setting but not active in the
backend yet. The toggle is read-only/disabled.

Account deactivation: links to support contact for account deletion
requests. Not a self-service action.

## Notifications Tab

Configure which in-app notifications you receive:

Attempt notifications: get notified when students reach milestone
attempt counts (1, 5, 10, 25, 50, 100).

Integrity alerts: get notified when a student's violation count exceeds
the exam's violation limit.

Generation complete: get notified when AI exam generation finishes
(success or failure).

Export complete: get notified when a result export is ready for
download.

Note: these are in-app notifications only. Quizzer does not send email
notifications for these events. Email is only used for signup
verification, password reset, and exam share invitations.

## Subscription Tier

Your subscription tier (Explorer, Professional, Elite) determines
access to certain features like AI model selection, link window
duration, daily generation quota, and Arena pack limits. The tier is
shown in your account area.

During the public beta, every plan is free and some limits may be
relaxed.

Tier cannot be changed by the user directly — it is set by the system
or admin. An Upgrade action is available in the sidebar.

## Common Questions

How do I change my password?
Go to Account Settings, Security tab, and use the Change password
option. You need your current password.

How do I change the theme to dark mode?
Go to Account Settings, Preferences tab, and set Theme to Dark.

How do I set default settings for all my exams?
Go to Account Settings, Workspace tab. Set default marks, default
duration, and default verification schema there.

Can I sign out of all devices?
Yes. Go to Account Settings, Security tab, and use Sign out
everywhere else.

Are my preferences synced across devices?
No. Preferences (theme, density, motion, etc.) are saved in your
browser's local storage and do not sync across devices or browsers.

How do I delete my account?
Account deletion is handled through support contact. It is not a
self-service feature in the Settings.

How do I change my email?
Email changes go through a separate authentication flow, not the
Profile tab directly.

Can I enable two-factor authentication?
The 2FA toggle is visible but not active yet. It is a planned feature.

## Related Features

See also: Onboarding, Roles, Exam Settings (per-exam overrides),
Verification Schema (account default), Notifications
