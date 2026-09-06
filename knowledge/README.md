# QUE Knowledge Base

Product knowledge that QUE uses to answer user questions about Quizzer.
Injected between the prepare and generate steps of the QUE agent graph.

## Design Principles

- Answer-oriented, not engineering-oriented. Written for users, not developers.
- Decision guides: when user asks X, navigate to the right path and explain.
- CORE.md is always injected. Up to 3 extra guides match the latest user
  message via keywords in manifest.json.
- Every claim is verified against the Quizzer codebase. Unverified claims
  are marked as UNKNOWN.
- Live account numbers still need tools. Guides must not invent them.

## Structure

```
knowledge/
  CORE.md                              # Always injected — product map + answer contract
  manifest.json                        # Retrieval config (keywords, paths, max_guides)

  product/
    overview.md                        # What Quizzer is, audience, core loop
    terminology.md                     # Glossary with user aliases and common confusions
    roles.md                           # Creator vs Taker vs Student account role

  exams/
    creating-exams.md                  # Create Exam wizard, sources, AI generation
    questions.md                       # Question types, review, approve, edit, sections
    exam-settings.md                   # All configurable settings (timing, proctoring, scoring, attempts)
    publishing-and-sharing.md          # Publish gate, link window, sharing methods
    taking-exams.md                    # Student/taker perspective: start to submit
    verification-schema.md             # Identity form before exam

  scoring/
    grading.md                         # Grading pipeline, grading styles, negative marking
    results-and-exports.md             # Results tab, exports (CSV, Excel, Sheets), integrity review

  monitoring/
    live-and-monitoring.md             # LIVE definition, Monitoring tab, integrity events, WebSocket

  analytics/
    analytics.md                       # Cross-exam aggregate trends, charts, filters, Arena analytics

  students/
    students-workspace.md              # Learner directory, readiness labels, support queue, cohort health

  arena/
    arena.md                           # Live quiz battles: hosting, joining, scoring, game history

  integrations/
    google-classroom.md                # Import courses/roster, assign exams, push grades, announcements
    google-calendar.md                 # Schedule exams as calendar events
    google-drive.md                    # Import source files from Drive, export results to Sheets

  account/
    onboarding.md                      # Signup, personas, four-step onboarding flow
    account-settings.md                # Profile, preferences, workspace defaults, security
    notifications.md                   # In-app notification types, preferences, email policy

  dashboard/
    dashboard.md                       # Teacher and student dashboard, live exams panel, quick actions

  navigation/
    navigation.md                      # UI map, sidebar, tabs, command palette, feature tours

  troubleshooting/
    common-problems.md                 # Symptom → root cause → fix for frequent issues
    empty-states.md                    # Empty data decision trees, dependency chains

  workflows/
    exam-lifecycle.md                  # Draft → Published → Archived states and transitions
    common-workflows.md                # Step-by-step recipes for common multi-feature tasks
```

## Document Count: 27 documents (1 always-injected + 26 keyword-matched)

## Document Standards

Every document follows this format:

- YAML frontmatter: source, status (verified/needs-confirmation/partial),
  last_verified date, confidence (high/medium/low).
- Sections: Overview, Who Can Use It, How It Works, How to Use It,
  Configuration/Options, Common Questions, Related Features,
  Limitations, Troubleshooting. Not every section is required.
- User aliases: major concepts include "Users may call this" lines.
- Self-contained: each document makes sense when retrieved independently.
- Product terminology: uses exact UI labels (Exams, not quizzes).
- No dynamic data: explains how features work, never current user state.

## Coverage Matrix

| Domain            | Documents | Question Types Covered                            |
|-------------------|-----------|---------------------------------------------------|
| Product           | 3         | Concepts, FAQ, Terminology                        |
| Exams             | 6         | How-To, Rules, Configuration, Concepts, FAQ       |
| Scoring           | 2         | How-To, Rules, Concepts, Troubleshooting          |
| Monitoring        | 1         | Concepts, Rules, Troubleshooting, FAQ             |
| Analytics         | 1         | Concepts, How-To, FAQ, Troubleshooting            |
| Students          | 1         | Concepts, How-To, FAQ, Troubleshooting            |
| Arena             | 1         | Concepts, How-To, Rules, Configuration, FAQ       |
| Integrations      | 3         | How-To, Configuration, Concepts, FAQ              |
| Account           | 3         | How-To, Configuration, Concepts, FAQ              |
| Dashboard         | 1         | Concepts, FAQ                                     |
| Navigation        | 1         | How-To, FAQ, Concepts                             |
| Troubleshooting   | 2         | Troubleshooting, FAQ, Decision Trees              |
| Workflows         | 2         | How-To, Step-by-Step, Cross-Feature               |

## How to Add or Update Knowledge

1. Verify information against the Quizzer codebase.
2. Use existing terminology from product/terminology.md.
3. Avoid duplicating existing knowledge. Cross-reference instead.
4. Place knowledge in the appropriate domain folder.
5. Keep documents self-contained.
6. Add examples where useful.
7. Mark uncertain information as UNKNOWN / NEEDS PRODUCT CONFIRMATION.
8. Update related documents when behavior changes.
9. Register new documents in manifest.json with appropriate keywords.
10. Update the last_verified date in frontmatter when re-checking.

## Retrieval

CORE.md is always injected. manifest.json maps each document to keyword
lists. The QUE agent matches the user's latest message against keywords
to select up to max_guides additional documents. No embeddings or vector
search — keyword matching only.
