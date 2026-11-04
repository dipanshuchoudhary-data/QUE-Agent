"""Hybrid retrieval: dense Chroma + BM25 fused with reciprocal rank fusion (RRF).

Phase 6 — evidence: dense miss clusters were complementary to lexical hits
(e.g. terminology / exam-settings). When ``QUE_RAG_RERANK_ENABLED`` is on, the
fused candidate pool is reordered by the configured cross-encoder before top-k.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import Settings, get_settings
from app.knowledge.assemble import AssembledKnowledge, assemble_selection
from app.knowledge.embeddings import EmbeddingsClient
from app.knowledge.sparse import query_bm25, sparse_ready
from app.knowledge.store import RetrievedChunk, index_ready, query_chunks


@dataclass(frozen=True)
class HybridSelection:
    pack_ids: list[str]
    content: str
    scores: dict[str, float] = field(default_factory=dict)
    chunk_ids: list[str] = field(default_factory=list)
    truncated: bool = False
    no_answer: bool = False
    hits: list[RetrievedChunk] = field(default_factory=list)
    mode: str = "hybrid"


def unique_by_doc_id(hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep the first (highest-ranked) chunk per document."""
    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for hit in hits:
        doc = hit.doc_id or hit.chunk_id
        if not doc or doc in seen or doc == "core":
            continue
        seen.add(doc)
        out.append(hit)
    return out


def prefer_canonical_intent(
    hits: list[RetrievedChunk],
    canonical_intent: str | None,
) -> list[RetrievedChunk]:
    intent = (canonical_intent or "").strip()
    if not intent or not hits:
        return hits
    matched: list[RetrievedChunk] = []
    rest: list[RetrievedChunk] = []
    for hit in hits:
        intents = {p.strip() for p in (hit.intents or "").split(",") if p.strip()}
        if intent in intents:
            matched.append(hit)
        else:
            rest.append(hit)
    return matched + rest if matched else hits


def top_k_for_execution(execution_class: str | None, default_k: int) -> int:
    """One top-k (``QUE_RAG_TOP_K``) for every route; no per-route override."""
    return max(1, default_k)


def fuse_by_document(
    ranked_lists: list[list[RetrievedChunk]],
    *,
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    """RRF over document ranks. The first list is the dense ranking.

    Chunk-level RRF misses a guide when its best dense section and its best
    BM25 section are different chunk ids. Selection keeps one chunk per
    document, so scores add up on ``doc_id``. The text injected into the
    prompt is the dense section when that document was in the dense list.
    """
    scores: dict[str, float] = {}
    dense_chunk: dict[str, RetrievedChunk] = {}
    fallback_chunk: dict[str, RetrievedChunk] = {}
    for list_index, hits in enumerate(ranked_lists):
        for rank, hit in enumerate(unique_by_doc_id(hits), start=1):
            doc = hit.doc_id or hit.chunk_id
            if not doc or doc == "core":
                continue
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (rrf_k + rank)
            if list_index == 0:
                dense_chunk.setdefault(doc, hit)
            else:
                fallback_chunk.setdefault(doc, hit)
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    out: list[RetrievedChunk] = []
    for doc, rrf_score in ordered:
        base = dense_chunk.get(doc) or fallback_chunk[doc]
        out.append(
            RetrievedChunk(
                chunk_id=base.chunk_id,
                doc_id=base.doc_id,
                path=base.path,
                title=base.title,
                section=base.section,
                text=base.text,
                score=float(rrf_score),
                corpus_version=base.corpus_version,
                domain=base.domain,
                intents=base.intents,
            )
        )
    return out


def pin_dense_leader(
    top: list[RetrievedChunk],
    dense_hits: list[RetrievedChunk],
    *,
    min_score: float,
) -> list[RetrievedChunk]:
    """Keep the best dense guide inside the result window.

    Document fusion prefers a guide both retrievers mention. That can evict
    the dense rank-1 guide from a two-slot window when BM25 never retrieved
    it. The dense leader stays when its cosine score clears the floor.
    """
    if not top:
        return top
    leaders = [
        hit
        for hit in unique_by_doc_id(dense_hits)
        if hit.doc_id and hit.doc_id != "core"
    ]
    if not leaders or leaders[0].score < min_score:
        return top
    leader = leaders[0]
    if any(hit.doc_id == leader.doc_id for hit in top):
        return top
    if len(top) == 1:
        return [leader]
    return [*top[:-1], leader]


def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievedChunk]],
    *,
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    """Classic RRF: score = Σ 1/(rrf_k + rank). Rank is 1-based within each list."""
    fused: dict[str, float] = {}
    by_id: dict[str, RetrievedChunk] = {}
    for hits in ranked_lists:
        for rank, hit in enumerate(hits, start=1):
            cid = hit.chunk_id
            if not cid:
                continue
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (rrf_k + rank)
            # Prefer the first-seen chunk body; keep max provenance score for labels.
            prior = by_id.get(cid)
            if prior is None or hit.score > prior.score:
                by_id[cid] = hit
    ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))
    out: list[RetrievedChunk] = []
    for cid, rrf_score in ordered:
        base = by_id[cid]
        out.append(
            RetrievedChunk(
                chunk_id=base.chunk_id,
                doc_id=base.doc_id,
                path=base.path,
                title=base.title,
                section=base.section,
                text=base.text,
                score=float(rrf_score),
                corpus_version=base.corpus_version,
                domain=base.domain,
                intents=base.intents,
            )
        )
    return out


