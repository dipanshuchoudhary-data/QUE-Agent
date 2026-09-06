---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# User Roles and Permissions

## Overview

Quizzer has two main account roles (Teacher and Student) and a separate
exam-taking experience that does not require any account at all. Your
role determines what you can see and do in the interface.

Users may call this: permissions, access level, account type, what can
I see, why is my sidebar limited.

## Teacher Role

Anyone who signs up and selects a non-student persona during onboarding
gets the Teacher role. This includes actual teachers, trainers,
freelancers, HR professionals, developers, content creators, business
team leads, self-study users, and anyone else who wants to create
assessments.

What teachers can access:

Sidebar workspaces:
- Dashboard: overview of exam activity, live exams, metrics, quick
  actions, activation checklist
- Exams: full exam library (draft, published, archived), create,
  manage, publish, share, delete
- Arena: host live quiz battles, create packs, view game history
- Students: learner directory, readiness labels, support queue, cohort
  health, CSV export
- Analytics: cross-exam performance trends, charts, Arena analytics
- Integrations: connect/manage Google Classroom, Calendar, Drive

Exam workspace tabs (inside each exam):
- Questions: view, edit, approve, reject, regenerate, bulk actions
- Monitoring: live attempt tracking, integrity events, violation data
- Results: graded scores, integrity flags, violation timelines, export
- Links: published URL, link window status, sharing options
- Settings: timing, proctoring, scoring, attempts, verification schema

Quick actions:
- Create Exam: the primary action to start a new exam
- Upgrade: change subscription tier

Account:
- Settings: profile, preferences, workspace defaults, security,
  notifications (sidebar ACCOUNT → Settings)
- Send feedback: report bugs or ideas (sidebar ACCOUNT → Send feedback)
- Help & Support: feature tours, Explore Quizzer
- Avatar menu: Log out only

Teachers see the full sidebar, all workspace features, and all exam
workspace tabs. There is no feature gating between teacher personas —
a Corporate Trainer and a University Professor have identical access.

## Student Role

Users who select the Student persona during onboarding get the Student
role. This role has a deliberately limited interface designed for
learners.

What student accounts can access:
- Student Dashboard: welcome page with guidance cards explaining how
  to use exam links, stay exam-ready, and understand the assessment
  flow
- Help: feature tours
- Account Settings: profile and preferences
- Exam attempts: via shared exam links (the same focused exam
  interface that non-account takers see)

What student accounts CANNOT access:
- Exams workspace (no exam creation or management)
- Arena hosting (cannot create rooms or quiz packs)
- Students workspace (teacher tool)
- Analytics (teacher tool)
- Integrations (teacher tool)
- The Create Exam action (not shown)
- Any exam workspace tabs (Questions, Monitoring, Results, Links,
  Settings)

The Student Dashboard does NOT list available exams, show scores, or
provide exam links. It provides informational cards only. Students
enter exams exclusively through links shared by their teacher.

Users may call this: student account, learner account, restricted
account, limited access.

## Exam Taker (No Account Needed)

Anyone with a published exam link can take an exam without creating
a Quizzer account. This is the most common way students interact with
Quizzer.

Before starting, takers fill out a verification form (name, enrollment
number, etc.) configured by the teacher. They receive an attempt token
that identifies their session.

What takers see:
- Exam start page: exam title, duration, number of questions, rules
  summary, proctoring notices
- Verification form: identity fields configured by the teacher, plus
  access code entry if required
- Exam interface: questions, timer, question navigator, auto-save,
  submit button
- Proctoring overlays: fullscreen enforcement, violation warnings,
  webcam status (if enabled)
- Submit confirmation: confirmation that the exam was submitted

What takers CANNOT see:
- Any part of the creator workspace
- Other students' answers or scores
- The exam's Settings, Questions tab, or any management interface
- The teacher's identity or account information

Takers interact with a completely separate, focused interface. The exam
URL is a different application route from the creator workspace.

Users may call this: test taker, exam participant, student (in the
context of taking an exam).

