"""Write a finished retriever baseline as a CSV and a Markdown report.

    uv run python -m evals.write_report
    uv run python -m evals.write_report --baseline evals/baselines/retriever_judged_k3_c5_large_rerank.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "evals" / "retriever_goldens.json"
DEFAULT_BASELINE = ROOT / "evals" / "baselines" / "retriever_judged_k3_c5_large_rerank.json"

_METRICS = (
    ("ContextualRecallMetric", "recall"),
    ("ContextualPrecisionMetric", "precision"),
    ("ContextualRelevancyMetric", "relevancy"),
)


def _score(case: dict, name: str) -> float | None:
    block = case.get(name)
    if isinstance(block, dict) and block.get("score") is not None:
        return float(block["score"])
    return None


def _reason(case: dict, name: str) -> str:
    block = case.get(name)
    if not isinstance(block, dict):
        return ""
    return str(block.get("reason") or block.get("error") or "")


def _row_average(case: dict) -> float | None:
    scores = [score for name, _label in _METRICS if (score := _score(case, name)) is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def _cell(value: object) -> str:
    return str(value if value is not None else "").replace("|", "/")


def write_report(baseline: Path) -> tuple[Path, Path]:
    payload = json.loads(baseline.read_text(encoding="utf-8"))
    summary = payload.get("summary") or {}
    goldens = {
        row["id"]: row
        for row in json.loads(GOLDENS.read_text(encoding="utf-8")).get("goldens", [])
    }
    cases = list(payload.get("cases") or [])

    csv_path = baseline.with_suffix(".csv")
    md_path = baseline.with_suffix(".md")
    try:
        _write_csv(csv_path, cases, goldens)
        _write_md(md_path, baseline, summary, cases, goldens)
    except PermissionError as exc:
        print(f"skipped full report, file is open: {exc.filename}")
    _write_weak(baseline, payload, cases)
    return csv_path, md_path


def _write_csv(path: Path, cases: list[dict], goldens: dict[str, dict]) -> None:
    fields = [
        "id",
        "flag",
        "category",
        "difficulty",
        "query",
        "recall",
        "precision",
        "relevancy",
        "row_average",
        "expected_guides",
        "retrieved_guides",
        "missing_guides",
        "flag_reasons",
        "recall_reason",
        "precision_reason",
        "relevancy_reason",
        "expected_answer",
        "injected_chars",
        "latency_ms",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for case in cases:
            golden = goldens.get(case["id"], {})
            diagnostic = case.get("guide_id_diagnostic") or {}
            average = _row_average(case)
            writer.writerow(
                {
                    "id": case.get("id", ""),
                    "flag": case.get("flag") or "",
                    "category": golden.get("category", ""),
                    "difficulty": golden.get("difficulty", ""),
                    "query": case.get("query", ""),
                    "recall": _fmt(_score(case, "ContextualRecallMetric")),
                    "precision": _fmt(_score(case, "ContextualPrecisionMetric")),
                    "relevancy": _fmt(_score(case, "ContextualRelevancyMetric")),
                    "row_average": _fmt(average),
                    "expected_guides": ", ".join(diagnostic.get("expected") or []),
                    "retrieved_guides": ", ".join(diagnostic.get("retrieved") or []),
                    "missing_guides": ", ".join(diagnostic.get("missing") or []),
                    "flag_reasons": "; ".join(case.get("flag_reasons") or []),
                    "recall_reason": _reason(case, "ContextualRecallMetric"),
                    "precision_reason": _reason(case, "ContextualPrecisionMetric"),
                    "relevancy_reason": _reason(case, "ContextualRelevancyMetric"),
                    "expected_answer": golden.get("expected_output", ""),
                    "injected_chars": case.get("injected_chars", ""),
                    "latency_ms": case.get("latency_ms", ""),
                }
            )


def _write_md(
    path: Path,
    baseline: Path,
    summary: dict,
    cases: list[dict],
    goldens: dict[str, dict],
) -> None:
    config = summary.get("config") or {}
    lines = [
        "# Retriever eval report",
        "",
        f"Source: `{baseline.name}`.",
        "",
        "## Averages",
        "",
        "| Metric | Mean |",
        "|---|---:|",
        f"| Contextual recall | {_fmt(summary.get('contextual_recall_mean'))} |",
        f"| Contextual precision | {_fmt(summary.get('contextual_precision_mean'))} |",
        f"| Contextual relevancy | {_fmt(summary.get('contextual_relevancy_mean'))} |",
        f"| Average of the three | {_fmt(summary.get('metrics_average'))} |",
        f"| Abstention | {summary.get('abstention', '')} |",
        f"| Injected characters | {summary.get('injected_chars_mean', '')} |",
        f"| Latency p50 / p95 (ms) | {summary.get('latency_ms_p50', '')} / {summary.get('latency_ms_p95', '')} |",
        "",
        "Settings: "
        f"top-k {config.get('top_k', '')}, "
        f"candidate pool {config.get('candidate_k', '')}, "
        f"dense floor {config.get('min_score', '')}.",
        "",
        "A blank flag means the row met the benchmarks. `low` means a metric is under 0.50. "
        "`below_benchmark` means recall is under 0.70, precision under 0.75, or relevancy under 0.80.",
        "",
        "## Every row",
        "",
        "| Id | Flag | Query | Recall | Precision | Relevancy | Row avg | Missing guides |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for case in cases:
        diagnostic = case.get("guide_id_diagnostic") or {}
        missing = ", ".join(diagnostic.get("missing") or []) or "none"
        lines.append(
            "| {id} | {flag} | {query} | {recall} | {precision} | {relevancy} | {avg} | {missing} |".format(
                id=_cell(case.get("id")),
                flag=_cell(case.get("flag") or ""),
                query=_cell(case.get("query")),
                recall=_fmt(_score(case, "ContextualRecallMetric")),
                precision=_fmt(_score(case, "ContextualPrecisionMetric")),
                relevancy=_fmt(_score(case, "ContextualRelevancyMetric")),
                avg=_fmt(_row_average(case)),
                missing=_cell(missing),
            )
        )
    lines.append("")
    lines.append("The CSV next to this file has the judge's reason and the expected answer for every row.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _weak_metrics(case: dict) -> list[tuple[str, float, str]]:
    """Metrics under 0.60, with the judge's reason for that metric alone."""
    found: list[tuple[str, float, str]] = []
    for name, label in _METRICS:
        score = _score(case, name)
        if score is not None and score < 0.6:
            found.append((label, score, _reason(case, name)))
    return found


