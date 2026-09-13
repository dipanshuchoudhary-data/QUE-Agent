#!/usr/bin/env python3
"""QUE efficiency harness — offline by default (no LLM).

  uv run python scripts/benchmark_efficiency.py
  uv run python scripts/benchmark_efficiency.py --write-before
  uv run python scripts/benchmark_efficiency.py --write-after
  uv run python scripts/benchmark_efficiency.py --live
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CASES_PATH = ROOT / "evals" / "efficiency_cases.json"
BEFORE_PATH = ROOT / "evals" / "baselines" / "efficiency_before.json"
AFTER_PATH = ROOT / "evals" / "baselines" / "efficiency_after.json"


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return list(payload.get("cases") or [])


def _prompt_chars(messages: list) -> int:
    n = 0
    for message in messages or []:
        content = getattr(message, "content", message)
        if isinstance(content, str):
            n += len(content)
        else:
            n += len(str(content or ""))
    return n


def measure_offline_case(case: dict[str, Any]) -> dict[str, Any]:
    from app.orchestration.pipeline import _prepare_with_knowledge, decide_turn
    from app.schemas.chat import ChatRequest, QueUiContext

    query = str(case["query"])
    ui = case.get("ui")
    request = ChatRequest(
        messages=[{"role": "user", "content": query}],
        context=QueUiContext.model_validate(ui) if ui else None,
    )
    started = time.perf_counter()
    decision = decide_turn(request)
    understanding = decision.understanding
    early = decision.early_reply is not None
    packs: list[str] = []
    chunk_ids: list[str] = []
    prompt_chars = 0
    retrieval_count = 0
    if not early and understanding.route not in {"refuse", "canned_eligible", "clarify"}:
        state = _prepare_with_knowledge(
            request,
            resolution=decision.resolution,
            understanding=understanding,
        )
        prompt_chars = _prompt_chars(state.get("messages") or [])
        packs = list(state.get("knowledge_packs") or [])
        retrieval_count = len(packs)
        for src in state.get("sources_used") or []:
            if str(src).startswith("knowledge:") and str(src) != "knowledge:core":
                pass
    elif early:
        prompt_chars = len(decision.early_reply or "")
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
    execution_class = getattr(understanding, "execution_class", None) or understanding.route
    canonical = getattr(understanding, "canonical_intent", None)
    confidence = float(getattr(understanding, "confidence", 0.0) or 0.0)
    llm_would_run = (not early) and understanding.route not in {"refuse", "canned_eligible", "clarify"}
    if understanding.route == "tool":
        # Tools-off still early-replies TOOL_NOT_READY; graph would run when tools on.
        llm_would_run = decision.early_reply is None
    return {
        "id": case["id"],
        "query": query,
        "bucket": case.get("bucket"),
        "route": understanding.route,
        "execution_class": execution_class,
        "canonical_intent": canonical,
        "confidence": round(confidence, 3),
        "early_model": decision.early_model,
        "llm_would_run": llm_would_run,
        "prompt_chars": prompt_chars,
        "prompt_tokens_est": max(1, prompt_chars // 4) if prompt_chars else 0,
        "knowledge_packs": packs,
        "retrieval_count": retrieval_count,
        "chunk_ids": chunk_ids,
        "elapsed_ms": elapsed_ms,
    }


async def measure_live_case(case: dict[str, Any]) -> dict[str, Any]:
    from app.core.llm import last_llm_usage
    from app.orchestration.pipeline import complete
    from app.schemas.chat import ChatRequest, QueUiContext

    query = str(case["query"])
    ui = case.get("ui")
    request = ChatRequest(
        messages=[{"role": "user", "content": query}],
        context=QueUiContext.model_validate(ui) if ui else None,
        conversation_id=f"eff-{case['id']}",
    )
    started = time.perf_counter()
    response = await complete(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
    usage = last_llm_usage()
    return {
        "id": case["id"],
        "query": query,
        "model": response.model,
        "latency_ms": elapsed_ms,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "reasoning_tokens": usage.reasoning_tokens,
        "knowledge_packs": list(response.knowledge_packs or []),
        "answer_chars": len(response.message.content or ""),
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    llm_rows = [r for r in rows if r.get("llm_would_run")]
    simple = [r for r in rows if r.get("bucket") in {"exact", "paraphrase", "grammar"}]
    return {
        "n": len(rows),
        "llm_would_run": sum(1 for r in rows if r.get("llm_would_run")),
        "zero_llm": sum(1 for r in rows if not r.get("llm_would_run")),
        "simple_zero_llm": sum(1 for r in simple if not r.get("llm_would_run")),
        "simple_n": len(simple),
        "mean_prompt_chars_llm": round(
            (sum(r.get("prompt_chars") or 0 for r in llm_rows) / len(llm_rows)) if llm_rows else 0.0,
            1,
        ),
        "max_prompt_chars": max((r.get("prompt_chars") or 0) for r in rows) if rows else 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QUE efficiency benchmark")
    parser.add_argument("--live", action="store_true", help="Call complete() (needs LLM keys)")
    parser.add_argument("--write-before", action="store_true")
    parser.add_argument("--write-after", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    logging.getLogger().setLevel(logging.WARNING)
    cases = _load_cases()
    if args.live:
        import asyncio

        rows = asyncio.run(_live_all(cases))
    else:
        rows = [measure_offline_case(c) for c in cases]

    summary = _summarize(rows)
    payload = {"version": "1.0.0", "mode": "live" if args.live else "offline", "summary": summary, "cases": rows}

    print(f"{'ID':<10} {'CLASS':<22} {'LLM':<5} {'CHARS':>7}  QUERY")
    print("-" * 88)
    for row in rows:
        q = str(row.get("query") or "")[:48]
        print(
            f"{row['id']:<10} {str(row.get('execution_class') or row.get('model') or ''):<22} "
            f"{'yes' if row.get('llm_would_run') else 'no':<5} {int(row.get('prompt_chars') or 0):7d}  {q}"
        )
    print("-" * 88)
    print(
        f"zero_llm={summary.get('zero_llm')}/{summary.get('n')}  "
        f"simple_zero_llm={summary.get('simple_zero_llm')}/{summary.get('simple_n')}  "
        f"mean_prompt_chars_llm={summary.get('mean_prompt_chars_llm')}"
    )

    target = AFTER_PATH if args.write_after else (BEFORE_PATH if args.write_before else None)
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {target}")

    if args.json:
        print(json.dumps(payload, indent=2))
    return 0


async def _live_all(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in cases:
        try:
            out.append(await measure_live_case(case))
        except Exception as exc:  # noqa: BLE001
            out.append({"id": case["id"], "query": case["query"], "error": type(exc).__name__})
    return out


if __name__ == "__main__":
    raise SystemExit(main())
