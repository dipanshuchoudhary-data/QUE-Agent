"""Experiment 0: how much does the judge API vary when the prompt is identical?

    uv run python scripts/judge_api_variance.py --ids r16 s03 s17 --repeats 5

Sends the same prompt several times to ONE pinned judge model, with and without a seed,
and reports how often the raw reply and the six scores repeat. No cache is used.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCORE_KEYS = ("recall", "precision", "relevancy", "faithfulness", "answer_relevancy", "correctness")


def _scores(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return {k: round(float(data[k]["score"] if isinstance(data[k], dict) else data[k]), 3) for k in SCORE_KEYS}
    except (KeyError, ValueError, TypeError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="+", default=["r16", "s03", "s17"])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=ROOT / "evals" / "diagnostics" / "judge_api_variance.json")
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from evals.judge import QueJudge
    from scripts.run_deepeval_pipeline import _COMBINED_PROMPT, _chunks_for

    judge = QueJudge()
    model = judge._pool[0]  # pinned: the first model, never the failover one
    goldens = {g["id"]: g for g in json.loads((ROOT / "evals" / "retriever_goldens.json").read_text(encoding="utf-8"))["goldens"]}
    rows = {r["id"]: r for r in json.loads((ROOT / "evals" / "baselines" / "deepeval_pipeline.json").read_text(encoding="utf-8"))["rows"]}

    results: dict = {"model": model, "configs": {}}
    for config, extra in (("temp0_no_seed", {}), ("temp0_seed", {"seed": args.seed})):
        results["configs"][config] = {}
        for rid in args.ids:
            row = rows[rid]
            chunks = _chunks_for(row["query"])
            numbered = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(chunks, start=1)) or "(none)"
            prompt = _COMBINED_PROMPT.format(
                query=row["query"], expected=goldens[rid]["expected_output"], chunks=numbered, answer=row["answer"][:3000]
            ) + '\nReturn only JSON: {"recall": {"score": x, "reason": ""}, "precision": {...}, "relevancy": {...}, "faithfulness": {...}, "answer_relevancy": {...}, "correctness": {...}}'
            replies, scores, errors = [], [], 0
            for _ in range(args.repeats):
                try:
                    resp = judge._client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=4000,
                        **extra,
                    )
                    text = resp.choices[0].message.content or ""
                    replies.append(text)
                    scores.append(_scores(text))
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    results.setdefault("errors", []).append(f"{config}/{rid}: {str(exc)[:160]}")
                    if "seed" in str(exc).casefold():
                        break
                time.sleep(1)
            good = [s for s in scores if s]
            per_metric = {}
            for k in SCORE_KEYS:
                vals = [s[k] for s in good]
                if vals:
                    per_metric[k] = {"values": vals, "range": round(max(vals) - min(vals), 3), "sd": round(statistics.pstdev(vals), 3)}
            results["configs"][config][rid] = {
                "calls": len(replies) + errors,
                "errors": errors,
                "identical_replies": len(set(replies)) == 1 if replies else None,
                "identical_scores": len({json.dumps(s, sort_keys=True) for s in good}) == 1 if good else None,
                "metrics": per_metric,
            }
            print(config, rid, "identical scores:", results["configs"][config][rid]["identical_scores"], flush=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    for config, per_row in results["configs"].items():
        ranges = [m["range"] for r in per_row.values() for m in r["metrics"].values()]
        same = sum(1 for r in per_row.values() if r["identical_scores"])
        print(f"{config}: rows with identical scores {same}/{len(per_row)}; mean metric range {statistics.mean(ranges):.3f}; max {max(ranges):.3f}")
    print("model", model, "| errors", results.get("errors", []))


if __name__ == "__main__":
    main()
