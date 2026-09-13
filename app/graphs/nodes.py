"""QUE agent graph nodes — one responsibility each for future expansion."""

from __future__ import annotations

import re
import time
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.llm import LLMError, ainvoke_chat, last_llm_usage
from app.graphs.memory import append_assistant, max_dialog_turns, merge_dialog_with_incoming
from app.graphs.state import QueGraphState
from app.guardrails.output import apply_output_guardrail, grounding_from_messages
from app.identity import (
    IDENTITY_VERSION,
    build_system_prompt,
    pieces_for_prepare,
    pieces_from_messages,
)
from app.knowledge import select_knowledge
from app.obs.budget import CAPACITY_REPLY, allow_llm_call, note_llm_usage
from app.obs.context import add_span, current_trace
from app.obs.cost import usd_for_usage
from app.orchestration.history import sanitize_history
from app.orchestration.prompt_pack import compose_leading_systems
from app.orchestration.resolve import ResolvedRequest, resolve_request
from app.orchestration.ui_context import format_ui_context_system_message
from app.orchestration.understanding import OUT_OF_SCOPE_REFUSAL
from app.schemas.chat import ChatMessage
from app.tools.executor import execute_selected_tool


def _to_schema_messages(raw: list[dict[str, str]]) -> list[ChatMessage]:
    out: list[ChatMessage] = []
    for item in raw:
        role = item.get("role", "")
        content = item.get("content", "")
        if role not in {"system", "user", "assistant"}:
            continue
        out.append(ChatMessage(role=role, content=content))  # type: ignore[arg-type]
    return out


def _dialog_to_schema(dialog: list[BaseMessage]) -> list[ChatMessage]:
    out: list[ChatMessage] = []
    for message in dialog:
        content = message.content if isinstance(message.content, str) else str(message.content or "")
        if not content.strip():
            continue
        if isinstance(message, HumanMessage):
            out.append(ChatMessage(role="user", content=content))
        elif isinstance(message, AIMessage):
            out.append(ChatMessage(role="assistant", content=content))
    return out


def _resolution_from_state(state: QueGraphState, incoming: list[ChatMessage]) -> ResolvedRequest:
    latest = next((m.content.strip() for m in reversed(incoming) if m.role == "user"), "")
    raw_in_state = (state.get("raw_user_message") or "").strip()
    existing = (state.get("resolved_query") or "").strip()
    # Trust pre-seeded resolution only when it matches this turn's raw utterance
    # (avoids reusing a prior checkpoint's resolved_query).
    if existing and raw_in_state and latest and raw_in_state == latest:
        return ResolvedRequest(
            raw_message=raw_in_state,
            resolved_query=existing,
            is_follow_up=bool(state.get("is_follow_up")),
            topic=state.get("topic"),
            intent=state.get("intent") or "general_product_question",  # type: ignore[arg-type]
            response_mode=state.get("response_mode") or "normal",  # type: ignore[arg-type]
            reasons=("from_state",),
        )
    return resolve_request(
        incoming,
        prior_topic=state.get("topic")
        or state.get("previous_intent")
        or state.get("canonical_intent"),
        prior_task=state.get("current_task"),
        previous_intent=state.get("previous_intent") or state.get("canonical_intent"),
    )


