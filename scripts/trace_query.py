"""Run one query through the real chat pipeline and print what the generator got.

    uv run python scripts/trace_query.py "Where is Monitoring in the sidebar?"
    uv run python scripts/trace_query.py "How many students are live right now?" --role teacher
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def run_traced(query: str, *, ui_context: dict | None = None, conversation_id: str | None = None) -> dict:
    from app.obs.evidence import capture_evidence
    from app.orchestration import pipeline
    from app.schemas.chat import ChatMessage, ChatRequest, QueUiContext

    request = ChatRequest(
        messages=[ChatMessage(role="user", content=query)],
        conversation_id=conversation_id or f"trace-{abs(hash(query))}",
        context=QueUiContext(**ui_context) if ui_context else None,
    )
    with capture_evidence() as record:
        response = await pipeline.complete(request)
    return {
        "query": query,
        "answer": response.message.content,
        "model": response.model,
        "knowledge_packs": response.knowledge_packs,
        "sources_used": response.sources_used,
        "evidence": dict(record),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--role", default=None)
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    ui = {"user_role": args.role} if args.role else None
    out = asyncio.run(run_traced(args.query, ui_context=ui))
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
