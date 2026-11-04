"""Production config guards — fail at boot, not at request time."""

from __future__ import annotations

import pytest

from app.core.config import Settings


def _base(**overrides) -> dict:
    base = dict(
        APP_ENV="production",
        QUE_JWT_SECRET="a-strong-random-secret-that-is-long-enough-32c",
        QUE_SERVICE_KEY="another-strong-random-secret-key",
        LLM_API_KEY="sk-real-key",
        CORS_ALLOW_ORIGINS="https://app.quizzer.example",
    )
    base.update(overrides)
    return base


def test_production_settings_ok_with_all_guards_set():
    Settings(**_base())  # should not raise


def test_production_requires_llm_api_key():
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        Settings(**_base(LLM_API_KEY="", LLM_API_KEY_1="", LLM_API_KEY_2="", LLM_API_KEY_3="",
                          LLM_API_KEY_4="", LLM_API_KEY_5="", LLM_API_KEY_6="", LLM_API_KEY_7="",
                          LLM_API_KEY_8=""))


def test_production_accepts_numbered_llm_api_key():
    Settings(**_base(LLM_API_KEY="", LLM_API_KEY_1="sk-real-key"))  # should not raise


def test_production_requires_cors_origins():
    with pytest.raises(ValueError, match="CORS_ALLOW_ORIGINS"):
        Settings(**_base(CORS_ALLOW_ORIGINS=""))


def test_production_requires_strong_jwt_secret():
    with pytest.raises(ValueError, match="QUE_JWT_SECRET"):
        Settings(**_base(QUE_JWT_SECRET="short"))


def test_production_rejects_local_embedding_provider():
    with pytest.raises(ValueError, match="EMBEDDING_PROVIDER=local"):
        Settings(**_base(EMBEDDING_PROVIDER="local"))


def test_production_rejects_local_reranker_provider():
    with pytest.raises(ValueError, match="RERANKER_PROVIDER=local"):
        Settings(**_base(RERANKER_PROVIDER="local"))


def test_production_existing_api_stays_on_the_api_index():
    cfg = Settings(**_base(EMBEDDING_PROVIDER="existing_api", RERANKER_PROVIDER="existing_api"))
    assert cfg.uses_local_embeddings is False
    assert cfg.uses_local_reranker is False
    assert cfg.resolved_embedding_provider == "openrouter"
    assert cfg.active_chroma_path == cfg.que_chroma_path
    assert cfg.active_embedding_model == cfg.que_embedding_model


def test_production_requires_llm_key_instead_of_falling_back_local():
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        Settings(**_base(
            EMBEDDING_PROVIDER="existing_api",
            LLM_API_KEY="",
            LLM_API_KEY_1="",
            LLM_API_KEY_2="",
            LLM_API_KEY_3="",
            LLM_API_KEY_4="",
            LLM_API_KEY_5="",
            LLM_API_KEY_6="",
            LLM_API_KEY_7="",
            LLM_API_KEY_8="",
        ))


def test_local_env_does_not_enforce_any_guard():
    Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="",
        QUE_SERVICE_KEY="",
        LLM_API_KEY="",
        CORS_ALLOW_ORIGINS="",
    )  # should not raise
