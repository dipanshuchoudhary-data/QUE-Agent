"""Cross-encoder rerank of hybrid candidates.

Providers (``QUE_RAG_RERANK_PROVIDERS``, e.g. ``voyage,cohere``) are used round-robin
so load is spread across their rate limits. When one fails (429, 5xx, timeout) the next
is tried straight away, and the failed one rests for a cooldown. With no providers
configured, the old single OpenRouter-style ``/rerank`` call is used.

The dense cosine floor stays on the original dense scores. If every provider fails,
``RerankError`` is raised and the caller keeps the candidate order, so retrieval still
answers.
"""

from __future__ import annotations

import itertools
import logging
import random
import threading
import time
from dataclasses import dataclass, replace
from functools import lru_cache

import httpx

from app.core.config import Settings
from app.knowledge.store import RetrievedChunk

logger = logging.getLogger(__name__)

_MAX_DOC_CHARS = 8_000
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_blocked_keys: dict[str, float] = {}  # legacy path: key -> daily quota treated as spent until


class RerankError(RuntimeError):
    """The rerank call failed. Callers keep the pre-rerank order."""


@dataclass(frozen=True)
class _Provider:
    name: str
    base_url: str
    top_key: str  # name of the "how many to return" field
    cooldown_s: float


_PROVIDERS = {
    "voyage": _Provider("voyage", "https://api.voyageai.com/v1", "top_k", 20.0),
    "cohere": _Provider("cohere", "https://api.cohere.com/v2", "top_n", 8.0),
}

_lock = threading.Lock()
_counter = itertools.count(random.randrange(1000))  # random start so workers do not all begin on the same key
_cooldown_until: dict[str, float] = {}
_stats: dict[str, dict[str, int]] = {}


def provider_stats() -> dict[str, dict[str, int]]:
    """Per-provider ``ok`` / ``failed`` counts since process start (for eval summaries)."""
    return {name: dict(counts) for name, counts in _stats.items()}


def _count(name: str, field: str) -> None:
    _stats.setdefault(name, {"ok": 0, "failed": 0})[field] += 1


def _document_text(hit: RetrievedChunk) -> str:
    heading = " > ".join(part for part in (hit.title, hit.section) if part)
    body = hit.text or ""
    text = f"{heading}\n{body}".strip() if heading else body
    return text[:_MAX_DOC_CHARS]


def _configured(settings: Settings) -> list[tuple[_Provider, str, str, str]]:
    """(provider, api key, model, label) per key. A provider may list several keys, comma-separated."""
    out: list[tuple[_Provider, str, str, str]] = []
    names = [n.strip().casefold() for n in (settings.que_rag_rerank_providers or "").split(",") if n.strip()]
    for name in names:
        provider = _PROVIDERS.get(name)
        if provider is None:
            continue
        raw = getattr(settings, f"que_rerank_{name}_api_key", "") or ""
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        model = (getattr(settings, f"que_rerank_{name}_model", "") or "").strip()
        if not model:
            continue
        for i, key in enumerate(keys, start=1):
            out.append((provider, key, model, name if len(keys) == 1 else f"{name}#{i}"))
    return out


def rerank_chunks(
    query: str,
    hits: list[RetrievedChunk],
    *,
    settings: Settings,
    top_n: int | None = None,
) -> list[RetrievedChunk]:
    """Return ``hits`` ordered by the rerank model. Scores become relevance scores."""
    if len(hits) <= 1:
        return list(hits)
    documents = [_document_text(hit) for hit in hits]
    if not any(documents):
        return list(hits)
    take = len(hits) if top_n is None else max(1, min(top_n, len(hits)))
    q = (query or "")[:_MAX_DOC_CHARS]

    if settings.uses_local_reranker:
        # Development only. Never calls Voyage, Cohere, or OpenRouter, and never falls back to them.
        return _rerank_local(q, hits, documents, settings)[:take]

    chain = _configured(settings)
    if chain:
        body = _post_with_failover(chain, q, documents, take, timeout=settings.llm_timeout_seconds)
    else:
        body = _post_legacy(settings, q, documents, take)

    results = (body.get("results") or body.get("data")) if isinstance(body, dict) else None
    if not isinstance(results, list) or not results:
        raise RerankError("rerank response had no results")

    ordered: list[RetrievedChunk] = []
    seen: set[int] = set()
    for item in results:
        if not isinstance(item, dict):
            continue
        try:
            index = int(item["index"])
            score = float(item["relevance_score"])
        except (KeyError, TypeError, ValueError):
            continue
        if index in seen or index < 0 or index >= len(hits):
            continue
        seen.add(index)
        ordered.append(replace(hits[index], score=score))
    if not ordered:
        raise RerankError("rerank response had no usable indexes")
    for index, hit in enumerate(hits):
        if index not in seen:
            ordered.append(hit)
    return ordered


