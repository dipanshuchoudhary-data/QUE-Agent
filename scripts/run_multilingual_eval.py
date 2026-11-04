"""Multilingual / informal-query diagnostics (separate from the retriever goldens).

    # free, deterministic: routing + retrieval, no LLM
    uv run python scripts/run_multilingual_eval.py --out evals/baselines/ml_stageA.json

    # adds one production turn per case (LLM) and one judge call per answered row
    uv run python scripts/run_multilingual_eval.py --generate --out evals/baselines/ml_stageB.json

Metrics are diagnostic and reported per kind. A metric that does not apply to a case
is N/A (None) and is excluded from means - never counted as 0.

  routing_ok          outcome (answer | no_answer | clarify | refuse | tool | canned) is acceptable
  evidence_hit        an expected doc is in the top-2 retrieved (N/A when no docs expected)
  cross_language      top-2 docs overlap with the English anchor of the same group (N/A without anchor docs)
  ambiguity_ok        ambiguous case ended in an acceptable behaviour (N/A for non-ambiguous)
  grounded            (generate) answer states nothing the evidence does not support
  intent_preserved    (generate) answer addresses what the user meant, or honestly asks/declines
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CASES = ROOT / "evals" / "multilingual_cases.json"
JUDGE_CACHE = ROOT / "evals" / "diagnostics" / "ml_judge_cache.json"

_JUDGE_PROMPT = """You grade one answer from a product assistant for the exam platform Quizzer.

USER QUERY (may be Hinglish, Romanized Hindi, informal or ambiguous):
{query}

EVIDENCE THE ASSISTANT WAS GIVEN (product documentation excerpts; "(none)" means nothing was retrieved):
{evidence}

ASSISTANT ANSWER:
{answer}

