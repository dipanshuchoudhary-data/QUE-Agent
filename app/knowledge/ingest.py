"""Ingest knowledge packs into Chroma: parse → chunk → embed → upsert.

Incremental: only re-embed documents whose content hash changed; delete
retired docs; wipe + rebuild when the embedding model version changes.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings, get_settings
from app.knowledge.chunking import KnowledgeChunk, chunk_markdown, content_hash, strip_frontmatter
from app.knowledge.embeddings import EmbeddingsClient, get_embeddings
from app.knowledge.paths import KNOWLEDGE_ROOT, MANIFEST_PATH
from app.knowledge.sparse import SparseCorpusEntry, save_bm25_corpus
from app.knowledge.store import (
    IndexState,
    delete_doc_chunks,
    load_index_state,
    save_index_state,
    upsert_chunks,
    wipe_collection,
)

logger = logging.getLogger(__name__)

_EMBED_BATCH = 32


@dataclass(frozen=True)
class IngestReport:
    corpus_version: str
    embedding_model: str
    docs_total: int
    docs_unchanged: int
    docs_upserted: int
    docs_deleted: int
    chunks_upserted: int
    rebuilt: bool


def _load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"knowledge manifest missing: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _doc_file_hash(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    # Hash stripped body so frontmatter-only edits don't force re-embed unless prose changes.
    return content_hash(strip_frontmatter(raw))


def _chunk_doc(doc: dict, *, corpus_version: str) -> list[KnowledgeChunk]:
    doc_id = str(doc.get("id") or "")
    rel = str(doc.get("path") or "")
    title = str(doc.get("title") or doc_id)
    if not doc_id or not rel:
        return []
    path = KNOWLEDGE_ROOT / rel
    raw = path.read_text(encoding="utf-8")
    intents = doc.get("intents") or []
    if isinstance(intents, list):
        intents_s = ",".join(str(i) for i in intents)
    else:
        intents_s = str(intents or "")
    return chunk_markdown(
        doc_id=doc_id,
        path=rel,
        title=title,
        raw_markdown=raw,
        corpus_version=corpus_version,
        domain=str(doc.get("domain") or ""),
        intents=intents_s,
    )


def _is_retrievable(doc: dict) -> bool:
    if doc.get("retrieve") is False:
        return False
    if doc.get("always"):
        return False
    return True


def _embed_batches(
    texts: Sequence[str],
    embeddings: EmbeddingsClient,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    for i in range(0, len(texts), _EMBED_BATCH):
        batch = list(texts[i : i + _EMBED_BATCH])
        vectors.extend(embeddings.embed_documents(batch))
    return vectors


def build_index(
    *,
    settings: Settings | None = None,
    embeddings: EmbeddingsClient | None = None,
    force: bool = False,
) -> IngestReport:
    """Build or incrementally update the QUE knowledge vector index."""
    cfg = settings or get_settings()
    manifest = _load_manifest()
    corpus_version = str(manifest.get("version") or "0")
    docs = list(manifest.get("documents") or [])
    embed_model = cfg.que_embedding_model
    emb = embeddings or get_embeddings(settings=cfg)

    prior = load_index_state(cfg)
    rebuilt = False
    if force or (prior and prior.embedding_model and prior.embedding_model != embed_model):
        logger.info(
            "rag_index_rebuild",
            extra={
                "reason": "force" if force else "embedding_model_changed",
                "old_model": prior.embedding_model if prior else None,
                "new_model": embed_model,
            },
        )
        wipe_collection(cfg)
        prior = None
        rebuilt = True

    prior_docs = dict(prior.documents) if prior else {}
    active_ids: set[str] = set()
    unchanged = 0
    upserted_docs = 0
    chunks_written = 0
    deleted = 0

    for doc in docs:
        doc_id = str(doc.get("id") or "")
        rel = str(doc.get("path") or "")
        if not doc_id or not rel:
            continue
        path = KNOWLEDGE_ROOT / rel
        if not path.is_file():
            logger.warning("rag_skip_missing_file", extra={"doc_id": doc_id, "path": rel})
            continue
        if not _is_retrievable(doc):
            deleted_core = delete_doc_chunks(doc_id, settings=cfg)
            prior_docs.pop(doc_id, None)
            if deleted_core:
                deleted += deleted_core
            continue
        active_ids.add(doc_id)
        file_hash = _doc_file_hash(path)
        prev = prior_docs.get(doc_id) or {}
        if (
            not force
            and prev.get("content_hash") == file_hash
            and prev.get("corpus_version") == corpus_version
            and int(prev.get("chunk_count") or 0) > 0
        ):
            unchanged += 1
            continue

        chunks = _chunk_doc(doc, corpus_version=corpus_version)
        if not chunks:
            delete_doc_chunks(doc_id, settings=cfg)
            prior_docs.pop(doc_id, None)
            continue

        # Retire old chunk ids for this doc before upsert (ids may change).
        delete_doc_chunks(doc_id, settings=cfg)
        vectors = _embed_batches([c.text for c in chunks], emb)
        upsert_chunks(chunks, vectors, embedding_model=embed_model, settings=cfg)
        prior_docs[doc_id] = {
            "content_hash": file_hash,
            "path": rel,
            "title": str(doc.get("title") or doc_id),
            "chunk_count": len(chunks),
            "corpus_version": corpus_version,
            "always": bool(doc.get("always")),
        }
        upserted_docs += 1
        chunks_written += len(chunks)

    for stale_id in list(prior_docs.keys()):
        if stale_id not in active_ids:
            deleted += delete_doc_chunks(stale_id, settings=cfg)
            prior_docs.pop(stale_id, None)

    state = IndexState(
        embedding_model=embed_model,
        corpus_version=corpus_version,
        updated_at=datetime.now(UTC).isoformat(),
        documents=prior_docs,
    )
    save_index_state(state, cfg)

    # Sparse sidecar — always rewrite from active docs so BM25 matches Chroma.
    _write_bm25_corpus(docs, active_ids=active_ids, corpus_version=corpus_version, settings=cfg)

    report = IngestReport(
        corpus_version=corpus_version,
        embedding_model=embed_model,
        docs_total=len(active_ids),
        docs_unchanged=unchanged,
        docs_upserted=upserted_docs,
        docs_deleted=deleted,
        chunks_upserted=chunks_written,
        rebuilt=rebuilt,
    )
    logger.info("rag_index_built", extra=report.__dict__)
    return report


def _write_bm25_corpus(
    docs: list[dict],
    *,
    active_ids: set[str],
    corpus_version: str,
    settings: Settings,
) -> None:
    entries: list[SparseCorpusEntry] = []
    for doc in docs:
        doc_id = str(doc.get("id") or "")
        if doc_id not in active_ids:
            continue
        chunks = _chunk_doc(doc, corpus_version=corpus_version)
        for c in chunks:
            entries.append(
                SparseCorpusEntry(
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    path=c.path,
                    title=c.title,
                    section=c.section,
                    text=c.text,
                    corpus_version=c.corpus_version,
                    domain=c.domain,
                    intents=c.intents,
                )
            )
    save_bm25_corpus(entries, settings=settings, corpus_version=corpus_version)
    logger.info("rag_bm25_corpus_written", extra={"chunks": len(entries)})