def prepare_node(state: QueGraphState) -> dict:
    """Merge short-term dialog memory, resolve follow-ups, inject QUE identity."""
    incoming = _to_schema_messages(state.get("input_messages") or [])
    existing_dialog = list(state.get("dialog") or [])
    dialog = merge_dialog_with_incoming(
        existing_dialog,
        incoming,
        max_turns=max_dialog_turns(),
    )

    # Prefer checkpoint dialog for resolution when client history is thin.
    resolve_msgs = _dialog_to_schema(dialog) if dialog else incoming
    resolution = _resolution_from_state(state, resolve_msgs)

    history = sanitize_history(_dialog_to_schema(dialog)) if dialog else sanitize_history(incoming)
    # Standalone asks: keep a tighter recent window (follow-ups need more).
    if not resolution.is_follow_up:
        history = sanitize_history(history, max_messages=3, max_chars=1_500)
    else:
        history = sanitize_history(history, max_messages=6, max_chars=3_000)

    route = (state.get("understanding_route") or "").strip() or None
    pieces = pieces_for_prepare(
        intent=resolution.intent,
        route=route,
        response_mode=resolution.response_mode,
    )
    leading = compose_leading_systems(
        resolution=resolution,
        execution_class=state.get("execution_class"),
        route=route,
        pieces=pieces,
    )

    resolved = (resolution.resolved_query or "").strip()
    raw = (resolution.raw_message or "").strip()
    prompt: list[BaseMessage] = list(leading)
    for index, message in enumerate(history):
        # Drop a duplicate of the latest ask when older turns remain.
        if (
            index == len(history) - 1
            and message.role == "user"
            and message.content.strip() in {resolved, raw}
            and any(m.role == "user" for m in history[:-1])
        ):
            continue
        if message.role == "user":
            prompt.append(HumanMessage(content=message.content))
        else:
            prompt.append(AIMessage(content=message.content))

    sources = list(state.get("sources_used") or [])
    if "identity" not in sources:
        sources.append("identity")
    if existing_dialog and "memory" not in sources:
        sources.append("memory")
    if resolution.is_follow_up and "resolve" not in sources:
        sources.append("resolve")

    return {
        "dialog": dialog,
        "messages": prompt,
        "sources_used": sources,
        "identity_version": IDENTITY_VERSION,
        "memory_turns": len(dialog),
        "raw_user_message": resolution.raw_message,
        "resolved_query": resolution.resolved_query,
        "is_follow_up": resolution.is_follow_up,
        "topic": resolution.topic,
        "current_task": resolution.resolved_query,
        "intent": resolution.intent,
        "response_mode": resolution.response_mode,
        "retrieval_query": resolution.resolved_query,
    }


def _insert_after_leading_systems(messages: list[BaseMessage], extra: SystemMessage) -> list[BaseMessage]:
    insert_at = 0
    while insert_at < len(messages) and isinstance(messages[insert_at], SystemMessage):
        insert_at += 1
    if insert_at == 0:
        insert_at = 1 if messages and isinstance(messages[0], SystemMessage) else 0
    return [*messages[:insert_at], extra, *messages[insert_at:]]


def context_node(state: QueGraphState) -> dict:
    """Inject structured Quizzer UI context as a labeled system message.

    Phase 3: page/entity/role are never concatenated into the user message.
    Missing context is a no-op (backward compatible). Meta/chitchat skips UI.
    """
    from app.orchestration.runtime_mode import decide_runtime_mode_from_state
    from app.orchestration.ui_context import format_ui_context_system_message, ui_context_needed

    raw = state.get("ui_context")
    messages = list(state.get("messages") or [])
    sources = list(state.get("sources_used") or [])
    ui: dict | None = None

    if isinstance(raw, dict) and raw:
        ui = {k: v for k, v in raw.items() if v is not None and v != ""}
        if ui and ui_context_needed(
            ui,
            route=state.get("understanding_route"),
            intent=state.get("intent"),
            query=state.get("resolved_query") or state.get("raw_user_message"),
            execution_class=state.get("execution_class"),
        ):
            messages = _insert_after_leading_systems(
                messages,
                SystemMessage(content=format_ui_context_system_message(ui)),
            )
            if "ui_context" not in sources:
                sources.append("ui_context")
            page = str(ui.get("current_page") or "unknown")
            page_tag = f"ui_context:{page}"
            if page_tag not in sources:
                sources.append(page_tag)

    merged = {**dict(state), "messages": messages, "ui_context": ui or state.get("ui_context")}
    mode, mode_reason, _sel = decide_runtime_mode_from_state(merged)
    if "runtime" not in sources:
        sources.append("runtime")
    mode_tag = f"runtime:{mode}"
    if mode_tag not in sources:
        sources.append(mode_tag)

    out: dict = {
        "messages": messages,
        "sources_used": sources,
        "runtime_mode": mode,
        "runtime_mode_reason": mode_reason,
    }
    if ui:
        out["ui_context"] = ui
    return out