def _metric_group(score: float) -> str:
    if score <= 0.5:
        return "at_or_below_0.5"
    return "below_0.6"


def _write_weak(baseline: Path, payload: dict, cases: list[dict]) -> None:
    by_metric: dict[str, list[tuple[dict, float, str]]] = {label: [] for _name, label in _METRICS}
    for case in cases:
        weak = _weak_metrics(case)
        case["weak_metrics"] = [label for label, _score, _why in weak]
        groups = {_metric_group(score) for _label, score, _why in weak}
        if "at_or_below_0.5" in groups:
            case["weak_group"] = "at_or_below_0.5"
        elif "below_0.6" in groups:
            case["weak_group"] = "below_0.6"
        else:
            case["weak_group"] = ""
        for label, score, why in weak:
            by_metric[label].append((case, score, why))
    for rows in by_metric.values():
        rows.sort(key=lambda item: item[1])
    baseline.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    stem = baseline.parent / f"{baseline.stem}_below_0_6"
    _write_weak_csv(stem.with_suffix(".csv"), by_metric)
    _write_weak_md(stem.with_suffix(".md"), by_metric)
    print(f"wrote {stem.with_suffix('.csv')}")
    print(f"wrote {stem.with_suffix('.md')}")
    for _name, label in _METRICS:
        rows = by_metric[label]
        at_half = sum(1 for _case, score, _why in rows if score <= 0.5)
        print(f"{label}: {at_half} at or below 0.50, {len(rows) - at_half} below 0.60")


def _write_weak_csv(path: Path, by_metric: dict[str, list[tuple[dict, float, str]]]) -> None:
    fields = [
        "weak_metric",
        "group",
        "score",
        "id",
        "why",
        "query",
        "expected_guides",
        "retrieved_guides",
        "missing_guides",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for _name, label in _METRICS:
            for case, score, why in by_metric[label]:
                diagnostic = case.get("guide_id_diagnostic") or {}
                writer.writerow(
                    {
                        "weak_metric": label,
                        "group": _metric_group(score),
                        "score": _fmt(score),
                        "id": case.get("id", ""),
                        "why": why,
                        "query": case.get("query", ""),
                        "expected_guides": ", ".join(diagnostic.get("expected") or []),
                        "retrieved_guides": ", ".join(diagnostic.get("retrieved") or []),
                        "missing_guides": ", ".join(diagnostic.get("missing") or []),
                    }
                )


def _write_weak_md(path: Path, by_metric: dict[str, list[tuple[dict, float, str]]]) -> None:
    lines = [
        "# One metric at a time",
        "",
        "Read one section at a time. A row appears under a metric only when that metric is under 0.60. "
        "The reason is only for that metric.",
        "",
    ]
    for _name, label in _METRICS:
        rows = by_metric[label]
        at_half = sum(1 for _case, score, _why in rows if score <= 0.5)
        lines.append(
            f"- {label}: {at_half} at or below 0.50, {len(rows) - at_half} below 0.60 and above 0.50"
        )
    lines.append("")
    for name, label in _METRICS:
        lines.extend(_metric_section(name, label, by_metric[label]))
    path.write_text("\n".join(lines), encoding="utf-8")


def _metric_section(name: str, label: str, rows: list[tuple[dict, float, str]]) -> list[str]:
    at_half = [(case, score, why) for case, score, why in rows if score <= 0.5]
    under_six = [(case, score, why) for case, score, why in rows if score > 0.5]
    lines = [
        f"# {label.capitalize()}",
        "",
        f"{len(at_half)} at or below 0.50. {len(under_six)} below 0.60 and above 0.50.",
        "",
    ]
    lines.extend(_metric_band(name, "At or below 0.50", at_half))
    lines.extend(_metric_band(name, "Below 0.60 and above 0.50", under_six))
    return lines


def _metric_band(name: str, title: str, rows: list[tuple[dict, float, str]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.append("None.")
        lines.append("")
        return lines
    for case, score, why in rows:
        diagnostic = case.get("guide_id_diagnostic") or {}
        lines.append(f"### {case.get('id')} — {_cell(case.get('query'))}")
        lines.append("")
        lines.append(f"**{_fmt(score)}.** {why}")
        lines.append("")
        lines.append(
            "Expected guides: "
            + (", ".join(diagnostic.get("expected") or []) or "none")
            + ". Retrieved: "
            + (", ".join(diagnostic.get("retrieved") or []) or "none")
            + ". Missing: "
            + (", ".join(diagnostic.get("missing") or []) or "none")
            + "."
        )
        others = [
            f"{other_label} {_fmt(_score(case, other_name))}"
            for other_name, other_label in _METRICS
            if other_name != name and _score(case, other_name) is not None
        ]
        if others:
            lines.append("Other scores: " + ", ".join(others) + ".")
        lines.append("")
    return lines


def _fmt(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    args = parser.parse_args()
    csv_path, md_path = write_report(args.baseline)
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
