# QUE Knowledge Base

Product knowledge that QUE uses to answer user questions about Quizzer.
Injected between the prepare and generate steps of the QUE agent graph.

## Design Principles

- Answer-oriented, not engineering-oriented. Written for users, not developers.
- Decision guides: when user asks X, navigate to the right path and explain.
- CORE.md is listed in the manifest but **not retrieved**. Hybrid RAG + workflow
  cards (`knowledge/intents/*.json`) select domain packs. A tiny CORE skeleton is
  injected only when retrieval is thin or no-answer.
- Every claim is verified against the Quizzer codebase. Unverified claims
  are marked as UNKNOWN.
- Live account numbers still need tools. Guides must not invent them.

## Structure

```
knowledge/
  CORE.md                              # Product map (not retrieved; skeleton only if RAG is thin)
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

  intents/
    exam.publish.json                  # Deterministic how-to cards (no LLM)
    exam.share.json
    …
```

## Document Count: 27 documents (CORE listed, not retrieved) + workflow cards in `intents/`

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

## Retrieval (Phase 2 dense + Phase 6 hybrid)

**Hybrid (default when index + `bm25_corpus.json` exist):** dense Chroma
candidates fused with chunk BM25 via reciprocal rank fusion (`QUE_RAG_HYBRID`).
No-answer stays dense-gated (`QUE_RAG_MIN_SCORE`). Build/update:

```bash
uv run python -m app.knowledge --force
uv run python scripts/run_retrieval_eval.py --mode hybrid --latency
```

**Dense-only:** set `QUE_RAG_HYBRID=false` or omit the BM25 sidecar.

**Keyword (fallback):** CORE skeleton only when retrieval is thin; `manifest.json`
keywords select up to `max_guides` domain guides when the Chroma index is missing
or RAG is disabled (`QUE_RAG_ENABLED=false`). CORE.md is not retrieved.

### Chunking rationale

Split on `#` / `##` / `###` so each vector is about one UI path or decision.
Oversized sections split by paragraph with overlap (~150 chars). Each chunk
stores `doc_id`, path, title, section, content hash, corpus version, and
embedding model for incremental re-index and citations.
