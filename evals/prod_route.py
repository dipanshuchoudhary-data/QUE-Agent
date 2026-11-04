"""What production does with a query before retrieval runs.

Mirrors the lexical part of ``decide_turn`` for a single, cold turn: classify,
attach the canonical intent, then decide whether QUE answers from a workflow card
(no retrieval), refuses, asks to clarify, or retrieves chunks. The semantic router
(network) and conversation resolution (needs history) are not applied.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProdRoute:
    served_by: str  # retrieval | workflow_card | refuse | clarify | tool | conversational
    execution_class: str
    canonical_intent: str | None
    route: str


def route_for(query: str) -> ProdRoute:
    from app.orchestration.intent_catalog import (  # noqa: PLC0415
        finalize_understanding,
        has_workflow_card,
    )
    from app.orchestration.understanding import (  # noqa: PLC0415
        classify_request,
        is_hard_out_of_scope,
    )

    text = (query or "").strip()
    if is_hard_out_of_scope(text):
        return ProdRoute("refuse", "out_of_scope", None, "refuse")
    u = finalize_understanding(classify_request(text), text)
    exec_class = str(u.execution_class)
    canonical = u.canonical_intent
    route = str(u.route)
    if route == "refuse" or exec_class == "out_of_scope":
        served = "refuse"
    elif route == "clarify":
        served = "clarify"
    elif route == "tool" or exec_class == "tool_required":
        served = "tool"
    elif exec_class == "conversational":
        served = "conversational"
    elif exec_class == "deterministic" and canonical and has_workflow_card(canonical):
        served = "workflow_card"
    else:
        served = "retrieval"
    return ProdRoute(served, exec_class, canonical, route)
