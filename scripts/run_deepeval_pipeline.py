"""Per-query DeepEval scores for the whole pipeline: retriever and generator.

    uv run python scripts/run_deepeval_pipeline.py --n 20 --out evals/baselines/deepeval_pipeline.json

Uses the DeepEval metric classes with the repo judge (`evals.judge.QueJudge`):

  Retriever  ContextualRecallMetric, ContextualPrecisionMetric, ContextualRelevancyMetric
  Generator  FaithfulnessMetric (answer vs retrieved chunks, no invented facts)
             AnswerRelevancyMetric (answer vs the question)
             GEval "Answer Correctness" (answer vs the reference answer)

The answers come from an earlier full-pipeline run (`generator_full.json`) so no chat LLM
quota is spent. Retrieval is rerun with production routing and the 700-char injected text.
Reference answers are provisional (not human verified).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDENS = ROOT / "evals" / "retriever_goldens.json"
METRIC_KEYS = ("recall", "precision", "relevancy", "faithfulness", "answer_relevancy", "correctness")
GROUPS = {
    "Retriever": ("recall", "precision", "relevancy"),
    "Generator": ("faithfulness", "answer_relevancy", "correctness"),
}


def _build_metrics(judge, threshold: float, include_reason: bool = True):
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
        GEval,
    )
    from deepeval.test_case import SingleTurnParams

    common = {"model": judge, "threshold": threshold, "include_reason": include_reason, "async_mode": False}
    return {
        "recall": ContextualRecallMetric(**common),
        "precision": ContextualPrecisionMetric(**common),
        "relevancy": ContextualRelevancyMetric(**common),
        "faithfulness": FaithfulnessMetric(**common),
        "answer_relevancy": AnswerRelevancyMetric(**common),
        "correctness": GEval(
            name="Answer Correctness",
            criteria=(
                "Judge whether the actual output gives the same steps and facts as the expected output. "
                "Penalize missing key steps and anything that contradicts the expected output."
            ),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
            ],
            model=judge,
            threshold=threshold,
            async_mode=False,
        ),
    }


_COMBINED_PROMPT = """Score one answer from a product-help assistant. Use only the text below.

Retriever scores (about the retrieved chunks):
- recall: share of the facts in the reference answer that the chunks contain. 1 = all, 0 = none.
- precision: whether chunks that hold those facts are ranked above chunks that do not. 1 = relevant first.
- relevancy: share of the retrieved text that is about the question. 1 = no noise.

Generator scores (about the answer):
- faithfulness: share of the answer's claims that the GENERATOR CONTEXT supports and does not contradict. Ignore the reference. 0 if it states something the context contradicts, or if the context is empty and the answer still makes product claims.
- answer_relevancy: share of the answer's statements that address the question.
- correctness: how well the answer gives the same steps and facts as the reference answer. Penalize missing key steps and contradictions.

Each score is 0 to 1. Each reason is one short sentence.

Question:
{query}

Reference answer:
{expected}

Retrieved chunks, rank 1 first (for the retriever scores):
{chunks}

Generator context: the evidence the answer-writing model actually received in the same run (for faithfulness):
{generator_chunks}

