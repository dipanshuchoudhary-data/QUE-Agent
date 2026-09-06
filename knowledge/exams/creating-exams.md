---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Creating Exams

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

## Who Can Use It

Teacher-role accounts only. Student accounts do not see the Create Exam
action in the sidebar or on the Dashboard.

## Step-by-Step UI Guide: Creating Your First Exam

Follow these exact steps in the Quizzer interface:

Step 1 — Open the creation wizard:
Go to Dashboard in the sidebar and click the Create Exam quick action
card. You can also press Ctrl+K (or Cmd+K) to open the command palette
and type "Create Exam." Both take you to the creation wizard at the
/quizzes/create page.

Step 2 — Enter exam title:
The wizard opens with a title field at the top. Type your exam name
here (for example, "Biology Midterm Chapter 5"). You can also add an
optional description below the title.

Step 3 — Add your source content:
Below the title area, you will see the source content panel. You have
several options here:

Option A — Paste text: click into the text editor area and paste or
type your study material, lecture notes, or any text content.

Option B — Upload files: look for the file upload area (drag-and-drop
zone or a file selector button). Click it or drag files onto it.
Supported: PDF, DOCX, PPTX, TXT, PNG, JPG. You can upload up to 25
files, each up to 10 MB.

Option C — Web URL: find the URL input field and paste a web page
address. Quizzer extracts the text from the page.

Option D — YouTube URL: paste a YouTube link in the URL field. Quizzer
extracts the video transcript.

Option E — Import from Google Drive: if Drive is connected (via
Integrations), you will see an Import from Google Drive button in the
Files tab. Click it to open the Drive file picker.

You can combine multiple sources. For example, upload two PDFs and also
paste some extra notes.

Step 4 — Choose the AI generation mode:
After adding sources, you will see mode options:

Source-first (green recommended badge): click this if you want the AI
to read your content and decide how to structure the questions. Best
for most users.

Guided: click this if you want to control exactly how many questions,
what types, and how many sections. A blueprint editor appears where
you set section count, question type per section, and quantity.

Custom: click this if you want to skip AI entirely and write questions
yourself.

Step 5 — Configure the blueprint (Guided mode only):
If you chose Guided, you see the blueprint panel. Click Add Section to
create sections. For each section, select a question type from the
dropdown (MCQ, True/False, Short Answer, Long Answer, Multi-Select),
set the number of questions using the number field, and set marks per
question.

Step 6 — Start generation:
Click the Generate button (the primary emerald-green action button at
the bottom of the wizard). The system shows a processing indicator
while the AI works. This typically takes a few seconds to a couple of
minutes.

You can navigate away while waiting. An in-app notification (bell icon
in the top bar) will alert you when generation is complete or if it
failed.

Step 7 — Review the result:
When generation completes, your new exam appears in the Exams list
in the sidebar. Click on it to open the exam workspace. Select the
Questions tab to see all generated questions. Each question starts
with Draft status (shown in a badge on the question card).

From here, continue to the Questions review workflow to approve
questions, then configure Settings, then Publish.

## How to Start

Click Create Exam from:
- The Dashboard quick actions panel (emerald-green Create Exam card)
- The Exams workspace (create action)
- The command palette (press Ctrl+K or Cmd+K and type "Create Exam")

This opens the exam creation wizard.

If you have an unfinished draft from a previous session, Quizzer shows
a restore dialog. Click Restore to continue where you left off, or
Start Fresh to begin a new exam. Creation drafts are saved automatically
during the creation process.

## Step 1: Exam Title and Description

Enter a title for your exam. This is what appears in your Exams list
and on the student-facing start page. Optionally add a description
for additional context.

## Step 2: Adding Source Content

Sources are the material Quizzer's AI uses to generate questions. You
can add sources in several ways, and you can combine multiple source
types on a single exam:

Paste text: type or paste content directly into the text editor. Good
for lecture notes, summaries, or any text you have on hand.

Upload files: drag and drop or select files to upload. Supported
formats:
- PDF: text-based PDFs are extracted directly. Scanned PDFs go through
  OCR (optical character recognition) for text extraction. Image-only
  PDFs may produce poor results.
