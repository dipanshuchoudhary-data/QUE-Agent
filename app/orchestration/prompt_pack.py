"""Composable system prompt parts — each route chooses what is included.

Never concatenate untrusted RAG/UI/tool text into CORE_POLICY.
"""

from __future__ import annotations

from langchain_core.messages import SystemMessage

from app.identity.persona import build_system_prompt
from app.orchestration.resolve import ResolvedRequest, build_turn_instruction

_ROUTE_POLICY: dict[str, str] = {
    "simple_knowledge": "Answer in a few sentences or short numbered steps. No filler.",
    "complex_knowledge": "Be precise. If a detail is missing from packs, say you are not sure.",
    "tool_required": "Prefer TOOL_RESULT facts. Do not invent live counts.",
}


def route_policy(execution_class: str | None) -> str | None:
    key = (execution_class or "").strip()
    return _ROUTE_POLICY.get(key)


def compose_leading_systems(
    *,
    resolution: ResolvedRequest,
    execution_class: str | None,
    route: str | None,
    pieces: set[str] | None = None,
) -> list[SystemMessage]:
    """CORE_POLICY + optional route line + TURN_STATE. No knowledge/UI here."""
    wanted = set(pieces or ())
    # Route policy covers how-to brevity; skip duplicate howto piece.
    if execution_class in {"simple_knowledge", "complex_knowledge", "deterministic"}:
        wanted.discard("howto")
    identity = build_system_prompt(wanted)
    messages = [SystemMessage(content=identity)]
    policy = route_policy(execution_class)
    if policy:
        messages.append(SystemMessage(content=policy))
    messages.append(SystemMessage(content=build_turn_instruction(resolution)))
    return messages
