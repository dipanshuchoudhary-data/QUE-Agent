"""Embedding factory for QUE RAG.

Default (``EMBEDDING_PROVIDER`` unset or not ``local``): LangChain OpenAI-compatible
client on one chat API key (``QUE_EMBEDDING_KEY_INDEX``) and ``LLM_BASE_URL``.

``EMBEDDING_PROVIDER=local``: cached ``sentence-transformers`` on CPU, loaded with
``local_files_only=True``. Indexing and queries both go through :func:`get_embeddings`,
and the vectors are stored under ``LOCAL_CHROMA_PATH``, never the OpenRouter index.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

import httpx
from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings, get_settings
from app.core.llm import LLMError

logger = logging.getLogger(__name__)

_MINILM = "sentence-transformers/all-MiniLM-L6-v2"
_MINILM_DIM = 384


class EmbeddingsClient(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class LocalSentenceTransformerEmbeddings:
    """CPU MiniLM client. The model object is cached so index and query share it."""

    def __init__(self, model_name: str, *, cache_folder: str, device: str) -> None:
        self._model = _load_local_model(model_name, cache_folder, device)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(x) for x in row] for row in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache(maxsize=2)
def _load_local_model(model_name: str, cache_folder: str, device: str):
    from sentence_transformers import SentenceTransformer

    kwargs: dict[str, object] = {"device": device or "cpu", "local_files_only": True}
    if cache_folder:
        kwargs["cache_folder"] = cache_folder
    model = SentenceTransformer(model_name, **kwargs)
    dim_fn = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
    dim = int(dim_fn() or 0)
    if model_name == _MINILM and dim != _MINILM_DIM:
        raise LLMError(f"{model_name} returned dimension {dim}, expected {_MINILM_DIM}")
    return model


@dataclass
class _Endpoint:
    name: str
    url: str
    key: str
    model: str
    extra: dict = field(default_factory=dict)
    down_until: float = 0.0


class PooledEmbeddings:
    """One embedding model served by two providers, used round robin with instant failover.

    NVIDIA (`input_type=query`) and OpenRouter return identical vectors for the same text
    (checked: cosine 1.0), so the pool is one vector space and either provider can embed
    the index or a query. Both always use *query* mode: the model is asymmetric and
    OpenRouter has no passage mode, so mixing modes would split the index across spaces.

    Each call starts at the next provider. A timeout, HTTP error or bad payload skips that
    provider at once (no sleep) and parks it for `que_embed_cooldown_seconds`. A shared
    keep-alive HTTP client avoids a TLS handshake per call.
    """

    BATCH = 16

    def __init__(self, endpoints: list[_Endpoint], *, timeout: float, cooldown: float) -> None:
        if not endpoints:
            raise LLMError("No embedding pool key configured (NVIDIA_EMB_DIPANSHU / OPENROUTER_EMB_DIPANSHU)")
        self._eps = endpoints
        self._cooldown = cooldown
        self._lock = threading.Lock()
        self._next = 0
        self._client = httpx.Client(timeout=httpx.Timeout(timeout, connect=min(timeout, 3.0)))

    def _order(self) -> list[_Endpoint]:
        now = time.monotonic()
        with self._lock:
            start = self._next
            self._next = (self._next + 1) % len(self._eps)
        rotated = self._eps[start:] + self._eps[:start]
        live = [e for e in rotated if e.down_until <= now]
        return live or rotated  # everything parked: try them anyway rather than fail

    def _call(self, ep: _Endpoint, texts: list[str]) -> list[list[float]]:
        body = {"model": ep.model, "input": texts, "encoding_format": "float", **ep.extra}
        resp = self._client.post(ep.url, json=body, headers={"Authorization": f"Bearer {ep.key}"})
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        vectors = [[float(x) for x in d["embedding"]] for d in data]
        if len(vectors) != len(texts):
            raise ValueError("embedding count mismatch")
        return vectors

    def _embed(self, texts: list[str]) -> list[list[float]]:
        last: Exception | None = None
        for ep in self._order():
            try:
                return self._call(ep, texts)
            except Exception as exc:  # noqa: BLE001 - any failure moves to the next provider
                last = exc
                ep.down_until = time.monotonic() + self._cooldown
                logger.warning("embed_provider_skipped provider=%s error=%s", ep.name, type(exc).__name__)
        raise LLMError(f"All embedding providers failed: {type(last).__name__ if last else 'unknown'}")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        texts = list(texts)
        for i in range(0, len(texts), self.BATCH):
            out.extend(self._embed(texts[i : i + self.BATCH]))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


_pool_lock = threading.Lock()
_pool: PooledEmbeddings | None = None
_pool_sig: tuple | None = None


def _get_pool(cfg: Settings) -> PooledEmbeddings:
    """One shared pool per process so round robin, cooldowns and the HTTP client persist."""
    global _pool, _pool_sig
    sig = (
        cfg.nvidia_emb_dipanshu, cfg.openrouter_emb_dipanshu, cfg.nvidia_emb_base_url, cfg.nvidia_emb_model,
        cfg.openrouter_emb_base_url, cfg.openrouter_emb_model, cfg.que_embed_timeout_seconds,
    )
    with _pool_lock:
        if _pool is None or sig != _pool_sig:
            eps: list[_Endpoint] = []
            if cfg.nvidia_emb_dipanshu.strip():
                eps.append(
                    _Endpoint(
                        "nvidia_emb_dipanshu",
                        cfg.nvidia_emb_base_url.rstrip("/") + "/embeddings",
                        cfg.nvidia_emb_dipanshu.strip(),
                        cfg.nvidia_emb_model,
                        {"input_type": "query", "truncate": "END"},
                    )
                )
            if cfg.openrouter_emb_dipanshu.strip():
                eps.append(
                    _Endpoint(
                        "openrouter_emb_dipanshu",
                        cfg.openrouter_emb_base_url.rstrip("/") + "/embeddings",
                        cfg.openrouter_emb_dipanshu.strip(),
                        cfg.openrouter_emb_model,
                    )
                )
            _pool = PooledEmbeddings(eps, timeout=cfg.que_embed_timeout_seconds, cooldown=cfg.que_embed_cooldown_seconds)
            _pool_sig = sig
        return _pool


def get_embeddings(*, settings: Settings | None = None) -> EmbeddingsClient:
    """Embeddings for the active provider. Index build and retrieval both call this."""
    cfg = settings or get_settings()
    if cfg.uses_embedding_pool:
        return _get_pool(cfg)
    if cfg.uses_local_embeddings:
        return LocalSentenceTransformerEmbeddings(
            cfg.local_embedding_model,
            cache_folder=cfg.local_embedding_cache.strip(),
            device=cfg.local_embedding_device.strip() or "cpu",
        )
    keys = cfg.llm_api_keys
    if not keys:
        raise LLMError("LLM_API_KEY is not configured (required for embeddings)")
    position = min(max(int(cfg.que_embedding_key_index), 1), len(keys)) - 1
    return OpenAIEmbeddings(
        api_key=keys[position],
        base_url=cfg.llm_base_url,
        model=cfg.que_embedding_model,
        timeout=cfg.llm_timeout_seconds,
    )


def embed_texts(texts: list[str], *, settings: Settings | None = None) -> list[list[float]]:
    """Embed many documents (prototype warmup). Use embed_query_cached for queries."""
    if not texts:
        return []
    return get_embeddings(settings=settings).embed_documents(list(texts))
