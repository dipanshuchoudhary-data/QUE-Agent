"""Application settings (pydantic-settings)."""

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="QUE-Agent", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    cors_allow_origins: str = Field(default="", alias="CORS_ALLOW_ORIGINS")

    que_service_key: str = Field(default="", alias="QUE_SERVICE_KEY")
    allow_insecure_local_no_auth: bool = Field(default=False, alias="ALLOW_INSECURE_LOCAL_NO_AUTH")

    # Shared with Quizzer Backend — used to verify browser Que access JWTs.
    # Separate from QUE_SERVICE_KEY (server-to-server only).
    que_jwt_secret: str = Field(default="", alias="QUE_JWT_SECRET")
    que_jwt_algorithm: str = Field(default="HS256", alias="QUE_JWT_ALGORITHM")
    que_jwt_audience: str = Field(default="que-agent", alias="QUE_JWT_AUDIENCE")
    que_jwt_issuer: str = Field(default="quizzer", alias="QUE_JWT_ISSUER")

    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_api_key_1: str = Field(default="", alias="LLM_API_KEY_1")
    llm_api_key_2: str = Field(default="", alias="LLM_API_KEY_2")
    llm_api_key_3: str = Field(default="", alias="LLM_API_KEY_3")
    llm_api_key_4: str = Field(default="", alias="LLM_API_KEY_4")
    llm_api_key_5: str = Field(default="", alias="LLM_API_KEY_5")
    llm_api_key_6: str = Field(default="", alias="LLM_API_KEY_6")
    llm_api_key_7: str = Field(default="", alias="LLM_API_KEY_7")
    llm_api_key_8: str = Field(default="", alias="LLM_API_KEY_8")
    llm_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_models_raw: str = Field(default="", alias="LLM_MODELS")
    llm_timeout_seconds: float = Field(default=45.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_tokens: int = Field(default=700, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.35, alias="LLM_TEMPERATURE")
    llm_gateway_rr: bool = Field(default=True, alias="LLM_GATEWAY_RR")
    llm_max_attempts: int = Field(default=3, alias="LLM_MAX_ATTEMPTS")
    llm_retry_base_ms: int = Field(default=200, alias="LLM_RETRY_BASE_MS")
    llm_retry_cap_ms: int = Field(default=2000, alias="LLM_RETRY_CAP_MS")

    # QUE-owned in-process cache (NOT Quizzer Redis).
    que_cache_enabled: bool = Field(default=True, alias="QUE_CACHE_ENABLED")
    que_cache_max_entries: int = Field(default=512, alias="QUE_CACHE_MAX_ENTRIES")
    que_cache_intent_ttl_seconds: float = Field(default=3600.0, alias="QUE_CACHE_INTENT_TTL_SECONDS")
    que_cache_llm_ttl_seconds: float = Field(default=900.0, alias="QUE_CACHE_LLM_TTL_SECONDS")
    que_cache_variant_ttl_seconds: float = Field(default=1800.0, alias="QUE_CACHE_VARIANT_TTL_SECONDS")
    que_cache_retrieval_ttl_seconds: float = Field(
        default=1800.0,
        alias="QUE_CACHE_RETRIEVAL_TTL_SECONDS",
    )

    # Short-term conversation memory (LangGraph MemorySaver, per worker).
    que_memory_enabled: bool = Field(default=True, alias="QUE_MEMORY_ENABLED")
    que_memory_max_turns: int = Field(default=20, alias="QUE_MEMORY_MAX_TURNS")

    # Phase 2 RAG — QUE-owned Chroma index (NOT Quizzer DB / Redis).
    # When enabled and an index exists at QUE_CHROMA_PATH, knowledge_node uses
    # dense top-K retrieval. Otherwise falls back to keyword select_knowledge.
    que_rag_enabled: bool = Field(default=True, alias="QUE_RAG_ENABLED")
    que_chroma_path: str = Field(default="data/chroma", alias="QUE_CHROMA_PATH")
    que_embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        alias="QUE_EMBEDDING_MODEL",
    )
    que_rag_top_k: int = Field(default=6, alias="QUE_RAG_TOP_K")
    # Cosine similarity floor (Chroma hnsw:space=cosine returns distance;
    # we convert to similarity = 1 - distance). Below this → honest no-answer.
    que_rag_min_score: float = Field(default=0.28, alias="QUE_RAG_MIN_SCORE")
    que_rag_fallback_keyword: bool = Field(
        default=True,
        alias="QUE_RAG_FALLBACK_KEYWORD",
    )
    # Phase 6 hybrid — BM25 + dense RRF (default on when corpus exists).
    que_rag_hybrid: bool = Field(default=True, alias="QUE_RAG_HYBRID")
    que_rag_candidate_k: int = Field(default=20, alias="QUE_RAG_CANDIDATE_K")
    que_rag_rrf_k: int = Field(default=60, alias="QUE_RAG_RRF_K")

    # Phase 4 insight tools (QUE → Quizzer internal API).
    que_tools_enabled: bool = Field(default=False, alias="QUE_TOOLS_ENABLED")
    quizzer_internal_base_url: str = Field(default="", alias="QUIZZER_INTERNAL_BASE_URL")
    que_tool_max_calls: int = Field(default=2, alias="QUE_TOOL_MAX_CALLS")
    que_tool_timeout_seconds: float = Field(default=3.0, alias="QUE_TOOL_TIMEOUT_SECONDS")
    que_tool_circuit_failures: int = Field(default=5, alias="QUE_TOOL_CIRCUIT_FAILURES")
    que_tool_circuit_ttl_seconds: float = Field(default=30.0, alias="QUE_TOOL_CIRCUIT_TTL_SECONDS")
    # Phase 7 bounded agent loop (multi-tool turns only).
    que_agent_max_steps: int = Field(default=3, alias="QUE_AGENT_MAX_STEPS")
    que_agent_max_execution_ms: int = Field(default=8000, alias="QUE_AGENT_MAX_EXECUTION_MS")
    que_agent_max_tool_chars: int = Field(default=12000, alias="QUE_AGENT_MAX_TOOL_CHARS")

    # Lenient in-process rate limiting on /v1/chat[/stream] — stops obvious
    # abuse (scripted hammering) without throttling normal typing.
    que_rate_limit_enabled: bool = Field(default=True, alias="QUE_RATE_LIMIT_ENABLED")
    que_rate_limit_per_minute: int = Field(default=60, alias="QUE_RATE_LIMIT_PER_MINUTE")
    que_rate_limit_burst: int = Field(default=20, alias="QUE_RATE_LIMIT_BURST")

    # Phase 10 — layered input/output guardrails (on top of Phase 5 policy).
    que_guardrails_enabled: bool = Field(default=True, alias="QUE_GUARDRAILS_ENABLED")

    # Phase 11 — sampled online eval JSONL (hashed ids only; off by default).
    que_eval_online_sample: bool = Field(default=False, alias="QUE_EVAL_ONLINE_SAMPLE")
    que_eval_online_rate: float = Field(default=0.05, alias="QUE_EVAL_ONLINE_RATE")
    que_eval_online_path: str = Field(
        default="data/eval_online.jsonl",
        alias="QUE_EVAL_ONLINE_PATH",
    )

    # Phase 12 — observability + cost (in-process; not Datadog).
    que_obs_jsonl: str = Field(default="", alias="QUE_OBS_JSONL")
    que_obs_ring_size: int = Field(default=512, alias="QUE_OBS_RING_SIZE")
    que_budget_llm_calls_per_turn: int = Field(default=3, alias="QUE_BUDGET_LLM_CALLS_PER_TURN")
    que_budget_tokens_per_turn: int = Field(default=16000, alias="QUE_BUDGET_TOKENS_PER_TURN")
    que_budget_usd_per_user_hour: float = Field(
        default=0.50,
        alias="QUE_BUDGET_USD_PER_USER_HOUR",
    )
    # Confirmed write-tool executions (publish/notify/delete) per user per hour.
    # Independent of the LLM/tool budgets above — caps mutation blast radius.
    que_budget_write_actions_per_hour: int = Field(
        default=20,
        alias="QUE_BUDGET_WRITE_ACTIONS_PER_HOUR",
    )
    que_alert_error_rate: float = Field(default=0.35, alias="QUE_ALERT_ERROR_RATE")
    que_alert_usd_per_minute: float = Field(default=0.25, alias="QUE_ALERT_USD_PER_MINUTE")
    que_alert_cooldown_seconds: float = Field(default=60.0, alias="QUE_ALERT_COOLDOWN_SECONDS")

    # Phase 13 — LLM provider circuit (tools already have a breaker).
    que_llm_circuit_failures: int = Field(default=5, alias="QUE_LLM_CIRCUIT_FAILURES")
    que_llm_circuit_ttl_seconds: float = Field(default=30.0, alias="QUE_LLM_CIRCUIT_TTL_SECONDS")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8100, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() in {"local", "dev", "development"}

    @property
    def cors_origins(self) -> list[str]:
        if not self.cors_allow_origins.strip():
            return []
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def llm_api_keys(self) -> tuple[str, ...]:
        """Deduped chat/embedding keys: LLM_API_KEY then LLM_API_KEY_1…8."""
        ordered = (
            self.llm_api_key,
            self.llm_api_key_1,
            self.llm_api_key_2,
            self.llm_api_key_3,
            self.llm_api_key_4,
            self.llm_api_key_5,
            self.llm_api_key_6,
            self.llm_api_key_7,
            self.llm_api_key_8,
        )
        seen: list[str] = []
        for raw in ordered:
            key = (raw or "").strip()
            if key and key not in seen:
                seen.append(key)
        return tuple(seen)

    @property
    def llm_models(self) -> tuple[str, ...]:
        """Chat model pool. LLM_MODELS wins; else LLM_MODEL."""
        raw = (self.llm_models_raw or "").strip()
        if raw:
            return tuple(part.strip() for part in raw.split(",") if part.strip())
        model = (self.llm_model or "").strip()
        return (model,) if model else ()

    @property
    def llm_gateway_rr_active(self) -> bool:
        if not self.llm_gateway_rr:
            return False
        return len(self.llm_api_keys) >= 2 or len(self.llm_models) >= 2

    @field_validator("que_jwt_secret", "que_service_key")
    @classmethod
    def strip_secrets(cls, value: str) -> str:
        return (value or "").strip()

    @model_validator(mode="after")
    def enforce_production_guards(self) -> "Settings":
        if not self.is_local:
            if self.allow_insecure_local_no_auth:
                raise ValueError("ALLOW_INSECURE_LOCAL_NO_AUTH cannot be true outside local/dev")
            weak = {
                "change-me-to-a-long-random-secret",
                "changeme",
                "secret",
                "",
            }
            if not self.que_jwt_secret or self.que_jwt_secret in weak or len(self.que_jwt_secret) < 32:
                raise ValueError(
                    "QUE_JWT_SECRET must be a strong secret (≥32 chars) in non-local environments"
                )
            # Service key remains required for future QUE→Quizzer tool calls / ops.
            if not self.que_service_key or self.que_service_key in weak:
                raise ValueError("QUE_SERVICE_KEY must be set to a strong secret in non-local environments")
            if not self.llm_api_key.strip() and not any(
                getattr(self, f"llm_api_key_{i}").strip() for i in range(1, 9)
            ):
                raise ValueError(
                    "LLM_API_KEY (or LLM_API_KEY_1..8) must be set in non-local environments "
                    "— otherwise chat silently fails at request time instead of at boot"
                )
            if not self.cors_allow_origins.strip():
                raise ValueError(
                    "CORS_ALLOW_ORIGINS must be set in non-local environments "
                    "(empty means the browser client cannot reach QUE at all)"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
