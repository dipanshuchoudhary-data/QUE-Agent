"""Report for the refined-judge experiment: reproducibility, accuracy against reference labels,
cost, adjudication, and planted-defect probes. Read-only on the run files except the probe run.
"""

from __future__ import annotations

import difflib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

D = ROOT / "evals" / "diagnostics"
RUNS = D / "refined_runs.json"
ROWS = D / "refined_rows.json"
LABELS = ROOT / "evals" / "label_reference.json"
PROBES = ROOT / "evals" / "defect_probes.json"
PROBE_RUNS = D / "probe_runs.json"
OUT = D / "REFINED_JUDGE.md"
KEYS = ("recall", "precision", "relevancy", "faithfulness", "answer_relevancy", "correctness")
CREDIT = {"supported": 2, "conveyed": 2, "partial": 1, "unsupported": 0, "missing": 0, "contradicted": 0}


def _load(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


# ---- gold scores -----------------------------------------------------------------------


def _wprec(flags: list[int]) -> float:
    if not any(flags):
        return 0.0
    total, hits = 0.0, 0
    for k, f in enumerate(flags, start=1):
        hits += f
        total += (hits / k) * f
    return total / sum(flags)


def gold_scores(g: dict) -> dict:
    refw = {"S": 1.0, "P": 0.5, "U": 0.0, "C": 0.0}
    covw = {"C": 1.0, "P": 0.5, "M": 0.0, "X": -1.0}
    faith = [c for c in g["faith"] if c != "-"]
    return {
        "recall": statistics.mean(refw[c] for c in g["ref"]),
        "precision": _wprec([int(c) for c in g["prec"]]),
        "relevancy": g["rel"].count("U") / len(g["rel"]),
        "faithfulness": (faith.count("S") / len(faith)) if faith else 1.0,
        "answer_relevancy": g["arel"].count("A") / len(g["arel"]),
        "correctness": max(0.0, statistics.mean(covw[c] for c in g["cov"])),
    }


# ---- reproducibility -------------------------------------------------------------------


def _scores(entry: dict, arm: str) -> dict:
    return entry["scores_first"] if arm == "refined_first" else entry["scores"]


def _views(runs: dict) -> dict:
    """Arms to compare. refined_first = refined labels before adjudication (same calls, no step 3)."""
    views = {}
    # Same number of repeats for every arm: the first three. Extra repeats are reported separately.
    cap = {k: {rid: reps[:3] for rid, reps in runs[k]["rows"].items()} for k in runs}
    for name in ("original", "current", "refined"):
        if name in runs:
            views[name] = cap[name]
    if "refined" in runs:
        views["refined_first"] = cap["refined"]
    return views


def repro(views: dict, rids: list[str]) -> dict:
    out = {}
    for arm, rows in views.items():
        ranges, sds, per_metric_r, per_metric_sd = [], [], {k: [] for k in KEYS}, {k: [] for k in KEYS}
        n_rows = n_reps = 0
        flips = 0
        for rid in rids:
            reps = rows.get(rid, [])
            if len(reps) < 2:
                continue
            n_rows += 1
            n_reps = max(n_reps, len(reps))
            for k in KEYS:
                vals = [_scores(r, arm)[k] for r in reps]
                rng = max(vals) - min(vals)
                ranges.append(rng)
                per_metric_r[k].append(rng)
                per_metric_sd[k].append(statistics.pstdev(vals))
                sds.append(statistics.pstdev(vals))
            means = [statistics.mean(_scores(r, arm)[k] for k in KEYS) for r in reps]
            flips += (min(means) >= 0.7) != (max(means) >= 0.7)
        if ranges:
            out[arm] = {
                "rows": n_rows, "reps": n_reps, "mean_range": statistics.mean(ranges), "max_range": max(ranges),
                "mean_sd": statistics.mean(sds), "gt_0_2": sum(x > 0.2 for x in ranges) / len(ranges),
                "flips": flips,
                "metric_range": {k: statistics.mean(v) for k, v in per_metric_r.items()},
                "metric_max": {k: max(v) for k, v in per_metric_r.items()},
                "metric_sd": {k: statistics.mean(v) for k, v in per_metric_sd.items()},
            }
    return out


# ---- labels ----------------------------------------------------------------------------


def _label_items(arm: str, e: dict) -> dict:
    """Fixed-index label lists from one run entry. original has none."""
    if arm == "current":
        v = e["verdicts"]
        r, g = v["retriever"][0], v["generator"][0]
        return {
            "ref": [x["label"] for x in r["reference_claims"]],
            "cov": [x["label"] for x in g["reference_coverage"]],
            "rel": [x["label"] for x in sorted(r["chunks"], key=lambda c: c["chunk"])],
        }
    if arm in ("refined", "refined_first"):
        s = e["state_final"] if arm == "refined" else e["state_first"]
        return {
            "ref": [x["label"] for x in s["ref"]],
            "cov": [x["label"] for x in s["cov"]],
            "rel": [x["label"] for x in s["chunk_units"]],
            "arel": [x["label"] for x in s["answer_units"]],
        }
    return {}


def label_stability(views: dict, rids: list[str]) -> dict:
    out = {}
    for arm in ("current", "refined_first", "refined"):
        if arm not in views:
            continue
        total = disagree = sp = pu = 0
        for rid in rids:
            reps = views[arm].get(rid, [])
            if len(reps) < 2:
                continue
            items = [_label_items(arm, r) for r in reps]
            for kind in ("ref", "cov"):
                for i in range(len(items[0][kind])):
                    labs = {it[kind][i] for it in items}
                    total += 1
                    disagree += len(labs) > 1
                    if "partial" in labs and (labs & {"supported", "conveyed"}):
                        sp += 1
                    if "partial" in labs and (labs & {"unsupported", "missing"}):
                        pu += 1
        out[arm] = {"items": total, "disagree": disagree, "rate": disagree / total if total else 0, "sp": sp, "pu": pu}
    return out


def _unit_faith(arm: str, e: dict, units: list[str]) -> list[str | None]:
    """Judge faithfulness per answer unit: match each judge claim to its best unit; worst label wins."""
    if arm == "current":
        claims = [(c["claim"], c["label"]) for c in e["verdicts"]["generator"][0]["answer_claims"]]
    else:
        s = e["state_final"] if arm == "refined" else e["state_first"]
        claims = [(c["claim"], c["label"]) for c in s["answer_claims"]]
    rank = {"supported": 0, "unsupported": 1, "contradicted": 2}
    out: list[str | None] = [None] * len(units)
    for text, label in claims:
        sims = [difflib.SequenceMatcher(None, text.casefold(), u.casefold()).ratio() for u in units]
        if not sims or max(sims) < 0.35:
            continue
        i = sims.index(max(sims))
        if out[i] is None or rank[label] > rank[out[i]]:
            out[i] = label
    return out


def accuracy(views: dict, rids: list[str], labels: dict, rows: dict) -> dict:
    from evals.refined_judge import split_units

    gref = {"S": "supported", "P": "partial", "U": "unsupported", "C": "contradicted"}
    gcov = {"C": "conveyed", "P": "partial", "M": "missing", "X": "contradicted"}
    gfa = {"S": "supported", "U": "unsupported", "C": "contradicted"}
    out = {}
    for arm in ("original", "current", "refined_first", "refined"):
        if arm not in views:
            continue
        mae = {k: [] for k in KEYS}
        cnt = {"items": 0, "exact": 0, "fp": 0, "fn": 0, "false_contra": 0, "missed_contra": 0}
        faith = {"items": 0, "exact": 0, "fp": 0, "fn": 0, "unmatched": 0}
        for rid in rids:
            g = labels[rid]
            gs = gold_scores(g)
            for e in views[arm].get(rid, []):
                sc = _scores(e, arm)
                for k in KEYS:
                    mae[k].append(abs(sc[k] - gs[k]))
                if arm == "original":
                    continue
                items = _label_items(arm, e)
                for kind, gmap, gstr in (("ref", gref, g["ref"]), ("cov", gcov, g["cov"])):
                    for j, ch in enumerate(gstr):
                        gl, jl = gmap[ch], items[kind][j]
                        cnt["items"] += 1
                        cnt["exact"] += gl == jl
                        cg, cj = CREDIT[gl], CREDIT[jl]
                        cnt["fp"] += cj > cg
                        cnt["fn"] += cj < cg
                        cnt["false_contra"] += jl == "contradicted" and gl != "contradicted"
                        cnt["missed_contra"] += gl == "contradicted" and jl != "contradicted"
                units = split_units(rows[rid]["answer"][:3000])
                fl = _unit_faith(arm, e, units)
                for j, ch in enumerate(g["faith"]):
                    if ch == "-":
                        continue
                    if fl[j] is None:
                        faith["unmatched"] += 1
                        continue
                    gl, jl = gfa[ch], fl[j]
                    faith["items"] += 1
                    faith["exact"] += gl == jl
                    faith["fp"] += (jl == "supported") and gl != "supported"
                    faith["fn"] += (jl != "supported") and gl == "supported"
        out[arm] = {"mae": {k: statistics.mean(v) for k, v in mae.items() if v}, "labels": cnt, "faith": faith}
    return out


# ---- cost ------------------------------------------------------------------------------


def cost(views: dict, rids: list[str]) -> dict:
    out = {}
    for arm in ("original", "current", "refined"):
        if arm not in views:
            continue
        es = [e for rid in rids for e in views[arm].get(rid, [])]
        if not es:
            continue
        out[arm] = {
            "n": len(es),
            "calls": statistics.mean(e["usage"]["calls"] for e in es),
            "retries": statistics.mean(e["usage"]["retries"] for e in es),
            "seconds": statistics.mean(e["usage"]["seconds"] for e in es),
            "prompt": statistics.mean(e["usage"]["prompt_tokens"] for e in es),
            "completion": statistics.mean(e["usage"]["completion_tokens"] for e in es),
        }
    return out


# ---- adjudication ----------------------------------------------------------------------


def adjudication(views: dict, rids: list[str], labels: dict) -> dict:
    gref = {"S": "supported", "P": "partial", "U": "unsupported", "C": "contradicted"}
    gcov = {"C": "conveyed", "P": "partial", "M": "missing", "X": "contradicted"}
    n_runs = trig_runs = items = changed = first_ok = final_ok = 0
    extra_calls = []
    for rid in rids:
        for e in views.get("refined", {}).get(rid, []):
            n_runs += 1
            trig = e["adjudicated"]
            trig_runs += bool(trig)
            for t in trig:
                kind, idx = t[:3], int(t[3:]) if t[:3] in ("ref", "cov") else None
                if kind not in ("ref", "cov"):
                    continue
                gl = (gref if kind == "ref" else gcov)[labels[rid][kind][idx]]
                fl = e["state_first"][kind][idx]["label"]
                fin = e["state_final"][kind][idx]["label"]
                items += 1
                changed += fl != fin
                first_ok += fl == gl
                final_ok += fin == gl
    return {"runs": n_runs, "runs_triggered": trig_runs, "items": items, "changed": changed, "first_ok": first_ok, "final_ok": final_ok}


# ---- markdown --------------------------------------------------------------------------


def _pct(x: float) -> str:
    return f"{x:.0%}"


def main() -> None:
    runs = _load(RUNS, {})
    labels = _load(LABELS)["rows"]
    rows = _load(ROWS)
    views = _views(runs)
    rids = [r for r in rows if r in labels]
    rp = repro(views, rids)
    ls = label_stability(views, rids)
    ac = accuracy(views, rids, labels, rows)
    co = cost(views, rids)
    ad = adjudication(views, rids, labels)
    stab = _load(D / "claim_stability.json", {})

    L = ["", "## Experiment results (30 rows, frozen chunks, answers and atomic claims; cache off; one pinned model)", ""]
    L += ["Arms: **original** one prompt with free numbers; **current** closed labels, chunk-level relevancy; **refined** quotes, partial rule, unit-level relevancy, borderline adjudication; **refined_first** the refined labels before adjudication (same calls, step skipped).", ""]
    L += ["### Reproducibility", "", "| arm | rows | repeats | mean range | max range | mean SD | metric ranges > 0.2 | pass/fail flips @0.7 |", "|---|---|---|---|---|---|---|---|"]
    for a, s in rp.items():
        L.append(f"| {a} | {s['rows']} | {s['reps']} | {s['mean_range']:.3f} | {s['max_range']:.2f} | {s['mean_sd']:.3f} | {_pct(s['gt_0_2'])} | {s['flips']} |")
    L += ["", "Mean range by metric (max in brackets):", "", "| arm | " + " | ".join(KEYS) + " |", "|---|" + "---|" * len(KEYS)]
    for a, s in rp.items():
        L.append(f"| {a} | " + " | ".join(f"{s['metric_range'][k]:.3f} ({s['metric_max'][k]:.2f})" for k in KEYS) + " |")
    flip = _load(D / "flip_rows.json", [])
    ext = {a: {rid: runs[a]["rows"][rid] for rid in flip if rid in runs[a]["rows"]} for a in ("current", "refined") if a in runs}
    ext_rp = repro({f"{a} (all available repeats)": v for a, v in ext.items()}, flip)
    L += ["", "Rows where any label flipped in the first 3 repeats (" + str(len(flip)) + " rows), all repeats that finished before the daily quota ended:", "", "| arm | rows | repeats (max) | mean range | max range | mean SD |", "|---|---|---|---|---|---|"]
    for a, s in ext_rp.items():
        L.append(f"| {a} | {s['rows']} | {s['reps']} | {s['mean_range']:.3f} | {s['max_range']:.2f} | {s['mean_sd']:.3f} |")
    L += ["", "### Label disagreement across repeats (reference-claim and coverage labels)", "", "| arm | items | items where repeats disagree | rate | partial vs supported/conveyed flips | partial vs unsupported/missing flips |", "|---|---|---|---|---|---|"]
    for a, s in ls.items():
        L.append(f"| {a} | {s['items']} | {s['disagree']} | {_pct(s['rate'])} | {s['sp']} | {s['pu']} |")
    L += ["", "### Accuracy against the reference labels", "", "Reference labels were drafted by the assistant (not an independent human review). Score error is the mean absolute difference from the score computed on the reference labels with the same formulas.", ""]
    L += ["| arm | " + " | ".join(f"MAE {k}" for k in KEYS) + " |", "|---|" + "---|" * len(KEYS)]
    for a, s in ac.items():
        L.append(f"| {a} | " + " | ".join(f"{s['mae'].get(k, float('nan')):.3f}" for k in KEYS) + " |")
    L += ["", "Label level (reference-claim and coverage items; all repeats pooled). FP = judge gives more credit than the reference, FN = less credit.", "", "| arm | items | exact match | FP | FN | false contradictions | missed contradictions |", "|---|---|---|---|---|---|---|"]
    for a, s in ac.items():
        c = s["labels"]
        if c["items"]:
            L.append(f"| {a} | {c['items']} | {_pct(c['exact'] / c['items'])} | {c['fp']} ({_pct(c['fp'] / c['items'])}) | {c['fn']} ({_pct(c['fn'] / c['items'])}) | {c['false_contra']} | {c['missed_contra']} |")
    L += ["", "Faithfulness at answer-unit level (judge claims matched to units by text similarity; units with no matching claim are excluded):", "", "| arm | units compared | exact | FP (judge says supported, reference not) | FN | unmatched |", "|---|---|---|---|---|---|"]
    for a, s in ac.items():
        f = s["faith"]
        if f["items"]:
            L.append(f"| {a} | {f['items']} | {_pct(f['exact'] / f['items'])} | {f['fp']} | {f['fn']} | {f['unmatched']} |")
    L += ["", "### Cost per row", "", "| arm | judge calls | retries | seconds | prompt tokens | completion tokens |", "|---|---|---|---|---|---|"]
    for a, s in co.items():
        L.append(f"| {a} | {s['calls']:.1f} | {s['retries']:.2f} | {s['seconds']:.1f} | {s['prompt']:.0f} | {s['completion']:.0f} |")
    fails = {a: [f for f in runs[a].get("failures", []) if "429" not in f["error"] and "quota" not in f["error"]] for a in runs}
    L += ["", "Runs that failed on malformed judge output (not counted in any score above): " + "; ".join(f"{a} {len(f)}" + (f" ({', '.join(x['row'] + ': ' + x['error'][:60] for x in f[:3])})" if f else "") for a, f in fails.items())]
    L += ["", "Token prices for the pinned model were not verified, so no USD figure is given. The free tier has no per-token charge.", ""]
    L += ["### Adjudication", "", f"- Runs where adjudication triggered: {ad['runs_triggered']} of {ad['runs']}.", f"- Reference/coverage items adjudicated: {ad['items']}; label changed on {ad['changed']}.", f"- Agreement with reference on those items: first label {ad['first_ok']}/{ad['items']}, after adjudication {ad['final_ok']}/{ad['items']}."]
    if stab:
        cov = [x for s in stab.values() for x in s["coverage_of_frozen"]]
        L += ["", "### Claim extraction stability (12 rows, 2 re-extractions each)", "", f"Mean share of frozen claims with a close match in a re-extraction: {statistics.mean(cov):.2f}. Claim counts per row (frozen vs repeats): " + "; ".join(f"{k} {v['frozen_count']} vs {v['repeat_counts']}" for k, v in stab.items()) + "."]
    with OUT.open("a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


def accuracy_main() -> None:  # kept for the CLI name; accuracy is part of main()
    main()


# ---- probes ----------------------------------------------------------------------------


def probes_main(judge_factory) -> None:
    from evals.claim_judge import judge_row as current_row
    from evals.refined_judge import judge_row as refined_row
    from scripts.run_deepeval_pipeline import _judge_combined

    probes = _load(PROBES)["probes"]
    rows = _load(ROWS)
    claims = _load(ROOT / "evals" / "golden_claims.json")
    runs = _load(RUNS, {})
    saved = _load(PROBE_RUNS, {})
    judge = judge_factory()
    for p in probes:
        row, c = rows[p["base"]], claims[p["base"]]["claims"]
        entry = saved.setdefault(p["id"], {})
        for arm in ("original", "current", "refined"):
            if arm in entry:
                continue
            if arm == "original":
                o = _judge_combined(judge, row["query"], row["expected"], row["chunks"], p["answer"], use_cache=False)
                entry[arm] = {k: o[k]["score"] for k in KEYS}
            elif arm == "current":
                entry[arm] = current_row(judge, row["query"], c, row["chunks"], p["answer"])["scores"]
            else:
                entry[arm] = refined_row(judge, row["query"], c, row["chunks"], p["answer"])["scores"]
            PROBE_RUNS.write_text(json.dumps(saved, indent=1), encoding="utf-8")
        print(p["id"], p["kind"], {a: round(entry[a]["faithfulness"], 2) for a in entry}, flush=True)
    # detection table
    L = ["", "## Planted-defect probes", "", "Each probe is a frozen answer with one defect (or unchanged). Base = mean score of the same row over its repeats in that arm. Detected = the expected score moved by at least 0.10 in the right direction (controls: both faithfulness and correctness moved by less than 0.10). For contradiction probes the refined arm must also report a contradicted answer claim.", ""]
    L += ["| probe | defect | row | expected | original | current | refined |", "|---|---|---|---|---|---|---|"]
    det = {"original": 0, "current": 0, "refined": 0}
    for p in probes:
        cells = []
        for arm in ("original", "current", "refined"):
            reps = runs.get(arm, {}).get("rows", {}).get(p["base"], [])
            if not reps or arm not in saved.get(p["id"], {}):
                cells.append("n/a")
                continue
            base = {k: statistics.mean(r["scores"][k] for r in reps) for k in KEYS}
            now = saved[p["id"]][arm]
            df, dc = base["faithfulness"] - now["faithfulness"], base["correctness"] - now["correctness"]
            exp = p["expect"]
            if exp.startswith("faithfulness_down"):
                ok = df >= 0.10
                if exp.endswith("contradiction") and arm != "original":
                    ok = ok and now.get("contradicted_claims", 0) >= 1
            elif exp == "correctness_down":
                ok = dc >= 0.10
            else:
                ok = abs(df) < 0.10 and abs(dc) < 0.10
            det[arm] += ok
            cells.append(f"{'yes' if ok else 'NO'} (faith {df:+.2f}, corr {dc:+.2f})")
        L.append(f"| {p['id']} | {p['kind']} | {p['base']} | {p['expect']} | " + " | ".join(cells) + " |")
    L += ["", f"Detected: original {det['original']}/{len(probes)}, current {det['current']}/{len(probes)}, refined {det['refined']}/{len(probes)}."]
    with OUT.open("a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
