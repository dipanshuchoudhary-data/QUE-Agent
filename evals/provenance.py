"""Evidence provenance for end-to-end evals.

Two different questions need two different inputs:

- retriever quality  -> what retrieval returns for the query (rerun offline, no LLM)
- answer faithfulness -> what the generator was actually given in the same run

``capture`` runs one production turn and returns the answer together with the
evidence record written by the pipeline (``app.obs.evidence``). Everything the
judge sees for faithfulness comes from that record, never from a second retrieval.
"""

from __future__ import annotations

from typing import Any

ANSWER_PATH_KEYS = ("route", "execution_class", "runtime_mode", "runtime_mode_reason", "tool", "tool_error", "tool_fallback")


async def capture(
    query: str,
    *,
    conversation_id: str | None = None,
    role: str | None = None,
    history: list[dict] | None = None,
) -> dict[str, Any]:
    from app.obs.evidence import capture_evidence
    from app.orchestration import pipeline
    from app.schemas.chat import ChatMessage, ChatRequest, QueUiContext

    request = ChatRequest(
        messages=[*(ChatMessage(**m) for m in (history or [])), ChatMessage(role="user", content=query)],
        conversation_id=conversation_id or f"eval-{abs(hash(query))}",
        context=QueUiContext(user_role=role) if role else None,
    )
    with capture_evidence() as record:
        response = await pipeline.complete(request)
    evidence = dict(record)
    return {
        "answer": response.message.content,
        "model": response.model,
        "knowledge_packs": response.knowledge_packs,
        "sources_used": response.sources_used,
        "evidence": evidence,
        "executed_path": executed_path(evidence),
    }


def executed_path(evidence: dict[str, Any] | None) -> dict[str, Any]:
    """The route that actually ran (not the one predicted from the query text)."""
    route = (evidence or {}).get("route") or {}
    return {k: route.get(k) for k in ANSWER_PATH_KEYS}


def generator_chunks(evidence: dict[str, Any] | None) -> list[str] | None:
    """Documents present in the LLM prompt, formatted for the judge.

    ``None`` means the row has no provenance record (an older answers file); an
    empty list means the generator really received no retrieved evidence.
    """
    if not evidence or "generator_context" not in evidence:
        return None
    docs = evidence["generator_context"].get("documents") or []
    return [f"{d.get('title', '')}\n{d.get('text', '')}".strip() for d in docs]


def evidence_summary(evidence: dict[str, Any] | None) -> dict[str, Any]:
    """Small, saveable view: what was retrieved vs what the generator received."""
    ev = evidence or {}
    ctx = ev.get("generator_context") or {}
    retrieved = ev.get("retrieved") or {}
    return {
        "executed_path": executed_path(ev),
        "llm_called": ev.get("llm_called", True),
        "retrieved_chunk_ids": retrieved.get("chunk_ids", []),
        "retrieval_mode": retrieved.get("mode"),
        "retrieval_no_answer": retrieved.get("no_answer"),
        "generator_documents": [d.get("title") for d in ctx.get("documents", [])],
        "generator_tool_blocks": [b.split("\n", 1)[0] for b in ctx.get("tool_blocks", [])],
        "prompt_chars": ctx.get("prompt_chars"),
    }
