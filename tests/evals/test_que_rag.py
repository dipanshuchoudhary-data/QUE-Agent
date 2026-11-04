"""Hybrid retrieval eval for QUE (DeepEval, LLM-judged).

Runs the production retriever (dense + BM25, document-level fusion, top 3) on
the human-verified golden set in evals/retriever_goldens.json and scores:
contextual recall, contextual precision, contextual relevancy. Guide-id match
is recorded as a diagnostic only.

Skipped unless RUN_QUE_RAG_EVALS=1. The offline CI suite still scores keyword
recall and never calls the judge.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from tests.evals.metrics import (
    PRECISION_THRESHOLD,
    RECALL_THRESHOLD,
    RELEVANCY_THRESHOLD,
    guide_id_diagnostic,
    judge_retrieval,
)

from app.knowledge.hybrid import select_hybrid

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_QUE_RAG_EVALS") != "1",
    reason="QUE hybrid RAG eval calls the embedding index and the DeepEval judge.",
)

_ROOT = Path(__file__).resolve().parents[2]
_GOLDENS_PATH = _ROOT / "evals" / "retriever_goldens.json"


def _restore_live_llm_env() -> None:
    """pytest blanks provider keys. This opt-in file puts the local .env back."""
    from dotenv import dotenv_values

    from app.core.config import get_settings

    values = dotenv_values(_ROOT / ".env")
    keys = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "LLM_MODELS"]
    keys.extend(f"LLM_API_KEY_{index}" for index in range(1, 9))
    for key in keys:
        value = (values.get(key) or "").strip()
        if value:
            os.environ[key] = value
    get_settings.cache_clear()


def _load_rows() -> list[dict]:
    if not _GOLDENS_PATH.is_file():
        return []
    rows = json.loads(_GOLDENS_PATH.read_text(encoding="utf-8")).get("goldens", [])
    if os.environ.get("RUN_QUE_RAG_INCLUDE_UNVERIFIED") == "1":
        # Provisional local run only. Never the gate.
        return [row for row in rows if not row.get("rejected")]
    # Unreviewed rows never enter the gate.
    return [row for row in rows if row.get("human_verified")]


_ROWS = _load_rows()
_ANSWER_ROWS = [row for row in _ROWS if not row.get("expect_no_answer")]
_NO_ANSWER_ROWS = [row for row in _ROWS if row.get("expect_no_answer")]


def _retrieved_chunks(query: str) -> tuple[list[str], bool]:
    _restore_live_llm_env()
    selection = select_hybrid(query)
    if selection is None:
        pytest.fail("Hybrid index is not ready. Run: uv run python -m app.knowledge")
    chunks = [
        f"[{hit.doc_id}] {hit.section}\n{hit.text}".strip()
        for hit in selection.hits
        if hit.doc_id and hit.doc_id != "core"
    ]
    return chunks, bool(selection.no_answer)


@pytest.mark.parametrize("row", _ANSWER_ROWS, ids=[row["id"] for row in _ANSWER_ROWS])
def test_hybrid_retrieval(row: dict, record_property):
    chunks, no_answer = _retrieved_chunks(row["query"])
    diagnostic = guide_id_diagnostic(list(row.get("expected_doc_ids") or []), chunks)
    record_property("guide_id_diagnostic", json.dumps(diagnostic))
    record_property("injected_chars", sum(len(chunk) for chunk in chunks))
    assert not no_answer, f"{row['id']} abstained on an in-domain query"
    assert chunks, f"{row['id']} retrieved no guide text"
    # One judge call returns all three scores.
    scores = judge_retrieval(row["query"], row["expected_output"], chunks)
    assert scores["ContextualRecallMetric"]["score"] >= RECALL_THRESHOLD, scores
    assert scores["ContextualPrecisionMetric"]["score"] >= PRECISION_THRESHOLD, scores
    assert scores["ContextualRelevancyMetric"]["score"] >= RELEVANCY_THRESHOLD, scores


@pytest.mark.parametrize("row", _NO_ANSWER_ROWS, ids=[row["id"] for row in _NO_ANSWER_ROWS])
def test_out_of_domain_abstains(row: dict):
    _chunks, no_answer = _retrieved_chunks(row["query"])
    assert no_answer, f"{row['id']} retrieved product guides for an out-of-domain query"
