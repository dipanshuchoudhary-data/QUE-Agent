"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.knowledge import knowledge_available

# Configure env BEFORE importing the app / settings cache.
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("QUE_SERVICE_KEY", "test-service-key-not-for-production")
os.environ.setdefault(
    "QUE_JWT_SECRET",
    "test-que-jwt-secret-not-for-production-32c",
)
os.environ.setdefault("ALLOW_INSECURE_LOCAL_NO_AUTH", "false")
# Override local .env numbered keys so tests never hit a live provider.
os.environ["LLM_API_KEY"] = ""
for _i in range(1, 9):
    os.environ[f"LLM_API_KEY_{_i}"] = ""
# Local .env may select the nvidia_pool embeddings (2048 dims, live keys). Tests
# use fake embeddings and must not depend on it.
os.environ["EMBEDDING_PROVIDER"] = "existing_api"
os.environ["NVIDIA_EMB_DIPANSHU"] = ""
os.environ["OPENROUTER_EMB_DIPANSHU"] = ""
os.environ["QUE_EMBEDDING_MODEL"] = "openai/text-embedding-3-large"
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("QUE_BUDGET_TOKENS_PER_TURN", "32000")
os.environ.setdefault("QUE_BUDGET_USD_PER_USER_HOUR", "0")

# knowledge/ is gitignored — pack-content tests need a local checkout.
requires_knowledge = pytest.mark.skipif(
    not knowledge_available(),
    reason="knowledge/ packs not present (gitignored; local checkout required)",
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.core.config import get_settings
    from app.core.llm import reset_gateway_counters
    from app.core.que_cache import reset_que_caches
    from app.core.ratelimit import reset_rate_limits
    from app.graphs.que_graph import get_que_graph
    from app.obs.budget import reset_budgets
    from app.obs.metrics import reset_obs
    from app.orchestration.pending_actions import reset_pending_actions
    from app.tools.executor import reset_tool_circuit

    get_settings.cache_clear()
    get_que_graph.cache_clear()
    reset_que_caches()
    reset_obs()
    reset_budgets()
    reset_gateway_counters()
    reset_tool_circuit()
    reset_pending_actions()
    reset_rate_limits()
    yield
    get_settings.cache_clear()
    get_que_graph.cache_clear()
    reset_que_caches()
    reset_obs()
    reset_budgets()
    reset_gateway_counters()
    reset_tool_circuit()
    reset_pending_actions()
    reset_rate_limits()


@pytest.fixture
def service_key() -> str:
    return os.environ["QUE_SERVICE_KEY"]


@pytest.fixture
def que_jwt_secret() -> str:
    return os.environ["QUE_JWT_SECRET"]


@pytest.fixture
def client() -> TestClient:
    # Import after env is set so Settings() picks up test values.
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
