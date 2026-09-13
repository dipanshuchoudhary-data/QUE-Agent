"""Semantic router unit tests — no network when flag off / no keys."""

from __future__ import annotations

from app.orchestration.semantic_router import maybe_override_understanding, reset_semantic_router_cache
from app.orchestration.understanding import RequestUnderstanding


def test_semantic_router_noop_when_disabled():
    reset_semantic_router_cache()
    base = RequestUnderstanding(
        scope="in_scope",
        intent="knowledge",
        risk="read",
        freshness="static",
        data_need="knowledge",
        complexity="single_step",
        route="knowledge",
        reasons=("heuristic",),
    )
    from app.core.config import Settings

    out = maybe_override_understanding(
        "what can you help me with",
        base,
        settings=Settings(QUE_SEMANTIC_ROUTER=False, LLM_API_KEY=""),
    )
    assert out.route == "knowledge"
    assert out.reasons == ("heuristic",)


def test_semantic_router_noop_when_no_api_key():
    reset_semantic_router_cache()
    base = RequestUnderstanding(
        scope="in_scope",
        intent="knowledge",
        risk="read",
        freshness="static",
        data_need="knowledge",
        complexity="single_step",
        route="knowledge",
        reasons=("heuristic",),
    )
    from app.core.config import Settings

    out = maybe_override_understanding(
        "how to published the draft exam",
        base,
        settings=Settings(QUE_SEMANTIC_ROUTER=True, LLM_API_KEY=""),
    )
    assert out.route == "knowledge"
    assert out.reasons == ("heuristic",)
