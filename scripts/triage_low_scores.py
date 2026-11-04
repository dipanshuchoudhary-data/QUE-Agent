"""Assign each low-scoring query a root-cause bucket from saved eval artifacts. No API calls.

    uv run python scripts/triage_low_scores.py \
        --answers evals/baselines/generator_provenance_check.json \
        --scores evals/baselines/deepeval_pipeline_provenance.json

Inputs are the answers file written by ``run_generator_eval.py`` (route + evidence
captured in the same run as each answer) and, optionally, the per-metric scores from
``run_deepeval_pipeline.py``. Rules run in order and the first match wins, because an
earlier stage failing makes later metrics meaningless (a model that never saw the
evidence cannot be "unfaithful" in a way a prompt fix would help).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

LOW = 0.7

# bucket -> (what is wrong, where to fix it)
BUCKETS = {
    "llm_failure": ("model returned nothing / errored", "LLM gateway, model choice, retries"),
    "tool_failed": ("a live tool ran and errored", "tool path, Quizzer contract, policy/role"),
    "tool_route": ("a tool ran for a turn expected to be knowledge", "routing (understanding / selector)"),
    "card_mismatch": ("a static workflow card was served and scored low", "intent prototypes / card content"),
    "no_evidence_given": ("generator received no retrieved documents", "retrieval gating, route, no-answer handling"),
    "retrieval_gap": ("the needed fact is not in the retrieved chunks (low recall)", "chunking, query, KB content"),
    "ranking": ("evidence retrieved but ranked below noise (low precision)", "rerank / top-k"),
    "not_grounded": ("evidence was present and complete, answer still strays (low faithfulness)", "prompt, model, context placement"),
    "incomplete_answer": ("grounded but misses reference facts (low correctness)", "answer length, chunk cap, prompt"),
    "chunk_noise": ("only contextual relevancy is low", "chunk granularity (usually not a defect)"),
}


def classify(case: dict, scores: dict | None) -> str | None:
    judge = case.get("judge") or {}
    s = {k: v.get("score") for k, v in (scores or {}).items() if isinstance(v, dict)}
    low = {k for k, v in s.items() if v is not None and v < LOW}
    gen_low = (judge.get("completeness", 1) < LOW) or (judge.get("contradiction", 0) > 0.3)
    if not low and not gen_low and "error" not in case:
        return None

    path = case.get("executed_path") or {}
    ev = case.get("evidence") or {}
    docs = (ev.get("generator_context") or {}).get("documents")
    model = str(case.get("model", ""))

    if "error" in case:
        return "llm_failure"
    if path.get("tool_error"):
        return "tool_failed"
    if path.get("runtime_mode") in ("workflow", "agent") and case.get("route_predicted") != "tool":
        return "tool_route"
    if model.startswith("workflow:"):
        return "card_mismatch"
    if ev.get("generator_context") is not None and not docs and ev.get("llm_called", True):
        return "no_evidence_given"
    if s.get("recall") is not None and s["recall"] < LOW:
        return "retrieval_gap"
    if s.get("precision") is not None and s["precision"] < LOW:
        return "ranking"
    if s.get("faithfulness") is not None and s["faithfulness"] < LOW:
        return "not_grounded"
    if s.get("correctness") is not None and s["correctness"] < LOW:
        return "incomplete_answer"
    if low == {"relevancy"}:
        return "chunk_noise"
    return "incomplete_answer" if gen_low else "chunk_noise"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", type=Path, required=True)
    ap.add_argument("--scores", type=Path)
    ap.add_argument("--out", type=Path, help="optional markdown output")
    args = ap.parse_args()

    cases = json.loads(args.answers.read_text(encoding="utf-8"))["cases"]
    scored = {}
    if args.scores and args.scores.exists():
        scored = {r["id"]: r["scores"] for r in json.loads(args.scores.read_text(encoding="utf-8"))["rows"]}

    rows = []
    for c in cases:
        bucket = classify(c, scored.get(c["id"]))
        if bucket:
            rows.append((c["id"], bucket, c["query"], scored.get(c["id"]) is not None))

    counts = Counter(b for _, b, _, _ in rows)
    lines = [f"Low-scoring rows: {len(rows)} of {len(cases)}", ""]
    lines += ["| Bucket | Rows | What is wrong | Fix in |", "|---|---|---|---|"]
    for b, n in counts.most_common():
        lines.append(f"| {b} | {n} | {BUCKETS[b][0]} | {BUCKETS[b][1]} |")
    lines += ["", "| id | bucket | query | per-metric scores used |", "|---|---|---|---|"]
    for i, b, q, has in sorted(rows, key=lambda r: r[1]):
        lines.append(f"| {i} | {b} | {q[:70]} | {'yes' if has else 'generator judge only'} |")
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
