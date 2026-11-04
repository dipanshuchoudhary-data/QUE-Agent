"""Check the LLM judge against human grades on retrieved context.

Step 1  (writes the sheet, you grade it):
    uv run python -m evals.judge_check sample --n 15
Step 2  (after filling human_relevant 0/1 in evals/judge_check.csv):
    uv run python -m evals.judge_check compare

The judge is trusted only if it agrees with the human grade on most rows.
Agreement and disagreements are printed; nothing is auto-tuned.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from deepeval.metrics import ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase

from app.knowledge.hybrid import select_hybrid
from evals.judge import QueJudge
from evals.retriever_goldens import load_verified

SHEET = Path(__file__).resolve().parent / "judge_check.csv"
FIELDS = ["id", "query", "retrieved_guides", "retrieved_text", "human_relevant", "judge_score", "judge_relevant"]


def _chunks(query: str) -> list[str]:
    selection = select_hybrid(query)
    if selection is None:
        return []
    return [f"[{h.doc_id}] {h.section}\n{h.text}" for h in selection.hits if h.doc_id != "core"]


def sample(n: int) -> None:
    rows = [r for r in load_verified() if not r.get("expect_no_answer")]
    random.Random(11).shuffle(rows)
    with SHEET.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, FIELDS)
        writer.writeheader()
        for row in rows[:n]:
            chunks = _chunks(row["query"])
            writer.writerow(
                {
                    "id": row["id"],
                    "query": row["query"],
                    "retrieved_guides": ",".join(c.split("]")[0].lstrip("[") for c in chunks),
                    "retrieved_text": "\n---\n".join(chunks),
                    "human_relevant": "",
                }
            )
    print(f"wrote {SHEET}. Fill human_relevant with 1 (answers the query) or 0, then run compare.")


def compare() -> None:
    judge = QueJudge()
    graded = []
    with SHEET.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["human_relevant"].strip() in {"0", "1"}:
                graded.append(row)
    agree = 0
    for row in graded:
        metric = ContextualRelevancyMetric(model=judge, threshold=0.5, async_mode=False)
        metric.measure(
            LLMTestCase(input=row["query"], actual_output=row["retrieved_text"], retrieval_context=row["retrieved_text"].split("\n---\n"))
        )
        judged = int(metric.score >= 0.5)
        human = int(row["human_relevant"])
        agree += judged == human
        flag = "" if judged == human else "  <-- DISAGREE"
        print(f"{row['id']}: human={human} judge={metric.score:.2f}{flag}")
    if graded:
        print(f"agreement {agree}/{len(graded)} = {agree / len(graded):.0%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--n", type=int, default=15)
    sub.add_parser("compare")
    args = parser.parse_args()
    sample(args.n) if args.cmd == "sample" else compare()
