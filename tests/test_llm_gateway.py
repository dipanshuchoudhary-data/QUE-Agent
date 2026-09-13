"""LLM gateway: round-robin, complexity routing, failover, empty pool."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.config import Settings
from app.core.llm import (
    LLMError,
    ainvoke_chat,
    astream_chat,
    is_retryable,
    iter_failover_lanes,
    prefer_strong_model,
    reset_gateway_counters,
)
from app.knowledge.embeddings import get_embeddings

MODELS_CSV = "model-a,model-b,model-c"
MODELS = tuple(part.strip() for part in MODELS_CSV.split(","))
PREFERRED = MODELS[1]

_EMPTY_NUMBERED = {
    "llm_api_key_1": "",
    "llm_api_key_2": "",
    "llm_api_key_3": "",
    "llm_api_key_4": "",
    "llm_api_key_5": "",
    "llm_api_key_6": "",
    "llm_api_key_7": "",
    "llm_api_key_8": "",
}


def _pool(**overrides) -> Settings:
    payload = {
        "APP_ENV": "local",
        "QUE_JWT_SECRET": "test-que-jwt-secret-not-for-production-32c",
        "llm_api_key": "key-a",
        **_EMPTY_NUMBERED,
        "llm_api_key_1": "key-b",
        "llm_model": PREFERRED,
        "llm_models_raw": MODELS_CSV,
        "llm_gateway_rr": True,
        "llm_max_attempts": 3,
        "llm_retry_base_ms": 0,
        "llm_retry_cap_ms": 0,
    }
    payload.update(overrides)
    return Settings(**payload)


@pytest.fixture(autouse=True)
def _reset_rr():
    reset_gateway_counters()
    yield
    reset_gateway_counters()


def test_prefer_strong_model_for_agent_and_multi_step():
    assert prefer_strong_model(complexity="multi_step", runtime_mode="knowledge") is True
    assert prefer_strong_model(complexity="simple", runtime_mode="agent") is True
    assert prefer_strong_model(complexity="simple", runtime_mode="workflow") is False


def test_round_robin_rotates_key_then_model():
    cfg = _pool()
    first_lanes = [iter_failover_lanes(cfg)[0] for _ in range(4)]
    assert [lane.key_index for lane in first_lanes] == [0, 1, 0, 1]
    assert [lane.model for lane in first_lanes] == [
        MODELS[0],
        MODELS[1],
        MODELS[2],
        MODELS[0],
    ]
    assert first_lanes[0].api_key == "key-a"
    assert first_lanes[1].api_key == "key-b"


def test_agent_and_multi_step_prefer_llm_model_first():
    cfg = _pool()
    agent_starts = [iter_failover_lanes(cfg, runtime_mode="agent")[0] for _ in range(3)]
    assert all(lane.model == PREFERRED for lane in agent_starts)
    assert [lane.key_index for lane in agent_starts] == [0, 1, 0]

    reset_gateway_counters()
    lanes = iter_failover_lanes(cfg, complexity="multi_step")
    assert lanes[0].model == PREFERRED
    model_order: list[str] = []
    for lane in lanes:
        if lane.model not in model_order:
            model_order.append(lane.model)
    start = MODELS.index(PREFERRED)
    assert model_order == [MODELS[(start + i) % len(MODELS)] for i in range(len(MODELS))]


def test_empty_key_pool_raises_llm_error():
    cfg = _pool(llm_api_key="", llm_api_key_1="")
    with pytest.raises(LLMError, match="LLM_API_KEY"):
        iter_failover_lanes(cfg)


@pytest.mark.asyncio
async def test_ainvoke_empty_keys_raises_llm_error():
    cfg = _pool(llm_api_key="", llm_api_key_1="")
    with pytest.raises(LLMError, match="LLM_API_KEY"):
        await ainvoke_chat([HumanMessage(content="hi")], settings=cfg)


@pytest.mark.asyncio
async def test_failover_advances_key_then_model():
    cfg = _pool()
    seen: list[tuple[str, int]] = []

    class FakeModel:
        def __init__(self, lane):
            self._lane = lane

        async def ainvoke(self, messages):
            seen.append((self._lane.model, self._lane.key_index))
            if self._lane.model == MODELS[0]:
                raise RuntimeError("429 rate limit")
            return AIMessage(content="ok")

    def fake_get(*, settings=None, lane=None, **kwargs):
        assert lane is not None
        return FakeModel(lane)

    with patch("app.core.llm.get_chat_model", side_effect=fake_get):
        response, lane = await ainvoke_chat(
            [HumanMessage(content="hi")],
            settings=cfg,
        )

    assert seen == [
        (MODELS[0], 0),
        (MODELS[0], 1),
        (MODELS[1], 0),
    ]
    assert response.content == "ok"
    assert lane.model == MODELS[1]
    assert lane.key_index == 0


@pytest.mark.asyncio
async def test_astream_does_not_splice_models_after_first_token():
    cfg = _pool()
    seen: list[int] = []

    class FakeModel:
        def __init__(self, lane):
            self._lane = lane

        async def astream(self, messages):
            seen.append(self._lane.key_index)
            yield AIMessage(content="partial")
            raise RuntimeError("503 overloaded")

    with patch("app.core.llm.get_chat_model", side_effect=lambda **kw: FakeModel(kw["lane"])):
        chunks: list[str] = []
        with pytest.raises(LLMError, match="503"):
            async for piece, _lane in astream_chat(
                [HumanMessage(content="hi")],
                settings=cfg,
            ):
                chunks.append(piece)

    assert chunks == ["partial"]
    assert seen == [0]


class _StatusExc(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def test_is_retryable_skips_auth_and_forbidden():
    assert is_retryable(_StatusExc(401, "Unauthorized")) is False
    assert is_retryable(_StatusExc(403, "Forbidden")) is False
    assert is_retryable(_StatusExc(429, "rate limit")) is True


@pytest.mark.asyncio
async def test_failover_does_not_advance_on_401():
    cfg = _pool()
    seen: list[tuple[str, int]] = []

    class FakeModel:
        def __init__(self, lane):
            self._lane = lane

        async def ainvoke(self, messages):
            seen.append((self._lane.model, self._lane.key_index))
            raise _StatusExc(401, "Unauthorized")

    with patch("app.core.llm.get_chat_model", side_effect=lambda **kw: FakeModel(kw["lane"])):
        with pytest.raises(LLMError):
            await ainvoke_chat([HumanMessage(content="hi")], settings=cfg)

    assert len(seen) == 1
    assert seen[0][1] == 0


def test_embeddings_use_first_configured_key():
    cfg = _pool(llm_api_key="", llm_api_key_1="embed-key")
    assert cfg.llm_api_keys[0] == "embed-key"
    client = get_embeddings(settings=cfg)
    secret = getattr(client, "openai_api_key", None) or getattr(client, "api_key", None)
    assert secret is not None
    value = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    assert value == "embed-key"
