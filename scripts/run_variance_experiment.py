"""Repeatability experiment: same frozen rows, several repeats, cache OFF, one pinned judge model.

    uv run python scripts/run_variance_experiment.py freeze
    uv run python scripts/run_variance_experiment.py run --arm one_call --repeats 3
    uv run python scripts/run_variance_experiment.py run --arm claims --repeats 3
    uv run python scripts/run_variance_experiment.py run --arm claims_vote --repeats 2 --ids r02 s17 ...
    uv run python scripts/run_variance_experiment.py report

Arms:
  one_call     current mode: one prompt, free 0-1 numbers from the LLM
  claims       claim-level labels, 2 calls per row, scores computed in code
  claims_vote  same, run twice, third pass only where the two disagree

Results are appended to evals/diagnostics/variance_runs.json after every row, so a run that
hits the daily quota can be resumed the next day with the same command.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RUNS = ROOT / "evals" / "diagnostics" / "variance_runs.json"
CHUNKS = ROOT / "evals" / "diagnostics" / "frozen_chunks.json"
REPORT = ROOT / "evals" / "diagnostics" / "VARIANCE_RESULTS.md"
FROZEN = ["r02", "s17", "r16", "s11", "p06", "s03", "r12", "s07", "p05", "m06", "a06", "t06"]
KEYS = ("recall", "precision", "relevancy", "faithfulness", "answer_relevancy", "correctness")
THRESHOLD = 0.7


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _setup(pin: str):
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from evals.judge import QueJudge

    judge = QueJudge(pin=pin)
    counter = {"calls": 0}
    original = judge._complete

    def counted(*a, **k):
        counter["calls"] += 1
        return original(*a, **k)

    judge._complete = counted
    return judge, counter


def _rows() -> dict:
    rows = {r["id"]: r for r in _load(ROOT / "evals" / "baselines" / "deepeval_pipeline.json", {})["rows"]}
    goldens = {g["id"]: g for g in _load(ROOT / "evals" / "retriever_goldens.json", {})["goldens"]}
    chunks = _load(CHUNKS, {})
    return {i: {**rows[i], "expected": goldens[i]["expected_output"], "chunks": chunks.get(i, [])} for i in FROZEN}


def cmd_freeze(args) -> None:
    from evals.claim_judge import freeze_claims
    from scripts.run_deepeval_pipeline import _chunks_for

    judge, counter = _setup(args.model)
    rows = _rows()
    if not CHUNKS.exists():
        CHUNKS.write_text(json.dumps({i: _chunks_for(r["query"]) for i, r in rows.items()}, indent=1), encoding="utf-8")
        rows = _rows()
    store = freeze_claims(judge, {i: r["expected"] for i, r in rows.items()})
    print(f"frozen claims for {len(store)} rows, {counter['calls']} judge calls")
    for i, e in store.items():
        print(i, len(e["claims"]), "claims")


def cmd_run(args) -> None:
    from evals.claim_judge import golden_hash, judge_row, load_claims
    from scripts.run_deepeval_pipeline import _judge_combined

    judge, counter = _setup(args.model)
    rows = _rows()
    ids = args.ids or FROZEN
    claims = load_claims()
    runs = _load(RUNS, {})
    arm = runs.setdefault(args.arm, {"model": args.model, "rows": {}})
    for rep in range(args.repeats):
        for rid in ids:
            slot = arm["rows"].setdefault(rid, [])
            if len(slot) > rep:
                continue
            r = rows[rid]
            before = counter["calls"]
            try:
                if args.arm == "one_call":
                    out = _judge_combined(judge, r["query"], r["expected"], r["chunks"], r["answer"], use_cache=False)
                    entry = {"scores": {k: out[k]["score"] for k in KEYS}}
                else:
                    c = claims[rid]
                    if c["hash"] != golden_hash(r["expected"]):
                        raise RuntimeError(f"{rid}: golden changed since claims were frozen")
                    out = judge_row(judge, r["query"], c["claims"], r["chunks"], r["answer"], vote=args.arm == "claims_vote")
                    entry = {k: out[k] for k in ("scores", "agreement", "passes")}
                    entry["verdicts"] = out["verdicts"]
                entry["calls"] = counter["calls"] - before
            except Exception as exc:  # noqa: BLE001  quota or malformed labels: record, stop, resume later
                print(f"STOP at {args.arm} rep {rep} row {rid}: {str(exc)[:200]}")
                RUNS.write_text(json.dumps(runs, indent=1), encoding="utf-8")
                return
            slot.append(entry)
            RUNS.write_text(json.dumps(runs, indent=1), encoding="utf-8")
            print(args.arm, rep, rid, {k: round(v, 2) for k, v in entry["scores"].items() if k in KEYS}, entry["calls"], "calls", flush=True)
    print("done", args.arm, "total calls this session:", counter["calls"])


def _arm_stats(arm: dict) -> dict | None:
    per_row, ranges, flips, calls, n_rep = {}, [], 0, [], 0
    for rid, reps in arm["rows"].items():
        if len(reps) < 2:
            continue
        n_rep = max(n_rep, len(reps))
        calls.extend(r["calls"] for r in reps)
        row = {}
        for k in KEYS:
            vals = [r["scores"][k] for r in reps]
            row[k] = (max(vals) - min(vals), statistics.pstdev(vals))
        per_row[rid] = row
        mean_scores = [statistics.mean(r["scores"][k] for k in KEYS) for r in reps]
        if (min(mean_scores) >= THRESHOLD) != (max(mean_scores) >= THRESHOLD):
            flips += 1
    if not per_row:
        return None
    all_ranges = [v[0] for r in per_row.values() for v in r.values()]
    return {
        "rows": len(per_row),
        "repeats": n_rep,
        "mean_range": statistics.mean(all_ranges),
        "share_range_gt_0_2": sum(x > 0.2 for x in all_ranges) / len(all_ranges),
        "flips": flips,
        "calls_per_row": statistics.mean(calls),
        "per_metric_range": {k: statistics.mean(r[k][0] for r in per_row.values()) for k in KEYS},
        "per_metric_sd": {k: statistics.mean(r[k][1] for r in per_row.values()) for k in KEYS},
        "per_row": per_row,
    }


def cmd_report(_args) -> None:
    runs = _load(RUNS, {})
    stats = {name: _arm_stats(arm) for name, arm in runs.items()}
    lines = ["# Judge repeatability: before and after", "", f"Frozen rows: {', '.join(FROZEN)}. Cache off. One pinned model per arm.", ""]
    lines += ["| arm | model | rows | repeats | mean range | share of metric ranges > 0.2 | pass/fail flips @0.7 | calls/row |", "|---|---|---|---|---|---|---|---|"]
    for name, s in stats.items():
        if s:
            lines.append(
                f"| {name} | {runs[name]['model']} | {s['rows']} | {s['repeats']} | {s['mean_range']:.3f} | "
                f"{s['share_range_gt_0_2']:.0%} | {s['flips']} | {s['calls_per_row']:.1f} |"
            )
    lines += ["", "## Mean per-row range (max - min across repeats) by metric", "", "| arm | " + " | ".join(KEYS) + " |", "|---|" + "---|" * len(KEYS)]
    for name, s in stats.items():
        if s:
            lines.append(f"| {name} | " + " | ".join(f"{s['per_metric_range'][k]:.3f}" for k in KEYS) + " |")
    lines += ["", "## Per-row range of the worst metric", "", "| row | " + " | ".join(n for n, s in stats.items() if s) + " |", "|---|" + "---|" * sum(1 for s in stats.values() if s)]
    for rid in FROZEN:
        cells = []
        for s in stats.values():
            if s:
                r = s["per_row"].get(rid)
                cells.append(f"{max(v[0] for v in r.values()):.2f}" if r else "-")
        lines.append(f"| {rid} | " + " | ".join(cells) + " |")
    vote = runs.get("claims_vote")
    if vote:
        ag = [e["agreement"] for reps in vote["rows"].values() for e in reps]
        if ag:
            lines += ["", f"Vote arm: mean pass-1 vs pass-2 label agreement retriever {statistics.mean(a['retriever'] for a in ag):.2f}, generator {statistics.mean(a['generator'] for a in ag):.2f}."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["freeze", "run", "report"])
    p.add_argument("--arm", choices=["one_call", "claims", "claims_vote"], default="claims")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--ids", nargs="*")
    p.add_argument("--model", default="gemini-3.5-flash-lite")
    args = p.parse_args()
    {"freeze": cmd_freeze, "run": cmd_run, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
