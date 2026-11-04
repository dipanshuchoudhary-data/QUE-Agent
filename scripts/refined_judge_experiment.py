"""Refined-judge experiment on 30 frozen rows.

    uv run python scripts/refined_judge_experiment.py select
    uv run python scripts/refined_judge_experiment.py freeze            # atomic claims for the 30 rows
    uv run python scripts/refined_judge_experiment.py stability         # re-extract, compare claim sets
    uv run python scripts/refined_judge_experiment.py run --arm refined --repeats 3
    uv run python scripts/refined_judge_experiment.py report

Arms (same frozen chunks, answers, atomic reference claims, pinned model, cache off):
  original   one prompt, free 0-1 numbers
  current    claim_judge.py: closed labels, chunk-level relevancy, 2 calls
  refined    refined_judge.py: quotes, partial rule, unit-level relevancy, adjudication on borderline
  refined_noadj  refined without the adjudication step (isolates what adjudication adds)

Results are saved after every row so a quota stop can be resumed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

D = ROOT / "evals" / "diagnostics"
ROWS = D / "refined_rows.json"
RUNS = D / "refined_runs.json"
STAB = D / "claim_stability.json"
CLAIMS = ROOT / "evals" / "golden_claims.json"
MODEL = "gemini-3.5-flash-lite"
KEYS = ("recall", "precision", "relevancy", "faithfulness", "answer_relevancy", "correctness")
FROZEN12 = ["r02", "s17", "r16", "s11", "p06", "s03", "r12", "s07", "p05", "m06", "a06", "t06"]
N_ROWS = 30


def _load(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def _judge():
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from evals.judge import QueJudge

    return QueJudge(pin=MODEL)


def _snap():
    from evals.judge import QueJudge

    return dict(QueJudge.stats)


def _delta(before: dict) -> dict:
    now = _snap()
    return {k: round(now[k] - before[k], 3) for k in now}


# ---- select ----------------------------------------------------------------------------


def cmd_select(_a) -> None:
    from scripts.run_deepeval_pipeline import _chunks_for

    answers = {c["id"]: c for c in _load(ROOT / "evals" / "baselines" / "generator_full.json")["cases"] if "answer" in c}
    goldens = {g["id"]: g for g in _load(ROOT / "evals" / "retriever_goldens.json")["goldens"]}
    frozen_chunks = _load(D / "frozen_chunks.json", {})
    existing = _load(ROWS, {})
    chosen = list(FROZEN12)
    pool: dict[str, list[str]] = {}
    for rid, case in answers.items():
        if rid in chosen or case["served_by"] != "retrieval" or rid not in goldens:
            continue
        pool.setdefault(goldens[rid]["category"], []).append(rid)
    for ids in pool.values():
        ids.sort()
    while len(chosen) < N_ROWS and any(pool.values()):
        for cat in sorted(pool, key=lambda c: -len(pool[c])):
            if pool[cat] and len(chosen) < N_ROWS:
                chosen.append(pool[cat].pop(0))
    rows = {}
    for rid in chosen:
        if rid in existing:
            rows[rid] = existing[rid]
            continue
        g = goldens[rid]
        chunks = frozen_chunks.get(rid) or _chunks_for(g["query"])
        rows[rid] = {
            "id": rid,
            "query": g["query"],
            "category": g["category"],
            "difficulty": g["difficulty"],
            "expected": g["expected_output"],
            "answer": answers[rid]["answer"],
            "chunks": chunks,
        }
    _save(ROWS, rows)
    empty = [r for r, v in rows.items() if not v["chunks"]]
    print(len(rows), "rows;", "no chunks for", empty or "none")
    from collections import Counter

    print(Counter(v["category"] for v in rows.values()))


# ---- atomic claims ---------------------------------------------------------------------


def cmd_freeze(_a) -> None:
    from evals.claim_judge import golden_hash
    from evals.refined_judge import extract_atomic

    judge = _judge()
    rows = _load(ROWS)
    store = _load(CLAIMS, {})
    for rid, r in rows.items():
        h = golden_hash(r["expected"])
        entry = store.get(rid, {})
        if entry.get("atomic") and entry.get("atomic_hash") == h:
            continue
        atomic = extract_atomic(judge, r["expected"])
        if "claims_v1" not in entry and entry.get("claims") and entry.get("hash") == h:
            entry["claims_v1"] = entry["claims"]
        entry.update({"hash": h, "reference": r["expected"], "atomic_hash": h, "atomic": atomic, "claims": [a["text"] for a in atomic]})
        store[rid] = entry
        _save(CLAIMS, store)
        split = sum(a["parent_id"] is not None for a in atomic)
        print(rid, len(entry.get("claims_v1", [])), "->", len(atomic), "claims,", split, "from splits", flush=True)
    print("calls", _snap()["calls"])


def cmd_stability(_a) -> None:
    from evals.refined_judge import claim_set_agreement, extract_atomic

    judge = _judge()
    store = _load(CLAIMS)
    rows = _load(ROWS)
    out = _load(STAB, {})
    for rid in FROZEN12:
        if rid in out:
            continue
        base = store[rid]["claims"]
        again = [[a["text"] for a in extract_atomic(judge, rows[rid]["expected"])] for _ in range(2)]
        out[rid] = {
            "frozen": base,
            "repeat_counts": [len(x) for x in again],
            "frozen_count": len(base),
            "coverage_of_frozen": [round(claim_set_agreement(base, x), 2) for x in again],
            "coverage_of_repeat": [round(claim_set_agreement(x, base), 2) for x in again],
        }
        _save(STAB, out)
        print(rid, out[rid]["frozen_count"], out[rid]["repeat_counts"], out[rid]["coverage_of_frozen"], flush=True)


# ---- run -------------------------------------------------------------------------------


def _run_one(arm: str, judge, row: dict, claims: dict) -> dict:
    before = _snap()
    t0 = time.perf_counter()
    if arm == "original":
        from scripts.run_deepeval_pipeline import _judge_combined

        out = _judge_combined(judge, row["query"], row["expected"], row["chunks"], row["answer"], use_cache=False)
        entry = {"scores": {k: out[k]["score"] for k in KEYS}}
    elif arm == "current":
        from evals.claim_judge import judge_row

        out = judge_row(judge, row["query"], claims["claims"], row["chunks"], row["answer"])
        entry = {"scores": out["scores"], "verdicts": out["verdicts"]}
    else:
        from evals.refined_judge import judge_row

        out = judge_row(judge, row["query"], claims["claims"], row["chunks"], row["answer"], adjudicate=arm == "refined")
        entry = {
            "scores": out["scores"],
            "scores_first": out["scores_first"],
            "band": out["band"],
            "uncertain": out["uncertain"],
            "adjudicated": out["adjudicated"],
            "adjudication_changed": out["adjudication_changed"],
            "state_first": out["state_first"],
            "state_final": out["state_final"],
            "adjudication": out["adjudication"],
        }
    entry["usage"] = _delta(before)
    entry["wall_seconds"] = round(time.perf_counter() - t0, 2)
    return entry


def cmd_run(a) -> None:
    judge = _judge()
    rows = _load(ROWS)
    claims = _load(CLAIMS)
    runs = _load(RUNS, {})
    arm = runs.setdefault(a.arm, {"model": MODEL, "rows": {}})
    ids = a.ids or list(rows)
    for rep in range(a.repeats):
        for rid in ids:
            slot = arm["rows"].setdefault(rid, [])
            if len(slot) > rep:
                continue
            try:
                entry = _run_one(a.arm, judge, rows[rid], claims[rid])
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                arm.setdefault("failures", []).append({"rep": rep, "row": rid, "error": msg[:300]})
                _save(RUNS, runs)
                if any(s in msg for s in ("429", "PerDay", "quota", "RESOURCE_EXHAUSTED")):
                    print(f"STOP (quota) {a.arm} rep {rep} row {rid}: {msg[:200]}")
                    return
                # Malformed judge output is a real failure of that run: record it and keep going.
                print(f"FAIL {a.arm} rep {rep} row {rid}: {msg[:160]}", flush=True)
                continue
            slot.append(entry)
            _save(RUNS, runs)
            u = entry["usage"]
            print(a.arm, rep, rid, {k: round(v, 2) for k, v in entry["scores"].items() if k in KEYS}, f"calls={int(u['calls'])} retries={int(u['retries'])}", flush=True)
    print("done", a.arm)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["select", "freeze", "stability", "run", "report", "labels", "probes"])
    p.add_argument("--arm", choices=["original", "current", "refined", "refined_noadj"], default="refined")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--ids", nargs="*")
    a = p.parse_args()
    if a.cmd == "report":
        from scripts.refined_report import main as report_main

        report_main()
        return
    if a.cmd == "labels":
        from scripts.refined_report import accuracy_main

        accuracy_main()
        return
    if a.cmd == "probes":
        from scripts.refined_report import probes_main

        probes_main(_judge)
        return
    {"select": cmd_select, "freeze": cmd_freeze, "stability": cmd_stability, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