Answer to score:
{answer}
"""


def _judge_combined(
    judge,
    query: str,
    expected: str,
    chunks: list[str],
    answer: str,
    use_cache: bool = True,
    generator_chunks: list[str] | None = None,
) -> dict:
    """All six scores in ONE judge call. Cached on disk so unchanged rows cost nothing."""
    import hashlib

    from pydantic import BaseModel, Field

    class _S(BaseModel):
        score: float = Field(ge=0, le=1)
        reason: str

    class _All(BaseModel):
        recall: _S
        precision: _S
        relevancy: _S
        faithfulness: _S
        answer_relevancy: _S
        correctness: _S

    numbered = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(chunks, start=1)) or "(none)"
    gen = chunks if generator_chunks is None else generator_chunks
    gen_numbered = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(gen, start=1)) or "(none: the generator received no retrieved evidence)"
    prompt = _COMBINED_PROMPT.format(
        query=query, expected=expected, chunks=numbered, generator_chunks=gen_numbered, answer=answer[:3000]
    )
    key = hashlib.sha1(prompt.encode()).hexdigest()
    cache_path = ROOT / "evals" / "diagnostics" / "judge_cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    if not use_cache or key not in cache:
        judged = judge.generate(prompt, schema=_All)
        if not isinstance(judged, _All):
            judged = _All.model_validate(judged)
        result = {k: v for k, v in judged.model_dump().items()}
        if not use_cache:
            return result
        cache[key] = result
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
    return cache[key]


def _chunks_for(query: str) -> list[str]:
    from evals.prod_route import route_for

    from app.knowledge.assemble import _MAX_CHUNK_CHARS, truncate_text
    from app.knowledge.hybrid import select_hybrid

    route = route_for(query)
    selection = select_hybrid(query, execution_class=route.execution_class, canonical_intent=route.canonical_intent)
    if selection is None:
        return []
    return [
        f"[{h.doc_id}] {h.section}\n{truncate_text(h.text, _MAX_CHUNK_CHARS)[0]}".strip()
        for h in selection.hits
        if h.doc_id and h.doc_id != "core"
    ]


def _mean(rows: list[dict], key: str):
    vals = [r["scores"][key]["score"] for r in rows if r["scores"].get(key, {}).get("score") is not None]
    return round(statistics.mean(vals), 3) if vals else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", type=Path, default=ROOT / "evals" / "baselines" / "generator_full.json")
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("combined", "deepeval"),
        default="combined",
        help="combined = one judge call per row for all six scores (default); "
        "deepeval = the full DeepEval metric classes (about 14 calls per row, 9 with --no-reasons)",
    )
    parser.add_argument("--no-reasons", action="store_true", help="deepeval mode: skip the reason call of each metric")
    parser.add_argument("--compare", type=Path, help="earlier deepeval-mode result to compare against")
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    from deepeval.test_case import LLMTestCase
    from evals.judge import QueJudge
    from evals.provenance import evidence_summary, generator_chunks
    from evals.rerank_cache import install

    install()
    judge = QueJudge()
    metrics = _build_metrics(judge, args.threshold, include_reason=not args.no_reasons) if args.mode == "deepeval" else {}

    goldens = {g["id"]: g for g in json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]}
    answered = [
        c
        for c in json.loads(args.answers.read_text(encoding="utf-8"))["cases"]
        if c.get("answer") and c["served_by"] == "retrieval" and not str(c.get("model", "")).startswith("guardrail")
    ]
    sample = answered[: args.n]

    rows: list[dict] = []
    for case in sample:
        golden = goldens[case["id"]]
        # Retriever scores: rerun retrieval (retriever-only view, no LLM). Faithfulness: the
        # context the generator really received in the same run as the answer. Answers
        # saved before provenance capture have no such record; they fall back to the
        # rerun and are labelled so the number is not read as production evidence.
        chunks = _chunks_for(case["query"])
        gen_chunks = generator_chunks(case.get("evidence"))
        context_source = "generator_context" if gen_chunks is not None else "retriever_rerun_legacy"
        if gen_chunks is None:
            gen_chunks = chunks
        test_case = LLMTestCase(
            input=case["query"],
            actual_output=case["answer"],
            expected_output=golden["expected_output"],
            retrieval_context=chunks,
            context=chunks,
        )
        faith_case = LLMTestCase(
            input=case["query"],
            actual_output=case["answer"],
            expected_output=golden["expected_output"],
            retrieval_context=gen_chunks,
            context=gen_chunks,
        )
        row = {
            "id": case["id"],
            "query": case["query"],
            "answer": case["answer"],
            "chunks": len(chunks),
            "generator_chunks": len(gen_chunks),
            "context_source": context_source,
            "evidence": evidence_summary(case.get("evidence")) if case.get("evidence") else None,
            "scores": {},
        }
        if args.mode == "combined":
            try:
                row["scores"] = {
                    k: {"score": round(float(v["score"]), 3), "reason": v["reason"][:400]}
                    for k, v in _judge_combined(
                        judge, case["query"], golden["expected_output"], chunks, case["answer"],
                        generator_chunks=gen_chunks,
                    ).items()
                }
            except Exception as exc:  # noqa: BLE001
                row["scores"] = {k: {"score": None, "error": str(exc)[:200]} for k in METRIC_KEYS}
        for key, metric in metrics.items():
            try:
                if key == "faithfulness" and not gen_chunks:
                    # DeepEval cannot score an empty context; an answer written with no
                    # evidence is not "faithful", so report it instead of skipping the row.
                    row["scores"][key] = {"score": 0.0, "reason": "The generator received no retrieved evidence."}
                    continue
                metric.measure(faith_case if key == "faithfulness" else test_case, _show_indicator=False)
                row["scores"][key] = {"score": round(float(metric.score), 3), "reason": (metric.reason or "")[:400]}
            except Exception as exc:  # noqa: BLE001 - one failed metric must not hide the others
                row["scores"][key] = {"score": None, "error": str(exc)[:200]}
        rows.append(row)
        print(case["id"], {k: v.get("score") for k, v in row["scores"].items()}, flush=True)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"rows_done": len(rows), "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "rows": len(rows),
        "threshold": args.threshold,
        "means": {k: _mean(rows, k) for k in METRIC_KEYS},
        "below_threshold": {
            k: [r["id"] for r in rows if (r["scores"].get(k, {}).get("score") is not None) and r["scores"][k]["score"] < args.threshold]
            for k in METRIC_KEYS
        },
        "errors": sum(1 for r in rows for v in r["scores"].values() if v.get("score") is None),
        "judge_models_used": judge.used_models(),
        "provisional": True,
        # Faithfulness provenance: only "generator_context" rows score the answer against
        # the evidence the model received. Legacy rows reused a second retrieval.
        "faithfulness_context_source": {
            s: sum(1 for r in rows if r["context_source"] == s)
            for s in ("generator_context", "retriever_rerun_legacy")
        },
        "no_generator_evidence": [r["id"] for r in rows if r["generator_chunks"] == 0 and r["context_source"] == "generator_context"],
    }
    summary["mode"] = args.mode
    summary["judge_calls_per_row"] = 1 if args.mode == "combined" else (9 if args.no_reasons else 14)
    if args.compare and args.compare.exists():
        summary["vs_deepeval"] = _compare(rows, json.loads(args.compare.read_text(encoding="utf-8"))["rows"])
    args.out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(args.out.with_suffix(".md"), summary, rows)
    from evals.scorebook import update

    update(
        f"deepeval_pipeline:{args.out.stem}",
        [
            {"id": r["id"], "query": r["query"], "scores": {k: v.get("score") for k, v in r["scores"].items()}}
            for r in rows
        ],
    )
    print(json.dumps(summary["means"], indent=2))
    print("wrote", args.out, "and", args.out.with_suffix(".md"))


def _compare(rows: list[dict], ref_rows: list[dict]) -> dict:
    ref = {r["id"]: r for r in ref_rows}
    out = {}
    for k in METRIC_KEYS:
        pairs = [
            (r["scores"][k]["score"], ref[r["id"]]["scores"][k]["score"])
            for r in rows
            if r["id"] in ref and r["scores"].get(k, {}).get("score") is not None and ref[r["id"]]["scores"].get(k, {}).get("score") is not None
        ]
        if not pairs:
            continue
        diffs = [abs(a - b) for a, b in pairs]
        agree = sum((a >= 0.7) == (b >= 0.7) for a, b in pairs)
        out[k] = {
            "rows": len(pairs),
            "mean_combined": round(statistics.mean(a for a, _ in pairs), 3),
            "mean_deepeval": round(statistics.mean(b for _, b in pairs), 3),
            "mean_abs_diff": round(statistics.mean(diffs), 3),
            "within_0.2": sum(d <= 0.2 for d in diffs),
            "same_pass_fail": agree,
        }
    return out


def _fmt(value) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _write_markdown(path: Path, summary: dict, rows: list[dict]) -> None:
    t = summary["threshold"]
    lines = [
        "# DeepEval pipeline scores, per query",
        "",
        f"Rows: {summary['rows']}. Bar: {t}. Reference answers are provisional. Marked `*` = below the bar.",
        "",
        "Retriever: contextual recall, precision, relevancy. Generator: faithfulness, answer relevancy, answer correctness (G-Eval against the reference).",
        "",
        "| Query | Recall | Precision | Relevancy | Faithfulness | Answer relevancy | Correctness |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        cells = []
        for k in METRIC_KEYS:
            s = r["scores"].get(k, {}).get("score")
            cells.append(_fmt(s) + ("*" if s is not None and s < t else ""))
        lines.append(f"| {r['id']} {r['query'][:60]} | " + " | ".join(cells) + " |")
    lines.append("| **Mean** | " + " | ".join(_fmt(summary["means"][k]) for k in METRIC_KEYS) + " |")
    lines += ["", "## Reasons for scores below the bar", ""]
    for r in rows:
        weak = [(k, v) for k, v in r["scores"].items() if v.get("score") is not None and v["score"] < t]
        if not weak:
            continue
        lines.append(f"### {r['id']}: {r['query']}")
        for k, v in weak:
            lines.append(f"- {k} {v['score']:.2f}: {v.get('reason', '')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
