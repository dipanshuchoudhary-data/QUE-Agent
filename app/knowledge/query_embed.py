"""Turn-local cache so semantic routing and RAG share one query embedding."""

from __future__ import annotations

import threading
from collections import OrderedDict

from app.core.config import Settings, get_settings
from app.knowledge.embeddings import EmbeddingsClient, get_embeddings

_lock = threading.Lock()
_cache: OrderedDict[str, list[float]] = OrderedDict()
_MAX = 64


def reset_query_embed_cache() -> None:
    global _cache
    with _lock:
        _cache = OrderedDict()


def embed_query_cached(
    query: str,
    *,
    settings: Settings | None = None,
    embeddings: EmbeddingsClient | None = None,
) -> list[float]:
    q = (query or "").strip()
    cfg = settings or get_settings()
    key = f"{cfg.que_embedding_model}::{q}"
    with _lock:
        hit = _cache.get(key)
        if hit is not None:
            _cache.move_to_end(key)
            return list(hit)
    emb = embeddings or get_embeddings(settings=cfg)
    vec = list(emb.embed_query(q))
    with _lock:
        _cache[key] = vec
        _cache.move_to_end(key)
        while len(_cache) > _MAX:
            _cache.popitem(last=False)
    return vec
