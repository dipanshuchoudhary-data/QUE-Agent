"""Faithfulness-only sweep over every golden query, ranked lowest first.

    uv run python scripts/run_faithfulness_all.py --out evals/baselines/faithfulness_all.json

Each query runs through the real pipeline with evidence capture, so the answer is
scored against the context the generator actually received (never a rerun). One
judge call per LLM-written answer. Turns answered without the LLM (cards, canned,
refusals, deterministic tool replies) have no generation to check and are listed
separately. Resumable: rows already in --out are skipped.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDENS = ROOT / "evals" / "retriever_goldens.json"

PROMPT = """You check whether an answer is faithful to the context the assistant was given.

Question: {query}

Context the assistant received:
{context}

Answer:
{answer}

Split the answer into its factual claims (steps, names, locations, numbers, conditions).
Ignore greetings, offers to help, and restating the question. A claim is SUPPORTED if the
context states it or directly implies it; otherwise UNSUPPORTED (invented, or contradicts
the context). Return only JSON:
{{"claims": [{{"claim": "<short>", "supported": true|false}}], "note": "<one sentence on the main problem, or 'ok'>"}}"""


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    return json.loads(m.group(0)) if m else {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", nargs="*", help="restrict to these golden ids")
    args = ap.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from evals.judge import QueJudge
    from evals.provenance import capture, generator_chunks
    from evals.rerank_cache import install

    install()
    judge = QueJudge()
    goldens = [
        g
        for g in json.loads(GOLDENS.read_text(encoding="utf-8"))["goldens"]
        if not g.get("rejected")
        and not g.get("expect_no_answer")
        and str(g.get("expected_output", "")).strip().upper() != "NOT IN GUIDE"
    ]
    if args.only:
        goldens = [g for g in goldens if g["id"] in set(args.only)]
    done = {}
    if args.out.exists():
        done = {r["id"]: r for r in json.loads(args.out.read_text(encoding="utf-8")).get("rows", [])}

    for g in goldens:
        if g["id"] in done and "error" not in done[g["id"]]:
            continue
        row = {"id": g["id"], "query": g["query"]}
        try:
            got = asyncio.run(capture(g["query"]))
            ev = got.get("evidence") or {}
            row["answer"] = got["answer"]
            row["model"] = got.get("model")
            row["route"] = (got.get("executed_path") or {}).get("route")
            row["runtime_mode"] = (got.get("executed_path") or {}).get("runtime_mode")
            row["llm_called"] = bool(ev.get("llm_called"))
            chunks = generator_chunks(ev)
            row["context_chunks"] = len(chunks or [])
            row["truncated"] = bool((ev.get("retrieved") or {}).get("truncated"))
            if not row["llm_called"]:
                row["faithfulness"] = None
                row["skipped"] = "no_llm_generation"
            elif not (got["answer"] or "").strip():
                row["faithfulness"] = None
                row["skipped"] = "empty_answer"
            elif not chunks:
                row["faithfulness"] = 0.0
                row["note"] = "answered with no evidence in the prompt"
                row["unsupported"] = ["(whole answer: no context)"]
            else:
                ctx = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(chunks, 1))
                raw = judge._complete(
                    [{"role": "user", "content": PROMPT.format(query=g["query"], context=ctx, answer=got["answer"][:3000])}],
                    max_tokens=900,
                )
                data = _parse(raw if isinstance(raw, str) else str(raw))
                claims = data.get("claims") or []
                if claims:
                    ok = sum(1 for c in claims if c.get("supported"))
                    row["faithfulness"] = round(ok / len(claims), 3)
                    row["claims"] = len(claims)
                    row["unsupported"] = [c.get("claim") for c in claims if not c.get("supported")]
                    row["note"] = data.get("note")
                else:
                    row["faithfulness"] = None
                    row["skipped"] = "judge_returned_no_claims"
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)[:200]
        done[g["id"]] = row
        print(g["id"], row.get("faithfulness"), row.get("skipped") or row.get("error") or "", flush=True)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"rows": list(done.values())}, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = list(done.values())
    from evals.scorebook import update

    update(
        f"faithfulness_all:{args.out.stem}",
        [{"id": r["id"], "query": r["query"], "scores": {"faithfulness": r.get("faithfulness")}} for r in rows],
    )
    scored = sorted((r for r in rows if r.get("faithfulness") is not None), key=lambda r: r["faithfulness"])
    skipped = [r for r in rows if r.get("faithfulness") is None]
    lines = ["# Faithfulness sweep (all golden queries, lowest first)", ""]
    if scored:
        lines.append(f"Scored {len(scored)} LLM-written answers; mean {sum(r['faithfulness'] for r in scored)/len(scored):.3f}. "
                     f"Below 0.7: {sum(r['faithfulness'] < 0.7 for r in scored)}. Not scored: {len(skipped)}.")
    lines += ["", "| id | faith | claims | route | unsupported / note | query |", "|---|---|---|---|---|---|"]
    for r in scored:
        bad = "; ".join(r.get("unsupported") or [])[:160] or r.get("note") or ""
        lines.append(f"| {r['id']} | {r['faithfulness']:.2f} | {r.get('claims','')} | {r.get('runtime_mode')} | {bad} | {r['query'][:55]} |")
    lines += ["", "## Not scored", ""]
    for r in skipped:
        lines.append(f"- {r['id']}: {r.get('skipped') or r.get('error')} ({r['query'][:60]})")
    args.out.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", args.out.with_suffix(".md"))


if __name__ == "__main__":
    main()
