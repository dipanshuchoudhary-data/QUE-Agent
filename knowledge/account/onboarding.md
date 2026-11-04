---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Onboarding

## Overview

When you first sign up for Quizzer, you go through a four-step
onboarding flow that personalizes your workspace. The onboarding
collects your name, lets you choose a persona, fills in relevant
details, and then creates your workspace.

Users may call this: signup, getting started, first-time setup,
registration, creating an account.

## Step-by-Step UI Guide: Signing Up and Onboarding

Step 1 — Go to the signup page:
Open Quizzer in your browser. On the login page, click the Sign Up
link (usually below the login form, or as a tab at the top).

Step 2 — Create your account:
Option A — Email: type your email address and choose a password. Click
the Sign Up button (emerald-green). Quizzer sends a verification email
to your inbox. Open the email and click the verification link.

Option B — Google: click the Continue with Google button (Google icon).
Select your Google account. No email verification needed.

Option C — Microsoft: click the Continue with Microsoft button. Sign
in with your Microsoft account.

Step 3 — Welcome screen (onboarding screen 1 of 4):
After signing in, the onboarding flow starts. You see a split-screen
layout with a large illustration on the left and a setup card on the
right. Type your display name in the name field. Click Continue
(emerald-green button).

Step 4 — Choose your persona (onboarding screen 2 of 4):
You see ten persona cards displayed as a grid. Each card has an icon,
a title (like "K-12 Teacher", "University Professor", "Student"), and
a short description. Click the card that best describes you.

Important: if you click Student, your account will have limited access
(no exam creation). All other choices give you full teacher access.

Step 5 — Fill in details (onboarding screen 3 of 4):
Based on your persona, you see 2-4 fields asking for details. For
example, a teacher might see Institution, Subject Area, and Courses
Taught. These fields are optional. Fill in what you want and click
Continue.

Step 6 — Workspace creation (onboarding screen 4 of 4):
A celebration animation plays with cycling text while your workspace
is set up. After a few seconds, you are automatically redirected to
your Dashboard.

Email+password signups must verify their email: Quizzer sends a
verification email and you click the link. Google and Microsoft sign-ins
do not require separate verification. If you close the browser during
onboarding, you restart at screen 1 on your next visit, but previously
saved answers are restored from your profile.

## Sign-Up Options

Email and password: create an account with your email address and a
password. Quizzer sends a verification email (via Supabase Auth). You
must verify your email before you can fully use the account.

Google Sign-In: sign in with your Google account. No email verification
needed.

Microsoft Sign-In: sign in with your Microsoft account via Azure OAuth.

## The Four Onboarding Screens (inside Steps 3-6 above)

Screen 1 — Welcome: enter your display name. This is the name shown
across your workspace.

Screen 2 — Persona: choose from ten persona cards that describe how you
will use Quizzer. Your persona personalizes the onboarding questions
and workspace greeting, but does NOT affect permissions. Only the
Student persona sets the Student role. All other personas set the
Teacher role.

Screen 3 — Details: answer dynamic questions based on your persona. For
example, a teacher might see institution, subject area, and courses
taught. A corporate trainer might see company name and team size. These
fields are optional and help personalize the experience.

Screen 4 — Creating workspace: a brief celebration animation while your
workspace is set up, then you are redirected to your dashboard.

If you refresh the browser during onboarding, you restart at screen 1
but any previously saved answers are restored from your profile.

## The Ten Personas

Student: for self-study and practice. Sets the Student role (limited
interface).

K-12 Teacher: for elementary and secondary school teachers.

University Professor: for higher education instructors.

Corporate Trainer: for workplace training and skills assessment.

Freelance Tutor: for independent tutors and private instructors.

Content Creator: for people creating educational content.

HR Professional: for hiring assessments and compliance testing.

Developer / Engineer: for technical assessments and coding evaluations.

Business Team Lead: for team knowledge checks and onboarding quizzes.

Other: catch-all for any other use case.

All personas except Student get the Teacher role with full workspace
access. The persona only affects the copy, greeting, and detail
questions — not what features you can use.

## Role Assignment

Your role is set once during onboarding and cannot be changed by you
afterward. If you chose the wrong persona and got the wrong role (for
example, chose Student but wanted Teacher access), you would need to
contact support.

The persona label is stored but cannot be changed through the UI after
onboarding; it only affects copy and greeting, not permissions. If you
chose Student but want to create exams, you need support to change your
role, or you can create a new account with a different persona.

## After Onboarding

After completing onboarding, you are taken to your dashboard:

Teacher role: full workspace with Dashboard, Exams, Arena, Students,
Analytics, and Integrations.

Student role: limited workspace with Dashboard and Help only.

## Related Features

See also: Roles, Account Settings, Dashboard
