---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Verification Schema

## Overview

Verification Schema is the identity form students fill out before
starting an exam. It determines which fields are collected (such as
name, enrollment number, class, section, batch) and how those fields
are configured.

This is the first thing students interact with before an exam. It
collects who they are, not what they know. It is NOT related to answer
grading, scoring rules, or answer keys.

Users may call this: student identity form, registration fields,
enrollment form, identity verification, student info form, before-exam
form, student details.

## Step-by-Step UI Guide: Setting Up Verification Schema

Step 1 — Open exam settings:
In the left sidebar, click Exams. Click on your exam card. Click the
Settings tab (rightmost tab in the tab row).

Step 2 — Find verification schema:
Scroll down in the Settings page until you see the Verification Schema
section. Click on it to expand the configuration panel.

Step 3 — Choose a preset (optional):
At the top of the verification panel, you will see preset buttons:
College, School, Coaching, Minimal. Click one to load a starter set
of fields. For example, clicking College loads Name, Enrollment Number,
Section, Semester, and Branch fields automatically.

Step 4 — Customize fields:
Each field shows its label, type, and required status. For each field:

To edit: click the field row to expand it. Change the Label (what
students see), Type (Text, Number, or Select dropdown), and toggle the
Required switch (on = students must fill it, shown with a red asterisk).

To add a field: click the Add Field button at the bottom of the field
list. A new empty field appears. Configure its label, type, and
options.

To remove a field: click the delete icon (trash icon) on the field
row.

To reorder: drag fields up or down to change the order students see
them.

For Select-type fields: after choosing Select as the type, an Options
area appears. Type each option (for example: Section A, Section B,
Section C) and press Enter or click Add to add each one.

Step 5 — Set account default (optional):
If you want the same fields on every new exam, go to Account Settings
(sidebar ACCOUNT → **Settings**). Click the
Workspace tab. Find Default Verification Schema and configure it
there. All new exams inherit this default.

Step 6 — Save:
Changes auto-save. You will see a brief save confirmation.

## Who Configures It

Teachers configure the verification schema. Students see and fill the
form when they open an exam link and are about to start.

## Where It Lives

Per-exam configuration: open the exam from Exams, go to the Settings
tab, and expand the Verification Schema section. This configures the
form for that specific exam.

Account-wide default: go to Account Settings → Workspace tab. The
default schema is applied automatically to all new exams you create.
Individual exams can then override or customize this default.

## What It Is (and What It Is Not)

Verification Schema IS:
- The identity form shown to students before an exam
- A configuration for which fields to collect (name, enrollment, etc.)
- The way teachers identify students in Results and Students workspace
- The mechanism for attempt deduplication (preventing extra retakes)

Verification Schema is NOT:
- Answer grading or scoring rules
- Answer keys or correct answers
- The grading style setting (that is a separate scoring option)
- A login or account system (students do not create accounts)
- Related to question review (Draft/Approved/Rejected)

## How It Works

The teacher defines which fields students must fill out. These fields
serve two critical purposes:

1. Identity: the values appear in Results, Monitoring, and the
   Students workspace so the teacher can identify each student by
   name, enrollment number, etc.

2. Attempt deduplication: certain fields are marked as identity fields.
   These determine whether a student has already used their allowed
   attempts. For example, if enrollment number is an identity field
   and Maximum Attempts is 1, a student who already submitted with
   that enrollment number cannot start a second attempt.

The deduplication uses the combination of identity-marked fields. If
name and enrollment number are both identity fields, the system checks
that specific combination. A different name with the same enrollment
number might or might not match, depending on the exact field
configuration.

## Preset Contexts

The verification schema offers preset starting configurations that
load a common set of fields for different educational contexts:

College: fields typical for college and university students.
Includes: name, enrollment number, section, semester, branch/
department, institution type. Fields are pre-configured with
appropriate types, requirements, and labels.

School: fields typical for K-12 students.
Includes: name, roll number, class, section. Simpler than the college
preset.

Coaching: fields typical for coaching institute or test prep students.
Includes: name, batch, center, phone/email. Oriented toward
identifying which coaching batch or center a student belongs to.

Minimal: just a name field. The simplest configuration. Use when you
only need to identify students by name and do not need institutional
details.

Selecting a preset loads a starter set of fields that you can then
customize (add, remove, modify fields). Presets are starting points,
not locked configurations.

## Field Configuration

Each field in the schema has these configurable properties:

Label: the text shown to the student above the input (for example,
"Enrollment Number", "Full Name", "Class/Grade").

