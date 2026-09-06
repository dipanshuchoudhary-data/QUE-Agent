---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Google Drive Integration

## Overview

Quizzer integrates with Google Drive for two purposes: importing source
documents during exam creation, and exporting exam results to Google
Sheets.

Users may call this: Drive import, import from Drive, export to Sheets,
Google Sheets export, Drive connection.

## Step-by-Step UI Guide: Using Google Drive with Quizzer

To import source files from Drive during exam creation:

Step 1 — Connect Drive:
In the left sidebar, click Integrations. Find the Google Drive card.
Click Connect. Authorize Quizzer in the Google popup. The card shows
"Connected" (green status).

Step 2 — Start creating an exam:
Open Create Exam from the Dashboard quick actions or press Ctrl+K and
type "Create Exam." The creation wizard opens.

Step 3 — Import from Drive:
In the source content area, look for the Files tab. You will see an
Import from Google Drive button (this only appears when Drive is
connected). Click it. A Drive file picker opens showing your files
filtered to supported types (Google Docs, PDFs, Word documents, text
files).

Step 4 — Select your file:
Browse or search your Drive files. Click the file you want. Click
Select or Import. The file is downloaded and processed through the
text extraction pipeline, just like a direct upload.

To export results to Google Sheets:

Step 1 — Open Results:
Go to Exams, open your exam, click the Results tab.

Step 2 — Click Export:
Click the Export button and select Google Sheets from the format
options. A new spreadsheet is created in your Google Drive with the
results data.

## How to Connect

Go to Integrations in the sidebar, find Google Drive, and click Connect.
This starts a Google OAuth flow where you grant Quizzer permission to
access your Drive files (read-only listing and file download).

## Importing Source Files

After connecting Google Drive, the exam creation wizard shows an
Import from Google Drive option in the Files tab.

How it works:
1. Click Import from Google Drive during exam creation.
2. A file picker shows your Drive files, filtered to supported types
   (Google Docs, PDFs, Word documents, plain text files).
3. Select a file to import.
4. The file is downloaded from your Drive and processed through the
   same document extraction pipeline as any direct upload.
5. The extracted text becomes source material for AI question
   generation.

This is the same pipeline as uploading a file directly — the only
difference is the file comes from your Drive account instead of your
local computer.

The Import from Google Drive button only appears when Drive is
connected (verified via the integration status).

## Exporting Results to Google Sheets

Teachers can export exam results directly to a Google Sheets
spreadsheet:

1. Go to the Results tab for a specific exam.
2. Use the Google Sheets export option (available when Drive is
   connected).
3. A new spreadsheet is created in your Google Drive with the exam
   results data.

This is also available from the Arena game history for exporting Arena
battle results.

## Drive Section on Integrations Page

The Integrations page has a Drive section that shows:
- Connected status
- File listing and search (browse your Drive files)
- Open in Drive externally option

The actual import-as-source action lives inside the exam creation
wizard, not on the Integrations page.

## Plan Availability

Explorer tier: Drive integration is locked. Available on Professional
and Elite tiers. During the public beta, this restriction may be
relaxed.

## Limitations

Drive import supports: Google Docs, PDFs, Word documents (.docx),
plain text files. Spreadsheets, presentations, images, and other file
types may not be importable as exam source material.

Drive access is read-only for file listing and download. Quizzer
creates new files (Sheets exports) but does not modify existing Drive
files.

## Common Questions

How do I import a file from Google Drive?
Connect Google Drive from Integrations first. Then, during exam
creation, go to the Files tab and click Import from Google Drive.
Select your file.

How do I export results to Google Sheets?
Connect Google Drive from Integrations. Go to the Results tab for
your exam and use the Google Sheets export option. A new spreadsheet
is created in your Drive.

What file types can I import from Drive?
Google Docs, PDFs, Word documents (.docx), and plain text files.

Where does the imported file go?
It is processed through the same document extraction pipeline as a
direct upload. The extracted text becomes source material for AI
question generation on that exam.

Where is the Google Sheets export saved?
In your connected Google Drive account. A new spreadsheet is created
with the results data.

Can I edit Drive files from Quizzer?
No. Drive access is read-only. Quizzer can list, search, and download
files from your Drive, and create new Sheets files, but it does not
modify existing files.

## Related Features

See also: Creating Exams (source files), Results and Exports (export
options), Integrations overview