- DOCX: Microsoft Word documents. Text and basic formatting extracted.
- PPTX: PowerPoint presentations. Text from slides extracted.
- TXT: plain text files. Direct text extraction.
- Images (PNG, JPG): processed with OCR for text extraction.

Each file goes through a document extraction pipeline before the AI
can use it. The extraction step converts files into clean text that
the AI model can read.

Web URL: provide a web page address and Quizzer extracts the text
content from the page. Best for articles, blog posts, or online
documentation. May not work well on heavily JavaScript-rendered pages.

YouTube URL: provide a YouTube video link and Quizzer extracts the
video's transcript. Best when the video has auto-generated or manual
captions. Videos without captions may produce no usable content.

Import from Google Drive: if you have connected Google Drive via the
Integrations page, an Import from Google Drive option appears in the
Files tab during creation. This opens a file picker showing your Drive
files filtered to supported types (Google Docs, PDFs, Word documents,
plain text). The selected file is downloaded and processed through the
same extraction pipeline as a direct upload.

You can add up to 25 documents per exam. Each file must be within the
upload size limit (10 MB per file).

Users may call this: upload, add material, add content, import, source
material, study material.

## Step 3: AI Generation Mode

After adding sources, you choose how the AI generates questions:

Source-first (Recommended): the AI reads your uploaded content and
extracts questions directly from it. It detects the structure, topics,
and types of questions present in the material. The AI decides how
many questions to generate, what types, and how to organize them.

Important: Source-first prioritizes the document content, not
instructions typed in the text box. If you type "make 5 true/false
questions" but the source material contains paragraphs about history,
Source-first may produce MCQs about history instead of exactly 5
true/false questions. Use Guided mode for exact specifications.

Guided: you specify an exact blueprint with the number of sections,
question types per section, question count per section, and marks
per question. The AI follows your specification and uses the source
material as context. Use this when you need precise control over
the exam structure.

Custom: create questions manually without AI generation. Add questions
one at a time, choosing the type and filling in the content yourself.
No AI is involved. Best when you have specific questions in mind or
want to create from scratch.

Users may call this: generation mode, how to create questions, AI mode,
auto-generate, source-first vs guided.

## The Blueprint (Guided Mode)

When using Guided mode, the blueprint defines the exact exam structure:

Sections: logical groupings of questions (e.g., "Part A: Multiple
Choice", "Part B: Short Answer"). Maximum 20 sections.

Question type per section: MCQ, True/False, Short Answer, Long Answer,
or Multi-Select.

Questions per section: how many questions to generate in each section.
Maximum 50 per section, 100 total across all sections.

Marks per question: point value for each question in the section.
Default is 1 mark. Range: 1 to 100.

The blueprint is your specification — the AI generates exactly what
you ask for, using the source material as the knowledge base.

## AI Generation Process

After selecting a mode and triggering generation:

1. The system creates a generation job. The exam enters a Processing
   state with a progress indicator.
2. Source content is sent to the AI model along with the blueprint
   (Guided) or extraction instructions (Source-first).
3. The AI generates questions, options, correct answers, and section
   organization.
4. When complete, the exam moves to Generated status.
5. Questions appear on the Questions tab for review.
6. You receive an in-app notification (Generation complete or
   Generation failed).

Generation typically takes a few seconds to a couple of minutes,
depending on content length, question count, and AI model load.

During generation, you can navigate away. The notification alerts you
when it finishes.

## What Happens If Generation Fails

If generation fails, you receive a Generation failed notification.
Common causes:

Source too short: the uploaded content does not have enough material
for the AI to generate the requested number of questions. Try adding
more source content or reducing the question count.

Extraction error: the file could not be processed (corrupted PDF,
image-only PDF with poor OCR, unsupported format within a supported
extension). Try a different file or paste the text directly.

Daily quota exceeded: you have used all your daily AI generations for
your subscription tier. Wait until the next day when the quota resets.

AI service error: a temporary error with the AI model. Try again
after a few minutes.

Content too large: the extracted text exceeds the AI model's context
window. Try splitting the content across multiple exams or using a
shorter excerpt.

You can retry generation after addressing the issue.

## Daily Generation Quota

Each subscription tier has a daily limit on AI exam generations:

Explorer: 1 generation per day.
Professional: 3 generations per day.
Elite: 10 generations per day.

The quota resets daily. During the public beta, these limits may be
relaxed.

A single "generation" is one run of the AI pipeline for one exam. If
you regenerate individual questions later (from the Questions tab),
that does not count against the daily quota — only the initial full
exam generation counts.

Users may call this: generation limit, daily limit, how many exams
can I create, quota.

## AI Model Selection

Quizzer's AI gateway routes generation requests to the best available
AI model based on complexity factors: content length, question count,
question types requested, and subscription tier.

Teachers on higher tiers may have access to more powerful models.
During the beta, model selection may be locked to a default model for
all users.

You do not manually choose an AI model — the system selects
automatically. The model used is not exposed in the UI.

## Draft and Auto-Save

During creation, your progress is automatically saved as a creation
session. If you close the browser and return, you can resume where
you left off.

The creation session saves: exam title, description, uploaded source
content, selected generation mode, and blueprint configuration.

If you start a new exam while a draft exists, the previous draft
remains accessible. You can return to it from the Exams workspace.

## After Generation

Once AI generation completes, the exam appears in your Exams list
with its generated questions. The next steps are:

1. Open the exam from Exams.
2. Go to the Questions tab to review all generated questions.
3. Approve, reject, or edit each question.
4. Configure exam Settings (duration, proctoring, scoring, etc.).
5. Publish when all questions are Approved.

Generated questions start with Draft status. They must be reviewed
and Approved before the exam can be published.

## Tips for Better AI Generation

Provide clear, well-structured source content. The AI generates better
questions from organized material with clear topics and concepts.

Use Guided mode when you need exact control. Source-first is convenient
but may not match your exact expectations for question count or type.

For best OCR results on scanned PDFs, ensure the scan is clean and
text is legible. Blurry or low-resolution scans produce poor text
extraction.

YouTube URLs work best when the video has good captions (manual or
auto-generated). Videos with poor audio or no captions may not produce
useful text.

Splitting very large documents across multiple exams can produce better
results than feeding everything into one generation.

## Common Questions

How do I create an exam?
Click Create Exam, add your source content (paste text, upload files,
or provide URLs), choose a generation mode, and run AI generation.

What file types can I upload?
PDF, DOCX, PPTX, TXT, and images (PNG, JPG).

How long does generation take?
Usually a few seconds to a couple of minutes, depending on content
length and question count.

Can I create questions manually without AI?
Yes. Choose the Custom mode during creation, or add questions manually
from the Questions tab after creating the exam.

What is the difference between Source-first and Guided?
Source-first lets the AI decide question types and counts based on the
content. Guided follows your exact blueprint specifying section count,
question type, and quantity. Use Guided when you need precise control.

Why did generation fail?
Check the notification for details. Common causes: source content too
short, extraction errors on scanned PDFs, daily quota exceeded, or
temporary AI service errors.

Can I import files from Google Drive?
Yes, if you have connected Google Drive via Integrations. The import
option appears in the Files tab during exam creation.

How many exams can I generate per day?
Depends on your tier: Explorer gets 1/day, Professional gets 3/day,
Elite gets 10/day. The quota resets daily.

Does regenerating individual questions count against my daily quota?
No. Only the initial full exam generation counts. Regenerating single
questions from the Questions tab does not use a quota slot.

Can I combine multiple sources on one exam?
Yes. You can upload multiple files, paste text, and provide URLs all
on the same exam. They are all combined as source material.

What is the maximum number of questions I can generate?
In Guided mode, the blueprint supports up to 100 total questions
across up to 20 sections. Source-first determines the count
automatically based on the content.

## Related Features

See also: Questions, Exam Settings, Publishing and Sharing, Exam
Lifecycle, Google Drive Integration