Type: the kind of input field:
- Text: free text entry. Students type whatever they want.
- Number: numeric entry only. Useful for enrollment numbers, roll
  numbers, phone numbers.
- Select: dropdown with predefined options. Students choose from a
  list. Good for class, section, semester, institution type.

Required: whether the student must fill this field to start the exam.
Required fields show an asterisk and block the Start button until
completed.

Placeholder: hint text shown inside the empty field (e.g., "Enter
your enrollment number"). Disappears when the student starts typing.

Help text: optional guidance shown below the field (e.g., "Use the
enrollment number from your student ID card").

Options (for select-type fields): the list of choices in the dropdown
(e.g., Section A, Section B, Section C).

Length constraints:
- Minimum length: the minimum number of characters or digits.
- Maximum length: the maximum allowed.
Useful for enforcing enrollment number formats (e.g., exactly 10
digits).

Pattern: optional validation pattern for enforcing specific formats.
For example, a regex pattern that requires enrollment numbers to start
with a letter followed by digits.

Case: option to force lowercase or uppercase input. Helps normalize
data (e.g., all enrollment numbers in uppercase).

Identity field: whether this field is used for attempt deduplication.
Fields marked as identity fields determine uniqueness across attempts.

## Using the Account Default

If you want the same verification fields on every exam:

1. Go to Account Settings → Workspace tab.
2. Configure the default verification schema with your preferred
   fields.
3. Save.

All new exams automatically inherit this default. You do not need to
configure each exam individually.

Each exam can then either:
- Use the account default as-is (no customization needed)
- Override it with a custom schema (expand the verification section
  in the exam's Settings and modify)

You can switch between using the default and a custom configuration
from the exam's Settings tab.

## What Students See

When a student opens the exam link and is about to start, they see:

1. The exam start page with title, duration, rules.
2. The verification form with all configured fields.
3. Required fields are marked with asterisks.
4. Select fields show dropdowns with the configured options.
5. The Start button is disabled until all required fields are filled.
6. If access codes are required, the code entry field appears here too.

After filling the form and clicking Start, the data is saved with
the attempt record. The student's identity is now associated with
their exam attempt.

## Field Ordering

Fields appear to students in the order they are configured in the
schema. You can reorder fields in the Settings tab to control the
visual layout of the form.

## Common Field Combinations

College exams: Name (text, required), Enrollment Number (number,
required, identity), Institution Type (select: University, College),
Course (text), Section (select: A, B, C), Semester (select: 1-8).

School exams: Name (text, required), Roll Number (number, required,
identity), Class (select: 1-12), Section (select: A, B, C, D).

Coaching: Name (text, required), Batch (select: Morning, Evening),
Center (select: Branch 1, Branch 2), Phone (number).

Hiring assessment: Name (text, required), Email (text, required),
Position Applied For (text).

Quick quiz: Name (text, required). Nothing else.

## Edge Cases

No verification schema: if the teacher does not configure any fields,
a minimal form (name only) may still appear, or students may proceed
directly to the exam.

Changing schema after publish: changes affect future attempts. Students
who already submitted are not asked to re-verify.

Changing identity fields after attempts exist: may affect deduplication
for future attempts. Existing attempt records keep their original
verification data.

## Common Questions

What is Verification Schema?
It is the identity form students fill before starting an exam. It
collects information like name and enrollment number to identify
students. It is not related to answer grading.

Where do I configure it?
Per-exam: Exams → open exam → Settings → Verification Schema.
Account default: Account Settings → Workspace tab.

Can I use the same fields for every exam?
Yes. Set the default verification schema under Account Settings →
Workspace tab. New exams inherit it automatically.

What preset options are available?
College, School, Coaching, and Minimal (name only). Each loads a
starter set of fields that you can customize.

Does the verification schema affect grading?
No. Verification Schema collects student identity before the exam.
Grading uses the correct answers on each question and the grading
style setting. These are completely separate.

How are students identified for attempt limits?
Fields marked as identity fields determine uniqueness. If enrollment
number is an identity field and Maximum Attempts is 1, a student who
submitted with that enrollment number cannot start again.

Can students change their verification info after starting?
No. The verification data is locked once the attempt starts.

What if a student enters the wrong enrollment number?
The data is saved as entered. If it does not match a previous attempt's
identity fields, it may be treated as a different student. There is
no correction mechanism after submission.

Can I add custom fields beyond the presets?
Yes. Presets are starting points. You can add, remove, rename, and
reconfigure any field.

## Related Features

See also: Exam Settings, Taking Exams (verification step), Account
Settings (workspace defaults), Results and Exports (student identity
in results), Students Workspace (learner identification)
