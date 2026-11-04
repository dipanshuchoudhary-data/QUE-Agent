"""Claim-level LLM judging with scores computed in code.

The LLM only makes semantic decisions: it splits text into claims and picks one label per
claim from a closed set. It never writes a number. Every metric score is an arithmetic
function of those labels, so a score can only move when a label moves.

Two judge calls per row (a third pass runs only where two passes disagree):

  retriever call  reference claims vs chunks     -> recall, precision, relevancy
  generator call  answer vs chunks and reference -> faithfulness, answer_relevancy, correctness

Reference claims are frozen once per golden answer in ``evals/golden_claims.json``.
A missing or malformed label raises; it is never turned into a score.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_FILE = ROOT / "evals" / "golden_claims.json"

PROMPT_VERSION = "claims-v1"

CLAIM_SUPPORT = {"supported": 1.0, "partial": 0.5, "unsupported": 0.0, "contradicted": 0.0}
CHUNK_REL = {"relevant": 1.0, "partly": 0.5, "not_relevant": 0.0}


class _Claims(BaseModel):
    claims: list[str]


class _RefLabel(BaseModel):
    claim_index: int
    label: Literal["supported", "partial", "unsupported", "contradicted"]
    chunks: list[int]
    note: str


class _ChunkLabel(BaseModel):
    chunk: int
    label: Literal["relevant", "partly", "not_relevant"]


class _RetrieverVerdict(BaseModel):
    reference_claims: list[_RefLabel]
    chunks: list[_ChunkLabel]


class _AnswerClaim(BaseModel):
    claim: str
    label: Literal["supported", "unsupported", "contradicted"]
    chunks: list[int]
    note: str


class _Statement(BaseModel):
    statement: str
    label: Literal["addresses_question", "off_topic"]


class _Coverage(BaseModel):
    claim_index: int
    label: Literal["conveyed", "partial", "missing", "contradicted"]
    note: str


class _GeneratorVerdict(BaseModel):
    answer_claims: list[_AnswerClaim]
    statements: list[_Statement]
    reference_coverage: list[_Coverage]


_EXTRACT = """Split the reference answer below into atomic claims.

Rules:
- One claim = one checkable fact or one step. Do not merge two facts into one claim.
- Keep the original meaning and wording. Add nothing. Drop pure greetings.
- Keep the original order.

Reference answer:
{text}

Return JSON: {{"claims": ["...", "..."]}}"""

_RETRIEVER = """You check retrieved text for a product-help assistant. Use ONLY the text below. Write no scores.

Question:
{query}

Reference claims (numbered from 0):
{claims}

Retrieved chunks (numbered from 1, rank 1 first):
{chunks}

Task A. For EVERY reference claim, in order, give claim_index and one label:
- supported: the chunks state this fact or step.
- partial: the chunks state part of it, or only imply it.
- unsupported: the chunks do not contain it.
- contradicted: the chunks say something that conflicts with it.
List the chunk numbers that hold the evidence (empty if none) and a note of at most 12 words.

Task B. For EVERY chunk, give one label for how useful it is for answering the question:
- relevant: mostly about the question.
- partly: contains some useful sentences mixed with other material.
- not_relevant: not useful for this question.

Return JSON with keys "reference_claims" and "chunks"."""

_GENERATOR = """You check one answer from a product-help assistant. Use ONLY the text below. Write no scores.

Question:
{query}

Retrieved chunks (numbered from 1):
{chunks}

Reference claims (numbered from 0):
{claims}

Answer to check:
{answer}

Task A. Split the answer into its factual claims. For each, one label:
- supported: the chunks state it.
- unsupported: the chunks neither state nor contradict it.
- contradicted: the chunks conflict with it.
List evidence chunk numbers and a note of at most 12 words.

Task B. Split the answer into its statements. For each, one label:
- addresses_question: it helps answer the question asked.
- off_topic: it does not.

Task C. For EVERY reference claim, in order, give claim_index and one label for the answer:
- conveyed: the answer gives the same fact or step.
- partial: the answer gives part of it, or vaguely.
- missing: the answer does not mention it.
- contradicted: the answer says something that conflicts with it.