## Onboarding Personas

During signup, users choose from ten personas that personalize the
onboarding experience:

1. Student — sets the Student role (limited interface)
2. K-12 Teacher — sets the Teacher role
3. University Professor — sets the Teacher role
4. Corporate Trainer — sets the Teacher role
5. Freelance Tutor — sets the Teacher role
6. Content Creator — sets the Teacher role
7. HR Professional — sets the Teacher role
8. Developer / Engineer — sets the Teacher role
9. Business Team Lead — sets the Teacher role
10. Other — sets the Teacher role

Personas affect the welcome copy, the detail questions shown during
onboarding (institution, courses taught, company name, etc.), and the
initial workspace greeting. They do NOT affect permissions. Only the
Student persona sets the Student role with its limited interface.

A Corporate Trainer and a University Professor have the exact same
feature access. The persona is cosmetic except for role assignment.

## Role Assignment

Role is set once during onboarding and cannot be changed afterward by
the user through any UI action. The role is stored on the user's
profile record.

If someone chose the wrong persona and got the wrong role (for example,
chose Student but wants to create exams), they need to either:
- Contact support to change their role
- Create a new account with a different persona

There is no role-switching feature or multi-role support.

## Teachers Taking Their Own Exams

A teacher can take their own published exams by opening the published
exam link in a browser. They experience the same exam-taking interface
as any other taker. Their teacher account and exam-taker session are
completely separate contexts.

## Admin / Staff

There is a staff/admin level that can broadcast system announcements
to all users. This is not accessible to regular users and is managed
through backend tools.

## How to Check Your Role

Step 1: look at your sidebar. If you see Dashboard, Exams, Arena,
Students, Analytics, and Integrations in the left sidebar, you have
the Teacher role (full access).

Step 2: if you only see Dashboard and Help in the sidebar (no Exams,
no Arena, no Students), you have the Student role (limited access).

Step 3: if you are not logged in and just opened an exam link, you are
an Exam Taker (no account needed). You see the exam start page with
the verification form.

## Permission Summary Table

Feature                  | Teacher | Student | Taker (no account)
Dashboard                | Full    | Limited | No access
Exams workspace          | Yes     | No      | No access
Create Exam              | Yes     | No      | No access
Exam workspace tabs      | Yes     | No      | No access
Arena hosting            | Yes     | No      | No access
Students workspace       | Yes     | No      | No access
Analytics                | Yes     | No      | No access
Integrations             | Yes     | No      | No access
Account Settings         | Yes     | Yes     | No access
Help                     | Yes     | Yes     | No access
Take exams via link      | Yes     | Yes     | Yes
Verification form        | Yes     | Yes     | Yes

## Common Questions

Can a student create exams?
No. Student accounts only see the Student Dashboard and Help. To
create exams, sign up with any non-student persona during onboarding.

Do students need an account to take an exam?
No. Anyone with a published exam link can take the exam by filling
the verification form. No account required.

Why can I only see Dashboard and Help?
Your account has the Student role, set during onboarding. Student
accounts have a limited interface. To access exam creation and
management features, you need a Teacher role account.

Can I change my role?
Not through the UI. Contact support for role changes, or create a new
account with a different persona.

Can I have both roles?
No. Each account has one role. However, a teacher can take their own
exams using the published link just like any other taker.

What is the difference between a student account and a student taking
an exam?
A student account is a logged-in Quizzer user with the Student role
and limited sidebar navigation. A student taking an exam is anyone
(with or without an account) who opens a published exam link and
fills out the verification form. Most exam takers are not student
accounts.

I signed up as a student but want to create exams. What do I do?
Contact support to change your role, or create a new account with a
non-student persona.

Can teachers see student accounts?
The Students workspace shows people who took exams (identified by
verification form fields), not Quizzer user accounts. It is possible
for a student account holder to also appear in the Students workspace
if they took an exam, but these are tracked separately.

## Related Features

See also: Onboarding, Account Settings, Terminology, Navigation,
Dashboard
