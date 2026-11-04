"""Push the verified retriever goldens to LangSmith and run an experiment.

Role split: DeepEval scores quality (recall / precision / relevancy). LangSmith
keeps the dataset, a per-run experiment, and the ``que.retrieve`` trace for each
row so a bad score can be opened and inspected (hits, scores, chars, latency).
Deterministic evaluators only here; the LLM judge stays in DeepEval.

    uv run python scripts/langsmith_retriever_eval.py --prefix baseline

Needs LANGSMITH_API_KEY (and LANGSMITH_TRACING=true to see child traces).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATASET = "que-retriever-goldens"
GOLDENS = ROOT / "evals" / "retriever_goldens.json"


def _rows() -> list[dict]:
    data = json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]
    return [row for row in data if row.get("human_verified")]


def _ensure_dataset(client, rows: list[dict]):
    if client.has_dataset(dataset_name=DATASET):
        client.delete_dataset(dataset_name=DATASET)
    dataset = client.create_dataset(DATASET, description="QUE retriever goldens (human verified only)")
    client.create_examples(
        dataset_id=dataset.id,
        inputs=[{"query": r["query"]} for r in rows],
        outputs=[
            {
                "expected_output": r.get("expected_output", ""),
                "expected_doc_ids": r.get("expected_doc_ids", []),
                "expect_no_answer": bool(r.get("expect_no_answer")),
            }
            for r in rows
        ],
        metadata=[{"row_id": r["id"], "origin": r.get("origin")} for r in rows],
    )
    return dataset


def _target(inputs: dict) -> dict:
    from app.knowledge.hybrid import select_hybrid

    selection = select_hybrid(inputs["query"])
    if selection is None:
        return {"error": "index_not_ready", "doc_ids": [], "no_answer": False, "chars": 0}
    hits = [h for h in selection.hits if h.doc_id and h.doc_id != "core"]
    return {
        "doc_ids": [h.doc_id for h in hits],
        "no_answer": bool(selection.no_answer),
        "chars": sum(len(h.text) for h in hits),
    }


def _guide_recall(outputs: dict, reference_outputs: dict) -> dict:
    if reference_outputs.get("expect_no_answer"):
        return {"key": "guide_id_recall", "score": None}
    expected = reference_outputs.get("expected_doc_ids") or []
    if not expected:
        return {"key": "guide_id_recall", "score": None}
    got = set(outputs.get("doc_ids") or [])
    return {"key": "guide_id_recall", "score": sum(d in got for d in expected) / len(expected)}


def _abstained_correctly(outputs: dict, reference_outputs: dict) -> dict:
    want = bool(reference_outputs.get("expect_no_answer"))
    return {"key": "abstain_correct", "score": float(bool(outputs.get("no_answer")) == want)}


def _chars(outputs: dict) -> dict:
    return {"key": "injected_chars", "score": float(outputs.get("chars") or 0)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="retriever")
    args = parser.parse_args()
    if not os.environ.get("LANGSMITH_API_KEY"):
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    from langsmith import Client, evaluate

    rows = _rows()
    if not rows:
        raise SystemExit("No human_verified rows in evals/retriever_goldens.json")
    client = Client()
    _ensure_dataset(client, rows)
    result = evaluate(
        _target,
        data=DATASET,
        evaluators=[_guide_recall, _abstained_correctly, _chars],
        experiment_prefix=args.prefix,
        max_concurrency=1,
    )
    print("experiment:", getattr(result, "experiment_name", result))


if __name__ == "__main__":
    main()
