"""Compare the DeepEval judge with hand grades from evals/judge_check.md.

Fill each ``Human:`` line with 0 or 1 per metric, e.g.

    Human: recall (all needed info present) = 1  precision (relevant first) = 0  relevancy (no noise) = 1

then run:

    uv run python scripts/compare_judge_to_human.py --baseline evals/baselines/retriever_judged_k3_c5_large_rerank.json

Reports agreement per metric (judge score >= 0.7 counts as 1). Low agreement means the
metric scores cannot be trusted yet, however high they look.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "evals" / "judge_check.md"
_HEADER = re.compile(r"^## (\S+):", re.MULTILINE)
_GRADE = re.compile(r"(recall|precision|relevancy)[^=\n]*=\s*([01])\b")
_MAP = {
    "recall": "ContextualRecallMetric",
    "precision": "ContextualPrecisionMetric",
    "relevancy": "ContextualRelevancyMetric",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.7)
    args = parser.parse_args()

    cases = {c["id"]: c for c in json.loads(args.baseline.read_text(encoding="utf-8"))["cases"]}
    sheet = SHEET.read_text(encoding="utf-8")
    parts = _HEADER.split(sheet)
    agree = {k: [0, 0] for k in _MAP}
    detail: list[str] = []
    for case_id, body in zip(parts[1::2], parts[2::2], strict=False):
        grades = {m.group(1): int(m.group(2)) for m in _GRADE.finditer(body)}
        case = cases.get(case_id)
        if not grades or not case:
            continue
        for key, metric in _MAP.items():
            if key not in grades:
                continue
            score = (case.get(metric) or {}).get("score")
            if score is None:
                continue
            judge = int(score >= args.threshold)
            agree[key][1] += 1
            agree[key][0] += int(judge == grades[key])
            if judge != grades[key]:
                detail.append(f"{case_id} {key}: human={grades[key]} judge={score:.2f}")
    for key, (ok, total) in agree.items():
        rate = f"{ok}/{total} = {ok / total:.0%}" if total else "no graded rows"
        print(f"{key:10s} agreement {rate}")
    if detail:
        print("\nDisagreements:")
        print("\n".join(detail))


if __name__ == "__main__":
    main()
