"""Dense RAG ingest + retrieve tests with fake embeddings (no API)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from tests.conftest import requires_knowledge

from app.core.config import Settings, get_settings
from app.knowledge.chunking import chunk_markdown
from app.knowledge.dense import select_dense
from app.knowledge.ingest import build_index
from app.knowledge.paths import MANIFEST_PATH
from app.knowledge.retrieve import select_knowledge
from app.knowledge.store import (
    IndexState,
    delete_doc_chunks,
    index_ready,
    query_chunks,
    save_index_state,
    upsert_chunks,
    wipe_collection,
)


class FakeEmbeddings:
    """Deterministic bag-of-token vectors — enough for same-topic nearest neighbor."""

    dim = 64

    def _vec(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        base = [((digest[i % len(digest)] / 255.0) * 2 - 1) for i in range(self.dim)]
        for token in text.casefold().split():
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            base[h % self.dim] += 1.0
        norm = sum(x * x for x in base) ** 0.5 or 1.0
        return [x / norm for x in base]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


@pytest.fixture()
def rag_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    chroma = tmp_path / "chroma"
    monkeypatch.setenv("QUE_CHROMA_PATH", str(chroma))
    monkeypatch.setenv("QUE_RAG_ENABLED", "true")
    monkeypatch.setenv("QUE_RAG_MIN_SCORE", "0.05")
    monkeypatch.setenv("QUE_EMBEDDING_MODEL", "fake/hash-emb")
    monkeypatch.setenv("APP_ENV", "local")
    get_settings.cache_clear()
    settings = Settings(
        app_env="local",
        que_chroma_path=str(chroma),
        que_rag_enabled=True,
        que_rag_min_score=0.05,
        que_embedding_model="fake/hash-emb",
        que_rag_top_k=5,
        que_rag_fallback_keyword=True,
    )
    yield settings
    get_settings.cache_clear()
    try:
        wipe_collection(settings)
    except Exception:  # noqa: BLE001
        pass


def test_upsert_and_query_roundtrip(rag_settings: Settings):
    emb = FakeEmbeddings()
    chunks = chunk_markdown(
        doc_id="creating-exams",
        path="exams/creating-exams.md",
        title="Creating Exams",
        raw_markdown="## Create\n\nClick **Create Exam** to start a new quiz.\n",
        corpus_version="test",
    )
    assert chunks
    vectors = emb.embed_documents([c.text for c in chunks])
    wipe_collection(rag_settings)
    upsert_chunks(chunks, vectors, embedding_model="fake/hash-emb", settings=rag_settings)
    save_index_state(
        IndexState(
            embedding_model="fake/hash-emb",
            corpus_version="test",
            updated_at="now",
            documents={
                "creating-exams": {
                    "content_hash": "x",
                    "chunk_count": len(chunks),
                    "path": "exams/creating-exams.md",
                    "corpus_version": "test",
                }
            },
        ),
        rag_settings,
    )
    assert index_ready(rag_settings)
    hits = query_chunks(
        emb.embed_query("How do I create an exam?"),
        top_k=3,
        settings=rag_settings,
    )
    assert hits
    assert hits[0].doc_id == "creating-exams"


def test_delete_retires_doc(rag_settings: Settings):
    emb = FakeEmbeddings()
    chunks = chunk_markdown(
        doc_id="arena",
        path="arena/arena.md",
        title="Arena",
        raw_markdown="## Host\n\nHost an Arena battle with a room code.\n",
        corpus_version="test",
    )
    wipe_collection(rag_settings)
    upsert_chunks(
        chunks,
        emb.embed_documents([c.text for c in chunks]),
        embedding_model="fake/hash-emb",
        settings=rag_settings,
    )
    deleted = delete_doc_chunks("arena", settings=rag_settings)
    assert deleted >= 1
    hits = query_chunks(emb.embed_query("Arena room code"), top_k=3, settings=rag_settings)
    assert all(h.doc_id != "arena" for h in hits)


@requires_knowledge
def test_build_index_incremental(rag_settings: Settings):
    if not MANIFEST_PATH.is_file():
        pytest.skip("knowledge/ not present")

    emb = FakeEmbeddings()
    report1 = build_index(settings=rag_settings, embeddings=emb, force=True)
    assert report1.docs_upserted >= 1
    assert report1.chunks_upserted >= 1
    report2 = build_index(settings=rag_settings, embeddings=emb, force=False)
    assert report2.docs_unchanged == report2.docs_total
    assert report2.docs_upserted == 0


@requires_knowledge
def test_dense_no_answer_path(rag_settings: Settings):
    if not MANIFEST_PATH.is_file():
        pytest.skip("knowledge/ not present")

    emb = FakeEmbeddings()
    build_index(settings=rag_settings, embeddings=emb, force=True)
    high = Settings(
        app_env="local",
        que_chroma_path=rag_settings.que_chroma_path,
        que_rag_enabled=True,
        que_rag_min_score=0.99,
        que_embedding_model="fake/hash-emb",
        que_rag_top_k=5,
    )
    sel = select_dense(
        "zzzz unrelated quantum pineapple weather xyz",
        settings=high,
        embeddings=emb,
    )
    assert sel is not None
    assert sel.no_answer is True
    assert "not sure" in sel.content.casefold() or "not sufficiently relevant" in sel.content.casefold()
    assert "core" in sel.pack_ids


def test_select_knowledge_falls_back_to_keyword():
    sel = select_knowledge(
        [{"role": "user", "content": "How do I create a quiz?"}],
        settings=Settings(
            app_env="local",
            que_rag_enabled=True,
            que_chroma_path="data/chroma-missing-for-test",
            que_rag_fallback_keyword=True,
        ),
    )
    assert sel.mode in {"keyword", "dense_unavailable_keyword"}
    assert sel.pack_ids
    assert "creating-exams" in sel.pack_ids
    # ≥2 retrieved packs skip the CORE skeleton; thin hits still include it.
    if len(sel.pack_ids) < 2:
        assert "core" in sel.pack_ids
    assert len(sel.content) < 6_000
