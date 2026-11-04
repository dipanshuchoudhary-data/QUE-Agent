"""Judge-free retrieval ablations, one variable per variant.

    uv run python scripts/ablate_retrieval.py --baseline evals/baselines/phase1_raw_k3_c5.json \
        --variants base,neighbor1,dynamic0.6,rerank_off --out evals/diagnostics/ablations

No LLM judge is called, so runs are cheap and repeatable. Per variant it reports, over the
same rows: claim coverage (share of expected-answer claims whose words are found in the
final text, threshold 0.6), doc hit rate, noise (final chunks from non-expected docs),
mean final characters, and how often rerank ran or failed open. Coverage is a word-overlap
proxy for recall, not a replacement for the judge.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDENS = ROOT / "evals" / "retriever_goldens.json"
M = ("ContextualRecallMetric", "ContextualPrecisionMetric", "ContextualRelevancyMetric")

VARIANTS: dict[str, dict] = {
    "base": {"que_rag_top_k": 2, "que_rag_candidate_k": 4},
    "neighbor1": {"que_rag_top_k": 2, "que_rag_candidate_k": 4, "que_rag_neighbor_expand": 1},
    "neighbor2": {"que_rag_top_k": 2, "que_rag_candidate_k": 4, "que_rag_neighbor_expand": 2},
    "dynamic0.6": {"que_rag_top_k": 2, "que_rag_candidate_k": 4, "que_rag_dynamic_k_ratio": 0.6},
    "dynamic0.8": {"que_rag_top_k": 2, "que_rag_candidate_k": 4, "que_rag_dynamic_k_ratio": 0.8},
    "normalize": {"que_rag_top_k": 2, "que_rag_candidate_k": 4, "que_rag_query_normalize": True},
    "rerank_off": {"que_rag_top_k": 2, "que_rag_candidate_k": 4, "que_rag_rerank_enabled": False},
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--variants", default="base,neighbor1,dynamic0.6,rerank_off")
    parser.add_argument("--rows", choices=("weak_or_retrieval", "weak", "all"), default="weak_or_retrieval")
    parser.add_argument("--embed-model", default="")
    parser.add_argument("--chroma", default="")
    parser.add_argument("--out", type=Path, default=ROOT / "evals" / "diagnostics" / "ablations")
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    from evals.prod_route import route_for
    from evals.rerank_cache import install
    from scripts.diagnose_retrieval import _claims, _support, _tokens

    from app.core.config import get_settings
    from app.knowledge.embeddings import EmbeddingsClient  # noqa: F401
    from app.knowledge.hybrid import select_hybrid
    from app.knowledge.sparse import load_bm25_corpus

    stats = install()
    base_cfg = get_settings()
    if args.embed_model:
        base_cfg = base_cfg.model_copy(update={"que_embedding_model": args.embed_model})
    if args.chroma:
        base_cfg = base_cfg.model_copy(update={"que_chroma_path": args.chroma})

    goldens = {g["id"]: g for g in json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]}
    cases = json.loads(args.baseline.read_text(encoding="utf-8"))["cases"]
    rows = []
    for c in cases:
        g = goldens.get(c["id"])
        if not g or g.get("expect_no_answer"):
            continue
        scores = [(c.get(m) or {}).get("score") for m in M]
        scores = [s for s in scores if s is not None]
        weak = bool(scores) and min(scores) < 0.7
        retrieval = route_for(c["query"]).served_by == "retrieval"
        if args.rows == "all" or (args.rows == "weak" and weak) or (args.rows == "weak_or_retrieval" and (weak or retrieval)):
            rows.append(g)
    print("rows:", len(rows), flush=True)

    names = [v.strip() for v in args.variants.split(",") if v.strip()]
    results: dict[str, list[dict]] = {n: [] for n in names}
    for g in rows:
        for name in names:
            cfg = base_cfg.model_copy(update=VARIANTS[name])
            trace: dict = {}
            try:
                sel = select_hybrid(g["query"], settings=cfg, trace=trace)
            except Exception as exc:  # noqa: BLE001
                print("ERR", g["id"], name, str(exc)[:100], flush=True)
                continue
            if sel is None:
                continue
            hits = [h for h in sel.hits if h.doc_id and h.doc_id != "core"]
            text = " ".join(h.text for h in hits)
            toks = _tokens(text)
            claims = _claims(str(g.get("expected_output") or ""))
            covered = [_support(c, toks) >= 0.6 for c in claims] if claims else []
            exp = set(g.get("expected_doc_ids") or [])
            docs = [h.doc_id for h in hits]
            results[name].append(
                {
                    "id": g["id"],
                    "coverage": (sum(covered) / len(covered)) if covered else None,
                    "doc_hit": bool(exp & set(docs)) if exp else None,
                    "noise": (sum(d not in exp for d in docs) / len(docs)) if docs and exp else None,
                    "chunks": len(hits),
                    "chars": sum(len(h.text) for h in hits),
                    "rerank": trace.get("rerank"),
                }
            )
        print(g["id"], flush=True)

    summary = {}
    for name, rs in results.items():
        def mean(key, rs=rs):
            vals = [r[key] for r in rs if r[key] is not None]
            return round(statistics.mean(vals), 3) if vals else None

        summary[name] = {
            "rows": len(rs),
            "coverage": mean("coverage"),
            "full_coverage_rows": sum(1 for r in rs if r["coverage"] == 1.0),
            "doc_hit": mean("doc_hit"),
            "noise": mean("noise"),
            "chunks": mean("chunks"),
            "chars": mean("chars"),
            "rerank_ok": sum(r["rerank"] == "ok" for r in rs),
            "rerank_failed": sum(r["rerank"] == "failed" for r in rs),
            "rerank_skipped": sum(r["rerank"] == "skipped" for r in rs),
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(
        json.dumps({"summary": summary, "rerank_cache": stats, "results": results}, indent=2), encoding="utf-8"
    )
    lines = [
        "| Variant | Rows | Coverage | Rows fully covered | Doc hit | Noise | Chunks | Chars | Rerank ok/failed/skipped |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for n, s in summary.items():
        lines.append(
            f"| {n} | {s['rows']} | {s['coverage']} | {s['full_coverage_rows']} | {s['doc_hit']} | {s['noise']} | "
            f"{s['chunks']} | {s['chars']} | {s['rerank_ok']}/{s['rerank_failed']}/{s['rerank_skipped']} |"
        )
    args.out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    _ = load_bm25_corpus


if __name__ == "__main__":
    main()