async def tools_node(state: QueGraphState) -> dict:
    """Run one insight tool workflow and inject TOOL_RESULT / clarify / error."""
    query = (
        state.get("retrieval_query")
        or state.get("resolved_query")
        or state.get("raw_user_message")
        or ""
    )
    raw = state.get("raw_user_message") or ""
    ui = state.get("ui_context") if isinstance(state.get("ui_context"), dict) else None
    request_id = str(state.get("request_id") or "").strip() or uuid.uuid4().hex
    started = time.perf_counter()
    execution = await execute_selected_tool(
        query=str(query),
        raw_query=str(raw) if raw else None,
        ui_context=ui,
        user_id=state.get("user_id"),
        request_id=request_id,
        route=state.get("understanding_route"),
        conversation_id=state.get("conversation_id"),
    )
    add_span(
        "tool",
        execution.latency_ms or (time.perf_counter() - started) * 1000.0,
        ok=not execution.error_code,
        extra={"name": execution.selection.tool.name if execution.selection.tool else None},
    )
    messages = _insert_after_leading_systems(
        list(state.get("messages") or []),
        SystemMessage(content=execution.system_message),
    )
    sources = list(state.get("sources_used") or [])
    if "tools" not in sources:
        sources.append("tools")
    tool_name = execution.selection.tool.name if execution.selection.tool else None
    if tool_name:
        tag = f"tool:{tool_name}"
        if tag not in sources:
            sources.append(tag)
    if execution.error_code and "tool_error" not in sources:
        sources.append("tool_error")
    if execution.selection.needs_clarify and "tool_clarify" not in sources:
        sources.append("tool_clarify")

    return {
        "messages": messages,
        "sources_used": sources,
        "tool_name": tool_name,
        "tool_args": dict(execution.selection.args),
        "tool_error": execution.error_code,
        "tool_latency_ms": execution.latency_ms,
        "runtime_mode": state.get("runtime_mode") or "workflow",
        "tools_used": [tool_name] if tool_name else [],
        "agent_steps": 1 if tool_name else 0,
        "agent_termination_reason": "converged",
    }


async def agent_node(state: QueGraphState) -> dict:
    """Bounded multi-tool loop; injects every TOOL_RESULT then generate."""
    from app.orchestration.agent_loop import run_agent_loop

    query = (
        state.get("retrieval_query")
        or state.get("resolved_query")
        or state.get("raw_user_message")
        or ""
    )
    raw = state.get("raw_user_message") or ""
    ui = state.get("ui_context") if isinstance(state.get("ui_context"), dict) else None
    request_id = str(state.get("request_id") or "").strip() or uuid.uuid4().hex
    result = await run_agent_loop(
        query=str(query),
        raw_query=str(raw) if raw else None,
        ui_context=ui,
        user_id=state.get("user_id"),
        route=state.get("understanding_route"),
        request_id=request_id,
    )
    return apply_agent_loop_result(state, result)


def apply_agent_loop_result(state: QueGraphState, result: object) -> dict:
    """Merge an AgentLoopResult into graph state (shared by graph + SSE)."""
    from app.orchestration.agent_loop import PARTIAL_REASONS, AgentLoopResult

    assert isinstance(result, AgentLoopResult)
    messages = list(state.get("messages") or [])
    for block in result.system_messages:
        if block.strip():
            messages = _insert_after_leading_systems(messages, SystemMessage(content=block))

    sources = list(state.get("sources_used") or [])
    if "tools" not in sources:
        sources.append("tools")
    if "agent" not in sources:
        sources.append("agent")
    for name in result.tools_used:
        tag = f"tool:{name}"
        if tag not in sources:
            sources.append(tag)
    if result.termination_reason in PARTIAL_REASONS and "agent_partial" not in sources:
        sources.append("agent_partial")
    term_tag = f"agent_term:{result.termination_reason}"
    if term_tag not in sources:
        sources.append(term_tag)
    if any(ex.error_code for ex in result.executions) and "tool_error" not in sources:
        sources.append("tool_error")
    if result.termination_reason == "clarify" and "tool_clarify" not in sources:
        sources.append("tool_clarify")

    last = result.executions[-1] if result.executions else None
    for step in result.steps:
        add_span(
            "tool",
            step.elapsed_ms,
            ok=step.ok,
            extra={"name": step.tool_name},
        )
    return {
        "messages": messages,
        "sources_used": sources,
        "runtime_mode": "agent",
        "agent_steps": len(result.steps),
        "agent_termination_reason": result.termination_reason,
        "tools_used": list(result.tools_used),
        "tool_name": result.tools_used[-1] if result.tools_used else None,
        "tool_args": dict(last.selection.args) if last else {},
        "tool_error": last.error_code if last else None,
        "tool_latency_ms": sum(s.elapsed_ms for s in result.steps),
    }


# Short stub when meta/capabilities somehow reach knowledge without canned.
_CAPABILITIES_STUB = (
    "PRIVATE REFERENCE — capabilities only. QUE explains Quizzer how-tos; "
    "cannot change settings or invent live numbers. 2–4 short sentences; **bold** UI labels."
)


def _skip_full_knowledge(state: QueGraphState) -> bool:
    """Meta/chitchat must not pay CORE + RAG cost."""
    intent = (state.get("intent") or "").strip()
    route = (state.get("understanding_route") or "").strip()
    if intent in {"chitchat", "meta"}:
        return True
    if route == "canned_eligible":
        return True
    if (state.get("execution_class") or "").strip() == "deterministic":
        return True
    return False