def _brief(hits: list[RetrievedChunk]) -> list[dict]:
    """Small, loggable view of a hit list (no chunk text)."""
    return [
        {
            "chunk_id": h.chunk_id,
            "doc_id": h.doc_id,
            "section": h.section,
            "score": round(float(h.score), 4),
        }
        for h in hits
    ]


def _rerank_pool(
    query: str,
    pool: list[RetrievedChunk],
    *,
    settings: Settings,
    trace: dict | None = None,
) -> list[RetrievedChunk]:
    """Reorder the candidate pool. On failure, keep the fused order."""
    if len(pool) <= 1:
        if trace is not None:
            trace["rerank"] = "skipped"
        return pool
    from app.knowledge.rerank import RerankError, rerank_chunks

    try:
        ordered = rerank_chunks(query, pool, settings=settings, top_n=len(pool))
    except RerankError:
        if trace is not None:
            trace["rerank"] = "failed"
        return pool
    if trace is not None:
        trace["rerank"] = "ok"
    return ordered


def _from_assembled(asm: AssembledKnowledge, *, mode: str = "hybrid") -> HybridSelection:
    return HybridSelection(
        pack_ids=list(asm.pack_ids),
        content=asm.content,
        scores=dict(asm.scores),
        chunk_ids=list(asm.chunk_ids),
        truncated=asm.truncated,
        no_answer=asm.no_answer,
        hits=list(asm.hits),
        mode=mode,
    )


def _expand_neighbors(top: list[RetrievedChunk], n: int, cfg: Settings) -> list[RetrievedChunk]:
    """Add up to ``n`` chunks that follow the leader inside the same document section."""
    from dataclasses import replace

    from app.knowledge.sparse import load_bm25_corpus

    try:
        corpus = load_bm25_corpus(cfg)
    except Exception:  # noqa: BLE001 - expansion is optional
        return top
    lead = top[0]
    pos = next((i for i, e in enumerate(corpus) if e.chunk_id == lead.chunk_id), None)
    if pos is None:
        return top
    have = {h.chunk_id for h in top}
    extra: list[RetrievedChunk] = []
    for e in corpus[pos + 1 :]:
        if len(extra) >= n or e.doc_id != lead.doc_id or e.section != lead.section:
            break
        if e.chunk_id in have:
            continue
        extra.append(
            replace(lead, chunk_id=e.chunk_id, text=e.text, score=lead.score * 0.99)
        )
    return [lead, *extra, *top[1:]]


