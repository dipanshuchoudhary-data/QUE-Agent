"""Hybrid retrieval: dense Chroma + BM25 fused with reciprocal rank fusion (RRF).

Phase 6 — evidence: dense miss clusters were complementary to lexical hits
(e.g. terminology / exam-settings). Neural cross-encoder rerank is deferred.
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
    exec_l = (execution_class or "").strip()
    if exec_l == "simple_knowledge":
        return 1
    if exec_l == "complex_knowledge":
        return max(default_k, 2)
    return max(1, default_k)


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


def select_hybrid(
    query: str,
    *,
    settings: Settings | None = None,
    embeddings: EmbeddingsClient | None = None,
    query_vector: list[float] | None = None,
    canonical_intent: str | None = None,
    execution_class: str | None = None,
) -> HybridSelection | None:
    """Dense + BM25 → RRF → unique-doc top-K. Returns None if dense index unavailable."""
    cfg = settings or get_settings()
    if not cfg.que_rag_enabled or not index_ready(cfg):
        return None

    q = (query or "").strip()
    if not q:
        asm = assemble_selection([], no_answer=True)
        return _from_assembled(asm, mode="hybrid")

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
        fused = reciprocal_rank_fusion(
            [dense_hits, sparse_hits],
            rrf_k=int(cfg.que_rag_rrf_k),
        )
        mode = "hybrid"
    else:
        fused = dense_hits
        mode = "dense"

    fused = prefer_canonical_intent(fused, canonical_intent)
    fused = unique_by_doc_id(fused)
    top = fused[:take]

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
    if no_answer:
        asm = assemble_selection(top, no_answer=True, score_label="rrf")
        return _from_assembled(asm, mode=mode)

    asm = assemble_selection(top, no_answer=False, score_label="rrf" if sparse_hits else "score")
    return _from_assembled(asm, mode=mode)