def knowledge_node(state: QueGraphState) -> dict:
    """Inject selected product-knowledge packs after identity, before generate.

    Phase 2: ``select_knowledge`` prefers dense Chroma hits when an index exists;
    otherwise keyword packs. Mode / no-answer are recorded in ``sources_used``.
    Meta/capabilities turns inject a tiny stub instead of CORE+RAG.
    """
    from app.orchestration.cache_policy import allow_retrieval_from_fields

    messages = list(state.get("messages") or [])
    sources = list(state.get("sources_used") or [])

    if _skip_full_knowledge(state):
        messages = _insert_after_leading_systems(
            messages,
            SystemMessage(content=_CAPABILITIES_STUB),
        )
        if "knowledge_stub:capabilities" not in sources:
            sources.append("knowledge_stub:capabilities")
        return {
            "messages": messages,
            "sources_used": sources,
            "knowledge_packs": [],
            "retrieval_query": state.get("retrieval_query"),
        }

    retrieval_query = (state.get("retrieval_query") or state.get("resolved_query") or "").strip()
    selection = select_knowledge(
        list(state.get("input_messages") or []),
        query=retrieval_query or None,
        use_cache=allow_retrieval_from_fields(
            freshness=state.get("understanding_freshness"),
            route=state.get("understanding_route"),
            data_need=state.get("data_need"),
        ),
        canonical_intent=state.get("canonical_intent"),
        execution_class=state.get("execution_class"),
    )
    if selection.content.strip():
        # Place knowledge after identity / turn / UI-context system messages.
        messages = _insert_after_leading_systems(
            messages,
            SystemMessage(content=selection.content),
        )

    if selection.pack_ids and "knowledge" not in sources:
        sources.append("knowledge")
    mode_tag = f"knowledge_mode:{selection.mode}"
    if mode_tag not in sources:
        sources.append(mode_tag)
    if selection.no_answer and "knowledge_no_answer" not in sources:
        sources.append("knowledge_no_answer")
    for pack_id in selection.pack_ids:
        tag = f"knowledge:{pack_id}"
        if tag not in sources:
            sources.append(tag)

    return {
        "messages": messages,
        "sources_used": sources,
        "knowledge_packs": list(selection.pack_ids),
        "retrieval_query": retrieval_query or state.get("retrieval_query"),
    }


def _validate_answer(content: str, *, response_mode: str | None, in_scope: bool) -> str:
    text = (content or "").strip()
    if not text:
        raise LLMError("LLM returned an empty response")
    if in_scope and OUT_OF_SCOPE_REFUSAL[:40] in text:
        return (
            "I can continue on that Quizzer topic. "
            "Ask me to explain step by step, give an example, or cover a related setting."
        )
    if response_mode == "step_by_step":
        has_steps = bool(
            re.search(r"(?m)^\s*1[\).\]]\s+\S", text) or re.search(r"\b1[\).\]]\s+\S", text)
        )
        if not has_steps and len(text) < 120:
            pass
    return text


def _apply_output_guard_to_state(state: QueGraphState, content: str) -> tuple[str, str | None]:
    ui = state.get("ui_context") if isinstance(state.get("ui_context"), dict) else {}
    blob = grounding_from_messages(state.get("messages") or [])
    safe, hit = apply_output_guardrail(
        content,
        user_text=str(state.get("raw_user_message") or ""),
        role=(ui or {}).get("user_role"),
        tool_blob=blob or None,
        ui_blob=blob or None,
        settings=get_settings(),
    )
    if hit is None:
        return content, None
    return safe, "guardrail:output"


def _refresh_identity_pieces(state: QueGraphState, messages: list[BaseMessage]) -> list[BaseMessage]:
    """Rebuild the first system message with pieces that actually apply this turn."""
    pieces = pieces_for_prepare(
        intent=state.get("intent"),
        route=state.get("understanding_route"),
        response_mode=state.get("response_mode"),
    )
    pieces |= pieces_from_messages(messages)
    identity = build_system_prompt(pieces)
    if messages and isinstance(messages[0], SystemMessage):
        return [SystemMessage(content=identity), *messages[1:]]
    return [SystemMessage(content=identity), *messages]


