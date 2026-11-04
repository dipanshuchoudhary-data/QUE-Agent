"""Read-only retrieval diagnostics for judged rows under a score bar.

    uv run python scripts/diagnose_retrieval.py --baseline evals/baselines/retriever_judged_k3_c5_large_rerank.json

For each row it reports, without calling the judge:
  - claim-to-evidence: which KB chunk supports each expected-answer claim (token overlap)
  - where those evidence chunks sit in dense top-20, BM25 top-20, fused docs, and the final set
  - whether rerank ran, and what production would do with the query (card, retrieval, refuse)
  - a suggested cause from the failure taxonomy (a hint, to be confirmed by a person)

Nothing in the index or the goldens is changed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDENS = ROOT / "evals" / "retriever_goldens.json"
OUT_DIR = ROOT / "evals" / "diagnostics"
METRICS = ("ContextualRecallMetric", "ContextualPrecisionMetric", "ContextualRelevancyMetric")

_STOP = set(
    "the a an and or of to in on for with is are be it its this that these those as at by from "
    "you your they their them can will may if then so not no do does did how what where when "
    "which who into out up down over under also any all each per via than more most such "
    "click open go new use used using see shown shows student students teacher teachers".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall((text or "").casefold()) if len(t) > 2 and t not in _STOP}


def _claims(expected: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (expected or "").strip())
    out: list[str] = []
    for part in parts:
        for piece in re.split(r";\s+|\s+Next,\s+|\s+Finally,\s+|\s+After\s+", part):
            piece = piece.strip(" .")
            if len(piece) >= 25:
                out.append(piece)
    return out or ([expected.strip()] if expected.strip() else [])


def _support(claim: str, chunk_tokens: set[str]) -> float:
    need = _tokens(claim)
    if not need:
        return 0.0
    return len(need & chunk_tokens) / len(need)


def _rank_of(chunk_id: str, hits: list[dict]) -> int | None:
    for i, h in enumerate(hits, start=1):
        if h["chunk_id"] == chunk_id:
            return i
    return None


def _doc_rank(doc_id: str, hits: list[dict]) -> int | None:
    seen: list[str] = []
    for h in hits:
        if h["doc_id"] not in seen:
            seen.append(h["doc_id"])
    return seen.index(doc_id) + 1 if doc_id in seen else None


def _brief(hits) -> list[dict]:
    return [
        {
            "chunk_id": h.chunk_id,
            "doc_id": h.doc_id,
            "section": h.section,
            "score": round(float(h.score), 4),
        }
        for h in hits
    ]


def _suggest(row: dict, golden: dict, evidence: list[dict], final_docs: list[str], trace: dict) -> str:
    if (golden.get("expected_output") or "").strip().upper() == "NOT IN GUIDE":
        return "EVAL_ERROR (expected answer is NOT IN GUIDE)"
    if golden.get("category") == "ambiguous":
        return "AMBIGUOUS_QUERY"
    weak = [e for e in evidence if e["support"] < 0.5]
    if evidence and len(weak) == len(evidence):
        return "KB_GAP or GOLDEN_MISMATCH (no chunk supports the claims)"
    expected_docs = set(golden.get("expected_doc_ids") or [])
    if expected_docs and not (expected_docs & set(final_docs)):
        dense_docs = {h["doc_id"] for h in trace.get("dense", [])}
        if golden.get("category") == "typo_short_hinglish":
            return "LANGUAGE_MISMATCH / DOC_MISS"
        if not (expected_docs & dense_docs):
            return "DOC_MISS"
        return "RANKING_FAILURE (doc found, cut before final)"
    strong = [e for e in evidence if e["support"] >= 0.5]
    final_chunks = {h["chunk_id"] for h in trace.get("final", [])}
    if strong and not any(e["chunk_id"] in final_chunks for e in strong):
        return "EVIDENCE_MISS (right doc, supporting chunk not selected)"
    extra = [d for d in final_docs if d not in expected_docs]
    if extra:
        return "CONTEXT_NOISE (off-topic docs in final set)"
    return "REVIEW (evidence selected; check judge)"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--below", type=float, default=0.7)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", type=Path, default=OUT_DIR / "retrieval_audit")
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    from evals.prod_route import route_for

    from app.core.config import get_settings
    from app.knowledge.hybrid import select_hybrid
    from app.knowledge.query_embed import embed_query_cached
    from app.knowledge.sparse import load_bm25_corpus, query_bm25
    from app.knowledge.store import query_chunks

    data = json.loads(args.baseline.read_text(encoding="utf-8"))
    summary_cfg = (data.get("summary") or {}).get("config") or {}
    cfg = get_settings().model_copy(
        update={
            "que_rag_top_k": int(summary_cfg.get("top_k") or get_settings().que_rag_top_k),
            "que_rag_candidate_k": int(summary_cfg.get("candidate_k") or get_settings().que_rag_candidate_k),
        }
    )
    goldens = {g["id"]: g for g in json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]}

    targets = []
    for case in data["cases"]:
        scores = {
            n: (case.get(n) or {}).get("score")
            for n in METRICS
            if (case.get(n) or {}).get("score") is not None
        }
        if scores and min(scores.values()) < args.below:
            targets.append((case, scores))
    if args.limit:
        targets = targets[: args.limit]

    corpus = load_bm25_corpus(cfg)
    corpus_tokens = {e.chunk_id: _tokens(f"{e.title} {e.section} {e.text}") for e in corpus}
    by_id = {e.chunk_id: e for e in corpus}

    results: list[dict] = []
    for case, scores in targets:
        golden = goldens.get(case["id"], {})
        expected = str(golden.get("expected_output") or "")
        expected_docs = list(golden.get("expected_doc_ids") or [])
        route = route_for(case["query"])

        evidence: list[dict] = []
        for claim in _claims(expected):
            if expected.strip().upper() == "NOT IN GUIDE":
                break
            best = {"chunk_id": "", "support": 0.0, "scope": "kb"}
            for e in corpus:
                s = _support(claim, corpus_tokens[e.chunk_id])
                in_expected = e.doc_id in expected_docs
                if s > best["support"] or (s == best["support"] and in_expected and best["scope"] != "expected"):
                    best = {"chunk_id": e.chunk_id, "support": round(s, 2), "scope": "expected" if in_expected else "kb"}
            entry = by_id.get(best["chunk_id"])
            evidence.append(
                {
                    "claim": claim,
                    "chunk_id": best["chunk_id"],
                    "doc_id": entry.doc_id if entry else "",
                    "section": entry.section if entry else "",
                    "support": best["support"],
                    "in_expected_doc": best["scope"] == "expected",
                }
            )

        trace: dict = {}
        vector = embed_query_cached(case["query"], settings=cfg)
        dense20 = _brief(query_chunks(vector, top_k=20, settings=cfg))
        sparse20 = _brief(query_bm25(case["query"], top_k=20, settings=cfg))
        select_hybrid(case["query"], settings=cfg, query_vector=vector, trace=trace)
        final_docs = [h["doc_id"] for h in trace.get("final", [])]

        for e in evidence:
            e["dense_rank_top20"] = _rank_of(e["chunk_id"], dense20)
            e["bm25_rank_top20"] = _rank_of(e["chunk_id"], sparse20)
            e["doc_rank_fused"] = _doc_rank(e["doc_id"], trace.get("fused", []))
            e["in_final"] = any(h["chunk_id"] == e["chunk_id"] for h in trace.get("final", []))

        results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "category": golden.get("category"),
                "scores": {k.replace("Contextual", "").replace("Metric", "").lower(): v for k, v in scores.items()},
                "expected_docs": expected_docs,
                "prod_route": route.served_by,
                "prod_execution_class": route.execution_class,
                "prod_canonical_intent": route.canonical_intent,
                "rerank": trace.get("rerank"),
                "dense_top": dense20[:5],
                "dense_docs_top20": sorted({h["doc_id"] for h in dense20}),
                "bm25_docs_top20": sorted({h["doc_id"] for h in sparse20}),
                "fused_docs": [h["doc_id"] for h in trace.get("fused", [])],
                "final": trace.get("final", []),
                "evidence": evidence,
                "suggested_cause": _suggest(case, golden, evidence, final_docs, {**trace, "dense": dense20}),
            }
        )
        print(case["id"], results[-1]["suggested_cause"], "| rerank", trace.get("rerank"), flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    json_path = args.out.with_suffix(".json")
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path = args.out.with_suffix(".md")
    md_path.write_text(_markdown(results, args.below, cfg), encoding="utf-8")
    print("wrote", json_path)
    print("wrote", md_path)


def _markdown(results: list[dict], below: float, cfg) -> str:
    from collections import Counter

    cause = Counter(r["suggested_cause"].split(" (")[0] for r in results)
    served = Counter(r["prod_route"] for r in results)
    rerank = Counter(str(r["rerank"]) for r in results)
    lines = [
        "# Retrieval audit",
        "",
        f"Rows with any metric under {below}: {len(results)}. Retrieval settings match the scored run "
        f"(top-k {cfg.que_rag_top_k}, candidate pool {cfg.que_rag_candidate_k}, rerank "
        f"{'on' if cfg.que_rag_rerank_enabled else 'off'}). Causes below are heuristic suggestions.",
        "",
        "Suggested causes: " + ", ".join(f"{k} {v}" for k, v in cause.most_common()),
        "",
        "Production would serve these rows by: " + ", ".join(f"{k} {v}" for k, v in served.most_common()),
        "",
        "Rerank during this diagnostic: " + ", ".join(f"{k} {v}" for k, v in rerank.most_common()),
        "",
    ]
    for r in results:
        s = r["scores"]
        lines.append(f"## {r['id']} — {r['query']}")
        lines.append("")
        lines.append(
            f"Scores: recall {s.get('recall')}, precision {s.get('precision')}, relevancy {s.get('relevancy')}. "
            f"Category {r['category']}. Suggested cause: **{r['suggested_cause']}**."
        )
        lines.append(
            f"Production route: {r['prod_route']} ({r['prod_execution_class']}"
            f"{', ' + r['prod_canonical_intent'] if r['prod_canonical_intent'] else ''}). "
            f"Rerank: {r['rerank']}."
        )
        lines.append(
            f"Expected docs: {', '.join(r['expected_docs']) or 'none'}. "
            f"Fused doc order: {', '.join(r['fused_docs'][:6]) or 'none'}. "
            f"Final: {', '.join(h['doc_id'] + ' / ' + h['section'] for h in r['final']) or 'none'}."
        )
        lines.append("")
        if r["evidence"]:
            lines.append("| Claim | Best KB chunk | Support | Dense rank | BM25 rank | Doc rank | In final |")
            lines.append("|---|---|---:|---:|---:|---:|---|")
            for e in r["evidence"]:
                claim = e["claim"].replace("|", "/")
                where = f"{e['doc_id']} / {e['section']}".replace("|", "/")
                lines.append(
                    f"| {claim[:90]} | {where[:70]} | {e['support']} | {e['dense_rank_top20']} | "
                    f"{e['bm25_rank_top20']} | {e['doc_rank_fused']} | {'yes' if e['in_final'] else 'no'} |"
                )
            lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
