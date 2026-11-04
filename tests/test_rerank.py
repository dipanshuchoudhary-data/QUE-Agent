"""Rerank ordering and fail-open behavior. No network."""

from __future__ import annotations

from app.core.config import Settings
from app.knowledge.rerank import rerank_chunks
from app.knowledge.store import RetrievedChunk


def _hit(chunk_id: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        doc_id=chunk_id,
        path=f"{chunk_id}.md",
        title=chunk_id,
        section="",
        text=text,
        score=0.4,
        corpus_version="test",
    )


def _settings() -> Settings:
    return Settings(
        app_env="local",
        llm_api_key="test-key",
        llm_base_url="https://openrouter.ai/api/v1",
        que_rag_rerank_model="nvidia/llama-nemotron-rerank-vl-1b-v2:free",
        que_rag_rerank_providers="",
    )


class _Response:
    def __init__(self, status: int, payload: dict | None = None) -> None:
        self.status_code = status
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_rerank_puts_the_higher_score_first(monkeypatch) -> None:
    hits = [_hit("a", "arena"), _hit("b", "create a quiz")]

    class _Client:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> bool:
            return False

        def post(self, url, json, headers):  # noqa: A002
            assert url.endswith("/rerank")
            assert json["model"] == "nvidia/llama-nemotron-rerank-vl-1b-v2:free"
            assert headers["Authorization"].startswith("Bearer ")
            return _Response(
                200,
                {"results": [{"index": 1, "relevance_score": 0.91}, {"index": 0, "relevance_score": 0.2}]},
            )

    monkeypatch.setattr("app.knowledge.rerank.httpx.Client", _Client)
    ordered = rerank_chunks("How do I create a quiz?", hits, settings=_settings())
    assert [hit.doc_id for hit in ordered] == ["b", "a"]
    assert ordered[0].score == 0.91
    assert hits[1].score == 0.4


def test_rerank_keeps_order_when_the_call_fails(monkeypatch) -> None:
    hits = [_hit("a", "one"), _hit("b", "two")]

    class _Client:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> bool:
            return False

        def post(self, url, json, headers):  # noqa: A002
            return _Response(400, {})

    monkeypatch.setattr("app.knowledge.rerank.httpx.Client", _Client)
    from app.knowledge.hybrid import _rerank_pool

    ordered = _rerank_pool("question", hits, settings=_settings())
    assert [hit.doc_id for hit in ordered] == ["a", "b"]


def _chain_settings() -> Settings:
    return Settings(
        app_env="local",
        llm_api_key="test-key",
        que_rag_rerank_providers="voyage,cohere",
        que_rerank_voyage_api_key="v-key",
        que_rerank_cohere_api_key="c-key",
    )


def _reset_chain_state() -> None:
    import itertools

    import app.knowledge.rerank as rr

    rr._cooldown_until.clear()
    rr._stats.clear()
    rr._counter = itertools.count()


def _client(calls: list[str], fail: set[str]):
    class _Client:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> bool:
            return False

        def post(self, url, json, headers):  # noqa: A002
            name = "voyage" if "voyageai" in url else "cohere"
            calls.append(name)
            if name in fail:
                return _Response(429, {})
            key = "data" if name == "voyage" else "results"
            return _Response(200, {key: [{"index": 1, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.1}]})

    return _Client


def test_providers_alternate_round_robin(monkeypatch) -> None:
    _reset_chain_state()
    calls: list[str] = []
    monkeypatch.setattr("app.knowledge.rerank.httpx.Client", _client(calls, set()))
    hits = [_hit("a", "one"), _hit("b", "two")]
    for _ in range(4):
        ordered = rerank_chunks("q", hits, settings=_chain_settings())
        assert [h.doc_id for h in ordered] == ["b", "a"]
    assert calls == ["voyage", "cohere", "voyage", "cohere"]


def test_failed_provider_falls_over_and_rests(monkeypatch) -> None:
    _reset_chain_state()
    calls: list[str] = []
    monkeypatch.setattr("app.knowledge.rerank.httpx.Client", _client(calls, {"voyage"}))
    hits = [_hit("a", "one"), _hit("b", "two")]
    first = rerank_chunks("q", hits, settings=_chain_settings())
    assert [h.doc_id for h in first] == ["b", "a"]
    assert calls == ["voyage", "cohere"]  # voyage 429, cohere served it
    calls.clear()
    rerank_chunks("q", hits, settings=_chain_settings())
    rerank_chunks("q", hits, settings=_chain_settings())
    assert calls == ["cohere", "cohere"]  # voyage is resting, no wasted calls


def test_all_providers_failing_raises_so_callers_keep_order(monkeypatch) -> None:
    _reset_chain_state()
    calls: list[str] = []
    monkeypatch.setattr("app.knowledge.rerank.httpx.Client", _client(calls, {"voyage", "cohere"}))
    from app.knowledge.hybrid import _rerank_pool

    hits = [_hit("a", "one"), _hit("b", "two")]
    ordered = _rerank_pool("q", hits, settings=_chain_settings())
    assert [h.doc_id for h in ordered] == ["a", "b"]


def test_load_is_spread_evenly_across_every_key(monkeypatch) -> None:
    _reset_chain_state()
    used: list[str] = []

    class _Client:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> bool:
            return False

        def post(self, url, json, headers):  # noqa: A002
            used.append(headers["Authorization"])
            return _Response(200, {"results": [{"index": 0, "relevance_score": 0.9}]})

    monkeypatch.setattr("app.knowledge.rerank.httpx.Client", _Client)
    cfg = Settings(
        app_env="local",
        llm_api_key="test-key",
        que_rag_rerank_providers="voyage,cohere",
        que_rerank_voyage_api_key="v1",
        que_rerank_cohere_api_key="c1,c2,c3,c4",
    )
    hits = [_hit("a", "one"), _hit("b", "two")]
    for _ in range(25):
        rerank_chunks("q", hits, settings=cfg)
    counts = {k: used.count(k) for k in set(used)}
    assert len(counts) == 5
    assert set(counts.values()) == {5}  # no key takes more than its share
