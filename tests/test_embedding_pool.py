"""Embedding pool: round robin, instant failover, cooldown, one vector space."""

from __future__ import annotations

import pytest

from app.core.llm import LLMError
from app.knowledge.embeddings import PooledEmbeddings, _Endpoint


def _pool(**kw):
    eps = [_Endpoint("a", "http://a", "k", "m"), _Endpoint("b", "http://b", "k", "m")]
    pool = PooledEmbeddings(eps, timeout=1.0, cooldown=kw.get("cooldown", 30.0))
    return pool, eps


def _fake(pool, calls, fail=()):
    def call(ep, texts):
        calls.append(ep.name)
        if ep.name in fail:
            raise RuntimeError("boom")
        return [[1.0, 0.0] for _ in texts]

    pool._call = call


def test_round_robin_alternates():
    pool, _ = _pool()
    calls: list[str] = []
    _fake(pool, calls)
    for _ in range(4):
        pool.embed_query("x")
    assert calls == ["a", "b", "a", "b"]


def test_failover_is_immediate_and_provider_is_parked():
    pool, eps = _pool()
    calls: list[str] = []
    _fake(pool, calls, fail={"a"})
    assert pool.embed_query("x") == [1.0, 0.0]
    assert calls == ["a", "b"]  # a failed, b answered in the same call
    calls.clear()
    pool.embed_query("x")
    pool.embed_query("x")
    assert calls == ["b", "b"]  # a is parked, not retried


def test_parked_provider_returns_after_cooldown():
    pool, eps = _pool(cooldown=0.0)
    calls: list[str] = []
    _fake(pool, calls, fail={"a"})
    pool.embed_query("x")
    calls.clear()
    pool.embed_query("x")
    pool.embed_query("x")  # cooldown 0: a is back in rotation
    assert "a" in calls


def test_all_down_raises_llm_error():
    pool, _ = _pool()
    _fake(pool, [], fail={"a", "b"})
    with pytest.raises(LLMError):
        pool.embed_query("x")


def test_documents_are_batched():
    pool, _ = _pool()
    sizes: list[int] = []

    def call(ep, texts):
        sizes.append(len(texts))
        return [[0.0] for _ in texts]

    pool._call = call
    assert len(pool.embed_documents([str(i) for i in range(40)])) == 40
    assert sizes == [16, 16, 8]


def test_no_keys_is_an_error():
    with pytest.raises(LLMError):
        PooledEmbeddings([], timeout=1.0, cooldown=1.0)