Return JSON with keys "answer_claims", "statements", "reference_coverage"."""


def _numbered(items: list[str], start: int) -> str:
    return "\n".join(f"[{i}] {t}" for i, t in enumerate(items, start=start)) or "(none)"


def _chunks_text(chunks: list[str]) -> str:
    return "\n\n".join(f"[{i}] {c}" for i, c in enumerate(chunks, start=1)) or "(none)"


def golden_hash(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]


def load_claims() -> dict:
    return json.loads(CLAIMS_FILE.read_text(encoding="utf-8")) if CLAIMS_FILE.exists() else {}


def freeze_claims(judge, rows: dict[str, str]) -> dict:
    """Extract reference claims once per golden answer. Existing, unchanged entries are kept."""
    store = load_claims()
    for rid, text in rows.items():
        h = golden_hash(text)
        if store.get(rid, {}).get("hash") == h:
            continue
        out = judge.generate(_EXTRACT.format(text=text), schema=_Claims)
        store[rid] = {"hash": h, "reference": text, "claims": [c.strip() for c in out.claims if c.strip()]}
    CLAIMS_FILE.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    return store


# ---- aggregation: pure functions of labels ---------------------------------------------


def _recall(v: _RetrieverVerdict) -> float:
    return statistics.mean(CLAIM_SUPPORT[c.label] for c in v.reference_claims)


def _relevancy(v: _RetrieverVerdict) -> float:
    return statistics.mean(CHUNK_REL[c.label] for c in v.chunks) if v.chunks else 0.0


def _precision(v: _RetrieverVerdict) -> float:
    """Weighted precision@k (DeepEval's formula) over chunk labels; partly counts as relevant."""
    flags = [1 if c.label != "not_relevant" else 0 for c in sorted(v.chunks, key=lambda c: c.chunk)]
    if not any(flags):
        return 0.0
    total, hits = 0.0, 0
    for k, flag in enumerate(flags, start=1):
        hits += flag
        total += (hits / k) * flag
    return total / sum(flags)


def _faithfulness(v: _GeneratorVerdict) -> float:
    n = len(v.answer_claims)
    return sum(c.label == "supported" for c in v.answer_claims) / n if n else 1.0


def _answer_relevancy(v: _GeneratorVerdict) -> float:
    n = len(v.statements)
    return sum(s.label == "addresses_question" for s in v.statements) / n if n else 0.0


def _correctness(v: _GeneratorVerdict) -> float:
    n = len(v.reference_coverage)
    pts = {"conveyed": 1.0, "partial": 0.5, "missing": 0.0, "contradicted": -1.0}
    return max(0.0, sum(pts[c.label] for c in v.reference_coverage) / n)


def _check_fixed(items, n: int, what: str, start: int, key: str) -> None:
    got = [getattr(i, key) for i in items]
    if got != list(range(start, start + n)):
        raise ValueError(f"{what}: expected indexes {start}..{start + n - 1} once each, got {got}")


def retriever_scores(v: _RetrieverVerdict) -> dict:
    return {"recall": _recall(v), "precision": _precision(v), "relevancy": _relevancy(v)}


def generator_scores(v: _GeneratorVerdict) -> dict:
    return {
        "faithfulness": _faithfulness(v),
        "answer_relevancy": _answer_relevancy(v),
        "correctness": _correctness(v),
        "unsupported_share": (
            sum(c.label == "unsupported" for c in v.answer_claims) / len(v.answer_claims) if v.answer_claims else 0.0
        ),
        "contradicted_claims": sum(c.label == "contradicted" for c in v.answer_claims),
    }


# ---- judge calls -----------------------------------------------------------------------


def _retriever_pass(judge, query: str, claims: list[str], chunks: list[str]) -> _RetrieverVerdict:
    prompt = _RETRIEVER.format(query=query, claims=_numbered(claims, 0), chunks=_chunks_text(chunks))
    for attempt in range(2):
        v = judge.generate(prompt, schema=_RetrieverVerdict)
        try:
            _check_fixed(v.reference_claims, len(claims), "reference_claims", 0, "claim_index")
            _check_fixed(v.chunks, len(chunks), "chunks", 1, "chunk")
            return v
        except ValueError:
            if attempt:
                raise
    raise RuntimeError("unreachable")


def _generator_pass(judge, query: str, claims: list[str], chunks: list[str], answer: str) -> _GeneratorVerdict:
    prompt = _GENERATOR.format(
        query=query, chunks=_chunks_text(chunks), claims=_numbered(claims, 0), answer=answer[:3000]
    )
    for attempt in range(2):
        v = judge.generate(prompt, schema=_GeneratorVerdict)
        try:
            _check_fixed(v.reference_coverage, len(claims), "reference_coverage", 0, "claim_index")
            return v
        except ValueError:
            if attempt:
                raise
    raise RuntimeError("unreachable")


def _fixed_labels_r(v: _RetrieverVerdict) -> list[str]:
    return [c.label for c in v.reference_claims] + [c.label for c in sorted(v.chunks, key=lambda c: c.chunk)]


def _fixed_labels_g(v: _GeneratorVerdict) -> list[str]:
    return [c.label for c in v.reference_coverage]


def judge_row(judge, query: str, claims: list[str], chunks: list[str], answer: str, *, vote: bool = False) -> dict:
    """Scores for one row. ``vote`` runs each call twice and a third time only on disagreement."""
    r_passes = [_retriever_pass(judge, query, claims, chunks)]
    g_passes = [_generator_pass(judge, query, claims, chunks, answer)]
    agreement = {"retriever": 1.0, "generator": 1.0}
    if vote:
        r_passes.append(_retriever_pass(judge, query, claims, chunks))
        g_passes.append(_generator_pass(judge, query, claims, chunks, answer))
        for name, passes, fixed, again in (
            ("retriever", r_passes, _fixed_labels_r, lambda: _retriever_pass(judge, query, claims, chunks)),
            ("generator", g_passes, _fixed_labels_g, lambda: _generator_pass(judge, query, claims, chunks, answer)),
        ):
            a, b = fixed(passes[0]), fixed(passes[1])
            agreement[name] = sum(x == y for x, y in zip(a, b, strict=True)) / len(a) if a else 1.0
            scorer = retriever_scores if name == "retriever" else generator_scores
            differs = a != b or any(
                abs(scorer(passes[0])[k] - scorer(passes[1])[k]) > 1e-9 for k in scorer(passes[0]) if k != "contradicted_claims"
            )
            if differs:
                passes.append(again())
    r_scores = [retriever_scores(p) for p in r_passes]
    g_scores = [generator_scores(p) for p in g_passes]
    merged: dict = {}
    for group in (r_scores, g_scores):
        for key in group[0]:
            merged[key] = statistics.median(s[key] for s in group)
    return {
        "scores": merged,
        "agreement": agreement,
        "passes": {"retriever": len(r_passes), "generator": len(g_passes)},
        "verdicts": {
            "retriever": [p.model_dump() for p in r_passes],
            "generator": [p.model_dump() for p in g_passes],
        },
    }
