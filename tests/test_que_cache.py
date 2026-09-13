"""QUE-local cache tests (not Quizzer Redis)."""

from __future__ import annotations

import random
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.core.config import Settings, get_settings
from app.core.llm import ChatLane
from app.core.que_cache import (
    get_cached_intent,
    get_cached_llm_reply,
    get_cached_retrieval,
    reset_que_caches,
    set_cached_intent,
    set_cached_llm_reply,
    set_cached_retrieval,
)
from app.graphs.que_graph import get_que_graph
from app.orchestration.cache_policy import (
    allow_llm_reply_cache,
    allow_retrieval_cache,
    llm_reply_ttl,
    retrieval_ttl,
)
from app.orchestration.canned import match_canned_reply
from app.orchestration.pipeline import _history_fingerprint, complete
from app.orchestration.understanding import RequestUnderstanding, classify_request
from app.schemas.chat import ChatRequest

_LANE = ChatLane(model="test-model", key_index=0, api_key="test")
_HOWTO = "What's the difference between exam duration and link window?"
_LIVE = "How many exams did I create today?"


def _settings(**overrides) -> Settings:
    payload = {
        "APP_ENV": "local",
        "QUE_JWT_SECRET": "test-que-jwt-secret-not-for-production-32c",
        "QUE_TOOLS_ENABLED": False,
    }
    payload.update(overrides)
    return Settings(**payload)


def test_intent_cache_roundtrip():
    reset_que_caches()
    assert get_cached_intent("helo") is None
    set_cached_intent("helo", "greeting")
    assert get_cached_intent("helo") == "greeting"


def test_llm_cache_roundtrip():
    reset_que_caches()
    key = "hist-demo"
    assert get_cached_llm_reply(key) is None
    set_cached_llm_reply(key, content="Open Exams first.", model="test-model")
    hit = get_cached_llm_reply(key)
    assert hit is not None
    assert hit["content"] == "Open Exams first."
    assert hit["model"] == "test-model"


def test_canned_avoids_same_variant_twice_in_conversation():
    reset_que_caches()
    cid = "conv-variant-1"
    first = match_canned_reply("hello", conversation_id=cid, rng=random.Random(0))
    second = match_canned_reply("hello", conversation_id=cid, rng=random.Random(0))
    assert first and second
    assert first.text != second.text


def test_freshness_policy_static_vs_live():
    howto = classify_request(_HOWTO)
    assert howto.freshness == "static"
    assert allow_llm_reply_cache(howto) is True
    assert allow_retrieval_cache(howto) is True

    live = classify_request(_LIVE)
    assert live.freshness in {"dynamic", "critical"}
    assert live.data_need == "live_tool"
    assert allow_llm_reply_cache(live) is False
    assert allow_retrieval_cache(live) is False


def test_critical_understanding_bypasses_all_reply_caches():
    u = RequestUnderstanding(
        scope="in_scope",
        intent="live_data",
        risk="read",
        freshness="critical",
        data_need="live_tool",
        complexity="single_step",
        route="tool",
    )
    assert allow_llm_reply_cache(u) is False
    assert allow_retrieval_cache(u) is False


def test_retrieval_ttl_differs_from_llm_ttl():
    cfg = _settings(
        que_cache_llm_ttl_seconds=900,
        que_cache_retrieval_ttl_seconds=1800,
    )
    assert llm_reply_ttl(cfg) == 900
    assert retrieval_ttl(cfg) == 1800
    assert retrieval_ttl(cfg) != llm_reply_ttl(cfg)


def test_retrieval_cache_roundtrip():
    reset_que_caches()
    cfg = get_settings()
    assert get_cached_retrieval("how to publish", settings=cfg) is None
    set_cached_retrieval(
        "how to publish",
        {"content": "pack text", "pack_ids": ["publishing"], "mode": "keyword", "scores": {}},
        settings=cfg,
    )
    hit = get_cached_retrieval("how to publish", settings=cfg)
    assert hit is not None
    assert hit["content"] == "pack text"


