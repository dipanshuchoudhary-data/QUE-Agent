"""Embedding factory for QUE RAG (LangChain OpenAI-compatible client).

Uses the first configured chat API key (``LLM_API_KEY`` / ``LLM_API_KEY_N``)
and ``LLM_BASE_URL``. Chat round-robin does not apply — embeddings stay on
one key so the Chroma index stays consistent.
"""

from __future__ import annotations

from typing import Protocol

from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings, get_settings
from app.core.llm import LLMError


class EmbeddingsClient(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def get_embeddings(*, settings: Settings | None = None) -> OpenAIEmbeddings:
    """Build LangChain ``OpenAIEmbeddings`` pointed at the configured API."""
    cfg = settings or get_settings()
    keys = cfg.llm_api_keys
    if not keys:
        raise LLMError("LLM_API_KEY is not configured (required for embeddings)")
    return OpenAIEmbeddings(
        api_key=keys[0],
        base_url=cfg.llm_base_url,
        model=cfg.que_embedding_model,
        timeout=cfg.llm_timeout_seconds,
    )


def embed_texts(texts: list[str], *, settings: Settings | None = None) -> list[list[float]]:
    """Embed many documents (prototype warmup). Use embed_query_cached for queries."""
    if not texts:
        return []
    return get_embeddings(settings=settings).embed_documents(list(texts))
