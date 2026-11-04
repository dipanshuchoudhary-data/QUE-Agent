"""Unit tests for section-aware knowledge chunking (no LLM / Chroma)."""

from __future__ import annotations

from app.knowledge.chunking import chunk_markdown, strip_frontmatter


def test_strip_frontmatter():
    raw = "---\ntitle: x\n---\n\n# Hello\nBody"
    assert strip_frontmatter(raw).startswith("# Hello")


def test_chunks_by_heading():
    md = """---
id: demo
---

# Title

Intro paragraph about the product.

## Create exam

Click **Create Exam** in the sidebar.

## Publish

Use **Publish** when questions are approved.
"""
    chunks = chunk_markdown(
        doc_id="demo",
        path="demo.md",
        title="Demo",
        raw_markdown=md,
        corpus_version="1.0.0",
        target_chars=0,  # heading split only; small-section merging is tested separately
    )
    assert len(chunks) >= 2
    sections = {c.section for c in chunks}
    assert "Create exam" in sections or any("Create" in c.section for c in chunks)
    assert all(c.doc_id == "demo" for c in chunks)
    assert all(c.content_hash for c in chunks)
    assert all(c.corpus_version == "1.0.0" for c in chunks)


def test_oversized_section_splits():
    long_body = "Paragraph about Quizzer.\n\n" * 80
    md = f"## Huge section\n\n{long_body}"
    chunks = chunk_markdown(
        doc_id="big",
        path="big.md",
        title="Big",
        raw_markdown=md,
        corpus_version="1",
        max_chars=400,
        overlap_chars=40,
        target_chars=0,  # isolates splitting; the floor is tested separately
    )
    assert len(chunks) >= 2
    assert all(c.char_count <= 450 for c in chunks)


def test_contextual_text_prefixes_title_and_section_but_not_empty_parts():
    from app.knowledge.chunking import contextual_text

    assert contextual_text('Publishing', 'Overview', 'body') == 'Publishing > Overview\nbody'
    assert contextual_text('', '', 'body') == 'body'



def test_alias_line_is_attached_never_a_standalone_chunk():
    body = "## Written Grading\n" + "\n\n".join(f"Step {i}: " + "x" * 300 for i in range(3))
    body += "\n\nUsers may call this: how short answers are graded, AI grading."
    chunks = chunk_markdown(
        doc_id="g", path="g.md", title="Grading", raw_markdown=body, corpus_version="1", max_chars=900,
        target_chars=0,  # isolates alias handling from the size floor
    )
    assert len(chunks) >= 2
    assert not any(c.text.lstrip().startswith("Users may call this:") for c in chunks)
    assert "Users may call this" in chunks[-1].text
    assert "Step 2" in chunks[-1].text


def test_small_sections_merge_up_to_target_but_never_past_max():
    body = "\n".join(f"## Part {i}\n" + ("word " * 30).strip() for i in range(8))  # ~160 chars each
    chunks = chunk_markdown(
        doc_id="g", path="g.md", title="G", raw_markdown=body, corpus_version="1",
        max_chars=900, target_chars=400,
    )
    assert len(chunks) < 8
    assert all(c.char_count <= 900 for c in chunks)
    assert all(c.char_count >= 400 for c in chunks[:-1])


def test_single_short_guide_stays_one_chunk():
    chunks = chunk_markdown(
        doc_id="g", path="g.md", title="G", raw_markdown="## A\nshort text here that is fine and long enough to keep.",
        corpus_version="1",
    )
    assert len(chunks) == 1


def test_no_chunk_below_the_floor_even_when_neighbours_are_large():
    big = "word " * 170  # ~850 chars: a neighbour that cannot absorb a small section under 900
    body = f"## Big one\n{big}\n\n## Tiny\nshort section text only.\n\n## Big two\n{big}\n\n## Tiny two\nanother short one here."
    chunks = chunk_markdown(
        doc_id="g", path="g.md", title="G", raw_markdown=body, corpus_version="1",
        max_chars=900, target_chars=400,
    )
    assert chunks
    assert all(c.char_count >= 400 for c in chunks)
    assert all(c.char_count <= 900 for c in chunks)  # the ceiling is hard too
    joined = " ".join(c.text for c in chunks)
    assert "short section text only" in joined and "another short one here" in joined


def test_real_guides_every_chunk_between_400_and_900():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "knowledge"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    checked = 0
    for doc in manifest["documents"]:
        path = root / doc["path"]
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        chunks = chunk_markdown(
            doc_id=doc["id"], path=doc["path"], title=doc.get("title", ""), raw_markdown=raw, corpus_version="t"
        )
        for c in chunks:
            assert 400 <= c.char_count <= 900, (doc["id"], c.section, c.char_count)
            checked += 1
    assert checked > 100
