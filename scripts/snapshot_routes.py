"""Free, deterministic per-row snapshot of how QUE handles every eval query.

    uv run python scripts/snapshot_routes.py --out evals/baselines/ml_baseline_routes.json

No LLM and no judge: for each query it records the production routing decision
(`decide_turn`) and, when the turn would retrieve, the retrieved chunk ids, scores
and no-answer flag. Run it before and after a change and diff per row
(`--compare before.json`), so regressions are judged row by row, not by averages.

Pin the environment first (local MiniLM or the API index) and keep it the same
for both runs; the pinned settings are saved in the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCES = (
    "retriever_goldens.json",
    "hard_cases.json",
    "scope_golden.json",
    "tool_cases.json",
    "efficiency_cases.json",
    "agent_cases.json",
    "multilingual_cases.json",
)


def _walk(obj, out: list[tuple[str, str]]) -> None:
    if isinstance(obj, dict):
        q = obj.get("query") or obj.get("question")
        if isinstance(q, str) and q.strip():
            out.append((str(obj.get("id") or ""), q.strip()))
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _walk(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, out)


def load_queries() -> tuple[list[dict], dict[str, str]]:
    rows: list[dict] = []
    hashes: dict[str, str] = {}
    for name in SOURCES:
        path = ROOT / "evals" / name
        if not path.exists():
            continue
        hashes[name] = hashlib.sha1(path.read_bytes()).hexdigest()[:12]
        found: list[tuple[str, str]] = []
        _walk(json.loads(path.read_text(encoding="utf-8")), found)
        for rid, query in found:
            rows.append({"key": f"{name}:{rid or len(rows)}", "source": name, "id": rid, "query": query})
    return rows, hashes


def snapshot_row(query: str, history: list[dict] | None = None) -> dict:
    from app.core.config import get_settings
    from app.knowledge.hybrid import select_hybrid
    from app.orchestration.pipeline import decide_turn
    from app.schemas.chat import ChatRequest

    started = time.perf_counter()
    decision = decide_turn(
        ChatRequest(
            messages=[*(history or []), {"role": "user", "content": query}],
            conversation_id="snapshot",
        )
    )
    u = decision.understanding
    row = {
        "route": u.route,
        "execution_class": u.execution_class,
        "canonical_intent": u.canonical_intent,
        "early_model": decision.early_model,
        "reasons": list(u.reasons),
        "retrieval": None,
    }
    if decision.early_reply is None and u.route in {"knowledge"}:
        trace: dict = {}
        selection = select_hybrid(
            decision.resolution.resolved_query or query,
            settings=get_settings(),
            canonical_intent=u.canonical_intent,
            execution_class=u.execution_class,
            trace=trace,
        )
        if selection is not None:
            row["retrieval"] = {
                "no_answer": bool(selection.no_answer),
                "chunk_ids": list(selection.chunk_ids),
                "scores": {k: round(float(v), 3) for k, v in selection.scores.items() if k in selection.chunk_ids},
                "docs": list(selection.pack_ids),
            }
    row["ms"] = round((time.perf_counter() - started) * 1000, 1)
    return row


def compare(before: dict, after: dict) -> dict:
    changes = []
    for key, b in before["rows"].items():
        a = after["rows"].get(key)
        if a is None:
            continue
        diffs = {}
        for field in ("route", "execution_class", "canonical_intent", "early_model"):
            if b.get(field) != a.get(field):
                diffs[field] = [b.get(field), a.get(field)]
        br, ar = b.get("retrieval"), a.get("retrieval")
        if (br or {}).get("chunk_ids") != (ar or {}).get("chunk_ids"):
            diffs["chunk_ids"] = [(br or {}).get("chunk_ids"), (ar or {}).get("chunk_ids")]
        if (br or {}).get("no_answer") != (ar or {}).get("no_answer"):
            diffs["no_answer"] = [(br or {}).get("no_answer"), (ar or {}).get("no_answer")]
        if diffs:
            changes.append({"key": key, "query": b["query"], "diffs": diffs})
    return {"rows_compared": len(before["rows"]), "rows_changed": len(changes), "changes": changes}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compare", type=Path, help="earlier snapshot to diff against")
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from app.core.config import get_settings

    cfg = get_settings()
    rows_in, hashes = load_queries()
    pins = {
        "embedding_provider": cfg.resolved_embedding_provider,
        "embedding_model": cfg.active_embedding_model,
        "reranker_provider": cfg.resolved_reranker_provider,
        "index": str(cfg.active_chroma_path),
        "top_k": cfg.que_rag_top_k,
        "candidate_k": cfg.que_rag_candidate_k,
        "min_score": cfg.que_rag_min_score,
        "rerank": cfg.que_rag_rerank_enabled,
        "semantic_router": cfg.que_semantic_router,
        "tools_enabled": cfg.que_tools_enabled,
        "dataset_hashes": hashes,
        "git_head": subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip(),
    }
    rows: dict[str, dict] = {}
    for item in rows_in:
        try:
            snap = snapshot_row(item["query"])
        except Exception as exc:  # noqa: BLE001 - one bad row must not hide the rest
            snap = {"error": f"{type(exc).__name__}: {exc}"[:200]}
        rows[item["key"]] = {"query": item["query"], **snap}
    payload = {"pins": pins, "rows": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("rows:", len(rows), "errors:", sum("error" in r for r in rows.values()))
    if args.compare:
        diff = compare(json.loads(args.compare.read_text(encoding="utf-8")), payload)
        out = args.out.with_suffix(".diff.json")
        out.write_text(json.dumps(diff, indent=2, ensure_ascii=False), encoding="utf-8")
        print("changed rows:", diff["rows_changed"], "of", diff["rows_compared"], "->", out)


if __name__ == "__main__":
    main()
