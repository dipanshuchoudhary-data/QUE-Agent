"""Full-pipeline answer check on a small, fixed sample (retrieval + generator).

    uv run python scripts/run_generator_eval.py --n 16 --out evals/baselines/generator_check.json

Each sampled question goes through the real chat pipeline (routing, cards, retrieval,
LLM). One judge call per row scores the final answer against the provisional golden
answer: completeness, contradiction (steps that conflict with the golden), and
relevancy. Goldens are not human-verified, so treat scores as provisional.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDENS = ROOT / "evals" / "retriever_goldens.json"

PROMPT = """You grade a product-help answer.

Question: {query}

Reference answer (provisional, from the product guide):
{expected}

Answer to grade:
{answer}

Return only JSON with numbers from 0 to 1:
{{"completeness": <share of the reference steps/facts the answer covers>,
"contradiction": <0 if nothing in the answer conflicts with the reference, up to 1 if it clearly conflicts or invents steps>,
"relevancy": <how directly the answer addresses the question>,
"note": "<one short sentence>"}}"""


def _parse(text: str) -> dict:
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    return json.loads(match.group(0)) if match else {}


async def _ask(query: str) -> dict:
    # Runs the real turn and records, in the same execution, the route that ran and the
    # evidence blocks inside the LLM prompt (``evidence``). Faithfulness must be scored
    # against that record, not against a second retrieval.
    from evals.provenance import capture

    return await capture(query)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=0, help="0 = every eligible row")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    from evals.judge import QueJudge
    from evals.prod_route import route_for

    judge = QueJudge()
    goldens = [g for g in json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"] if not g.get("rejected")]
    pool = []
    for g in goldens:
        if g.get("expect_no_answer") or str(g.get("expected_output", "")).strip().upper() == "NOT IN GUIDE":
            continue
        served = route_for(g["query"]).served_by
        if served in ("retrieval", "workflow_card"):
            pool.append((g, served))
    random.Random(args.seed).shuffle(pool)
    sample = pool[: args.n] if args.n else pool

    cases = []
    for g, served in sample:
        item = {"id": g["id"], "query": g["query"], "served_by": served, "route_predicted": served}
        try:
            item.update(asyncio.run(_ask(g["query"])))
            actual = (item.get("executed_path") or {}).get("runtime_mode")
            item["route_mismatch"] = actual in ("workflow", "agent")  # predicted a knowledge turn, a tool ran
            raw = judge._complete([{"role": "user", "content": PROMPT.format(query=g["query"], expected=g["expected_output"], answer=item["answer"][:3000])}], max_tokens=600)
            item["judge"] = _parse(raw if isinstance(raw, str) else str(raw))
        except Exception as exc:  # noqa: BLE001
            item["error"] = str(exc)[:200]
        cases.append(item)
        print(g["id"], served, item.get("judge") or item.get("error"), flush=True)

    def mean(key: str, by: str | None = None):
        vals = [
            c["judge"][key]
            for c in cases
            if isinstance(c.get("judge", {}).get(key), (int, float)) and (by is None or c["served_by"] == by)
        ]
        return round(statistics.mean(vals), 3) if vals else None

    summary = {
        "rows": len(cases),
        "errors": sum("error" in c for c in cases),
        "route_mismatches": sum(bool(c.get("route_mismatch")) for c in cases),
        "completeness": mean("completeness"),
        "contradiction": mean("contradiction"),
        "relevancy": mean("relevancy"),
        "by_route": {
            r: {"completeness": mean("completeness", r), "contradiction": mean("contradiction", r), "relevancy": mean("relevancy", r)}
            for r in ("retrieval", "workflow_card")
        },
        "judge_calls": len(cases),
        "provisional": True,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary, "cases": cases}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
