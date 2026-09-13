"""Phase 13 — failure matrix: retries, circuits, cache fallthrough, tool errors."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.config import Settings, get_settings
from app.core.errors import ERROR_LLM_UNAVAILABLE, public_llm_error
from app.core.llm import (
    ChatLane,
    LLMError,
    ainvoke_chat,
    force_llm_circuit_open,
    is_retryable,
    reset_llm_circuit,
)
from app.orchestration.pipeline import complete
from app.schemas.chat import ChatRequest
from app.tools.executor import (
    force_tool_circuit_open,
    invoke_tool_selection,
    reset_tool_circuit,
)
from app.tools.quizzer_client import ToolClientError
from app.tools.registry import get_tool
from app.tools.select import ToolSelection

_TEST_LANE = ChatLane(model="test-model", key_index=0, api_key="test")

MODELS_CSV = "model-a,model-b"
_EMPTY_NUMBERED = {f"llm_api_key_{i}": "" for i in range(1, 9)}


def _pool(**overrides) -> Settings:
    payload = {
        "APP_ENV": "local",
        "QUE_JWT_SECRET": "test-que-jwt-secret-not-for-production-32c",
        "llm_api_key": "key-a",
        **_EMPTY_NUMBERED,
        "llm_api_key_1": "key-b",
        "llm_model": "model-a",
        "llm_models_raw": MODELS_CSV,
        "llm_gateway_rr": True,
        "llm_max_attempts": 3,
        "llm_max_attempts_non_agent": 3,
        "llm_retry_base_ms": 0,
        "llm_retry_cap_ms": 0,
        "que_llm_circuit_failures": 5,
        "que_llm_circuit_ttl_seconds": 30,
    }
    payload.update(overrides)
    return Settings(**payload)


class _HttpExc(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def test_401_403_400_are_not_retryable():
    assert is_retryable(_HttpExc(401, "Unauthorized")) is False
    assert is_retryable(_HttpExc(403, "Forbidden")) is False
    assert is_retryable(_HttpExc(400, "Bad Request")) is False
    assert is_retryable(_HttpExc(429, "rate limit")) is True
    assert is_retryable(_HttpExc(503, "overloaded")) is True
    assert is_retryable(TimeoutError("timed out")) is True


@pytest.mark.asyncio
async def test_ainvoke_does_not_retry_401():
    cfg = _pool()
    seen: list[tuple[str, int]] = []

    class FakeModel:
        def __init__(self, lane):
            self._lane = lane

        async def ainvoke(self, messages):
            seen.append((self._lane.model, self._lane.key_index))
            raise _HttpExc(401, "Unauthorized")

    with patch("app.core.llm.get_chat_model", side_effect=lambda **kw: FakeModel(kw["lane"])):
        with pytest.raises(LLMError, match="Unauthorized"):
            await ainvoke_chat([HumanMessage(content="hi")], settings=cfg)

    assert seen == [("model-a", 0)]


@pytest.mark.asyncio
async def test_ainvoke_retries_5xx_then_succeeds():
    cfg = _pool()
    seen: list[int] = []

    class FakeModel:
        def __init__(self, lane):
            self._lane = lane

        async def ainvoke(self, messages):
            seen.append(self._lane.key_index)
            if self._lane.key_index == 0:
                raise _HttpExc(503, "overloaded")
            return AIMessage(content="ok")

    with patch("app.core.llm.get_chat_model", side_effect=lambda **kw: FakeModel(kw["lane"])):
        response, lane = await ainvoke_chat([HumanMessage(content="hi")], settings=cfg)

    assert seen == [0, 1]
    assert response.content == "ok"
    assert lane.key_index == 1


@pytest.mark.asyncio
async def test_llm_circuit_open_skips_provider():
    cfg = _pool()
    force_llm_circuit_open(ttl_seconds=30)
    called = {"n": 0}

    def boom(**kwargs):
        called["n"] += 1
        raise AssertionError("provider must not be called")

    with patch("app.core.llm.get_chat_model", side_effect=boom):
        with pytest.raises(LLMError, match="circuit open"):
            await ainvoke_chat([HumanMessage(content="hi")], settings=cfg)
    assert called["n"] == 0
    reset_llm_circuit()


def test_public_llm_error_maps_circuit_open_to_try_again():
    code, message = public_llm_error(LLMError("LLM circuit open"))
    assert code == ERROR_LLM_UNAVAILABLE
    assert "try again" in message.casefold()


@pytest.mark.asyncio
async def test_tool_circuit_open_returns_tool_error():
    reset_tool_circuit()
    spec = get_tool("summarize_my_exams")
    assert spec is not None
    selection = ToolSelection(tool=spec, args={}, reason="test", needs_clarify=False)
    force_tool_circuit_open(ttl_seconds=30)
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
        que_tools_enabled=True,
        quizzer_internal_base_url="http://127.0.0.1:9",
        que_service_key="test-service-key-not-for-production",
        que_budget_usd_per_user_hour=0.0,
    )
    invoke = AsyncMock(side_effect=AssertionError("Quizzer must not be called"))
    with patch("app.tools.executor.invoke_quizzer_tool", invoke):
        execution = await invoke_tool_selection(
            selection,
            user_id="u1",
            request_id="rid-1",
            ui_context={"user_role": "teacher"},
            settings=cfg,
        )
    assert invoke.await_count == 0
    assert execution.error_code == "unavailable"
    assert "circuit" in (execution.error_message or "").casefold()
    assert "TOOL_ERROR" in execution.system_message
    reset_tool_circuit()


@pytest.mark.asyncio
async def test_tool_timeout_is_tool_error_not_hang():
    spec = get_tool("summarize_my_exams")
    assert spec is not None
    selection = ToolSelection(tool=spec, args={}, reason="test", needs_clarify=False)
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
        que_tools_enabled=True,
        quizzer_internal_base_url="http://127.0.0.1:8000",
        que_service_key="test-service-key-not-for-production",
        que_budget_usd_per_user_hour=0.0,
    )
    with patch(
        "app.tools.executor.invoke_quizzer_tool",
        AsyncMock(side_effect=ToolClientError("upstream_timeout", "Quizzer tool timed out")),
    ):
        execution = await invoke_tool_selection(
            selection,
            user_id="u1",
            request_id="rid-2",
            ui_context={"user_role": "teacher"},
            settings=cfg,
        )
    assert execution.error_code == "upstream_timeout"
    assert "TOOL_ERROR" in execution.system_message


@pytest.mark.asyncio
async def test_invalid_quizzer_json_is_tool_client_error():
    spec = get_tool("summarize_my_exams")
    assert spec is not None
    selection = ToolSelection(tool=spec, args={}, reason="test", needs_clarify=False)
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
        que_tools_enabled=True,
        quizzer_internal_base_url="http://127.0.0.1:8000",
        que_service_key="test-service-key-not-for-production",
        que_budget_usd_per_user_hour=0.0,
    )

    class _FakeResp:
        status_code = 200

        def json(self):
            raise ValueError("not json")

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            return _FakeResp()

    with patch("app.tools.quizzer_client.httpx.AsyncClient", _FakeClient):
        execution = await invoke_tool_selection(
            selection,
            user_id="u1",
            request_id="rid-3",
            ui_context={"user_role": "teacher"},
            settings=cfg,
        )
    assert execution.error_code == "unavailable"
    assert "non-JSON" in (execution.error_message or "")
    assert "TOOL_ERROR" in execution.system_message


@pytest.mark.asyncio
async def test_cache_disabled_falls_through_to_llm(monkeypatch):
    monkeypatch.setenv("QUE_CACHE_ENABLED", "false")
    get_settings.cache_clear()
    fake = AsyncMock(
        side_effect=[
            (AIMessage(content="first how-to"), _TEST_LANE),
            (AIMessage(content="second how-to"), _TEST_LANE),
        ]
    )
    req = ChatRequest(
        messages=[{"role": "user", "content": "What's the difference between exam duration and link window?"}],
        conversation_id="cache-off-1",
        user_id="teacher-cache",
    )
    with patch("app.graphs.nodes.ainvoke_chat", fake):
        a = await complete(req)
        b = await complete(req)
    assert fake.await_count == 2
    assert a.message.content == "first how-to"
    assert b.message.content == "second how-to"
    assert not str(b.model).startswith("cache:")
