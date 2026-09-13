"""Turn-level span tracer. Never store raw query text or emails."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


def hash_user_id(user_id: str | None) -> str:
    raw = (user_id or "").strip() or "anon"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class Span:
    name: str
    ms: float
    ok: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnTrace:
    request_id: str
    user_hash: str
    route: str | None = None
    freshness: str | None = None
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    execution_class: str | None = None
    canonical_intent: str | None = None
    cost_usd: float | None = None
    error: bool = False
    spans: list[Span] = field(default_factory=list)

    def add_span(
        self,
        name: str,
        ms: float,
        *,
        ok: bool = True,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.spans.append(Span(name=name, ms=round(ms, 2), ok=ok, extra=extra or {}))

    @contextmanager
    def span(self, name: str, extra: dict[str, Any] | None = None) -> Iterator[None]:
        started = time.perf_counter()
        ok = True
        try:
            yield
        except Exception:
            ok = False
            raise
        finally:
            self.add_span(name, (time.perf_counter() - started) * 1000.0, ok=ok, extra=extra)

    def as_log_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_hash": self.user_hash,
            "route": self.route,
            "freshness": self.freshness,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "execution_class": self.execution_class,
            "canonical_intent": self.canonical_intent,
            "cost_usd": self.cost_usd,
            "error": self.error,
            "spans": [
                {"name": s.name, "ms": s.ms, "ok": s.ok, **s.extra} for s in self.spans
            ],
        }


def new_trace(
    *,
    request_id: str,
    user_id: str | None,
    route: str | None = None,
    freshness: str | None = None,
) -> TurnTrace:
    return TurnTrace(
        request_id=request_id,
        user_hash=hash_user_id(user_id),
        route=route,
        freshness=freshness,
    )
