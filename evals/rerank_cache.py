"""Disk cache for rerank calls made by eval scripts only.

Same query + same candidate chunks + same model gives the same ordering, so repeated
eval runs (raw, production, ablations) do not spend the daily free rerank quota twice.
Failures are never cached. Production code does not import this.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

CACHE_PATH = Path(__file__).resolve().parent / "diagnostics" / "rerank_cache.json"


def install() -> dict:
    import app.knowledge.rerank as rr

    stats = {"hits": 0, "calls": 0}
    memo: dict[str, list[list]] = {}
    if CACHE_PATH.exists():
        memo = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    original = rr.rerank_chunks

    def cached(query, hits, *, settings, top_n=None):
        key = hashlib.sha1(
            (
                settings.resolved_reranker_provider
                + "|"
                + settings.active_rerank_model
                + "|"
                + query
                + "|"
                + "|".join(h.chunk_id for h in hits)
                + f"|{top_n}"
            ).encode()
        ).hexdigest()
        by_id = {h.chunk_id: h for h in hits}
        if key in memo:
            stats["hits"] += 1
            return [replace(by_id[cid], score=score) for cid, score in memo[key] if cid in by_id]
        stats["calls"] += 1
        out = original(query, hits, settings=settings, top_n=top_n)
        memo[key] = [[h.chunk_id, h.score] for h in out]
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(memo), encoding="utf-8")
        return out

    rr.rerank_chunks = cached
    return stats
