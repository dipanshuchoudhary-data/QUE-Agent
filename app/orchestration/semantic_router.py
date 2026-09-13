"""Lightweight embedding similarity router — no extra LLM call.

Heuristics in ``understanding.classify_request`` remain the baseline.
When ``QUE_SEMANTIC_ROUTER`` is on, we embed the query once, compare to
intent prototypes, and only override when similarity is high-confidence.
"""

from __future__ import annotations

import json
import logging
import math
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.que_cache import get_cached_intent, set_cached_intent
from app.orchestration.understanding import RequestUnderstanding

logger = logging.getLogger(__name__)

_PROTOTYPES_PATH = Path(__file__).resolve().parent / "intent_prototypes.json"
_LOCK = threading.Lock()
_VECTORS: dict[str, list[float]] | None = None
_META: dict[str, Any] | None = None


@dataclass(frozen=True)
class SemanticHit:
    prototype_id: str
    score: float
    route: str
    intent: str


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


@lru_cache(maxsize=1)
def _load_meta() -> dict[str, Any]:
    raw = json.loads(_PROTOTYPES_PATH.read_text(encoding="utf-8"))
    return raw


def _ensure_vectors(settings: Settings) -> dict[str, list[float]]:
    global _VECTORS
    with _LOCK:
        if _VECTORS is not None:
            return _VECTORS
        from app.knowledge.embeddings import embed_texts

        meta = _load_meta()
        texts: list[str] = []
        keys: list[str] = []
        for proto in meta.get("prototypes") or []:
            pid = str(proto.get("id") or "")
            for i, t in enumerate(proto.get("texts") or []):
                texts.append(str(t))
                keys.append(f"{pid}::{i}")
        if not texts:
            _VECTORS = {}
            return _VECTORS
        try:
            vectors = embed_texts(texts, settings=settings)
        except Exception as exc:  # noqa: BLE001
            logger.warning("semantic_router_embed_failed error=%s", type(exc).__name__)
            _VECTORS = {}
            return _VECTORS
        _VECTORS = {k: list(v) for k, v in zip(keys, vectors, strict=False)}
        return _VECTORS


def _best_hit(query: str, settings: Settings) -> SemanticHit | None:
    cache_key = f"sem::{query.casefold().strip()}"
    cached = get_cached_intent(cache_key)
    vectors = _ensure_vectors(settings)
    if not vectors:
        return None
    from app.knowledge.query_embed import embed_query_cached

    try:
        qv = embed_query_cached(query, settings=settings)
    except Exception:  # noqa: BLE001
        return None

    meta = _load_meta()
    best: SemanticHit | None = None
    for proto in meta.get("prototypes") or []:
        pid = str(proto.get("id") or "")
        route = str(proto.get("route") or "knowledge")
        intent = str(proto.get("intent") or "knowledge")
        scores: list[float] = []
        for i, _t in enumerate(proto.get("texts") or []):
            key = f"{pid}::{i}"
            vec = vectors.get(key)
            if vec:
                scores.append(_cosine(qv, vec))
        if not scores:
            continue
        score = max(scores)
        if best is None or score > best.score:
            best = SemanticHit(prototype_id=pid, score=score, route=route, intent=intent)
    if best is not None:
        set_cached_intent(cache_key, f"{best.prototype_id}:{best.score:.3f}")
        if cached:
            pass
    return best


def maybe_override_understanding(
    query: str,
    base: RequestUnderstanding,
    *,
    settings: Settings | None = None,
) -> RequestUnderstanding:
    """High-confidence prototype match can override heuristic route/intent."""
    cfg = settings or get_settings()
    if not bool(getattr(cfg, "que_semantic_router", False)):
        return base
    if not cfg.llm_api_keys:
        return base
    # Never override hard refuse from jailbreak patterns.
    if base.route == "refuse" and base.intent == "out_of_scope":
        # Still allow semantic OOS confirm, but don't soften jailbreaks.
        if any(r.startswith("out_pattern:") for r in base.reasons):
            return base

    hit = _best_hit(query, cfg)
    if hit is None:
        return base
    meta = _load_meta()
    high = float(meta.get("threshold_high") or 0.78)
    if hit.score < high:
        return base

    # Don't demote an explicit tool/live need on medium product how-tos.
    if base.route == "tool" and hit.route == "knowledge" and hit.score < 0.88:
        return base

    reasons = (*base.reasons, f"semantic:{hit.prototype_id}:{hit.score:.2f}")
    canonical = hit.prototype_id
    if hit.prototype_id in {"greeting", "capabilities", "what_is_quizzer", "oos"}:
        canonical = None
    return RequestUnderstanding(
        scope="out_of_scope" if hit.route == "refuse" else "in_scope",
        intent=hit.intent,  # type: ignore[arg-type]
        risk=base.risk if hit.route != "refuse" else "read",
        freshness=base.freshness,
        data_need="none" if hit.route in {"refuse", "canned_eligible"} else base.data_need,
        complexity=base.complexity,
        route=hit.route,  # type: ignore[arg-type]
        reasons=reasons,
        execution_class=base.execution_class,
        canonical_intent=canonical,
        confidence=round(float(hit.score), 3),
    )


def reset_semantic_router_cache() -> None:
    """Test helper."""
    global _VECTORS
    with _LOCK:
        _VECTORS = None
    _load_meta.cache_clear()
