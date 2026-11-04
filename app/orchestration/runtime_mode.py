"""Explicit workflow-vs-agent routing (Phase 7).

Most live-data turns stay on the single-tool workflow. Agent mode is opt-in
by ask shape (multi-step / multi-intent), never the default for every tool route.
"""

from __future__ import annotations

from typing import Any, Literal

from app.core.config import Settings, get_settings
from app.orchestration.understanding import is_guidance_ask, is_multi_step_ask
from app.tools.select import ToolSelection, select_tool_prefer_raw

RuntimeMode = Literal["knowledge", "workflow", "agent"]


def looks_like_multi_tool_ask(text: str) -> bool:
    """Query shape that can justify more than one insight tool this turn."""
    return is_multi_step_ask(text)


def decide_runtime_mode(
    *,
    query: str,
    raw_query: str | None = None,
    ui_context: dict[str, Any] | None = None,
    route: str | None = None,
    data_need: str | None = None,
    complexity: str | None = None,
    tools_enabled: bool | None = None,
    settings: Settings | None = None,
) -> tuple[RuntimeMode, str, ToolSelection | None]:
    """Return (mode, reason, first_selection).

    knowledge — tools off, no live need, or policy deny
    workflow  — live/insight with one clear tool (Phase 4 path)
    agent     — tools on + live need + multi-step/multi-intent + a permitted tool
    """
    cfg = settings or get_settings()
    enabled = cfg.que_tools_enabled if tools_enabled is None else tools_enabled
    q = (query or "").strip()
    raw = (raw_query or "").strip()
    live = (route or "").strip() == "tool" or (data_need or "").strip() in {
        "live_tool",
        "insight_tool",
    }
    want_agent = (complexity or "") == "multi_step" or looks_like_multi_tool_ask(raw or q)

    if not enabled:
        return "knowledge", "tools_disabled", None

    # The tool selector matches topic words, so it cannot tell "Where is Monitoring
    # in the sidebar?" (guidance) from "Who is in Monitoring right now?" (live data).
    # The *form* of the ask can: how/where/what-does questions want a procedure from
    # product knowledge, not a tool call. Only chained asks (how + live) keep tools.
    if not (live and want_agent) and is_guidance_ask(raw or q):
        return "knowledge", "guidance_ask", None

    selection = select_tool_prefer_raw(
        raw_query=raw or None,
        resolved_query=q,
        ui_context=ui_context,
        route=route,
    )
    if selection.reason.startswith("policy_denied"):
        return "knowledge", "policy_denied", selection

    # Write tools always take the single-tool workflow path — never chained in
    # the bounded agent loop — so each mutation gets its own confirmation turn.
    if selection.tool is not None and selection.tool.risk_tier != "read" and not selection.needs_clarify:
        return "workflow", "write_tool_single_step", selection

    if want_agent and live and selection.tool is not None and not selection.needs_clarify:
        return "agent", "multi_step", selection

    if selection.tool is not None and not selection.needs_clarify:
        return "workflow", "single_tool", selection
    if live:
        return "workflow", "live_clarify", selection
    return "knowledge", "no_live_need", selection


def decide_runtime_mode_from_state(
    state: dict[str, Any],
    *,
    settings: Settings | None = None,
) -> tuple[RuntimeMode, str, ToolSelection | None]:
    ui = state.get("ui_context") if isinstance(state.get("ui_context"), dict) else None
    return decide_runtime_mode(
        query=str(state.get("retrieval_query") or state.get("resolved_query") or ""),
        raw_query=str(state.get("raw_user_message") or "") or None,
        ui_context=ui,
        route=str(state.get("understanding_route") or "") or None,
        data_need=str(state.get("data_need") or "") or None,
        complexity=str(state.get("understanding_complexity") or "") or None,
        settings=settings,
    )
