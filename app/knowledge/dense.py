"""Dense retrieval using shared assembly (Phase 2 path)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import Settings, get_settings
from app.knowledge.assemble import AssembledKnowledge, assemble_selection
from app.knowledge.embeddings import EmbeddingsClient, get_embeddings
from app.knowledge.store import RetrievedChunk, index_ready, query_chunks


@dataclass(frozen=True)
class DenseSelection:
    pack_ids: list[str]
    content: str
    scores: dict[str, float] = field(default_factory=dict)
    chunk_ids: list[str] = field(default_factory=list)
    truncated: bool = False
    no_answer: bool = False
    hits: list[RetrievedChunk] = field(default_factory=list)


def _from_assembled(asm: AssembledKnowledge) -> DenseSelection:
    return DenseSelection(
        pack_ids=list(asm.pack_ids),
        content=asm.content,
        scores=dict(asm.scores),
        chunk_ids=list(asm.chunk_ids),
        truncated=asm.truncated,
        no_answer=asm.no_answer,
        hits=list(asm.hits),
    )


def select_dense(
    query: str,
    *,
    settings: Settings | None = None,
    embeddings: EmbeddingsClient | None = None,
    canonical_intent: str | None = None,
    execution_class: str | None = None,
) -> DenseSelection | None:
    """Retrieve top-K chunks. Returns None if the index is unavailable."""
    cfg = settings or get_settings()
    if not cfg.que_rag_enabled or not index_ready(cfg):
        return None

    q = (query or "").strip()
    if not q:
        asm = assemble_selection([], no_answer=True)
        return _from_assembled(asm)

    emb = embeddings or get_embeddings(settings=cfg)
    from app.knowledge.hybrid import prefer_canonical_intent, top_k_for_execution, unique_by_doc_id
    from app.knowledge.query_embed import embed_query_cached

    take = top_k_for_execution(execution_class, int(cfg.que_rag_top_k))
    vector = embed_query_cached(q, settings=cfg, embeddings=emb)
    hits = query_chunks(vector, top_k=max(take * 3, int(cfg.que_rag_top_k)), settings=cfg)
    hits = prefer_canonical_intent(hits, canonical_intent)
    hits = unique_by_doc_id(hits)
    kept = [h for h in hits if h.score >= cfg.que_rag_min_score][:take]
    no_answer = not kept
    asm = assemble_selection(kept if kept else hits, no_answer=no_answer, score_label="score")
    return _from_assembled(asm)
