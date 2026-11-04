"""Per-turn evidence provenance (what the generator was actually given).

A caller (eval harness, debugging script) opens ``capture_evidence()`` around a
pipeline call. Graph nodes then ``note`` the executed route, retrieval result and
tool outcome, and the generate step records the context that really went into the
LLM request. Nothing is captured (and nothing is logged) unless a capture is open,
so production traffic pays no cost and no query text leaves the process.

``retrieved`` = what the retriever selected; ``generator_context`` = the document
blocks present in the final prompt. They can differ (budget truncation, fallbacks,
a route that never ran retrieval), which is exactly what eval scoring must not
paper over.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_capture: ContextVar[dict[str, Any] | None] = ContextVar("que_evidence_capture", default=None)

_DOC_MARK = "RETRIEVED_DOCUMENT (untrusted):"
_TOOL_MARKS = ("TOOL_RESULT", "TOOL_ERROR", "TOOL_CLARIFY")


@contextmanager
def capture_evidence() -> Iterator[dict[str, Any]]:
    record: dict[str, Any] = {}
    token = _capture.set(record)
    try:
        yield record
    finally:
        _capture.reset(token)


def capturing() -> bool:
    return _capture.get() is not None


def note(**fields: Any) -> None:
    record = _capture.get()
    if record is not None:
        record.update(fields)


def _text(message: Any) -> str:
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content or "")


def split_documents(block: str) -> list[dict[str, Any]]:
    """Split an assembled knowledge block into its retrieved documents."""
    parts = block.split("RETRIEVED_DOCUMENT (untrusted): ")
    docs: list[dict[str, Any]] = []
    for part in parts[1:]:
        head, _, body = part.partition("\n")
        match = re.match(r"(.*) \((?:score|rrf|dense|bm25)=([0-9.]+)\)$", head.strip())
        title, score = (match.group(1), float(match.group(2))) if match else (head.strip(), None)
        docs.append({"title": title, "score": score, "text": body.strip()})
    return docs


def record_generator_context(state: dict[str, Any], messages: list[Any]) -> None:
    """Record the evidence blocks inside the prompt about to be sent to the LLM."""
    if not capturing():
        return
    documents: list[dict[str, Any]] = []
    tool_blocks: list[str] = []
    stub = False
    for message in messages:
        if getattr(message, "type", "") != "system":
            continue
        text = _text(message)
        if _DOC_MARK in text:
            documents.extend(split_documents(text))
        elif text.startswith(_TOOL_MARKS):
            tool_blocks.append(text)
        elif "PRIVATE REFERENCE" in text and "capabilities only" in text:
            stub = True
    note(
        generator_context={
            "documents": documents,
            "tool_blocks": tool_blocks,
            "capabilities_stub": stub,
            "prompt_chars": sum(len(_text(m)) for m in messages),
        },
        route={
            "route": state.get("understanding_route"),
            "execution_class": state.get("execution_class"),
            "data_need": state.get("data_need"),
            "runtime_mode": state.get("runtime_mode"),
            "runtime_mode_reason": state.get("runtime_mode_reason"),
            "tool": state.get("tool_name"),
            "tool_error": state.get("tool_error"),
            "tool_fallback": state.get("tool_fallback"),
            "sources_used": list(state.get("sources_used") or []),
        },
    )
