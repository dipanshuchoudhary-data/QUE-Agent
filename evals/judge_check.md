# Judge check: grade each row yourself, then compare with the judge

## r29: Negative marking settings

Expected: When negative marking is enabled in the exam settings, correct answers receive full marks, wrong answers result in a configured penalty deduction, and unanswered questions receive no marks and no penalty. The penalty amount is set per exam using the Penalty for Wrong Answer setting, and negative marking applies to all question types.

Chunk 1:
```
[grading] Negative Marking
## Negative Marking
When negative marking is enabled in the exam settings:

Correct answer: full marks for the question.
Wrong answer: the configured penalty is deducted.
Unanswered: no marks gained, no penalty.

The penalty amount is set per exam via the Penalty for Wrong Answer
setting. Negative marking applies to all question types.

Users may call this: penalty for wrong answers, mark deduction, minus
marking, negative scoring.
```

Chunk 2:
```
[exam-settings] Scoring
## Scoring
Default Marks: the default point value assigned to each new question.
Individual questions can override this value. This setting also exists
as an account-wide default in Account Settings → Workspace tab.
Default: 1 mark.

Negative Marking: when enabled, wrong answers on objective questions
(MCQ, True/False, Multi-Select) cause a mark deduction. Unanswered
questions are not penalized.
Default: Off.

Penalty for Wrong Answer: the number of marks deducted per wrong
answer when negative marking is enabled. Applies uniformly to all
question types.
Default: 0 (effectively no penalty even if negative marking is toggled).

Violation Penalty: marks deducted during grading based on the number
of integrity violations the student accumulated. Separate from negative
marking for wrong answers. The formula uses the violation count to
calculate a penalty amount.
Defau
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s22: How do I set the correct answer for a True/False question?

Expected: Mark one of True or False as correct.

Chunk 1:
```
[questions] Correct Answers
## Correct Answers
MCQ: exactly one option must be marked as correct. The question cannot
be approved without a valid correct answer.

True/False: one of True or False must be marked as correct. Same
approval requirement.

Short Answer: one or more accepted answers can be set. The grading
pipeline uses smart matching, so minor variations (spelling differences,
extra spaces, case changes) may still match even if not explicitly
listed as accepted answers.

Long Answer: there is no single "correct answer" field. Grading uses
AI evaluation against the question context, the source material, and
the grading style setting. Teachers may set reference answers or key
points to guide the AI evaluator.

Multi-Select: one or more options must be marked as correct. All
correct options must be identified. The student must select exactly
the correct set for full marks.
```

Chunk 2:
```
[terminology] Questions
## Questions
Individual items within an exam. Quizzer supports five question types:

Multiple Choice (MCQ): one correct answer from a set of options.
True/False: binary choice between true and false.
Short Answer: typed text response, graded automatically with a smart
multi-step matching pipeline.
Long Answer: typed text response, may need teacher review if AI
confidence is low.
Multi-Select: multiple correct answers from a set of options.

Questions have a review status (Draft, Approved, Rejected) and a marks
value.

Users may call this: items, problems, prompts, tasks.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s02: How do I check my analytics in Quizzer?

Expected: Click Analytics (chart icon) in the left sidebar to open the Analytics workspace.

Chunk 1:
```
[analytics] Step-by-Step UI Guide: Using Analytics
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
Scroll down to see visualizations: score d
```

Chunk 2:
```
[account-settings] Common Questions
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

How do I change my ema
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s21: How do I publish an exam in Quizzer?

Expected: Open your exam from the Exams workspace, then use the Publish action found on the exam card or inside the exam workspace.

Chunk 1:
```
[product-overview] Overview
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
```

Chunk 2:
```
[creating-exams] Overview
## Overview
Creating an exam in Quizzer involves adding source content, running AI
generation to produce questions, and then reviewing those questions
before publishing. The creation wizard guides you through this process
step by step.

Quizzer's AI reads your source material and generates exam questions
from it. You review and approve the questions, configure exam settings,
and publish when ready.

Users may call this: make a quiz, create a test, build an exam, set up
an assessment, generate questions, new exam.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s16: How can I see active attempts across all exams in the live panel?

Expected: Go to the Dashboard by clicking Dashboard in the sidebar, and view the Live Exams panel to see all exams with currently active LIVE attempts.

Chunk 1:
```
[live-monitoring] Step-by-Step UI Guide: Monitoring Live Exams
Step 5 — Check the Dashboard live panel:
For a quick overview across all exams, go to the Dashboard (click
Dashboard in the sidebar). The Live Exams panel shows all exams with
currently active LIVE attempts, so you do not need to check each exam
individually.
```

