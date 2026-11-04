"""Compact report of the latest run only: original vs current vs refined on 30 rows.

    uv run python scripts/latest_run_report.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.refined_report import (  # noqa: E402
    KEYS,
    LABELS,
    PROBE_RUNS,
    PROBES,
    ROWS,
    RUNS,
    D,
    _load,
    _views,
    accuracy,
    cost,
    label_stability,
    repro,
)

SHORT = {"recall": "recall", "precision": "prec", "relevancy": "relev", "faithfulness": "faith", "answer_relevancy": "ans_rel", "correctness": "correct"}


def main() -> None:
    runs, labels, rows = _load(RUNS), _load(LABELS)["rows"], _load(ROWS)
    views = _views(runs)
    rids = [r for r in rows if r in labels]
    rp, ls, ac, co = repro(views, rids), label_stability(views, rids), accuracy(views, rids, labels, rows), cost(views, rids)
    arms = ("original", "current", "refined")
    L = ["# Latest run: original vs current vs refined", "",
         "30 questions, 3 repeats each, cache off, one pinned model (`gemini-3.5-flash-lite`), same frozen chunks, answers and reference claims.", "",
         "## Summary", "", "| | original | current | refined |", "|---|---|---|---|"]
    L.append("| Avg score change between runs | " + " | ".join(f"{rp[a]['mean_range']:.3f}" for a in arms) + " |")
    L.append("| Biggest score change | " + " | ".join(f"{rp[a]['max_range']:.2f}" for a in arms) + " |")
    L.append("| Label disagreement between runs | n/a | " + " | ".join(f"{ls[a]['rate']:.0%}" for a in ("current", "refined")) + " |")
    L.append("| partial vs supported flips | n/a | " + " | ".join(str(ls[a]["sp"]) for a in ("current", "refined")) + " |")
    L.append("| Labels matching reference | n/a | " + " | ".join(f"{ac[a]['labels']['exact'] / ac[a]['labels']['items']:.0%}" for a in ("current", "refined")) + " |")
    L.append("| Too generous (FP) / too strict (FN) labels | n/a | " + " | ".join(f"{ac[a]['labels']['fp']} / {ac[a]['labels']['fn']}" for a in ("current", "refined")) + " |")
    L.append("| Judge calls per question | " + " | ".join(f"{co[a]['calls']:.1f}" for a in arms) + " |")
    L.append("| Seconds per question | " + " | ".join(f"{co[a]['seconds']:.1f}" for a in arms) + " |")
    L.append("| Tokens per question | " + " | ".join(f"{co[a]['prompt'] + co[a]['completion']:.0f}" for a in arms) + " |")
    fails = {a: len([f for f in runs[a].get("failures", []) if "429" not in f["error"] and "quota" not in f["error"]]) for a in arms}
    L.append("| Failed runs (bad output) | " + " | ".join(str(fails[a]) for a in arms) + " |")

    L += ["", "## Score change between runs, by metric (average, max in brackets)", "", "| metric | original | current | refined |", "|---|---|---|---|"]
    for k in KEYS:
        L.append(f"| {k} | " + " | ".join(f"{rp[a]['metric_range'][k]:.3f} ({rp[a]['metric_max'][k]:.2f})" for a in arms) + " |")

    L += ["", "## Score error against reference labels (lower is better)", "", "| metric | original | current | refined |", "|---|---|---|---|"]
    for k in KEYS:
        L.append(f"| {k} | " + " | ".join(f"{ac[a]['mae'][k]:.3f}" for a in arms) + " |")

    # planted defects
    probes, saved = _load(PROBES)["probes"], _load(PROBE_RUNS, {})
    det = {a: 0 for a in arms}
    L += ["", "## Planted defects (12 tests: 3 invented facts, 4 contradictions, 3 omissions, 2 unchanged controls)", "", "| test | kind | original | current | refined |", "|---|---|---|---|---|"]
    for p in probes:
        cells = []
        for a in arms:
            reps = views[a].get(p["base"], [])
            base = {k: statistics.mean(r["scores"][k] for r in reps) for k in KEYS}
            now = saved[p["id"]][a]
            df, dc = base["faithfulness"] - now["faithfulness"], base["correctness"] - now["correctness"]
            exp = p["expect"]
            if exp.startswith("faithfulness_down"):
                ok = df >= 0.10 and (not exp.endswith("contradiction") or a == "original" or now.get("contradicted_claims", 0) >= 1)
            elif exp == "correctness_down":
                ok = dc >= 0.10
            else:
                ok = abs(df) < 0.10 and abs(dc) < 0.10
            det[a] += ok
            cells.append("caught" if ok else "**missed**")
        L.append(f"| {p['id']} {p['base']} | {p['kind']} | " + " | ".join(cells) + " |")
    L.append("| **total** | | " + " | ".join(f"**{det[a]}/{len(probes)}**" for a in arms) + " |")

    # per question
    L += ["", "## Per question (average of 3 runs; range = biggest change between runs on any metric)", "",
          "| id | query | " + " | ".join(f"{SHORT[k]}" for k in KEYS) + " | range cur | range ref |", "|---|---|" + "---|" * len(KEYS) + "---|---|"]
    for rid in rids:
        ref = views["refined"].get(rid, [])
        cur = views["current"].get(rid, [])
        if not ref:
            continue
        mean = {k: statistics.mean(r["scores"][k] for r in ref) for k in KEYS}
        rng = lambda reps: max((max(r["scores"][k] for r in reps) - min(r["scores"][k] for r in reps)) for k in KEYS) if len(reps) > 1 else float("nan")  # noqa: E731
        q = rows[rid]["query"][:38]
        L.append(f"| {rid} | {q} | " + " | ".join(f"{mean[k]:.2f}" for k in KEYS) + f" | {rng(cur):.2f} | {rng(ref):.2f} |")
    L += ["", "The per-question scores are the **refined** judge. `range cur` and `range ref` compare the biggest score change between runs for the current and refined judges.", "",
          "## Notes", "",
          "- Reference labels were written by me, not by a person. Review `evals/label_reference.json`.",
          "- Only 3 repeats per judge are shown. The daily quota cut the 5-repeat extension short.",
          "- Details of how each judge works and the t06 diagnosis: `REFINED_JUDGE_APPENDIX.md`."]
    out = D / "LATEST_RUN.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()