@lru_cache(maxsize=2)
def _load_local_reranker(model_name: str, cache_folder: str, device: str):
    from sentence_transformers import CrossEncoder

    kwargs: dict[str, object] = {"device": device or "cpu", "local_files_only": True}
    if cache_folder:
        kwargs["cache_folder"] = cache_folder
    return CrossEncoder(model_name, **kwargs)


def _rerank_local(
    query: str,
    hits: list[RetrievedChunk],
    documents: list[str],
    settings: Settings,
) -> list[RetrievedChunk]:
    try:
        model = _load_local_reranker(
            settings.local_rerank_model,
            settings.local_embedding_cache.strip(),
            settings.local_embedding_device.strip() or "cpu",
        )
    except Exception as exc:
        raise RerankError(f"Local reranker failed to load ({settings.local_rerank_model}): {exc}") from exc
    scores = model.predict([(query, doc) for doc in documents], show_progress_bar=False)
    order = sorted(range(len(hits)), key=lambda i: float(scores[i]), reverse=True)
    _count("local", "ok")
    return [replace(hits[i], score=float(scores[i])) for i in order]


def _post_with_failover(
    chain: list[tuple[_Provider, str, str, str]],
    query: str,
    documents: list[str],
    take: int,
    *,
    timeout: float,
) -> dict:
    with _lock:
        start = next(_counter) % len(chain)
    order = chain[start:] + chain[:start]
    now = time.monotonic()
    tried = 0
    for provider, key, model, label in order:
        if _cooldown_until.get(label, 0.0) > now:
            continue
        tried += 1
        cooldown = provider.cooldown_s
        payload = {"model": model, "query": query, "documents": documents, provider.top_key: take}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        url = f"{provider.base_url}/rerank"
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=headers)
            status = response.status_code
            if status >= 400:
                retry_after = getattr(response, "headers", {}).get("retry-after", "") if status == 429 else ""
                if str(retry_after).isdigit():
                    cooldown = min(float(retry_after), 120.0)
                raise RerankError(f"{provider.name} HTTP {status}")
            parsed = response.json()
            if not isinstance(parsed, dict):
                raise RerankError(f"{provider.name} response was not an object")
        except (httpx.HTTPError, ValueError, RerankError) as exc:
            _count(label, "failed")
            # Rate limits and outages rest the provider; a 4xx config error rests it too.
            _cooldown_until[label] = time.monotonic() + cooldown
            logger.warning("rag_rerank_failover", extra={"provider": label, "error": str(exc)[:80]})
            continue
        _count(label, "ok")
        return parsed
    raise RerankError("all rerank providers failed or are cooling down" if tried else "all rerank providers are cooling down")


def _post_legacy(settings: Settings, query: str, documents: list[str], take: int) -> dict:
    """Single OpenRouter-style endpoint using the LLM keys (the original behavior)."""
    model = (settings.que_rag_rerank_model or "").strip()
    keys = settings.llm_api_keys
    if not model or not keys:
        raise RerankError("rerank model or API key is not configured")
    url = f"{settings.llm_base_url.rstrip('/')}/rerank"
    payload = {"model": model, "query": query, "documents": documents, "top_n": take}
    now = time.monotonic()
    for key in keys:
        if _blocked_keys.get(key, 0.0) > now:
            continue
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            return _post_rerank(url, payload, headers, timeout=settings.llm_timeout_seconds)
        except RerankError as exc:
            if "daily quota" not in str(exc):
                raise
            _blocked_keys[key] = time.monotonic() + 600
    raise RerankError("rerank daily quota exhausted on all keys")


def _post_rerank(
    url: str,
    payload: dict,
    headers: dict[str, str],
    *,
    timeout: float,
) -> dict:
    last_status = 0
    for attempt in range(3):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            last_status = 0
            logger.warning("rag_rerank_http_error", extra={"attempt": attempt + 1})
            if attempt == 2:
                raise RerankError("rerank request failed") from exc
            time.sleep(1.5 * (attempt + 1))
            continue
        last_status = response.status_code
        if response.status_code == 429 and "per-day" in (response.text or "").casefold():
            logger.warning("rag_rerank_daily_quota_exhausted")
            raise RerankError("rerank daily quota exhausted")
        if response.status_code in _RETRY_STATUSES and attempt < 2:
            logger.warning(
                "rag_rerank_retry",
                extra={"status": response.status_code, "attempt": attempt + 1},
            )
            time.sleep(1.5 * (attempt + 1))
            continue
        if response.status_code >= 400:
            raise RerankError(f"rerank HTTP {response.status_code}")
        try:
            parsed = response.json()
        except ValueError as exc:
            raise RerankError("rerank response was not JSON") from exc
        if not isinstance(parsed, dict):
            raise RerankError("rerank response was not an object")
        return parsed
    raise RerankError(f"rerank HTTP {last_status}")
