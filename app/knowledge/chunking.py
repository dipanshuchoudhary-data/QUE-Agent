"""Section-aware markdown chunking for QUE knowledge packs.

Rationale (Phase 2 handbook): fixed character windows ignore heading
boundaries and mix unrelated UI paths. We split on ``#`` / ``##`` / ``###``,
keep the heading with its body, and only sub-split oversized sections by
paragraph with a small overlap so vectors stay about one decision/path.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)

# Soft targets — free-tier context budget still caps at retrieve time.
DEFAULT_MAX_CHARS = 1_200
DEFAULT_OVERLAP_CHARS = 150
DEFAULT_MIN_CHARS = 40


@dataclass(frozen=True)
class KnowledgeChunk:
    """One embeddable unit with provenance for citations / re-index."""

    chunk_id: str
    doc_id: str
    path: str
    title: str
    section: str
    text: str
    content_hash: str
    corpus_version: str
    char_count: int
    domain: str = ""
    intents: str = ""


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(text: str, *, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return (slug or "section")[:max_len]


def _hard_slice(body: str, *, max_chars: int, overlap: int) -> list[str]:
    parts: list[str] = []
    start = 0
    n = len(body)
    while start < n:
        end = min(n, start + max_chars)
        piece = body[start:end].strip()
        if piece:
            parts.append(piece)
        if end >= n:
            break
        start = max(start + 1, end - overlap)
    return parts


def _split_oversized(body: str, *, max_chars: int, overlap: int) -> list[str]:
    body = body.strip()
    if not body:
        return []
    if len(body) <= max_chars:
        return [body]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    # Single block (no paragraph breaks) or one giant paragraph → hard slice.
    if len(paragraphs) <= 1:
        return _hard_slice(body, max_chars=max_chars, overlap=overlap)

    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(para) > max_chars:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_hard_slice(para, max_chars=max_chars, overlap=overlap))
            continue
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        buf = para
    if buf:
        chunks.append(buf)
    return chunks


def chunk_markdown(
    *,
    doc_id: str,
    path: str,
    title: str,
    raw_markdown: str,
    corpus_version: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    min_chars: int = DEFAULT_MIN_CHARS,
    domain: str = "",
    intents: str = "",
) -> list[KnowledgeChunk]:
    """Parse one knowledge file into embeddable chunks with metadata."""
    body = strip_frontmatter(raw_markdown)
    if not body:
        return []

    matches = list(_HEADING_RE.finditer(body))
    sections: list[tuple[str, str]] = []
    if not matches:
        sections.append((title or doc_id, body))
    else:
        preamble = body[: matches[0].start()].strip()
        if preamble and len(preamble) >= min_chars:
            sections.append((title or "Introduction", preamble))
        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            section_body = body[start:end].strip()
            text = f"## {heading}\n{section_body}".strip() if section_body else f"## {heading}"
            sections.append((heading, text))

    out: list[KnowledgeChunk] = []
    for section_title, section_text in sections:
        pieces = _split_oversized(section_text, max_chars=max_chars, overlap=overlap_chars)
        for idx, piece in enumerate(pieces):
            if len(piece) < min_chars:
                continue
            digest = content_hash(piece)[:12]
            section_slug = _slug(section_title)
            chunk_id = f"{doc_id}::{section_slug}::{idx}::{digest}"
            out.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    path=path,
                    title=title,
                    section=section_title,
                    text=piece,
                    content_hash=content_hash(piece),
                    corpus_version=corpus_version,
                    char_count=len(piece),
                    domain=domain,
                    intents=intents,
                )
            )
    return out