Chunk 2:
```
[empty-states] Dashboard — Live Exams Panel
## Dashboard — Live Exams Panel
Shows: exams with currently active LIVE attempts.

Empty when: no students are actively taking any exam right now.

What to do: this is normal outside of exam hours. The panel fills
when students are actively in the middle of an attempt with their
browser open.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## r30: Command palette and sidebar navigation

Expected: Press Ctrl+K (Windows) or Cmd+K (Mac) to open the command palette, a search overlay used to quickly jump to any workspace, search exams, or trigger actions. To navigate the sidebar, click Exams on the left side of the screen to view your exam library as cards, then click any exam card to open its workspace. At the top of the exam workspace, a tab row appears allowing you to switch between Questions, Monitoring, Results, Links, and Settings.

Chunk 1:
```
[navigation] Command Palette
## Command Palette
Teachers can open the command palette with a keyboard shortcut (Ctrl+K
or Cmd+K) to quickly navigate to any workspace, search exams, or
trigger actions like Create Exam.

The command palette reads from the same navigation configuration as the
sidebar. It provides fuzzy search across workspace names, exam titles,
and action labels.

Users may call this: quick search, keyboard shortcut, command bar,
Ctrl+K, search bar.
```

Chunk 2:
```
[account-settings] How to Access
## How to Access
In the left sidebar, open the **ACCOUNT** section and click **Settings**
(goes to `/account/settings`). You can also use the command palette
(Ctrl+K / Cmd+K) and search for Settings.

Do **not** look for Settings inside the avatar menu. The avatar at the
bottom of the sidebar is for identity and **Log out** only.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s24: How do I get the Teacher role during onboarding?

Expected: Sign up and select a non-student persona during onboarding to get the Teacher role.

Chunk 1:
```
[onboarding] Role Assignment
## Role Assignment
Your role is set once during onboarding and cannot be changed by you
afterward. If you chose the wrong persona and got the wrong role (for
example, chose Student but wanted Teacher access), you would need to
contact support.
```

Chunk 2:
```
[roles] Teacher Role
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
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## r33: Results tab integrity review

Expected: To view integrity details, click on any result row in the Results tab to expand it. The Integrity Review Panel opens below, showing a chronological violation timeline and aggregated violation buckets.

Chunk 1:
```
[results-exports] Integrity Review
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
```

Chunk 2:
```
[terminology] Results
## Results
A tab within each exam workspace showing graded outcomes with scores,
violation counts, integrity flags, and export options per student.
Results are per-exam — each exam has its own Results tab.

Separate from Analytics, which shows aggregate trends across multiple
exams.

Users may call this: scores, grades, outcomes, marks, performance,
exam results.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s04: Why is Quizzer giving me errors and how do I fix them?

Expected: Find your specific symptom in the troubleshooting guide and follow the provided step-by-step resolution steps.

Chunk 1:
```
[creating-exams] Overview
## Overview
Creating an exam in Quizzer involves adding source content, running AI
generation to produce questions, and then reviewing those questions
before publishing. The creation wizard guides you through this process
step by step.

Quizzer's AI reads your source material and generates exam questions
from it. You review and approve the questions, configure exam settings,
and publish when ready.

Users may call this: make a quiz, create a test, build an exam, set up
an assessment, generate questions, new exam.
```

Chunk 2:
```
[common-problems] Overview
## Overview
This guide covers the most frequently encountered issues when using
Quizzer, along with their root causes and step-by-step solutions. If
you are experiencing a problem, find the symptom below and follow the
resolution steps.

Users may call this: help, troubleshooting, something is wrong, not
working, fix, error, issue, bug, problem.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## r13: What is Quizzer and who is it for?

Expected: Quizzer is an AI-powered assessment platform for creating, delivering, monitoring, and analyzing exams. It is built for anyone who needs to build assessments—ranging from students practicing on their own to solo teachers, tutors, trainers, freelancers, teams, startups, coaching institutes, schools, universities, HR professionals, and content creators.

Chunk 1:
```
[product-overview] Overview
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
```

Chunk 2:
```
[navigation] Overview
## Overview
Quizzer's interface is organized around a sidebar for main workspaces,
tabs within each exam for detailed management, and utility overlays
(command palette, search, notifications). Understanding where things
live prevents confusion between features that share similar names.

Users may call this: where is, how do I find, where do I go, sidebar,
menu, navigation, UI.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## r12: Question types MCQ and true false

Expected: Multiple Choice (MCQ) presents a set of answer options where exactly one is correct and is graded instantly by comparing to the correct option. True/False is a binary choice question where the student selects True or False and is graded instantly by comparing to the correct answer. Both MCQ and True/False question cards show their question type as a small badge on the Questions tab in the exam workspace.

Chunk 1:
```
[questions] Option Limits
## Option Limits
MCQ questions can have 2 to 6 answer options.
Multi-Select questions can have 2 to 8 answer options.
True/False is always exactly 2 options (True and False).
```

