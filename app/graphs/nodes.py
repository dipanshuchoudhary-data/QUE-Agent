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
from app.obs.evidence import note as note_evidence
from app.obs.evidence import record_generator_context
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
    tool_name = execution.selection.tool.name if execution.selection.tool else None
    sources = list(state.get("sources_used") or [])
    if "tools" not in sources:
        sources.append("tools")
    if tool_name:
        tag = f"tool:{tool_name}"
        if tag not in sources:
            sources.append(tag)
    if execution.error_code and "tool_error" not in sources:
        sources.append("tool_error")
    if execution.selection.needs_clarify and "tool_clarify" not in sources:
        sources.append("tool_clarify")

    out: dict = {
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
    base = {**dict(state), **out}

    if execution.error_code:
        add_span("tool_recovery", 0.0, extra={"live": _is_live_turn(state), "code": execution.error_code})
        if _is_live_turn(state):
            # Live data that could not be fetched: answer deterministically. No LLM
            # paraphrase and no static docs standing in for real-time numbers.
            return {
                **out,
                "messages": list(state.get("messages") or []),
                "direct_reply": tool_failure_reply(execution.error_code),
                "tool_fallback": "none",
            }
        # The ask did not need live data: the failed tool adds nothing, so answer
        # from product knowledge instead of surfacing a tool error.
        recovered = knowledge_node(base)
        recovered["sources_used"] = [*recovered["sources_used"], "tool_fallback:knowledge"]
        return {**out, **recovered, "tool_fallback": "knowledge"}

    messages = _insert_after_leading_systems(
        list(state.get("messages") or []),
        SystemMessage(content=execution.system_message),
    )
    base["messages"] = messages
    out["messages"] = messages
    if _wants_guidance_with_live(state) and not execution.selection.needs_clarify:
        out.update(knowledge_node(base))
    return out


def _is_live_turn(state: QueGraphState) -> bool:
    """Whether this turn asked for live Quizzer data (so docs can never substitute).

    Understanding says so explicitly for most live asks. A data-shaped ask that
    understanding left as "knowledge" but the tool selector claimed ("show me live
    exam health") is live too; only guidance-shaped asks are safe to answer from the KB.
    """
    from app.orchestration.understanding import is_guidance_ask

    if (state.get("understanding_route") or "").strip() == "tool" or (
        state.get("data_need") or ""
    ).strip() in {"live_tool", "insight_tool"}:
        return True
    text = str(state.get("raw_user_message") or state.get("resolved_query") or "")
    return not is_guidance_ask(text)


def _wants_guidance_with_live(state: QueGraphState) -> bool:
    """Live ask that is also a chained how-to: give the model KB next to TOOL_RESULT."""
    return _is_live_turn(state) and (state.get("understanding_complexity") or "") == "multi_step"


def tool_failure_reply(error_code: str | None) -> str:
    if error_code == "forbidden":
        return (
            "That live insight isn't available for your account role, so I can't pull it. "
            "Ask me how it works in Quizzer, or open the page directly."
        )
    return (
        "I couldn't reach your live Quizzer data just now, so I won't guess at numbers. "
        "Please try again in a moment, or open the relevant exam or page in Quizzer to see it directly."
    )


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
    out = {
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
    attempted = [ex for ex in result.executions if ex.selection.tool is not None]
    if attempted and all(ex.error_code for ex in attempted):
        # Every tool failed: no live evidence exists, so don't let the model improvise.
        return {
            **out,
            "messages": list(state.get("messages") or []),
            "direct_reply": tool_failure_reply(attempted[-1].error_code),
            "tool_fallback": "none",
        }
    if _wants_guidance_with_live(state) and result.successful_count:
        out.update(knowledge_node({**dict(state), **out}))
    return out


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
    note_evidence(
        retrieved={
            "query": retrieval_query,
            "mode": selection.mode,
            "no_answer": selection.no_answer,
            "chunk_ids": list(selection.chunk_ids),
            "scores": dict(selection.scores),
            "truncated": selection.truncated,
        }
    )

    update: dict = {
        "messages": messages,
        "sources_used": sources,
        "knowledge_packs": list(selection.pack_ids),
        "retrieval_query": retrieval_query or state.get("retrieval_query"),
    }
    if _is_unmatched_turn(state, selection):
        if get_settings().que_interpret_on_miss:
            update["knowledge_miss"] = True
        elif get_settings().que_noanswer_deterministic:
            _set_no_answer_reply(update, state, retrieval_query)
    return update


def _is_unmatched_turn(state: QueGraphState, selection) -> bool:
    """Retrieval found nothing and nothing else can ground the answer.

    Not for follow-ups (the thread may hold the answer), turns with UI context (the
    page/exam may be the referent), or tool-fallback turns.
    """
    if not selection.no_answer:
        return False
    if state.get("is_follow_up") or state.get("tool_fallback"):
        return False
    ui = state.get("ui_context") if isinstance(state.get("ui_context"), dict) else {}
    page = str(ui.get("current_page") or "").lower()
    if (page and page != "unknown") or ui.get("current_exam_id") or ui.get("current_entity_id"):
        return False
    return True


def _should_answer_no_match(state: QueGraphState, selection) -> bool:
    return bool(get_settings().que_noanswer_deterministic) and _is_unmatched_turn(state, selection)


def _set_no_answer_reply(update: dict, state: QueGraphState, retrieval_query: str) -> None:
    from app.orchestration.clarify import no_answer_reply

    update["direct_reply"] = no_answer_reply(str(state.get("raw_user_message") or retrieval_query))
    update["direct_model"] = "deterministic:no_answer"


async def resolve_knowledge_miss(state: QueGraphState) -> dict:
    """E2: interpret a missed ask once, then retry retrieval, ask, or decline honestly.

    Returns a state update (empty when the turn is not a pending miss). Called right
    before generation, in both the graph and the streaming path.
    """
    if not state.get("knowledge_miss") or (state.get("direct_reply") or "").strip():
        return {}
    from app.knowledge.interpret import interpret_query

    raw = str(state.get("raw_user_message") or state.get("retrieval_query") or "")
    out: dict = {"knowledge_miss": False}
    interp, cost = await interpret_query(raw, request_id=str(state.get("request_id") or ""), user_id=state.get("user_id"))
    outcome = "none"
    if interp is not None and interp.ambiguous:
        out["direct_reply"] = interp.clarify
        out["direct_model"] = "interpret:clarify"
        outcome = "clarify"
    elif interp is not None and interp.english and interp.english.casefold() != raw.casefold():
        from app.knowledge.assemble import _NO_ANSWER_INSTRUCTION  # noqa: PLC0415

        selection = select_knowledge(
            list(state.get("input_messages") or []),
            query=interp.english,
            use_cache=True,
            canonical_intent=state.get("canonical_intent"),
            execution_class=state.get("execution_class"),
        )
        if not selection.no_answer and selection.content.strip():
            kept = [
                m for m in list(state.get("messages") or [])
                if not (isinstance(m, SystemMessage) and _NO_ANSWER_INSTRUCTION in str(m.content))
            ]
            out["messages"] = _insert_after_leading_systems(kept, SystemMessage(content=selection.content))
            sources = [s for s in list(state.get("sources_used") or []) if s != "knowledge_no_answer"]
            sources.append("knowledge:interpreted")
            out["sources_used"] = sources
            out["knowledge_packs"] = list(selection.pack_ids)
            out["retrieval_query"] = interp.english
            note_evidence(
                retrieved={
                    "query": interp.english,
                    "mode": selection.mode,
                    "no_answer": False,
                    "chunk_ids": list(selection.chunk_ids),
                    "scores": dict(selection.scores),
                    "truncated": selection.truncated,
                }
            )
            outcome = "retry_hit"
        else:
            outcome = "retry_miss"
    if "direct_reply" not in out and outcome != "retry_hit" and get_settings().que_noanswer_deterministic:
        _set_no_answer_reply(out, state, raw)
    note_evidence(interpret={**cost, "outcome": outcome})
    return out


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
    resolved = await resolve_knowledge_miss(state)
    if resolved:
        state = {**state, **resolved}
    carry = {k: resolved[k] for k in ("knowledge_packs", "retrieval_query") if k in resolved}
    messages = _refresh_identity_pieces(state, list(state.get("messages") or []))
    if not messages:
        raise LLMError("No messages prepared for generation")

    direct = (state.get("direct_reply") or "").strip()
    if direct:
        record_generator_context(state, [])
        note_evidence(llm_called=False)
        sources = list(state.get("sources_used") or [])
        dialog = append_assistant(
            list(state.get("dialog") or []), direct, max_turns=max_dialog_turns()
        )
        return {
            **carry,
            "messages": [*messages, AIMessage(content=direct)],
            "dialog": dialog,
            "sources_used": sources,
            "model_name": state.get("direct_model") or "deterministic:tool_unavailable",
            "memory_turns": len(dialog),
            "topic": state.get("topic"),
            "current_task": state.get("resolved_query") or state.get("current_task"),
            "intent": state.get("intent"),
            "response_mode": state.get("response_mode"),
            "resolved_query": state.get("resolved_query"),
            "is_follow_up": state.get("is_follow_up"),
        }

    record_generator_context(state, messages)
    note_evidence(llm_called=True)
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
                **carry,
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
        **carry,
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