def select_hybrid(
    query: str,
    *,
    settings: Settings | None = None,
    embeddings: EmbeddingsClient | None = None,
    query_vector: list[float] | None = None,
    canonical_intent: str | None = None,
    execution_class: str | None = None,
    trace: dict | None = None,
) -> HybridSelection | None:
    """Dense + BM25 → RRF → unique-doc top-K. Returns None if dense index unavailable.

    ``trace`` is an optional dict filled with candidate lists and rerank status for
    diagnostics. It never changes the result.
    """
    cfg = settings or get_settings()
    if not cfg.que_rag_enabled or not index_ready(cfg):
        return None

    q = (query or "").strip()
    if not q:
        asm = assemble_selection([], no_answer=True)
        return _from_assembled(asm, mode="hybrid")

    if cfg.que_rag_query_normalize:
        from app.knowledge.query_normalize import normalize_for_retrieval

        q = normalize_for_retrieval(q) or q
    take = top_k_for_execution(execution_class, int(cfg.que_rag_top_k))
    candidate_k = max(int(cfg.que_rag_candidate_k), take)
    if query_vector is not None:
        vector = query_vector
    else:
        from app.knowledge.query_embed import embed_query_cached

        vector = embed_query_cached(q, settings=cfg, embeddings=embeddings)
    dense_hits = query_chunks(vector, top_k=candidate_k, settings=cfg)

    sparse_hits: list[RetrievedChunk] = []
    if sparse_ready(cfg):
        sparse_hits = query_bm25(q, top_k=candidate_k, settings=cfg)
        sparse_hits = [h for h in sparse_hits if h.doc_id != "core"]

    if sparse_hits:
        # Chunk-level RRF over both lists, then one pool of ``candidate_k`` chunks in
        # total (not candidate_k from each retriever). Several chunks of the same guide
        # may stay in the pool; top-k then counts chunks.
        fused = [
            h
            for h in reciprocal_rank_fusion(
                [dense_hits, sparse_hits],
                rrf_k=int(cfg.que_rag_rrf_k),
            )
            if h.doc_id != "core"
        ][:candidate_k]
        mode = "hybrid"
    else:
        fused = [h for h in dense_hits if h.doc_id != "core"][:candidate_k]
        mode = "dense"

    fused = prefer_canonical_intent(fused, canonical_intent)
    if trace is not None:
        trace["dense"] = _brief(dense_hits)
        trace["sparse"] = _brief(sparse_hits)
        trace["fused"] = _brief(fused)
        trace["take"] = take
        trace["candidate_k"] = candidate_k
        trace["rerank"] = "off"
    if cfg.que_rag_rerank_enabled:
        pool = pin_dense_leader(
            fused[:candidate_k],
            dense_hits,
            min_score=float(cfg.que_rag_min_score),
        )
        rr_trace = trace if trace is not None else {}
        reranked = _rerank_pool(q, pool, settings=cfg, trace=rr_trace)
        top = reranked[:take]
        ratio = float(cfg.que_rag_dynamic_k_ratio)
        if ratio > 0 and top and rr_trace.get("rerank") == "ok":
            best = top[0].score
            top = [h for i, h in enumerate(top) if i == 0 or h.score >= ratio * best]
    else:
        top = pin_dense_leader(
            fused[:take],
            dense_hits,
            min_score=float(cfg.que_rag_min_score),
        )

    if int(cfg.que_rag_neighbor_expand) > 0 and top:
        top = _expand_neighbors(top, int(cfg.que_rag_neighbor_expand), cfg)

    # Honest no-answer stays dense-gated: BM25 alone must not invent product
    # packs for out-of-domain asks (e.g. weather). Sparse still enriches recall
    # when at least one fused top hit also clears the dense cosine floor.
    dense_by_id = {h.chunk_id: h for h in dense_hits}
    dense_ok = any(
        (dense_by_id[h.chunk_id].score >= cfg.que_rag_min_score)
        for h in top
        if h.chunk_id in dense_by_id
    )
    # If fusion demoted all dense hits below top-K, still accept when any dense
    # candidate clears the floor (sparse-only top would otherwise starve).
    if not dense_ok:
        dense_ok = any(h.score >= cfg.que_rag_min_score for h in dense_hits)

    no_answer = not dense_ok
    if trace is not None:
        trace["final"] = _brief(top)
        trace["no_answer"] = no_answer
    if no_answer:
        asm = assemble_selection(top, no_answer=True, score_label="rrf")
        return _from_assembled(asm, mode=mode)

    asm = assemble_selection(top, no_answer=False, score_label="rrf" if sparse_hits else "score")
    return _from_assembled(asm, mode=mode)
