"""Sparse (BM25) retrieval over the QUE knowledge chunk corpus.

Corpus is a JSON sidecar next to Chroma (`bm25_corpus.json`), written during
ingest so sparse search stays aligned with dense vectors without extra embeds.
"""

from __future__ import annotations

import json
import math
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.core.config import Settings, get_settings
from app.knowledge.store import RetrievedChunk, chroma_path

CORPUS_FILENAME = "bm25_corpus.json"
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass(frozen=True)
class SparseCorpusEntry:
    chunk_id: str
    doc_id: str
    path: str
    title: str
    section: str
    text: str
    corpus_version: str
    domain: str = ""
    intents: str = ""


@dataclass
class _Bm25Index:
    entries: list[SparseCorpusEntry]
    bm25: BM25Okapi
    corpus_mtime_ns: int


_lock = threading.Lock()
_cached: _Bm25Index | None = None
_cached_path: str | None = None


def bm25_corpus_path(settings: Settings | None = None) -> Path:
    return chroma_path(settings) / CORPUS_FILENAME


def tokenize(text: str) -> list[str]:
    return [t.casefold() for t in _TOKEN_RE.findall(text or "")]


def _lucene_idf_bm25(tokenized_corpus: list[list[str]]) -> BM25Okapi:
    """BM25Okapi with Lucene-style IDF so tiny corpora still score > 0.

    Classic Okapi IDF is ``log((N-n+0.5)/(n+0.5))``, which is **0** when a term
    appears in exactly half the docs (e.g. 1 of 2) — useless for unit tests and
    small packs. Lucene uses ``log(1 + (N-n+0.5)/(n+0.5))``.
    """
    from collections import Counter

    bm25 = BM25Okapi(tokenized_corpus)
    df: Counter[str] = Counter()
    for doc in tokenized_corpus:
        for word in set(doc):
            df[word] += 1
    n_docs = max(1, len(tokenized_corpus))
    for word, freq in df.items():
        bm25.idf[word] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))
    return bm25


def save_bm25_corpus(
    entries: list[SparseCorpusEntry] | list[dict],
    *,
    settings: Settings | None = None,
    corpus_version: str = "",
) -> Path:
    """Write the full sparse corpus (call after ingest upserts/deletes)."""
    path = bm25_corpus_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for item in entries:
        if isinstance(item, SparseCorpusEntry):
            rows.append(
                {
                    "chunk_id": item.chunk_id,
                    "doc_id": item.doc_id,
                    "path": item.path,
                    "title": item.title,
                    "section": item.section,
                    "text": item.text,
                    "corpus_version": item.corpus_version,
                }
            )
        else:
            rows.append(
                {
                    "chunk_id": str(item.get("chunk_id") or ""),
                    "doc_id": str(item.get("doc_id") or ""),
                    "path": str(item.get("path") or ""),
                    "title": str(item.get("title") or ""),
                    "section": str(item.get("section") or ""),
                    "text": str(item.get("text") or ""),
                    "corpus_version": str(item.get("corpus_version") or corpus_version),
                }
            )
    payload = {
        "version": 1,
        "corpus_version": corpus_version or (rows[0]["corpus_version"] if rows else ""),
        "chunks": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    clear_sparse_cache()
    return path


def load_bm25_corpus(settings: Settings | None = None) -> list[SparseCorpusEntry]:
    path = bm25_corpus_path(settings)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out: list[SparseCorpusEntry] = []
    for row in list(data.get("chunks") or []):
        chunk_id = str(row.get("chunk_id") or "")
        text = str(row.get("text") or "")
        if not chunk_id or not text.strip():
            continue
        out.append(
            SparseCorpusEntry(
                chunk_id=chunk_id,
                doc_id=str(row.get("doc_id") or ""),
                path=str(row.get("path") or ""),
                title=str(row.get("title") or ""),
                section=str(row.get("section") or ""),
                text=text,
                corpus_version=str(row.get("corpus_version") or ""),
            )
        )
    return out


def sparse_ready(settings: Settings | None = None) -> bool:
    path = bm25_corpus_path(settings)
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("chunks"))


def clear_sparse_cache() -> None:
    global _cached, _cached_path
    with _lock:
        _cached = None
        _cached_path = None


def _get_index(settings: Settings | None = None) -> _Bm25Index | None:
    global _cached, _cached_path
    cfg = settings or get_settings()
    path = bm25_corpus_path(cfg)
    if not path.is_file():
        return None
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None

    with _lock:
        if (
            _cached is not None
            and _cached_path == str(path)
            and _cached.corpus_mtime_ns == mtime_ns
        ):
            return _cached

    entries = load_bm25_corpus(cfg)
    if not entries:
        return None
    tokenized = [tokenize(e.text) for e in entries]
    # BM25Okapi needs at least one non-empty doc; pad empty token lists.
    tokenized = [toks or ["_"] for toks in tokenized]
    index = _Bm25Index(
        entries=entries,
        bm25=_lucene_idf_bm25(tokenized),
        corpus_mtime_ns=mtime_ns,
    )
    with _lock:
        _cached = index
        _cached_path = str(path)
    return index


def query_bm25(
    query: str,
    *,
    top_k: int,
    settings: Settings | None = None,
) -> list[RetrievedChunk]:
    """Return top-K BM25 hits as RetrievedChunk (score = raw BM25)."""
    q = (query or "").strip()
    if not q or top_k <= 0:
        return []
    index = _get_index(settings)
    if index is None:
        return []
    tokens = tokenize(q)
    if not tokens:
        return []
    scores = index.bm25.get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda item: (-float(item[1]), item[0]))
    out: list[RetrievedChunk] = []
    for idx, score in ranked[:top_k]:
        if float(score) <= 0:
            break
        entry = index.entries[idx]
        out.append(
            RetrievedChunk(
                chunk_id=entry.chunk_id,
                doc_id=entry.doc_id,
                path=entry.path,
                title=entry.title,
                section=entry.section,
                text=entry.text,
        score=float(score),
                corpus_version=entry.corpus_version,
                domain=getattr(entry, "domain", "") or "",
                intents=getattr(entry, "intents", "") or "",
            )
        )
    return out
