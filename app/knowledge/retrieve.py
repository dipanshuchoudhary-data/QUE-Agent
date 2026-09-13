"""Load and select QUE product knowledge for the LangGraph knowledge node.

Phase 2: prefer hybrid (dense + BM25 RRF) when ``QUE_RAG_HYBRID`` and a sparse
corpus exist; else dense Chroma; else keyword-match against manifest keywords.
Assemble uses a tiny CORE skeleton (or skips it when ≥2 chunks hit).
Manifest lists every injectable document.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.knowledge.dense import select_dense
from app.knowledge.paths import KNOWLEDGE_ROOT, MANIFEST_PATH
from app.knowledge.store import index_ready

# Keyword fallback uses assemble_selection caps (not full-guide dumps).
_MAX_GUIDES_DEFAULT = 2

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_FALLBACK_GUIDE_IDS = ("lifecycle", "common-workflows", "product-overview")


@dataclass(frozen=True)
class KnowledgeSelection:
    """Selected pack ids and the text block to inject as a system message."""

    pack_ids: list[str]
    content: str
    scores: dict[str, float] = field(default_factory=dict)
    truncated: bool = False
    mode: str = "keyword"  # hybrid | dense | keyword | dense_unavailable_keyword | …
    no_answer: bool = False
    chunk_ids: list[str] = field(default_factory=list)


def selection_to_cache_payload(selection: KnowledgeSelection) -> dict:
    return {
        "pack_ids": list(selection.pack_ids),
        "content": selection.content,
        "scores": dict(selection.scores),
        "truncated": bool(selection.truncated),
        "mode": selection.mode,
        "no_answer": bool(selection.no_answer),
        "chunk_ids": list(selection.chunk_ids),
    }


def selection_from_cache_payload(payload: dict) -> KnowledgeSelection:
    scores_raw = payload.get("scores") or {}
    scores = {str(k): float(v) for k, v in scores_raw.items()} if isinstance(scores_raw, dict) else {}
    return KnowledgeSelection(
        pack_ids=[str(p) for p in (payload.get("pack_ids") or [])],
        content=str(payload.get("content") or ""),
        scores=scores,
        truncated=bool(payload.get("truncated")),
        mode=str(payload.get("mode") or "keyword"),
        no_answer=bool(payload.get("no_answer")),
        chunk_ids=[str(c) for c in (payload.get("chunk_ids") or [])],
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _strip_frontmatter(text: str) -> str:
    """Drop YAML --- ... --- header so the model sees product prose only."""
    return _FRONTMATTER_RE.sub("", text, count=1).strip()


def knowledge_available() -> bool:
    """True when knowledge/manifest.json is present (often gitignored locally)."""
    return MANIFEST_PATH.is_file()


@lru_cache
def _load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        return {"documents": [], "max_guides": _MAX_GUIDES_DEFAULT}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@lru_cache
def _read_pack(relative_path: str) -> str:
    path = KNOWLEDGE_ROOT / relative_path
    raw = path.read_text(encoding="utf-8")
    return _strip_frontmatter(raw)


def clear_knowledge_caches() -> None:
    """Test helper — drop manifest/file caches after fixture edits."""
    _load_manifest.cache_clear()
    _read_pack.cache_clear()


def validate_knowledge_manifest() -> list[str]:
    """Return list of problems (empty = healthy). Used by tests/startup checks."""
    problems: list[str] = []
    if not MANIFEST_PATH.is_file():
        return ["manifest missing (knowledge/ not checked out)"]
    try:
        manifest = _load_manifest()
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest unreadable: {exc}"]

    docs = list(manifest.get("documents") or [])
    if not docs:
        problems.append("manifest has no documents")
    seen: set[str] = set()
    for doc in docs:
        doc_id = str(doc.get("id") or "")
        rel = str(doc.get("path") or "")
        if not doc_id:
            problems.append(f"document missing id: {doc!r}")
            continue
        if doc_id in seen:
            problems.append(f"duplicate id: {doc_id}")
        seen.add(doc_id)
        if not rel:
            problems.append(f"{doc_id}: missing path")
            continue
        path = KNOWLEDGE_ROOT / rel
        if not path.is_file():
            problems.append(f"{doc_id}: file missing at {rel}")
    core = [d for d in docs if str(d.get("id") or "") == "core"]
    if not core:
        problems.append("CORE.md is not listed in the manifest")
    return problems


def _latest_user_text(input_messages: list[dict[str, str]]) -> str:
    for item in reversed(input_messages or []):
        if item.get("role") == "user" and (item.get("content") or "").strip():
            return str(item["content"])
    return ""


def _score_doc(query: str, keywords: list[str]) -> float:
    if not query or not keywords:
        return 0.0
    score = 0.0
    for raw in keywords:
        key = _norm(raw)
        if not key:
            continue
        if key in query:
            # Longer / multi-word phrases beat single tokens.
            words = key.count(" ") + 1
            score += 4.0 * words if words > 1 else 1.0
    return score


def _pick_fallback(guide_docs: list[dict]) -> list[dict]:
    by_id = {str(d.get("id") or ""): d for d in guide_docs}
    for fid in _FALLBACK_GUIDE_IDS:
        if fid in by_id:
            return [by_id[fid]]
    return guide_docs[:1] if guide_docs else []


_SECTION_HEADING_RE = re.compile(r"(?m)^#{1,3}\s+(.+)$")


def _best_section(body: str, query: str) -> str:
    """Pick the heading block that overlaps the query; avoid dumping a 12k file."""
    body = (body or "").strip()
    if not body:
        return ""
    qn = _norm(query)
    matches = list(_SECTION_HEADING_RE.finditer(body))
    if not matches:
        return body[:1200]
    best_i = 0
    best_score = -1.0
    q_words = [w for w in qn.split() if len(w) > 2]
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].casefold()
        score = sum(1.0 for w in q_words if w in block)
        if score > best_score:
            best_score = score
            best_i = i
    start = matches[best_i].start()
    end = matches[best_i + 1].start() if best_i + 1 < len(matches) else len(body)
    return body[start:end].strip()


def _select_keyword(
    input_messages: list[dict[str, str]],
    *,
    query: str | None = None,
    canonical_intent: str | None = None,
    execution_class: str | None = None,
) -> KnowledgeSelection:
    """Pick CORE + up to N keyword-matched guides for this turn."""
    manifest = _load_manifest()
    docs = list(manifest.get("documents") or [])
    max_guides = int(manifest.get("max_guides") or _MAX_GUIDES_DEFAULT)
    query_n = _norm(query if (query or "").strip() else _latest_user_text(input_messages))

    guide_docs = [
        d
        for d in docs
        if not d.get("always") and d.get("retrieve") is not False
    ]
    if canonical_intent:
        matching = [
            d
            for d in guide_docs
            if canonical_intent in [str(i) for i in (d.get("intents") or [])]
        ]
        if matching:
            guide_docs = matching + [d for d in guide_docs if d not in matching]
        exec_l = (execution_class or "").strip()
        if exec_l == "simple_knowledge":
            max_guides = min(max_guides, 1)
        elif exec_l == "complex_knowledge":
            max_guides = min(max_guides, 3)

    scored: list[tuple[float, dict]] = []
    score_map: dict[str, float] = {}
    for doc in guide_docs:
        score = _score_doc(query_n, list(doc.get("keywords") or []))
        if canonical_intent and canonical_intent in [str(i) for i in (doc.get("intents") or [])]:
            score += 8.0
        doc_id = str(doc.get("id") or "")
        if score > 0:
            scored.append((score, doc))
            if doc_id:
                score_map[doc_id] = score
    scored.sort(key=lambda item: (-item[0], str(item[1].get("id") or "")))
    chosen_guides = [doc for _, doc in scored[:max_guides]]

    # No keyword hit → still give one general product guide (not silence).
    if query_n and not chosen_guides:
        chosen_guides = _pick_fallback(guide_docs)
        for doc in chosen_guides:
            score_map[str(doc.get("id") or "")] = 0.0

    from app.knowledge.assemble import assemble_selection
    from app.knowledge.store import RetrievedChunk
    from app.orchestration.intent_catalog import card_for, render_workflow_card

    hits: list[RetrievedChunk] = []
    card = card_for(canonical_intent)
    if card:
        text = render_workflow_card(canonical_intent) or ""
        if text:
            hits.append(
                RetrievedChunk(
                    chunk_id=f"{canonical_intent}::card",
                    doc_id=str(card.get("domain") or canonical_intent or "card"),
                    path=f"intents/{canonical_intent}.json",
                    title=str(canonical_intent),
                    section="workflow",
                    text=text,
                    score=1.0,
                    corpus_version="card",
                    domain=str(card.get("domain") or ""),
                    intents=str(canonical_intent or ""),
                )
            )

    for doc in chosen_guides[:max_guides]:
        rel = str(doc.get("path") or "")
        doc_id = str(doc.get("id") or rel)
        if not rel:
            continue
        try:
            body = _read_pack(rel)
        except OSError:
            continue
        if not body:
            continue
        section = _best_section(body, query_n)
        intents = doc.get("intents") or []
        intents_s = ",".join(str(i) for i in intents) if isinstance(intents, list) else str(intents or "")
        hits.append(
            RetrievedChunk(
                chunk_id=doc_id,
                doc_id=doc_id,
                path=rel,
                title=str(doc.get("title") or doc_id),
                section="",
                text=section or body[:1200],
                score=float(score_map.get(doc_id) or 0.0),
                corpus_version="keyword",
                domain=str(doc.get("domain") or ""),
                intents=intents_s,
            )
        )

    asm = assemble_selection(hits, no_answer=not hits)
    return KnowledgeSelection(
        pack_ids=list(asm.pack_ids),
        content=asm.content,
        scores={**score_map, **asm.scores},
        truncated=asm.truncated,
        mode="keyword",
        no_answer=asm.no_answer,
        chunk_ids=list(asm.chunk_ids),
    )


def select_knowledge(
    input_messages: list[dict[str, str]],
    *,
    query: str | None = None,
    settings: Settings | None = None,
    use_cache: bool = True,
    canonical_intent: str | None = None,
    execution_class: str | None = None,
) -> KnowledgeSelection:
    """Select knowledge for this turn — hybrid/dense RAG when indexed, else keywords.

    Prefer ``query`` (resolved conversational ask) when provided so follow-ups
    like \"yes explain step by step\" retrieve the right packs/chunks.
    ``use_cache`` is the Phase 9 retrieval TTL map (product docs only).
    """
    cfg = settings or get_settings()
    q = (query if (query or "").strip() else _latest_user_text(input_messages)).strip()
    cache_q = q
    if canonical_intent or execution_class:
        cache_q = f"{q}::ci={canonical_intent or ''}::ec={execution_class or ''}"

    if use_cache and q:
        from app.core.que_cache import get_cached_retrieval

        cached = get_cached_retrieval(cache_q, settings=cfg)
        if cached is not None:
            return selection_from_cache_payload(cached)

    selection = _select_knowledge_uncached(
        input_messages,
        query=q or None,
        settings=cfg,
        canonical_intent=canonical_intent,
        execution_class=execution_class,
    )

    if use_cache and q:
        from app.core.que_cache import set_cached_retrieval

        set_cached_retrieval(cache_q, selection_to_cache_payload(selection), settings=cfg)
    return selection


def _select_knowledge_uncached(
    input_messages: list[dict[str, str]],
    *,
    query: str | None,
    settings: Settings,
    canonical_intent: str | None = None,
    execution_class: str | None = None,
) -> KnowledgeSelection:
    cfg = settings
    q = (query or "").strip()

    if cfg.que_rag_enabled and index_ready(cfg):
        selection: KnowledgeSelection | None = None
        try:
            if cfg.que_rag_hybrid:
                from app.knowledge.hybrid import select_hybrid
                from app.knowledge.sparse import sparse_ready

                if sparse_ready(cfg):
                    hybrid = select_hybrid(
                        q,
                        settings=cfg,
                        canonical_intent=canonical_intent,
                        execution_class=execution_class,
                    )
                    if hybrid is not None:
                        selection = KnowledgeSelection(
                            pack_ids=list(hybrid.pack_ids),
                            content=hybrid.content,
                            scores=dict(hybrid.scores),
                            truncated=hybrid.truncated,
                            mode=hybrid.mode,
                            no_answer=hybrid.no_answer,
                            chunk_ids=list(hybrid.chunk_ids),
                        )
            if selection is None:
                dense = select_dense(
                    q,
                    settings=cfg,
                    canonical_intent=canonical_intent,
                    execution_class=execution_class,
                )
                if dense is not None:
                    selection = KnowledgeSelection(
                        pack_ids=list(dense.pack_ids),
                        content=dense.content,
                        scores=dict(dense.scores),
                        truncated=dense.truncated,
                        mode="dense",
                        no_answer=dense.no_answer,
                        chunk_ids=list(dense.chunk_ids),
                    )
        except Exception:  # noqa: BLE001 — never fail the chat turn on RAG errors
            selection = None

        if selection is not None:
            return selection
        if not cfg.que_rag_fallback_keyword:
            return KnowledgeSelection(
                pack_ids=[],
                content=(
                    "PRIVATE REFERENCE: knowledge index unavailable. "
                    "Say you cannot look up product guides right now."
                ),
                mode="dense_unavailable",
                no_answer=True,
            )

    keyword = _select_keyword(
        input_messages,
        query=q or None,
        canonical_intent=canonical_intent,
        execution_class=execution_class,
    )
    if cfg.que_rag_enabled:
        return KnowledgeSelection(
            pack_ids=keyword.pack_ids,
            content=keyword.content,
            scores=keyword.scores,
            truncated=keyword.truncated,
            mode="dense_unavailable_keyword",
            no_answer=keyword.no_answer,
            chunk_ids=list(keyword.chunk_ids),
        )
    return keyword