Score each from 0 to 1:
- grounded: 1 if every product claim (button, page, setting, capability) in the answer is supported by the evidence, 0 if it states product behavior the evidence does not support. A pure clarifying question or an honest "I don't have that information" makes no claims: score 1.
- intent_preserved: 1 if the answer addresses what the user most plausibly meant, or honestly asks what they mean / says it cannot help with it. 0 if it answers a different question or invents a feature to satisfy the request.
Return JSON only."""


def _outcome(row: dict) -> str:
    if row.get("route") == "clarify" or row.get("early_model") == "scope:clarify_referent":
        return "clarify"
    if row.get("route") == "refuse":
        return "refuse"
    if row.get("route") == "tool":
        return "tool"
    if row.get("route") == "canned_eligible":
        return "canned"
    ret = row.get("retrieval")
    if ret is None:
        return "card"  # workflow card / deterministic reply: answered without retrieval
    return "no_answer" if ret["no_answer"] else "answer"


def _docs(row: dict) -> list[str]:
    ret = row.get("retrieval") or {}
    return [d for d in ret.get("docs", []) if d != "core"]


def _mean(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return round(statistics.mean(vals), 3) if vals else None


def stage_a(cases: list[dict]) -> list[dict]:
    from snapshot_routes import snapshot_row

    out = []
    for case in cases:
        snap = snapshot_row(case["query"], case.get("history"))
        outcome = _outcome(snap)
        expected = case.get("expected_docs") or []
        docs = _docs(snap)
        out.append(
            {
                "id": case["id"],
                "kind": case["kind"],
                "group": case["group"],
                "query": case["query"],
                "outcome": outcome,
                "docs": docs,
                "scores": (snap.get("retrieval") or {}).get("scores"),
                "routing_ok": outcome in case["acceptable"] or (outcome in {"canned", "card"} and "answer" in case["acceptable"]),
                "evidence_hit": (None if outcome == "card" or not expected else (outcome == "answer" and any(d in expected for d in docs))),
                "ambiguity_ok": (outcome in case["acceptable"]) if case["kind"] == "ambiguous" else None,
                "ms": snap["ms"],
            }
        )
    # cross-language consistency vs the English anchor of the group (docs known only if anchor expects docs)
    anchors = {c["group"]: r for c, r in zip(cases, out, strict=True) if c["kind"] == "english_anchor"}
    for c, r in zip(cases, out, strict=True):
        a = anchors.get(c["group"])
        if c["kind"] == "english_anchor" or a is None or not c.get("expected_docs") or not a["docs"]:
            r["cross_language"] = None
        else:
            r["cross_language"] = round(len(set(r["docs"]) & set(a["docs"])) / len(set(r["docs"]) | set(a["docs"])), 3) if r["docs"] else 0.0
    return out


async def stage_b(cases: list[dict], rows: list[dict], use_judge: bool) -> None:
    from evals.judge import QueJudge
    from evals.provenance import capture, generator_chunks
    from pydantic import BaseModel, Field

    from app.obs import metrics as obs

    class _J(BaseModel):
        grounded: float = Field(ge=0, le=1)
        intent_preserved: float = Field(ge=0, le=1)
        reason: str

    judge = QueJudge() if use_judge else None
    cache = json.loads(JUDGE_CACHE.read_text(encoding="utf-8")) if JUDGE_CACHE.exists() else {}
    for case, row in zip(cases, rows, strict=True):
        started = time.perf_counter()
        result = None
        for attempt in range(4):  # free providers 404/5xx at random; infra noise is not a system result
            try:
                result = await capture(case["query"], history=case.get("history"), conversation_id=f"ml-{case['id']}-{attempt}")
                row.pop("generate_error", None)
                break
            except Exception as exc:  # noqa: BLE001
                row["generate_error"] = f"{type(exc).__name__}: {exc}"[:200]
                row["generate_attempts"] = attempt + 1
                await asyncio.sleep(2)
        if result is None:
            continue
        row["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        turn = obs._turns[-1] if obs._turns else {}
        row["llm_called"] = result["evidence"].get("llm_called", True)
        # A turn without an LLM call may not write a trace row; never read the previous one.
        row["prompt_tokens"] = int(turn.get("prompt_tokens") or 0) if row["llm_called"] else 0
        row["completion_tokens"] = int(turn.get("completion_tokens") or 0) if row["llm_called"] else 0
        interp = result["evidence"].get("interpret")
        if interp:
            row["interpret"] = interp
            row["prompt_tokens"] += int(interp.get("tokens") or 0)
            row["latency_ms"] = row["latency_ms"]  # already includes the interpret call
        row["model"] = result["model"]
        row["answer"] = result["answer"]
        row["executed_path"] = result["executed_path"]
        gen = generator_chunks(result["evidence"]) or []
        row["generator_docs"] = len(gen)
        if judge is None:
            continue
        evidence = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(gen, 1)) or "(none)"
        prompt = _JUDGE_PROMPT.format(query=case["query"], evidence=evidence[:6000], answer=result["answer"][:2500])
        key = hashlib.sha1(prompt.encode()).hexdigest()
        if key not in cache:
            try:
                judged = judge.generate(prompt, schema=_J)
                judged = judged if isinstance(judged, _J) else _J.model_validate(judged)
                cache[key] = judged.model_dump()
                JUDGE_CACHE.write_text(json.dumps(cache), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                row["judge_error"] = str(exc)[:200]
                continue
        # Workflow cards are curated content, not retrieved evidence: grounding is N/A there.
        row["grounded"] = None if row["outcome"] == "card" else round(float(cache[key]["grounded"]), 3)
        row["intent_preserved"] = round(float(cache[key]["intent_preserved"]), 3)
        row["judge_reason"] = cache[key]["reason"][:300]
        print(case["id"], row["outcome"], row["grounded"], row["intent_preserved"], flush=True)


def summarize(rows: list[dict]) -> dict:
    def block(subset: list[dict]) -> dict:
        return {
            "n": len(subset),
            "routing_ok": _mean([float(r["routing_ok"]) for r in subset]),
            "evidence_hit": _mean([None if r["evidence_hit"] is None else float(r["evidence_hit"]) for r in subset]),
            "cross_language": _mean([r.get("cross_language") for r in subset]),
            "ambiguity_ok": _mean([None if r["ambiguity_ok"] is None else float(r["ambiguity_ok"]) for r in subset]),
            "grounded": _mean([r.get("grounded") for r in subset]),
            "intent_preserved": _mean([r.get("intent_preserved") for r in subset]),
            "latency_ms_mean": _mean([r.get("latency_ms") for r in subset]),
            "tokens_mean": _mean([(r["prompt_tokens"] + r["completion_tokens"]) if "prompt_tokens" in r else None for r in subset]),
            "llm_calls": sum(int(bool(r.get("llm_called"))) + int(bool((r.get("interpret") or {}).get("tokens"))) for r in subset) if any("llm_called" in r for r in subset) else None,
        }

    kinds = sorted({r["kind"] for r in rows})
    return {"all": block(rows), "by_kind": {k: block([r for r in rows if r["kind"] == k]) for k in kinds}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--generate", action="store_true", help="run production turns (LLM)")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--only", nargs="*", help="case ids")
    args = ap.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    rows = stage_a(cases)
    if args.generate:
        asyncio.run(stage_b(cases, rows, use_judge=not args.no_judge))
    payload = {"summary": summarize(rows), "rows": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"]["all"], indent=2))
    for r in rows:
        flag = "" if r["routing_ok"] else "  <-- routing"
        print(f"{r['id']} {r['kind']:<15} {r['outcome']:<10} docs={r['docs']}{flag}")


if __name__ == "__main__":
    main()
