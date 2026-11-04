"""QUE-local response/intent cache — not Quizzer Redis.

Process-memory TTL + LRU. Safe for a single QUE worker; each worker has its
own map. Optional Redis can be added later under QUE_* env vars only.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class CacheEntry:
    value: Any
    expires_at: float


class QueTtlLruCache:
    """Thread-safe in-process cache owned by QUE-Agent."""

    def __init__(self, *, max_entries: int = 512, default_ttl_seconds: float = 900.0) -> None:
        self._max = max(16, max_entries)
        self._default_ttl = max(1.0, default_ttl_seconds)
        self._data: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any, *, ttl_seconds: float | None = None) -> None:
        ttl = self._default_ttl if ttl_seconds is None else max(1.0, ttl_seconds)
        expires = time.monotonic() + ttl
        with self._lock:
            self._data[key] = CacheEntry(value=value, expires_at=expires)
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)


_intent_cache: QueTtlLruCache | None = None
_llm_cache: QueTtlLruCache | None = None
_variant_cache: QueTtlLruCache | None = None
_retrieval_cache: QueTtlLruCache | None = None
_init_lock = threading.Lock()

_CacheBundle = tuple[QueTtlLruCache, QueTtlLruCache, QueTtlLruCache, QueTtlLruCache]


def _build_caches(settings: Settings) -> _CacheBundle:
    max_entries = settings.que_cache_max_entries
    return (
        QueTtlLruCache(max_entries=max_entries, default_ttl_seconds=settings.que_cache_intent_ttl_seconds),
        QueTtlLruCache(max_entries=max_entries, default_ttl_seconds=settings.que_cache_llm_ttl_seconds),
        QueTtlLruCache(max_entries=max_entries, default_ttl_seconds=settings.que_cache_variant_ttl_seconds),
        QueTtlLruCache(
            max_entries=max_entries,
            default_ttl_seconds=settings.que_cache_retrieval_ttl_seconds,
        ),
    )


def reset_que_caches(*, settings: Settings | None = None) -> None:
    """Drop process caches (tests / config reload)."""
    global _intent_cache, _llm_cache, _variant_cache, _retrieval_cache
    with _init_lock:
        if settings is None:
            _intent_cache = None
            _llm_cache = None
            _variant_cache = None
            _retrieval_cache = None
            return
        _intent_cache, _llm_cache, _variant_cache, _retrieval_cache = _build_caches(settings)


def _caches() -> _CacheBundle | None:
    global _intent_cache, _llm_cache, _variant_cache, _retrieval_cache
    cfg = get_settings()
    if not cfg.que_cache_enabled:
        return None
    with _init_lock:
        if (
            _intent_cache is None
            or _llm_cache is None
            or _variant_cache is None
            or _retrieval_cache is None
        ):
            _intent_cache, _llm_cache, _variant_cache, _retrieval_cache = _build_caches(cfg)
        return _intent_cache, _llm_cache, _variant_cache, _retrieval_cache


def cache_key(*parts: str) -> str:
    raw = "\u241f".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_intent(squashed_query: str) -> str | None:
    caches = _caches()
    if not caches:
        return None
    intent_cache, _, _, _ = caches
    value = intent_cache.get(cache_key("intent", squashed_query))
    return value if isinstance(value, str) else None


def set_cached_intent(squashed_query: str, intent: str) -> None:
    caches = _caches()
    if not caches:
        return
    intent_cache, _, _, _ = caches
    intent_cache.set(cache_key("intent", squashed_query), intent)


def get_last_canned_variant(conversation_id: str | None, intent: str) -> str | None:
    caches = _caches()
    if not caches:
        return None
    _, _, variant_cache, _ = caches
    scope = conversation_id or "anon"
    value = variant_cache.get(cache_key("variant", scope, intent))
    return value if isinstance(value, str) else None


def set_last_canned_variant(conversation_id: str | None, intent: str, text: str) -> None:
    caches = _caches()
    if not caches:
        return
    _, _, variant_cache, _ = caches
    scope = conversation_id or "anon"
    variant_cache.set(cache_key("variant", scope, intent), text)


def get_cached_llm_reply(history_fingerprint: str) -> dict[str, Any] | None:
    """Return ``{content, model, knowledge_packs?}`` for a prior LLM answer."""
    caches = _caches()
    if not caches:
        return None
    _, llm_cache, _, _ = caches
    value = llm_cache.get(cache_key("llm", history_fingerprint))
    if isinstance(value, dict) and isinstance(value.get("content"), str):
        return value
    return None


def set_cached_llm_reply(
    history_fingerprint: str,
    *,
    content: str,
    model: str,
    knowledge_packs: list[str] | None = None,
) -> None:
    caches = _caches()
    if not caches:
        return
    _, llm_cache, _, _ = caches
    payload: dict[str, Any] = {"content": content, "model": model}
    if knowledge_packs:
        payload["knowledge_packs"] = list(knowledge_packs)
    llm_cache.set(cache_key("llm", history_fingerprint), payload)


def _retrieval_mode_tag(settings: Settings) -> str:
    return (
        f"rag={int(settings.que_rag_enabled)}"
        f":hybrid={int(settings.que_rag_hybrid)}"
        f":k={settings.que_rag_top_k}"
        f":min={settings.que_rag_min_score}"
        f":embed={settings.resolved_embedding_provider}:{settings.active_embedding_model}"
        f":rerank={int(settings.que_rag_rerank_enabled)}:{settings.resolved_reranker_provider}:{settings.active_rerank_model}"
    )


def _retrieval_key(query: str, *, settings: Settings) -> str:
    return cache_key("retrieval", query.strip().casefold(), _retrieval_mode_tag(settings))


def get_cached_retrieval(query: str, *, settings: Settings | None = None) -> dict[str, Any] | None:
    """Return a serialized KnowledgeSelection dict, or None."""
    q = (query or "").strip()
    if not q:
        return None
    caches = _caches()
    if not caches:
        return None
    cfg = settings or get_settings()
    _, _, _, retrieval_cache = caches
    value = retrieval_cache.get(_retrieval_key(q, settings=cfg))
    return value if isinstance(value, dict) and isinstance(value.get("content"), str) else None


def set_cached_retrieval(
    query: str,
    payload: dict[str, Any],
    *,
    settings: Settings | None = None,
) -> None:
    q = (query or "").strip()
    if not q or not isinstance(payload.get("content"), str):
        return
    caches = _caches()
    if not caches:
        return
    cfg = settings or get_settings()
    _, _, _, retrieval_cache = caches
    retrieval_cache.set(_retrieval_key(q, settings=cfg), payload)
