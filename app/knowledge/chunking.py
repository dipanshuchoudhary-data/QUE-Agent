"""Section-aware markdown chunking for QUE knowledge packs.

Rationale (Phase 2 handbook): fixed character windows ignore heading
boundaries and mix unrelated UI paths. We split on ``#`` / ``##`` / ``###``,
keep the heading with its body, and only sub-split oversized sections by
paragraph with a small overlap so vectors stay about one decision/path.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)

# Soft targets — free-tier context budget still caps at retrieve time.
# Env overrides exist only so scripts/benchmark_chunk_size.py can compare sizes; unset in prod.
DEFAULT_MAX_CHARS = int(os.getenv("QUE_CHUNK_MAX_CHARS", "900"))
DEFAULT_OVERLAP_CHARS = 120
DEFAULT_MIN_CHARS = 40
# Neighbouring sections shorter than this are joined (up to DEFAULT_MAX_CHARS).
DEFAULT_TARGET_CHARS = int(os.getenv("QUE_CHUNK_TARGET_CHARS", "400"))


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


def contextual_text(title: str, section: str, text: str) -> str:
    """Text used to EMBED and BM25-index a chunk: guide title + section + body.

    Bare chunks named only "Overview" matched every query and outranked the guide that
    actually answers it. The header carries the guide topic into the vector and the terms
    into BM25. The text injected into the prompt stays the plain chunk body.
    """
    head = " > ".join(part.strip() for part in (title, section) if part and part.strip())
    return f"{head}\n{text}" if head else text


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


_ALIAS_RE = re.compile(r"^\s*Users may call this:", re.IGNORECASE)


def _attach_aliases(chunks: list[str]) -> list[str]:
    """Fold chunks that are only "Users may call this: ..." lines into the chunk above.

    An alias line is near-identical to the questions it lists, so as its own chunk it
    out-ranks the guide text that actually answers them and gets injected with no facts.
    Attached to the previous chunk it still helps matching but can never stand alone.
    """
    out: list[str] = []
    for chunk in chunks:
        paragraphs = [p for p in re.split(r"\n\s*\n", chunk.strip()) if p.strip()]
        if out and paragraphs and all(_ALIAS_RE.match(p) for p in paragraphs):
            out[-1] = f"{out[-1]}\n\n{chunk.strip()}"
        else:
            out.append(chunk)
    return out


def _split_oversized(body: str, *, max_chars: int, overlap: int) -> list[str]:
    return _attach_aliases(_split_oversized_raw(body, max_chars=max_chars, overlap=overlap))


def _split_oversized_raw(body: str, *, max_chars: int, overlap: int) -> list[str]:
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


def _merge_small(
    pieces: list[tuple[str, str]], *, target_chars: int, max_chars: int
) -> list[tuple[str, str]]:
    """Join consecutive pieces until each reaches ``target_chars`` without passing ``max_chars``.

    The merged chunk keeps the first piece's section title. A short piece that cannot
    fit forward (next piece too big) is tried against the previous chunk instead.
    """
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(pieces):
        title, text = pieces[i]
        i += 1
        while len(text) < target_chars and i < len(pieces) and len(text) + 2 + len(pieces[i][1]) <= max_chars:
            text = f"{text}\n\n{pieces[i][1]}"
            i += 1
        if len(text) < target_chars and out and len(out[-1][1]) + 2 + len(text) <= max_chars:
            out[-1] = (out[-1][0], f"{out[-1][1]}\n\n{text}")
        else:
            out.append((title, text))

    # Hard floor: whatever is still under ``target_chars`` joins the shorter neighbour even
    # if that passes ``max_chars`` (so a chunk is at most max_chars + target_chars). Only a
    # guide whose whole text is under the floor can stay below it.
    while len(out) > 1:
        small = [k for k, (_, t) in enumerate(out) if len(t) < target_chars]
        if not small:
            break
        k = min(small, key=lambda j: len(out[j][1]))
        neighbours = [j for j in (k - 1, k + 1) if 0 <= j < len(out)]
        j = min(neighbours, key=lambda n: len(out[n][1]))
        lo, hi = sorted((k, j))
        out[lo] = (out[lo][0], f"{out[lo][1]}\n\n{out[hi][1]}")
        del out[hi]
    return out


def _units(sections: list[tuple[str, str]], *, max_chars: int, overlap: int) -> list[tuple[str, str]]:
    """Paragraph-level pieces (each at most ``max_chars``) tagged with their section title."""
    out: list[tuple[str, str]] = []
    for section_title, text in sections:
        for para in (p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()):
            pieces = [para] if len(para) <= max_chars else _hard_slice(para, max_chars=max_chars, overlap=overlap)
            for piece in pieces:
                # An alias line never stands alone: fold it into the paragraph above.
                if _ALIAS_RE.match(piece) and out and len(out[-1][1]) + 2 + len(piece) <= max_chars:
                    out[-1] = (out[-1][0], f"{out[-1][1]}\n\n{piece}")
                else:
                    out.append((section_title, piece))
    return out


def _len(units: list[tuple[str, str]]) -> int:
    return len("\n\n".join(t for _, t in units))


def _pack(units: list[tuple[str, str]], *, target_chars: int, max_chars: int) -> list[tuple[str, str]]:
    """Pack paragraph units into chunks of ``target_chars``..``max_chars``.

    Greedy fill up to ``max_chars``, then repair any chunk under ``target_chars`` by
    merging it with a neighbour when the result still fits, otherwise by moving units
    across from the neighbour while both stay in range. Both limits are hard; only a
    guide whose total text is under ``target_chars`` stays below it.
    """
    chunks: list[list[tuple[str, str]]] = []
    cur: list[tuple[str, str]] = []
    for u in units:
        if cur and _len([*cur, u]) > max_chars:
            chunks.append(cur)
            cur = [u]
        else:
            cur.append(u)
    if cur:
        chunks.append(cur)

    for _ in range(4 * len(chunks) + 8):
        small = [k for k, c in enumerate(chunks) if _len(c) < target_chars]
        if not small or len(chunks) == 1:
            break
        k = min(small, key=lambda j: _len(chunks[j]))
        neighbours = sorted((j for j in (k - 1, k + 1) if 0 <= j < len(chunks)), key=lambda j: _len(chunks[j]))
        done = False
        for j in neighbours:  # merge if it fits
            lo, hi = sorted((k, j))
            if _len(chunks[lo] + chunks[hi]) <= max_chars:
                chunks[lo] = chunks[lo] + chunks[hi]
                del chunks[hi]
                done = True
                break
        if done:
            continue
        for j in neighbours:  # otherwise re-split the pair at any point where both fit the range
            lo, hi = sorted((k, j))
            both = chunks[lo] + chunks[hi]
            for cut in range(1, len(both)):
                left, right = both[:cut], both[cut:]
                if target_chars <= _len(left) <= max_chars and target_chars <= _len(right) <= max_chars:
                    chunks[lo], chunks[hi] = left, right
                    done = True
                    break
            if done:
                break
        if done:
            continue
        for j in neighbours:  # last resort: cut the pair's text at a line break inside a big paragraph
            lo, hi = sorted((k, j))
            text = "\n\n".join(t for _, t in chunks[lo] + chunks[hi])
            cuts = [m.start() for m in re.finditer(r"\n", text)]
            fits = [
                c for c in cuts
                if target_chars <= len(text[:c].rstrip()) <= max_chars
                and target_chars <= len(text[c:].lstrip()) <= max_chars
            ]
            if fits:
                c = min(fits, key=lambda x: abs(len(text[:x]) - len(text[x:])))
                title_hi = chunks[hi][0][0] if len(chunks[lo]) + len(chunks[hi]) > 1 else chunks[lo][0][0]
                chunks[lo] = [(chunks[lo][0][0], text[:c].rstrip())]
                chunks[hi] = [(title_hi, text[c:].lstrip())]
                done = True
                break
        if not done:
            break
    return [(c[0][0], "\n\n".join(t for _, t in c)) for c in chunks]


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
    target_chars: int = DEFAULT_TARGET_CHARS,
    domain: str = "",
    intents: str = "",
) -> list[KnowledgeChunk]:
    """Parse one knowledge file into embeddable chunks with metadata.

    With ``target_chars`` > 0 every chunk is between ``target_chars`` and ``max_chars``
    (both hard): the guide is cut into paragraphs and packed, so a chunk may span
    neighbouring sections. A guide shorter than ``target_chars`` stays one chunk.
    ``target_chars=0`` keeps one chunk per heading section.
    """
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

    if target_chars > 0:
        units = _units(sections, max_chars=max_chars, overlap=overlap_chars)
        merged = _pack(units, target_chars=target_chars, max_chars=max_chars)
    else:  # no floor: one chunk per heading section (split only when over max_chars)
        raw: list[tuple[str, str]] = []
        for section_title, section_text in sections:
            for piece in _split_oversized(section_text, max_chars=max_chars, overlap=overlap_chars):
                raw.append((section_title, piece))
        merged = raw

    out: list[KnowledgeChunk] = []
    seen_idx: dict[str, int] = {}
    for section_title, piece in merged:
        if len(piece) < min_chars:
            continue
        idx = seen_idx.get(section_title, 0)
        seen_idx[section_title] = idx + 1
        digest = content_hash(piece)[:12]
        chunk_id = f"{doc_id}::{_slug(section_title)}::{idx}::{digest}"
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
