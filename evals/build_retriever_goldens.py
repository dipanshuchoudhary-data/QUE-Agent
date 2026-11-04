"""Merge seed cases and synthetic candidates into evals/retriever_goldens.json.

Seed rows (evals/retrieval_cases.json) only hold guide ids. Their expected
output is written by the judge model from the labeled guide text alone, then
left unverified until a human reviews it.

    uv run python -m evals.build_retriever_goldens
"""

from __future__ import annotations

import json
from pathlib import Path

from app.knowledge.chunking import strip_frontmatter
from app.knowledge.ingest import _load_manifest
from app.knowledge.paths import KNOWLEDGE_ROOT
from evals.judge import QueJudge

_ROOT = Path(__file__).resolve().parents[1]
SEED = _ROOT / "evals" / "retrieval_cases.json"
SYNTH = _ROOT / "tests" / "evals" / ".dataset.json"
OUT = _ROOT / "evals" / "retriever_goldens.json"

_PROMPT = """You write reference answers for a retrieval test.
Answer the question using ONLY the guide text below. 2-6 sentences (cover every guide the question needs),
concrete click paths or facts as the guide states them. If the guide does not answer it, reply exactly: NOT IN GUIDE.

Question: {query}

Guide text:
{guides}
"""


def _guide_text(doc_id: str, docs: dict[str, dict]) -> str:
    doc = docs.get(doc_id)
    if not doc:
        return ""
    raw = (KNOWLEDGE_ROOT / str(doc["path"])).read_text(encoding="utf-8")
    # Guides run long; cutting at 6000 chars hid the answer for r02, r14 and r32.
    return strip_frontmatter(raw)[:30000]


HARD = _ROOT / "evals" / "hard_cases.json"

# Very basic or duplicate rows, and rows with doubtful labels. Kept in the file as
# rejected (audit trail) so they never enter the gate.
REJECT = {
    "s01": "trivial settings question",
    "s04": "question too vague for its label",
    "s10": "duplicate of r21",
    "s12": "duplicate of r06",
    "s13": "label doubtful: Google Sheets export is not the Drive guide",
    "s18": "duplicate of r18",
    "s20": "expected answer is a one-line stub",
    "s24": "duplicate of r15",
}
CONFUSABLE_SEEDS = {"r14", "r31"}
HARD_SEEDS = {"r07", "r25", "r26", "r28", "r29", "r33", "r34"}


def _categorize(row: dict) -> None:
    """Fill category/difficulty for seed and synthetic rows that predate them."""
    if row.get("category"):
        return
    if row.get("expect_no_answer"):
        row["category"], row["difficulty"] = "out_of_domain", "easy"
    elif row["id"] in CONFUSABLE_SEEDS:
        row["category"], row["difficulty"] = "confusable", "hard"
    elif len(row.get("expected_doc_ids") or []) > 1:
        row["category"], row["difficulty"] = "multi_doc", "medium" if row["id"] not in HARD_SEEDS else "hard"
    else:
        row["category"] = "basic"
        row["difficulty"] = "medium" if row["id"] in HARD_SEEDS else "easy"


def _answer(judge: QueJudge, row: dict, docs: dict[str, dict]) -> str:
    guides = "\n\n".join(f"## guide: {d}\n{_guide_text(d, docs)}" for d in row["expected_doc_ids"])
    return judge._complete(
        [{"role": "user", "content": _PROMPT.format(query=row["query"], guides=guides)}],
        max_tokens=700,
    ).strip()


def main() -> None:
    docs = {str(d["id"]): d for d in _load_manifest().get("documents") or []}
    judge = QueJudge()
    # Reuse earlier answers and review flags so a rebuild costs no judge calls.
    previous: dict[str, dict] = {}
    if OUT.is_file():
        previous = {r["id"]: r for r in json.loads(OUT.read_text(encoding="utf-8")).get("goldens", [])}

    rows: list[dict] = []
    sources = [
        ("seed", json.loads(SEED.read_text(encoding="utf-8"))["cases"]),
        ("hard", json.loads(HARD.read_text(encoding="utf-8"))["cases"]),
    ]
    for origin, cases in sources:
        for case in cases:
            old = previous.get(case["id"])
            if old and old.get("query") == case["query"] and old.get("expected_output") != "NOT IN GUIDE":
                row = old
            else:
                row = {
                    "id": case["id"],
                    "query": case["query"],
                    "expected_doc_ids": case.get("expected_doc_ids") or [],
                    "origin": origin,
                    "human_verified": False,
                }
                for key in ("category", "difficulty"):
                    if case.get(key):
                        row[key] = case[key]
                if case.get("expect_no_answer"):
                    row["expect_no_answer"] = True
                    row["expected_output"] = ""
                else:
                    row["expected_output"] = _answer(judge, row, docs)
                print(row["id"], "->", row["expected_output"][:80].replace("\n", " "), flush=True)
            if row["expected_output"] == "NOT IN GUIDE":
                # The labeled guides do not answer this. Either the label or the query is wrong.
                row["label_suspect"] = True
            rows.append(row)

    if SYNTH.is_file():
        for item in json.loads(SYNTH.read_text(encoding="utf-8")).get("goldens", []):
            old = previous.get(item["id"])
            rows.append(old if old and old.get("query") == item["query"] else item)

    for row in rows:
        _categorize(row)
        if row["id"] in REJECT:
            row["rejected"], row["human_verified"], row["review_note"] = True, False, REJECT[row["id"]]

    OUT.write_text(json.dumps({"version": "2.0.0", "goldens": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
