"""Judged retriever baseline: DeepEval recall / precision / relevancy + efficiency.

Runs only human_verified rows from evals/retriever_goldens.json against the
production hybrid retriever. Writes per-case and per-metric results. Metrics are
never averaged into one number.

    uv run python scripts/run_retriever_judged_eval.py --out evals/baselines/retriever_judged.json
    uv run python scripts/run_retriever_judged_eval.py --grade-sheet 15   # hand-grading sheet only
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDENS = ROOT / "evals" / "retriever_goldens.json"


def _retrieve(query: str, *, mode: str = "raw", route=None):
    """``raw``: full chunks, no routing (the original baseline).

    ``production``: the text QUE really injects (700-char chunks) and the
    execution class production would pass in (it sets how many chunks are used).
    """
    from app.knowledge.assemble import _MAX_CHUNK_CHARS, truncate_text
    from app.knowledge.hybrid import select_hybrid

    kwargs: dict = {}
    if mode == "production" and route is not None:
        kwargs = {"execution_class": route.execution_class, "canonical_intent": route.canonical_intent}
    trace: dict = {}
    started = time.perf_counter()
    selection = select_hybrid(query, trace=trace, **kwargs)
    elapsed_ms = (time.perf_counter() - started) * 1000
    if selection is None:
        raise SystemExit("Hybrid index is not ready. Run: uv run python -m app.knowledge")
    hits = [h for h in selection.hits if h.doc_id and h.doc_id != "core"]
    chunks = []
    for h in hits:
        body = truncate_text(h.text, _MAX_CHUNK_CHARS)[0] if mode == "production" else h.text
        chunks.append(f"[{h.doc_id}] {h.section}\n{body}".strip())
    return selection, chunks, elapsed_ms, trace.get("rerank")


def _metric_means(cases: list[dict]) -> dict:
    """Mean of each judged metric, plus their average for before/after comparison."""
    names = (
        "ContextualRecallMetric",
        "ContextualPrecisionMetric",
        "ContextualRelevancyMetric",
    )
    means: dict[str, float | None] = {}
    for name in names:
        scores = [
            case[name]["score"]
            for case in cases
            if isinstance(case.get(name), dict) and case[name].get("score") is not None
        ]
        key = name.removeprefix("Contextual").removesuffix("Metric").lower()
        means[f"contextual_{key}_mean"] = round(statistics.mean(scores), 4) if scores else None
    present = [value for value in means.values() if value is not None]
    means["metrics_average"] = round(statistics.mean(present), 4) if present else None
    return means


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def _grade_sheet(rows: list[dict], n: int, out: Path) -> None:
    """Rows a human grades 0/1 per metric blind, to compare with the judge later."""
    rng = random.Random(11)
    picked = rng.sample(rows, min(n, len(rows)))
    lines = ["# Judge check: grade each row yourself, then compare with the judge\n"]
    for row in picked:
        _sel, chunks, _ms, _rr = _retrieve(row["query"])
        lines.append(f"## {row['id']}: {row['query']}\n")
        lines.append(f"Expected: {row.get('expected_output', '')}\n")
        for i, chunk in enumerate(chunks, start=1):
            lines.append(f"Chunk {i}:\n```\n{chunk[:900]}\n```\n")
        lines.append("Human: recall (all needed info present) = _  precision (relevant first) = _  relevancy (no noise) = _\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--grade-sheet", type=int, default=0)
    parser.add_argument("--include-unverified", action="store_true", help="provisional: score rows not yet reviewed")
    parser.add_argument("--limit", type=int, default=0, help="score only the first N answerable rows")
    parser.add_argument(
        "--mode",
        choices=("raw", "production"),
        default="raw",
        help="raw = full chunks, no routing (original baseline); production = injected 700-char text, "
        "production execution class, and rows answered by cards/tools/refusals reported as separate buckets",
    )
    parser.add_argument(
        "--only-ids",
        type=Path,
        help="JSON list of row ids to run (e.g. the rows under a bar), to keep judge calls small",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from evals.rerank_cache import install as _install_rerank_cache

    _install_rerank_cache()
    data = json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]
    rows = [r for r in data if r.get("human_verified")]
    if args.include_unverified:
        # Provisional run only: rows nobody has checked yet. Never a gate.
        rows = [r for r in data if not r.get("rejected")]
    if not rows:
        raise SystemExit("No human_verified rows in evals/retriever_goldens.json")

    if args.grade_sheet:
        _grade_sheet([r for r in rows if not r.get("expect_no_answer")], args.grade_sheet, ROOT / "evals" / "judge_check.md")
        return

    from evals.judge import QueJudge
    from tests.evals.metrics import guide_id_diagnostic, judge_retrieval

    from app.core.config import get_settings

    judge = QueJudge()
    cfg = get_settings()
    if args.limit:
        answerable = [r for r in rows if not r.get("expect_no_answer")][: args.limit]
        rows = answerable + [r for r in rows if r.get("expect_no_answer")]
    cases: list[dict] = []
    latencies: list[float] = []
    abstain_ok = abstain_total = 0
    if args.only_ids:
        keep = set(json.loads(args.only_ids.read_text(encoding="utf-8")))
        rows = [r for r in rows if r["id"] in keep]
    buckets: dict[str, list[str]] = {}
    rerank_status: dict[str, int] = {}
    route_of = None
    if args.mode == "production":
        from evals.prod_route import route_for as route_of  # noqa: PLC0415

    for row in rows:
        route = route_of(row["query"]) if route_of else None
        if (
            str(row.get("expected_output", "")).strip().upper() == "NOT IN GUIDE"
            and not row.get("expect_no_answer")
        ):
            # Golden says "not in guide" but is not marked as an abstention row: a person decides.
            buckets.setdefault("needs_human_review", []).append(row["id"])
            continue
        if route is not None and route.served_by != "retrieval":
            # Production answers these without retrieval; retrieval scores would be meaningless.
            buckets.setdefault(route.served_by, []).append(row["id"])
            continue
        selection, chunks, ms, rr = _retrieve(row["query"], mode=args.mode, route=route)
        latencies.append(ms)
        rerank_status[str(rr)] = rerank_status.get(str(rr), 0) + 1
        if row.get("expect_no_answer"):
            abstain_total += 1
            abstain_ok += int(bool(selection.no_answer))
            continue
        result = {
            "id": row["id"],
            "query": row["query"],
            "rerank": rr,
            "execution_class": route.execution_class if route else None,
            "final_docs": [h.doc_id for h in selection.hits if h.doc_id and h.doc_id != "core"],
            "injected_chars": sum(len(c) for c in chunks),
            "latency_ms": round(ms, 1),
            "guide_id_diagnostic": guide_id_diagnostic(row.get("expected_doc_ids") or [], chunks),
            "no_answer": bool(selection.no_answer),
            "judge_calls": 1,
        }
        try:
            result.update(
                judge_retrieval(row["query"], row["expected_output"], chunks, judge)
            )
        except Exception as exc:  # noqa: BLE001 - one bad judge call must not hide the other rows
            for name in (
                "ContextualRecallMetric",
                "ContextualPrecisionMetric",
                "ContextualRelevancyMetric",
            ):
                result[name] = {"score": None, "error": str(exc)[:200]}
        cases.append(result)
        print(row["id"], {k: v.get("score") for k, v in result.items() if isinstance(v, dict) and "score" in v}, flush=True)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps({"cases_done": len(cases), "cases": cases}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    metric_means = _metric_means(cases)
    summary = {
        "config": {
            "top_k": cfg.que_rag_top_k,
            "candidate_k": cfg.que_rag_candidate_k,
            "rrf_k": cfg.que_rag_rrf_k,
            "min_score": cfg.que_rag_min_score,
            "hybrid": cfg.que_rag_hybrid,
            "app_env": cfg.app_env,
            "embedding_provider": cfg.resolved_embedding_provider,
            "embedding_model": cfg.active_embedding_model,
            "embedding_dim": cfg.expected_embedding_dim or None,
            "reranker_provider": cfg.resolved_reranker_provider,
            "rerank": cfg.que_rag_rerank_enabled,
            "rerank_model": cfg.active_rerank_model,
            "index": cfg.active_chroma_path,
            "judge_model": cfg.llm_model,
        },
        "mode": args.mode,
        "rerank_status": rerank_status,
        "rerank_fail_open_rate": round(
            rerank_status.get("failed", 0)
            / max(1, rerank_status.get("failed", 0) + rerank_status.get("ok", 0)),
            3,
        ),
        "not_judged_buckets": {k: {"count": len(v), "ids": v} for k, v in buckets.items()},
        "rows_in_gate": len(rows),
        "rows_human_verified": sum(1 for r in rows if r.get("human_verified")),
        "provisional": bool(args.include_unverified),
        "judge_calls_per_answered_row": 1,
        "judge_models_used": judge.used_models(),
        **metric_means,
        "recall_cases_below_0_5": [
            c["id"] for c in cases if (c.get("ContextualRecallMetric") or {}).get("score") is not None
            and c["ContextualRecallMetric"]["score"] < 0.5
        ],
        "abstention": f"{abstain_ok}/{abstain_total}",
        "injected_chars_mean": round(statistics.mean(c["injected_chars"] for c in cases), 1) if cases else None,
        "latency_ms_p50": round(_pct(latencies, 0.5), 1),
        "latency_ms_p95": round(_pct(latencies, 0.95), 1),
    }
    payload = {"summary": summary, "cases": cases}
    print(json.dumps(summary, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", args.out)
        from evals.scorebook import update as _scorebook_update

        _scorebook_update(
            f"retriever:{args.out.stem}",
            [
                {
                    "id": c["id"],
                    "query": c["query"],
                    "scores": {
                        k: (c.get(k) or {}).get("score")
                        for k in ("ContextualRecallMetric", "ContextualPrecisionMetric", "ContextualRelevancyMetric")
                    },
                }
                for c in cases
            ],
        )
        from evals.write_report import write_report

        csv_path, md_path = write_report(args.out)
        print("wrote", csv_path)
        print("wrote", md_path)


if __name__ == "__main__":
    main()