def test_history_fingerprint_always_includes_user_and_isolates_anon():
    msgs = [{"role": "user", "content": _HOWTO}]
    with_user = _history_fingerprint(ChatRequest(messages=msgs, user_id="teacher-a"))
    anon = _history_fingerprint(ChatRequest(messages=msgs))
    other = _history_fingerprint(ChatRequest(messages=msgs, user_id="teacher-b"))
    assert with_user != anon
    assert with_user != other
    assert anon != other


@pytest.mark.asyncio
async def test_llm_cache_does_not_leak_across_users():
    get_settings.cache_clear()
    get_que_graph.cache_clear()
    reset_que_caches()
    n = {"i": 0}

    async def fake_ainvoke(messages, **kwargs):
        n["i"] += 1
        return AIMessage(content=f"howto-{n['i']}"), _LANE

    req_a = ChatRequest(
        messages=[{"role": "user", "content": _HOWTO}],
        conversation_id="iso-a",
        user_id="user-a",
    )
    req_b = ChatRequest(
        messages=[{"role": "user", "content": _HOWTO}],
        conversation_id="iso-b",
        user_id="user-b",
    )
    cfg = _settings()

    with patch("app.graphs.nodes.ainvoke_chat", new=AsyncMock(side_effect=fake_ainvoke)):
        first = await complete(req_a, settings=cfg)
        second_a = await complete(req_a, settings=cfg)
        other = await complete(req_b, settings=cfg)

    assert first.message.content == "howto-1"
    assert second_a.message.content == "howto-1"
    assert second_a.model.startswith("cache:")
    assert other.message.content == "howto-2"
    assert not str(other.model).startswith("cache:")
    get_que_graph.cache_clear()


@pytest.mark.asyncio
async def test_anon_llm_cache_does_not_collide_with_named_user():
    get_que_graph.cache_clear()
    reset_que_caches()
    n = {"i": 0}

    async def fake_ainvoke(messages, **kwargs):
        n["i"] += 1
        return AIMessage(content=f"anon-{n['i']}"), _LANE

    named = ChatRequest(
        messages=[{"role": "user", "content": _HOWTO}],
        conversation_id="anon-iso",
        user_id="real-user",
    )
    anon = ChatRequest(
        messages=[{"role": "user", "content": _HOWTO}],
        conversation_id="anon-iso",
    )
    cfg = _settings()

    with patch("app.graphs.nodes.ainvoke_chat", new=AsyncMock(side_effect=fake_ainvoke)):
        a = await complete(named, settings=cfg)
        b = await complete(anon, settings=cfg)

    assert a.message.content == "anon-1"
    assert b.message.content == "anon-2"
    get_que_graph.cache_clear()


@pytest.mark.asyncio
async def test_live_ask_never_uses_llm_reply_cache(monkeypatch):
    monkeypatch.setenv("QUE_TOOLS_ENABLED", "false")
    get_settings.cache_clear()
    get_que_graph.cache_clear()
    reset_que_caches()
    fake = AsyncMock(return_value=(AIMessage(content="should-not-cache"), _LANE))
    req = ChatRequest(
        messages=[{"role": "user", "content": _LIVE}],
        conversation_id="live-1",
        user_id="teacher-1",
    )
    cfg = _settings(QUE_TOOLS_ENABLED=False)

    with patch("app.graphs.nodes.ainvoke_chat", fake):
        first = await complete(req, settings=cfg)
        second = await complete(req, settings=cfg)

    assert classify_request(_LIVE).freshness == "critical"
    assert allow_llm_reply_cache(classify_request(_LIVE)) is False
    fake.assert_not_called()
    assert get_cached_llm_reply(_history_fingerprint(req)) is None
    assert "live" in first.message.content.casefold() or "can't" in first.message.content.casefold()
    assert first.message.content == second.message.content
    get_que_graph.cache_clear()
    get_settings.cache_clear()
