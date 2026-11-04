"""Retriever scores for QUE.

One Gemini call per question returns contextual recall, precision, and relevancy.
The three numbers are still reported separately. Guide-id match is a diagnostic
only: a neighboring guide can answer a question, so the id check never decides
pass or fail.
"""

from __future__ import annotations

import re

from evals.judge import QueJudge
from pydantic import BaseModel, Field

_DOC_ID_RE = re.compile(r"^\[([^\]]+)\]")

# Provisional. Frozen after the first judged run (see evals/RETRIEVER_EVAL.md).
RECALL_THRESHOLD = 0.7
PRECISION_THRESHOLD = 0.7
RELEVANCY_THRESHOLD = 0.7

_PROMPT = """Score this retriever. Use only the question, the expected answer, and the chunks below.

contextual_recall: fraction of the facts in the expected answer that appear in the chunks. 1 means every needed fact is there. 0 means none are.
contextual_precision: whether chunks that contain those facts are ranked above chunks that do not. 1 means relevant chunks come first. 0 means the top chunks are noise, or the facts are missing.
contextual_relevancy: fraction of the retrieved text that is about this question. 1 means no noise. 0 means none of it is about the question.

Each score is a number from 0 to 1. Each reason is one sentence.

Question:
{query}

Expected answer:
{expected}

Retrieved chunks, rank 1 first:
{chunks}
"""


def retrieved_doc_ids(retrieval_context: list[str]) -> list[str]:
    """Guide ids parsed from the ``[doc_id]`` prefix of each retrieved chunk."""
    found: list[str] = []
    for chunk in retrieval_context or []:
        match = _DOC_ID_RE.match(chunk or "")
        if match and match.group(1) not in found:
            found.append(match.group(1))
    return found


def guide_id_diagnostic(expected_doc_ids: list[str], retrieval_context: list[str]) -> dict:
    expected = [doc for doc in expected_doc_ids if doc and doc != "core"]
    got = retrieved_doc_ids(retrieval_context)
    hit = [doc for doc in expected if doc in got]
    return {
        "expected": expected,
        "retrieved": got,
        "missing": [doc for doc in expected if doc not in got],
        "recall": (len(hit) / len(expected)) if expected else None,
    }


class _Score(BaseModel):
    score: float = Field(ge=0, le=1)
    reason: str


class RetrievalJudgement(BaseModel):
    contextual_recall: _Score
    contextual_precision: _Score
    contextual_relevancy: _Score


def judge_retrieval(
    query: str,
    expected_output: str,
    chunks: list[str],
    judge: QueJudge | None = None,
) -> dict[str, dict]:
    """One Gemini call. Keys match the summary the baseline file already uses."""
    judge = judge or QueJudge()
    numbered = "\n\n".join(f"[{index}] {chunk}" for index, chunk in enumerate(chunks, start=1))
    judged = judge.generate(
        _PROMPT.format(query=query, expected=expected_output, chunks=numbered or "(none)"),
        schema=RetrievalJudgement,
    )
    if not isinstance(judged, RetrievalJudgement):
        judged = RetrievalJudgement.model_validate(judged)
    return {
        "ContextualRecallMetric": judged.contextual_recall.model_dump(),
        "ContextualPrecisionMetric": judged.contextual_precision.model_dump(),
        "ContextualRelevancyMetric": judged.contextual_relevancy.model_dump(),
    }
