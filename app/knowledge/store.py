"""QUE-owned Chroma vector store for knowledge chunks.

Not Quizzer Postgres/Redis — local persistent directory at ``QUE_CHROMA_PATH``.
We pass embeddings ourselves (LangChain OpenAIEmbeddings); Chroma only stores
and searches vectors with cosine distance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import Settings, get_settings
from app.knowledge.chunking import KnowledgeChunk

COLLECTION_NAME = "que_knowledge"
STATE_FILENAME = "index_state.json"


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    path: str
    title: str
    section: str
    text: str
    score: float  # cosine similarity in [0, 1] approx
    corpus_version: str
    domain: str = ""
    intents: str = ""


@dataclass
class IndexState:
    embedding_model: str
    corpus_version: str
    updated_at: str
    documents: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "embedding_model": self.embedding_model,
            "corpus_version": self.corpus_version,
            "updated_at": self.updated_at,
            "documents": self.documents,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndexState:
        return cls(
            embedding_model=str(data.get("embedding_model") or ""),
            corpus_version=str(data.get("corpus_version") or ""),
            updated_at=str(data.get("updated_at") or ""),
            documents=dict(data.get("documents") or {}),
        )


def chroma_path(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    path = Path(cfg.que_chroma_path)
    if not path.is_absolute():
        # Repo root (parent of app/)
        path = Path(__file__).resolve().parents[2] / path
    return path


def state_path(settings: Settings | None = None) -> Path:
    return chroma_path(settings) / STATE_FILENAME


def load_index_state(settings: Settings | None = None) -> IndexState | None:
    path = state_path(settings)
    if not path.is_file():
        return None
    try:
        return IndexState.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None


def save_index_state(state: IndexState, settings: Settings | None = None) -> None:
    root = chroma_path(settings)
    root.mkdir(parents=True, exist_ok=True)
    state_path(settings).write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def index_ready(settings: Settings | None = None) -> bool:
    """True when a non-empty Chroma collection + matching state file exist."""
    cfg = settings or get_settings()
    state = load_index_state(cfg)
    if state is None or not state.documents:
        return False
    if state.embedding_model != cfg.que_embedding_model:
        return False
    root = chroma_path(cfg)
    if not root.is_dir():
        return False
    try:
        client = get_client(cfg)
        collection = client.get_collection(COLLECTION_NAME)
        return collection.count() > 0
    except Exception:  # noqa: BLE001 — missing/corrupt index → keyword fallback
        return False


def get_client(settings: Settings | None = None) -> chromadb.ClientAPI:
    root = chroma_path(settings)
    root.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(root))


def get_or_create_collection(
    client: chromadb.ClientAPI | None = None,
    *,
    settings: Settings | None = None,
) -> Collection:
    cli = client or get_client(settings)
    return cli.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def wipe_collection(settings: Settings | None = None) -> None:
    """Drop the knowledge collection (used when embedding model changes)."""
    client = get_client(settings)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:  # noqa: BLE001
        pass
    get_or_create_collection(client, settings=settings)


def upsert_chunks(
    chunks: list[KnowledgeChunk],
    embeddings: list[list[float]],
    *,
    embedding_model: str,
    settings: Settings | None = None,
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings length mismatch")
    if not chunks:
        return
    collection = get_or_create_collection(settings=settings)
    now = datetime.now(UTC).isoformat()
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "doc_id": c.doc_id,
                "path": c.path,
                "title": c.title,
                "section": c.section,
                "content_hash": c.content_hash,
                "corpus_version": c.corpus_version,
                "embedding_model": embedding_model,
                "char_count": c.char_count,
                "indexed_at": now,
                "domain": c.domain or "",
                "intents": c.intents or "",
            }
            for c in chunks
        ],
    )


def delete_doc_chunks(doc_id: str, *, settings: Settings | None = None) -> int:
    """Retire all chunks for a document id. Returns deleted count (best-effort)."""
    collection = get_or_create_collection(settings=settings)
    existing = collection.get(where={"doc_id": doc_id}, include=[])
    ids = list(existing.get("ids") or [])
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def query_chunks(
    query_embedding: list[float],
    *,
    top_k: int,
    settings: Settings | None = None,
) -> list[RetrievedChunk]:
    collection = get_or_create_collection(settings=settings)
    if collection.count() == 0:
        return []
    n = min(max(top_k * 2, top_k + 4), collection.count())
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    out: list[RetrievedChunk] = []
    for chunk_id, text, meta, distance in zip(ids, docs, metas, distances, strict=False):
        meta = meta or {}
        # Chroma cosine space: distance ≈ 1 - cosine_similarity for normalized vectors.
        try:
            dist = float(distance)
        except (TypeError, ValueError):
            dist = 1.0
        score = max(0.0, min(1.0, 1.0 - dist))
        out.append(
            RetrievedChunk(
                chunk_id=str(chunk_id),
                doc_id=str(meta.get("doc_id") or ""),
                path=str(meta.get("path") or ""),
                title=str(meta.get("title") or ""),
                section=str(meta.get("section") or ""),
                text=str(text or ""),
                score=score,
                corpus_version=str(meta.get("corpus_version") or ""),
                domain=str(meta.get("domain") or ""),
                intents=str(meta.get("intents") or ""),
            )
        )
    return [h for h in out if h.doc_id != "core"][: max(top_k, 1)]