async def generate_node(state: QueGraphState) -> dict:
    """Call the chat model with the prepared message list; append reply to dialog."""
    messages = _refresh_identity_pieces(state, list(state.get("messages") or []))
    if not messages:
        raise LLMError("No messages prepared for generation")

    request_id = str(state.get("request_id") or "").strip()
    cfg = get_settings()
    if request_id:
        ok, deny = allow_llm_call(request_id, messages=messages, settings=cfg)
        if not ok:
            content = CAPACITY_REPLY
            sources = list(state.get("sources_used") or [])
            dialog = append_assistant(
                list(state.get("dialog") or []),
                content,
                max_turns=max_dialog_turns(),
            )
            return {
                "messages": [*messages, AIMessage(content=content)],
                "dialog": dialog,
                "sources_used": sources,
                "model_name": deny or "budget:turn",
                "memory_turns": len(dialog),
                "topic": state.get("topic"),
                "current_task": state.get("resolved_query") or state.get("current_task"),
                "intent": state.get("intent"),
                "response_mode": state.get("response_mode"),
                "resolved_query": state.get("resolved_query"),
                "is_follow_up": state.get("is_follow_up"),
            }

    t_llm = time.perf_counter()
    input_chars = sum(
        len(m.content if isinstance(m.content, str) else str(m.content or ""))
        for m in messages
    )
    try:
        response, lane = await ainvoke_chat(
            messages,
            complexity=state.get("understanding_complexity"),
            runtime_mode=state.get("runtime_mode"),
            intent=state.get("intent"),
            execution_class=state.get("execution_class"),
        )
    except LLMError:
        add_span(
            "llm",
            (time.perf_counter() - t_llm) * 1000.0,
            ok=False,
            extra={
                "route": state.get("understanding_route"),
                "runtime_mode": state.get("runtime_mode"),
                "input_chars": input_chars,
                "knowledge_used": bool(state.get("knowledge_packs")),
                "ui_injected": "ui_context" in (state.get("sources_used") or []),
            },
        )
        raise
    except Exception as exc:  # noqa: BLE001 — normalize provider errors
        add_span("llm", (time.perf_counter() - t_llm) * 1000.0, ok=False)
        raise LLMError(str(exc)) from exc

    llm_ms = (time.perf_counter() - t_llm) * 1000.0
    add_span(
        "llm",
        llm_ms,
            extra={
                "model": lane.model,
                "key_index": lane.key_index,
                "route": state.get("understanding_route"),
                "execution_class": state.get("execution_class"),
                "canonical_intent": state.get("canonical_intent"),
                "runtime_mode": state.get("runtime_mode"),
                "input_chars": input_chars,
                "knowledge_used": bool(state.get("knowledge_packs")),
                "ui_injected": "ui_context" in (state.get("sources_used") or []),
                "fallback": lane.key_index > 0 or ":free" in lane.model.casefold(),
            },
    )
    usage = last_llm_usage()
    usd = usd_for_usage(usage)
    if request_id:
        note_llm_usage(
            request_id,
            tokens=usage.total,
            usd=usd,
            user_id=state.get("user_id"),
        )
    trace = current_trace()
    if trace is not None:
        trace.model = lane.model
        if usage.total:
            trace.prompt_tokens = usage.prompt_tokens
            trace.completion_tokens = usage.completion_tokens
            trace.reasoning_tokens = usage.reasoning_tokens
            if usd is not None:
                trace.cost_usd = usd
            elif ":free" in lane.model.casefold():
                trace.cost_usd = 0.0

    content = response.content if isinstance(response.content, str) else str(response.content or "")
    content = _validate_answer(
        content,
        response_mode=state.get("response_mode"),
        in_scope=True,
    )
    content, guardrail_model = _apply_output_guard_to_state(state, content)
    if guardrail_model:
        add_span("guardrail", 0.0, extra={"layer": "output"})
    add_span("generate", llm_ms)

    sources = list(state.get("sources_used") or [])
    if "llm" not in sources:
        sources.append("llm")

    model_name = guardrail_model or lane.model
    dialog = append_assistant(
        list(state.get("dialog") or []),
        content,
        max_turns=max_dialog_turns(),
    )
    return {
        "messages": [*messages, AIMessage(content=content)],
        "dialog": dialog,
        "sources_used": sources,
        "model_name": model_name,
        "memory_turns": len(dialog),
        "topic": state.get("topic"),
        "current_task": state.get("resolved_query") or state.get("current_task"),
        "intent": state.get("intent"),
        "response_mode": state.get("response_mode"),
        "resolved_query": state.get("resolved_query"),
        "is_follow_up": state.get("is_follow_up"),
    }