Chunk 2:
```
[terminology] Questions
## Questions
Individual items within an exam. Quizzer supports five question types:

Multiple Choice (MCQ): one correct answer from a set of options.
True/False: binary choice between true and false.
Short Answer: typed text response, graded automatically with a smart
multi-step matching pipeline.
Long Answer: typed text response, may need teacher review if AI
confidence is low.
Multi-Select: multiple correct answers from a set of options.

Questions have a review status (Draft, Approved, Rejected) and a marks
value.

Users may call this: items, problems, prompts, tasks.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s17: Where is the Monitoring tab?

Expected: Open Exams, open the specific exam, then select the Monitoring tab.

Chunk 1:
```
[navigation] Common Questions
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
There is no s
```

Chunk 2:
```
[live-monitoring] The Monitoring Tab
## The Monitoring Tab
The Monitoring tab shows a table of attempts for the selected exam:

Each row includes:
- Student identity (from verification form)
- Attempt status (in progress, submitted, auto-submitted)
- Violation count
- Integrity event summary
- Timing information
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## r31: Link window vs exam duration meaning

Expected: Link window controls when students can begin by defining how long the published link accepts new starts (measured in hours or days). Duration is the per-attempt timer that controls how long students can work once they begin (measured in minutes). For example, a 60-minute exam with a 24-hour link window means students have 24 hours to start and 60 minutes once they start.

Chunk 1:
```
[terminology] Link Window vs Duration
## Link Window vs Duration
These are different and commonly confused:

Link window: how long the published link accepts new starts (hours
or days). Controls WHEN students can begin.

Duration: how long each student has once they start (minutes). Controls
HOW LONG students can work.

A 60-minute exam with a 24-hour link window means students have 24
hours to start, and 60 minutes once they begin.
```

Chunk 2:
```
[publishing] Link Window
## Link Window
The link window (available_until) controls how long the published link
accepts new attempt starts. It is a deadline after which students can
no longer begin the exam.

Default link windows by subscription tier:
- Explorer: 24 hours from publish time
- Professional: 1 week from publish time
- Elite: 1 week default, extendable to custom dates

During the public beta, link window caps may be relaxed so every user
gets longer windows.

When the link window expires:
- The exam remains published (status does not change)
- Students who open the link see that it is no longer available
- In-progress attempts that started before expiry may also be affected
- The teacher can renew/extend the link window at any time

Link window and duration are different things:
- Link window: how long the link accepts new starts (hours/days)
- Duration: how long each student
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s07: Why is my teacher dashboard completely empty right now?

Expected: Your teacher dashboard is empty because the account is brand new, no exams have been created yet, or no exams currently have LIVE activity.

Chunk 1:
```
[dashboard] What Makes the Dashboard Empty
## What Makes the Dashboard Empty
The teacher dashboard may show an empty or minimal state when:
- No exams have been created yet (the activation checklist guides you)
- No exams have LIVE activity
- The account is brand new

The Dashboard fills up as you create exams, publish them, and students
start taking them.
```

Chunk 2:
```
[empty-states] Dashboard — Live Exams Panel
## Dashboard — Live Exams Panel
Shows: exams with currently active LIVE attempts.

Empty when: no students are actively taking any exam right now.

What to do: this is normal outside of exam hours. The panel fills
when students are actively in the middle of an attempt with their
browser open.
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _

## s06: How do I get better AI-generated questions in Quizzer?

Expected: Provide clear, well-structured source content with organized material, clear topics, and concepts.

Chunk 1:
```
[creating-exams] AI Model Selection
## AI Model Selection
Quizzer's AI gateway routes generation requests to the best available
AI model based on complexity factors: content length, question count,
question types requested, and subscription tier.

Teachers on higher tiers may have access to more powerful models.
During the beta, model selection may be locked to a default model for
all users.

You do not manually choose an AI model — the system selects
automatically. The model used is not exposed in the UI.
```

Chunk 2:
```
[questions] Common Questions
## Common Questions
What question types does Quizzer support?
Multiple Choice (MCQ), True/False, Short Answer, Long Answer, and
Multi-Select for graded exams. Arena also has One Word Answer and
Guess It.

How do I approve questions?
Open the exam, go to the Questions tab, and click Approve on each
question. You can also use the bulk approve action to approve all
remaining drafts at once.

Can I edit AI-generated questions?
Yes. You can change any part of an AI-generated question including the
text, options, correct answer, type, and marks.

Why can I not publish my exam?
All questions must be in Approved status. Check the Questions tab for
any remaining Draft or Rejected questions and approve them. At least
one Approved question is required.

How do I add a question manually?
On the Questions tab, use the add question action. Select the type,
fill in the cont
```

Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _
