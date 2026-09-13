"""LangSmith dual-control + input redaction smoke tests."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.llm import ChatLane, _redact_lane_inputs


def test_production_blocks_langsmith_without_dual_control():
    with pytest.raises(ValueError, match="LangSmith"):
        Settings(
            APP_ENV="production",
            QUE_JWT_SECRET="x" * 40,
            QUE_SERVICE_KEY="y" * 40,
            LLM_API_KEY="sk-test",
            CORS_ALLOW_ORIGINS="https://app.example.com",
            LANGSMITH_TRACING=True,
            ALLOW_LANGSMITH_IN_PROD=False,
        )


def test_production_allows_langsmith_with_dual_control(monkeypatch):
    s = Settings(
        APP_ENV="production",
        QUE_JWT_SECRET="x" * 40,
        QUE_SERVICE_KEY="y" * 40,
        LLM_API_KEY="sk-test",
        CORS_ALLOW_ORIGINS="https://app.example.com",
        LANGSMITH_TRACING=True,
        ALLOW_LANGSMITH_IN_PROD=True,
        LANGSMITH_PROJECT="Que_agent",
        LANGSMITH_ENDPOINT="https://api.smith.langchain.com",
        LANGSMITH_API_KEY="lsv2_test",
    )
    assert s.langsmith_tracing is True
    assert s.langsmith_project == "Que_agent"


def test_redact_lane_inputs_strips_api_key():
    lane = ChatLane(model="openai/gpt-4o-mini", key_index=2, api_key="sk-secret")
    out = _redact_lane_inputs({"lane": lane, "api_key": "sk-secret", "attempt": 1})
    assert "api_key" not in out
    assert out["lane"] == {"model": "openai/gpt-4o-mini", "key_index": 2}
