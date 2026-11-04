"""Local MiniLM is opt-in and never shares the OpenRouter index."""

from app.core.config import Settings
from app.knowledge.embeddings import LocalSentenceTransformerEmbeddings, get_embeddings


def test_default_provider_keeps_openrouter_index_and_model():
    cfg = Settings(embedding_provider="openrouter", que_chroma_path="data/chroma")
    assert cfg.uses_local_embeddings is False
    assert cfg.active_chroma_path == "data/chroma"
    assert cfg.active_embedding_model == cfg.que_embedding_model


def test_local_provider_uses_a_separate_index_and_minilm():
    cfg = Settings(embedding_provider="local", que_chroma_path="data/chroma")
    assert cfg.uses_local_embeddings is True
    assert cfg.active_chroma_path == "data/chroma_local"
    assert cfg.active_chroma_path != cfg.que_chroma_path
    assert cfg.active_embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_development_local_providers_do_not_touch_the_api_index():
    cfg = Settings(
        APP_ENV="development",
        embedding_provider="local",
        reranker_provider="local",
        que_chroma_path="data/chroma",
    )
    assert cfg.is_local is True
    assert cfg.uses_local_embeddings is True
    assert cfg.uses_local_reranker is True
    assert cfg.active_chroma_path == "data/chroma_local"
    assert cfg.active_embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert cfg.active_rerank_model == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert cfg.expected_embedding_dim == 384


def test_local_rerank_does_not_call_an_api(monkeypatch):
    from app.knowledge.rerank import rerank_chunks
    from app.knowledge.store import RetrievedChunk

    class _Fake:
        def predict(self, pairs, **kwargs):
            assert kwargs["show_progress_bar"] is False
            return [0.1, 0.9]

    monkeypatch.setattr("app.knowledge.rerank._load_local_reranker", lambda *a, **k: _Fake())
    hits = [
        RetrievedChunk("a", "d", "p", "t", "s1", "low", 0.5, "1"),
        RetrievedChunk("b", "d", "p", "t", "s2", "high", 0.4, "1"),
    ]
    cfg = Settings(APP_ENV="development", embedding_provider="local", reranker_provider="local")
    ordered = rerank_chunks("q", hits, settings=cfg)
    assert [h.chunk_id for h in ordered] == ["b", "a"]
    assert ordered[0].score == 0.9


def test_local_embeddings_do_not_need_an_api_key(monkeypatch):
    class _Fake:
        def encode(self, texts, **kwargs):
            assert kwargs["normalize_embeddings"] is True
            return [[0.1, 0.2, 0.3] for _ in texts]

    monkeypatch.setattr(
        "app.knowledge.embeddings._load_local_model",
        lambda *args, **kwargs: _Fake(),
    )
    cfg = Settings(embedding_provider="local", llm_api_key="", local_embedding_model="sentence-transformers/all-MiniLM-L6-v2")
    client = get_embeddings(settings=cfg)
    assert isinstance(client, LocalSentenceTransformerEmbeddings)
    assert client.embed_query("ping") == [0.1, 0.2, 0.3]
    assert len(client.embed_documents(["a", "b"])) == 2
