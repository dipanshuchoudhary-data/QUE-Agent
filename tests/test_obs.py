"""Phase 12 — traces, percentiles, cost table, budgets, ops metrics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.config import Settings, get_settings
from app.core.llm import ChatLane, last_llm_usage
from app.obs.budget import (
    CAPACITY_REPLY,
    allow_llm_call,
    record_user_usd,
    reset_budgets,
    start_turn_budget,
    user_hour_exceeded,
)
from app.obs.cost import TokenUsage, extract_usage, usd_for_usage
from app.obs.metrics import percentile, record_turn, reset_obs, snapshot
from app.obs.trace import TurnTrace, hash_user_id, new_trace
from app.orchestration.pipeline import complete
from app.schemas.chat import ChatRequest

_TEST_LANE = ChatLane(model="test-model", key_index=0, api_key="test")


def test_percentiles_p50_p95_p99():
    vals = [float(i) for i in range(1, 101)]
    assert percentile(vals, 50) == 50.0
    assert percentile(vals, 95) == 95.0
    assert percentile(vals, 99) == 99.0
    assert percentile([], 50) is None
    assert percentile([7.0], 99) == 7.0


def test_cost_table_paid_free_unknown():
    paid = TokenUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000, model="openai/gpt-4o-mini")
    assert usd_for_usage(paid) == round(0.15 + 0.60, 8)
    free = TokenUsage(prompt_tokens=100, completion_tokens=20, model="google/gemma-4-31b-it:free")
    assert usd_for_usage(free) == 0.0
    unknown = TokenUsage(prompt_tokens=10, completion_tokens=10, model="some/vendor-model")
    assert usd_for_usage(unknown) is None
    assert usd_for_usage(TokenUsage(model="")) is None


def test_extract_usage_from_usage_metadata():
    class _Msg:
        usage_metadata = {"input_tokens": 12, "output_tokens": 4}
        response_metadata = {}
        content = "ok"

    usage = extract_usage(_Msg(), model="openai/gpt-4o-mini")
    assert usage.prompt_tokens == 12
    assert usage.completion_tokens == 4
    assert usage.total == 16


def test_extract_usage_reasoning_tokens():
    class _Msg:
        usage_metadata = {}
        response_metadata = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 1400,
                "completion_tokens_details": {"reasoning_tokens": 1280},
            }
        }
        content = "ok"

    usage = extract_usage(_Msg(), model="nvidia/nemotron-3.5-lightning:free")
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 1400
    assert usage.reasoning_tokens == 1280


def test_snapshot_includes_percentiles_and_zero_cost_success(monkeypatch):
    reset_obs()
    for ms in (10.0, 20.0, 30.0, 40.0):
        trace = new_trace(request_id=f"r{ms}", user_id="u1", route="knowledge", freshness="static")
        trace.model = "canned:greeting"
        trace.cost_usd = 0.0
        record_turn(trace, latency_ms=ms)
    snap = snapshot()
    assert snap["n"] == 4
    assert snap["latency_ms"]["p50"] is not None
    assert snap["cost_per_successful_task"] == 0.0
    assert hash_user_id("u1") != "u1"


def test_tiny_token_budget_skips_llm_before_ainvoke():
    reset_budgets()
    start_turn_budget(request_id="t-budget", user_id="u1")
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
        que_budget_tokens_per_turn=8,
        llm_max_tokens=700,
        que_budget_usd_per_user_hour=0.0,
    )
    ok, reason = allow_llm_call(
        "t-budget",
        messages=[HumanMessage(content="x" * 80)],
        settings=cfg,
    )
    assert ok is False
    assert reason == "budget:turn"


@pytest.mark.asyncio
async def test_complete_tiny_token_budget_does_not_call_llm(monkeypatch):
    monkeypatch.setenv("QUE_BUDGET_TOKENS_PER_TURN", "8")
    get_settings.cache_clear()
    fake = AsyncMock(return_value=(AIMessage(content="should not run"), _TEST_LANE))
    with patch("app.graphs.nodes.ainvoke_chat", fake):
        response = await complete(
            ChatRequest(
                messages=[{"role": "user", "content": "What's the difference between exam duration and link window?"}],
                conversation_id="budget-1",
                user_id="teacher-1",
            )
        )
    assert fake.await_count == 0
    assert response.message.content == CAPACITY_REPLY
    assert response.model == "budget:turn"
    snap = snapshot()
    assert snap["budget_breaches"] >= 1


@pytest.mark.asyncio
async def test_user_hour_usd_budget_skips_llm():
    reset_budgets()
    record_user_usd("teacher-hour", 1.0)
    assert user_hour_exceeded(
        "teacher-hour",
        settings=Settings(
            APP_ENV="local",
            QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
            que_budget_usd_per_user_hour=0.50,
        ),
    )
    fake = AsyncMock(return_value=(AIMessage(content="should not run"), _TEST_LANE))
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
        que_budget_usd_per_user_hour=0.50,
        que_budget_tokens_per_turn=32000,
    )
    with patch("app.graphs.nodes.ainvoke_chat", fake), patch(
        "app.orchestration.pipeline.get_settings",
        return_value=cfg,
    ):
        response = await complete(
            ChatRequest(
                messages=[{"role": "user", "content": "What's the difference between exam duration and link window?"}],
                conversation_id="budget-2",
                user_id="teacher-hour",
            ),
            settings=cfg,
        )
    assert fake.await_count == 0
    assert response.model == "budget:user"
    assert response.message.content == CAPACITY_REPLY


def test_ops_metrics_requires_service_key(client, service_key, que_jwt_secret):
    assert client.get("/v1/ops/metrics").status_code == 401
    token = jwt.encode(
        {
            "sub": "user-ops",
            "typ": "que_access",
            "aud": "que-agent",
            "iss": "quizzer",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        que_jwt_secret,
        algorithm="HS256",
    )
    jwt_resp = client.get(
        "/v1/ops/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert jwt_resp.status_code == 401
    ok = client.get("/v1/ops/metrics", headers={"X-Que-Service-Key": service_key})
    assert ok.status_code == 200
    body = ok.json()
    assert "latency_ms" in body
    assert "p50" in body["latency_ms"]
    assert "alerts" in body


def test_alert_window_sets_que_alert(caplog):
    reset_obs()
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
        que_alert_error_rate=0.2,
        que_alert_cooldown_seconds=60,
        que_alert_usd_per_minute=99,
    )
    for i in range(10):
        trace = TurnTrace(
            request_id=f"err{i}",
            user_hash="abcd",
            error=True,
            model="test",
        )
        record_turn(trace, latency_ms=5.0, settings=cfg)
    snap = snapshot(settings=cfg)
    assert any(a["kind"] == "error_rate" for a in snap["alerts"])


def test_hash_user_id_is_stable_and_short():
    assert hash_user_id("alice") == hash_user_id("alice")
    assert hash_user_id("alice") != hash_user_id("bob")
    assert len(hash_user_id("alice")) == 16


def test_last_llm_usage_defaults_empty():
    usage = last_llm_usage()
    assert usage.prompt_tokens >= 0
