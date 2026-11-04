"""Mark retriever rows that miss the benchmarks and show what was retrieved.

    uv run python -m evals.mark_low_scores
    uv run python -m evals.mark_low_scores --baseline evals/baselines/retriever_judged_k3_c5_large_rerank.json

Reads a finished judged baseline. Does not call the judge again. Retrieval is
repeated with the baseline's own top-k and candidate-k so the chunks match the scores.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "evals" / "baselines" / "retriever_judged_k3_c5_large_rerank.json"
GOLDENS = ROOT / "evals" / "retriever_goldens.json"
REVIEW = ROOT / "evals" / "low_score_review.md"

# Severe: clearly failed. Below: short of the benchmark for that metric.
LOW = 0.5
BARS = {
    "ContextualRecallMetric": 0.7,
    "ContextualPrecisionMetric": 0.75,
    "ContextualRelevancyMetric": 0.8,
}
LABELS = {
    "ContextualRecallMetric": "recall",
    "ContextualPrecisionMetric": "precision",
    "ContextualRelevancyMetric": "relevancy",
}


def _score(case: dict, name: str) -> float | None:
    block = case.get(name)
    if isinstance(block, dict) and block.get("score") is not None:
        return float(block["score"])
    return None


def _flag(case: dict) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    low = False
    below = False
    for name, bar in BARS.items():
        score = _score(case, name)
        if score is None:
            continue
        label = LABELS[name]
        if score < LOW:
            low = True
            reasons.append(f"{label} {score:.2f} is below 0.50")
        elif score < bar:
            below = True
            reasons.append(f"{label} {score:.2f} is below the {bar:.2f} benchmark")
    if low:
        return "low", reasons
    if below:
        return "below_benchmark", reasons
    return None, []


def _cause(case: dict, golden: dict) -> str:
    if golden.get("label_suspect"):
        return "query_or_label: the labeled guides did not contain an answer when the expected text was written"
    missing = (case.get("guide_id_diagnostic") or {}).get("missing") or []
    recall = _score(case, "ContextualRecallMetric")
    precision = _score(case, "ContextualPrecisionMetric")
    relevancy = _score(case, "ContextualRelevancyMetric")
    if missing and (recall is None or recall < BARS["ContextualRecallMetric"]):
        return "retrieval_miss: a labeled guide never entered the top results"
    if (recall is not None and recall < BARS["ContextualRecallMetric"]) and not missing:
        return "partial_chunk: the labeled guide was retrieved, but the chunk does not hold the whole answer"
    if (precision is not None and precision < BARS["ContextualPrecisionMetric"]) or (
        relevancy is not None and relevancy < BARS["ContextualRelevancyMetric"]
    ):
        return "noise: the answer is present, and another chunk is ranked with it or ahead of it"
    return "check the judge reason against the chunks"


def _chunks(query: str, settings) -> list[str]:
    from app.knowledge.hybrid import select_hybrid

    selection = select_hybrid(query, settings=settings)
    if selection is None:
        return ["(index not ready)"]
    lines = []
    for rank, hit in enumerate(selection.hits, start=1):
        if not hit.doc_id or hit.doc_id == "core":
            continue
        preview = " ".join(hit.text.split())
        if len(preview) > 420:
            preview = preview[:420] + "..."
        lines.append(f"{rank}. [{hit.doc_id}] {hit.section} — {preview}")
    if selection.no_answer:
        lines.append("Retriever abstained (no_answer).")
    return lines or ["(no guide chunks)"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    args = parser.parse_args()

    payload = json.loads(args.baseline.read_text(encoding="utf-8"))
    goldens = {
        row["id"]: row
        for row in json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]
        if not row.get("rejected")
    }
    config = payload.get("summary", {}).get("config") or {}

    from app.core.config import get_settings

    settings = get_settings().model_copy(
        update={
            "que_rag_top_k": int(config.get("top_k") or 2),
            "que_rag_candidate_k": int(config.get("candidate_k") or 8),
        }
    )

    flagged: list[tuple[dict, dict, str, list[str]]] = []
    for case in payload.get("cases") or []:
        flag, reasons = _flag(case)
        case["flag"] = flag
        case["flag_reasons"] = reasons
        if flag:
            flagged.append((case, goldens.get(case["id"], {}), flag, reasons))

    abstain_misses: list[tuple[dict, list[str]]] = []
    for golden in goldens.values():
        if not golden.get("expect_no_answer"):
            continue
        chunks = _chunks(golden["query"], settings)
        abstained = any(line.startswith("Retriever abstained") for line in chunks)
        if not abstained:
            abstain_misses.append((golden, chunks))

    flagged.sort(key=lambda item: (item[2] != "low", item[0]["id"]))
    lines = [
        "# Low and below-benchmark retriever rows",
        "",
        f"Source: `{args.baseline.relative_to(ROOT)}`.",
        f"Retrieval repeated at top-k {settings.que_rag_top_k}, candidate pool {settings.que_rag_candidate_k}, matching that run.",
        "",
        "Marks:",
        "- `low`: at least one metric is under 0.50.",
        "- `below_benchmark`: recall under 0.70, precision under 0.75, or relevancy under 0.80.",
        "",
        f"{sum(1 for _case, _golden, flag, _reasons in flagged if flag == 'low')} low, "
        f"{sum(1 for _case, _golden, flag, _reasons in flagged if flag == 'below_benchmark')} below benchmark, "
        f"{len(abstain_misses)} out-of-domain queries that still retrieved guides.",
        "",
        "| Mark | Id | Recall | Precision | Relevancy | Why to look |",
        "|---|---|---:|---:|---:|---|",
    ]
    for case, golden, flag, _reasons in flagged:
        cause = _cause(case, golden)
        lines.append(
            "| {mark} | {id} | {recall} | {precision} | {relevancy} | {cause} |".format(
                mark=flag,
                id=case["id"],
                recall=_fmt(_score(case, "ContextualRecallMetric")),
                precision=_fmt(_score(case, "ContextualPrecisionMetric")),
                relevancy=_fmt(_score(case, "ContextualRelevancyMetric")),
                cause=cause.split(":", 1)[0],
            )
        )
    if abstain_misses:
        lines.append("")
        lines.append("| Mark | Id | Recall | Precision | Relevancy | Why to look |")
        lines.append("|---|---|---:|---:|---:|---|")
        for golden, _retrieved in abstain_misses:
            lines.append(f"| abstain_miss | {golden['id']} |  |  |  | out_of_domain_retrieved |")

    lines.append("")
    for case, golden, flag, reasons in flagged:
        lines.extend(_detail(case, golden, flag, reasons, _chunks(case["query"], settings)))
    for golden, retrieved in abstain_misses:
        lines.extend(
            [
                f"## {golden['id']} — abstain_miss",
                "",
                f"Query: {golden['query']}",
                "",
                "This question is out of domain. The retriever still returned product guides.",
                "",
                "Retrieved:",
                "",
                *(f"- {line}" for line in retrieved),
                "",
            ]
        )

    REVIEW.write_text("\n".join(lines), encoding="utf-8")
    args.baseline.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"marked {len(flagged)} judged rows, {len(abstain_misses)} abstain misses -> {REVIEW}")


def _fmt(score: float | None) -> str:
    return "" if score is None else f"{score:.2f}"


def _detail(case: dict, golden: dict, flag: str, reasons: list[str], chunks: list[str]) -> list[str]:
    diagnostic = case.get("guide_id_diagnostic") or {}
    blocks = []
    for name, label in LABELS.items():
        block = case.get(name) or {}
        if block.get("reason"):
            blocks.append(f"- {label}: {block['reason']}")
    return [
        f"## {case['id']} — {flag}",
        "",
        f"Query: {case['query']}",
        f"Category: {golden.get('category', '')} / {golden.get('difficulty', '')}",
        f"Gap: {'; '.join(reasons)}",
        f"Cause: {_cause(case, golden)}",
        f"Expected guides: {', '.join(diagnostic.get('expected') or golden.get('expected_doc_ids') or [])}",
        f"Retrieved guides: {', '.join(diagnostic.get('retrieved') or [])}",
        f"Missing guides: {', '.join(diagnostic.get('missing') or []) or 'none'}",
        "",
        f"Expected answer: {golden.get('expected_output', '')}",
        "",
        "Judge:",
        "",
        *blocks,
        "",
        "Retrieved chunks:",
        "",
        *(f"- {line}" for line in chunks),
        "",
    ]


if __name__ == "__main__":
    main()
