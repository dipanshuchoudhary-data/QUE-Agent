"""HTTP-facing orchestration — runs the LangGraph agent for each turn.

The graph owns agent structure. This module maps ChatRequest ↔ graph I/O,
runs Request Understanding (Phase 1), and exposes complete / stream helpers.
"""

from __future__ import annotations

import dataclasses
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import structlog
from langchain_core.messages import AIMessage, BaseMessage

from langsmith.run_helpers import trace as langsmith_trace

from app.core.config import Settings, get_settings
from app.core.config import get_settings as _get_settings_for_tools
from app.core.llm import LLMError, astream_chat, last_llm_usage
from app.core.que_cache import (
    cache_key,
    get_cached_llm_reply,
    set_cached_llm_reply,
)
from app.evals.online import maybe_log_online_turn
from app.graphs.memory import (
    append_assistant,
    make_thread_id,
    max_dialog_turns,
    memory_enabled,
    merge_dialog_with_incoming,
    runnable_config,
)
from app.graphs.nodes import (
    agent_node,
    apply_agent_loop_result,
    context_node,
    knowledge_node,
    prepare_node,
    tools_node,
)
from app.graphs.que_graph import get_que_graph
from app.graphs.state import QueGraphState
from app.guardrails import INPUT_REFUSAL
from app.guardrails.input import scan_user_text
from app.guardrails.output import apply_output_guardrail, grounding_from_messages
from app.identity import identity_metadata
from app.obs.budget import (
    CAPACITY_REPLY,
    allow_llm_call,
    finish_turn_budget,
    note_llm_usage,
    start_turn_budget,
    user_hour_exceeded,
)
from app.obs.context import bind_trace, clear_trace
from app.obs.cost import usd_for_usage
from app.obs.metrics import record_turn
from app.obs.trace import TurnTrace, hash_user_id, new_trace
from app.orchestration.cache_policy import allow_llm_reply_cache, allow_retrieval_cache
from app.orchestration.canned import (
    latest_user_text,
    match_canned_reply,
    pick_canned_intent,
)
from app.orchestration.history import sanitize_history
from app.orchestration.pending_actions import clear_pending, get_pending, is_affirmative_reply, is_negative_reply
from app.orchestration.resolve import (
    ResolvedRequest,
    is_conversation_meta,
    resolve_request,
)
from app.orchestration.ui_context import live_data_reply_with_context
from app.orchestration.understanding import (
    OUT_OF_SCOPE_REFUSAL,
    RequestUnderstanding,
    _has_quizzer_hint,
    classify_request,
    is_hard_out_of_scope,
)
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

logger = structlog.get_logger(__name__)


def _maybe_online(
    *,
    decision: TurnDecision,
    request: ChatRequest,
    model: str | None = None,
    cache_hit: bool = False,
    cache_layer: str | None = None,
    guardrail: str | None = None,
    settings: Settings | None = None,
) -> None:
    g = guardrail or decision.guardrail
    if not g and (model or "").startswith("guardrail:"):
        g = (model or "").split(":", 1)[-1]
    maybe_log_online_turn(
        request_id=decision.request_id,
        user_id=request.user_id,
        query=decision.resolution.resolved_query or latest_user_text(request.messages),
        route=decision.understanding.route,
        freshness=decision.understanding.freshness,
        cache_hit=cache_hit,
        cache_layer=cache_layer,
        guardrail=g,
        model=model,
        settings=settings,
    )


def _begin_obs(decision: TurnDecision, request: ChatRequest) -> TurnTrace:
    start_turn_budget(request_id=decision.request_id, user_id=request.user_id)
    trace = new_trace(
        request_id=decision.request_id,
        user_id=request.user_id,
        route=decision.understanding.route,
        freshness=decision.understanding.freshness,
    )
    trace.execution_class = getattr(decision.understanding, "execution_class", None)
    trace.canonical_intent = getattr(decision.understanding, "canonical_intent", None)
    bind_trace(trace)
    return trace


def _end_obs(
    trace: TurnTrace,
    *,
    started: float,
    error: bool = False,
    model: str | None = None,
    settings: Settings | None = None,
) -> None:
    trace.error = error
    if model:
        trace.model = str(model)
    usage = last_llm_usage()
    if usage.total and not trace.prompt_tokens and not trace.completion_tokens:
        trace.prompt_tokens = usage.prompt_tokens
        trace.completion_tokens = usage.completion_tokens
        trace.reasoning_tokens = usage.reasoning_tokens
        usd = usd_for_usage(usage)
        if usd is not None:
            trace.cost_usd = usd
        elif ":free" in (trace.model or "").casefold():
            trace.cost_usd = 0.0
    elif usage.reasoning_tokens and not trace.reasoning_tokens:
        trace.reasoning_tokens = usage.reasoning_tokens
    if trace.cost_usd is None and not trace.prompt_tokens:
        trace.cost_usd = 0.0
    record_turn(trace, latency_ms=(time.perf_counter() - started) * 1000.0, settings=settings)
    finish_turn_budget(trace.request_id)
    clear_trace()


def _capacity_response(
    request: ChatRequest,
    decision: TurnDecision,
    *,
    model: str,
) -> ChatResponse:
    return ChatResponse(
        message=ChatMessage(role="assistant", content=CAPACITY_REPLY),
        conversation_id=request.conversation_id,
        model=model,
    )

def _langsmith_turn(decision: TurnDecision):
    """Parent LangSmith run so a turn is visible as que.turn + route tag."""
    from app.orchestration.intent_catalog import smith_route_tag

    tag = smith_route_tag(
        getattr(decision.understanding, "execution_class", None),
        decision.understanding.route,
    )
    return langsmith_trace(
        name="que.turn",
        run_type="chain",
        tags=["que-agent", f"que.route.{tag}"],
        metadata={
            "route": decision.understanding.route,
            "execution_class": getattr(decision.understanding, "execution_class", None),
            "canonical_intent": getattr(decision.understanding, "canonical_intent", None),
            "confidence": getattr(decision.understanding, "confidence", None),
            "runtime_mode": None,
        },
        inputs={"route": decision.understanding.route},
    )


TOOL_NOT_READY_REPLY = (
    "I can't read live Quizzer account or exam numbers yet. "
    "Open the relevant Dashboard or Results view in the app for current figures, "
    "or ask how to find that screen."
)

CLARIFY_REPLY = "Could you ask that as a Quizzer question — for example how to create, publish, or monitor an exam?"


def _prepare_with_knowledge(
    request: ChatRequest,
    *,
    dialog: list | None = None,
    resolution: ResolvedRequest | None = None,
    understanding: RequestUnderstanding | None = None,
) -> dict:
    """Sync prepare → context → knowledge (tests / non-tool path)."""
    initial = _request_to_input(request, resolution=resolution, understanding=understanding)
    if dialog is not None:
        initial["dialog"] = dialog
    state = prepare_node(initial)
    state = {**initial, **state}
    state = {**state, **context_node(state)}
    return knowledge_node(state)


async def _prepare_turn_async(
    request: ChatRequest,
    *,
    dialog: list | None = None,
    resolution: ResolvedRequest | None = None,
    understanding: RequestUnderstanding | None = None,
) -> dict:
    initial = _request_to_input(request, resolution=resolution, understanding=understanding)
    if dialog is not None:
        initial["dialog"] = dialog
    state = prepare_node(initial)
    state = {**initial, **state}
    state = {**state, **context_node(state)}
    mode = (state.get("runtime_mode") or "knowledge").strip()
    if mode == "agent":
        return {**state, **(await agent_node(state))}
    if mode == "workflow":
        state = {**state, **(await tools_node(state))}
        return state
    return knowledge_node(state)


def _tools_route_decision(state: dict) -> tuple[bool, object | None]:
    """Return (use_tools, ToolSelection|None) without executing."""
    from app.orchestration.runtime_mode import decide_runtime_mode_from_state

    mode, _reason, sel = decide_runtime_mode_from_state(state)
    if mode in {"workflow", "agent"}:
        return True, sel
    return False, sel


def _thread_config(request: ChatRequest) -> tuple[str | None, dict | None]:
    if not memory_enabled():
        return None, None
    thread_id = make_thread_id(request.conversation_id, request.user_id)
    if not thread_id:
        # Checkpointer requires a thread_id; one-shot turns get an ephemeral id.
        thread_id = f"ephemeral:{uuid.uuid4().hex}"
    return thread_id, runnable_config(thread_id)


async def _persist_dialog_turn(request: ChatRequest, assistant_text: str) -> int:
    """Write user+assistant into short-term memory (early replies / stream path)."""
    thread_id, config = _thread_config(request)
    if not config:
        return 0
    graph = get_que_graph()
    try:
        snap = await graph.aget_state(config)
        existing = list((snap.values or {}).get("dialog") or [])
    except Exception:  # noqa: BLE001
        existing = []
    dialog = merge_dialog_with_incoming(
        existing,
        list(request.messages),
        max_turns=max_dialog_turns(),
    )
    dialog = append_assistant(dialog, assistant_text, max_turns=max_dialog_turns())
    try:
        # as_node required when updating outside a running superstep.
        await graph.aupdate_state(
            config,
            {
                **_request_to_input(request),
                "dialog": dialog,
                "memory_turns": len(dialog),
            },
            as_node="generate",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "que_memory_persist_failed",
            thread_id=thread_id,
            error=str(exc),
            path="persist_dialog_turn",
        )
        return 0
    return len(dialog)


@dataclass
class PreparedTurn:
    """Messages after the prepare node — useful for unit tests without LLM calls."""

    messages: list[ChatMessage]
    sources_used: list[str] = field(default_factory=list)
    identity: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TurnDecision:
    """Outcome of understanding + fast paths before LLM."""

    request_id: str
    understanding: RequestUnderstanding
    resolution: ResolvedRequest
    early_reply: str | None = None
    early_model: str | None = None
    guardrail: str | None = None


def _request_to_input(
    request: ChatRequest,
    *,
    resolution: ResolvedRequest | None = None,
    understanding: RequestUnderstanding | None = None,
    request_id: str | None = None,
) -> QueGraphState:
    payload: QueGraphState = {
        "input_messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "messages": [],
        "sources_used": [],
        "conversation_id": request.conversation_id,
        "user_id": request.user_id,
    }
    if request_id:
        payload["request_id"] = request_id
    if request.context is not None:
        payload["ui_context"] = request.context.model_dump(exclude_none=True)
    if resolution is not None:
        payload["raw_user_message"] = resolution.raw_message
        payload["resolved_query"] = resolution.resolved_query
        payload["is_follow_up"] = resolution.is_follow_up
        payload["topic"] = resolution.topic
        payload["current_task"] = resolution.resolved_query
        payload["intent"] = resolution.intent
        payload["response_mode"] = resolution.response_mode
        payload["retrieval_query"] = resolution.resolved_query
        payload["active_topic"] = resolution.topic
        payload["previous_intent"] = resolution.intent
        payload["unresolved_question"] = (
            resolution.resolved_query if resolution.response_mode == "clarify" else None
        )
    if understanding is not None:
        payload["understanding_route"] = understanding.route
        payload["data_need"] = understanding.data_need
        payload["understanding_complexity"] = understanding.complexity
        payload["understanding_freshness"] = understanding.freshness
        payload["execution_class"] = getattr(understanding, "execution_class", None)
        payload["canonical_intent"] = getattr(understanding, "canonical_intent", None)
        payload["understanding_confidence"] = getattr(understanding, "confidence", None)
        if getattr(understanding, "canonical_intent", None):
            payload["previous_intent"] = understanding.canonical_intent
            payload["active_topic"] = understanding.canonical_intent
    return payload


def _log_request_trace(
    *,
    request_id: str,
    request: ChatRequest,
    resolution: ResolvedRequest,
    understanding: RequestUnderstanding,
    knowledge_packs: list[str] | None = None,
) -> None:
    logger.info(
        "que_request_trace",
        request_id=request_id,
        conversation_id=request.conversation_id,
        user_hash=hash_user_id(request.user_id),
        previous_context_available=bool(resolution.prior_user_message),
        is_follow_up=resolution.is_follow_up,
        topic=resolution.topic,
        resolve_intent=resolution.intent,
        response_mode=resolution.response_mode,
        scope_decision=understanding.scope,
        route=understanding.route,
        resolve_reasons=list(resolution.reasons),
        knowledge_packs=knowledge_packs or [],
        understanding_intent=understanding.intent,
        understanding_risk=understanding.risk,
        understanding_freshness=understanding.freshness,
        understanding_data_need=understanding.data_need,
        understanding_complexity=understanding.complexity,
        understanding_reasons=list(understanding.reasons),
        execution_class=getattr(understanding, "execution_class", None),
        canonical_intent=getattr(understanding, "canonical_intent", None),
        ui_page=(request.context.current_page if request.context else None),
        ui_role=(request.context.user_role if request.context else None),
    )


def _lc_to_schema(messages: list[BaseMessage]) -> list[ChatMessage]:
    out: list[ChatMessage] = []
    for message in messages:
        content = message.content if isinstance(message.content, str) else str(message.content or "")
        if not content.strip():
            continue
        msg_type = message.type
        if msg_type == "system":
            out.append(ChatMessage(role="system", content=content))
        elif msg_type == "human":
            out.append(ChatMessage(role="user", content=content))
        elif msg_type == "ai":
            out.append(ChatMessage(role="assistant", content=content))
    return out


def prepare_turn(request: ChatRequest) -> PreparedTurn:
    """Run prepare → context → knowledge (no LLM) — identity + UI + product packs."""
    partial = _prepare_with_knowledge(request)
    return PreparedTurn(
        messages=_lc_to_schema(partial["messages"]),
        sources_used=list(partial.get("sources_used") or []),
        identity=identity_metadata(),
    )


def _assistant_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content or "")
            if content.strip():
                return content
    raise LLMError("LLM returned an empty response")


def _history_fingerprint(request: ChatRequest) -> str:
    """Stable key for LLM reply cache — always scoped by user identity."""
    cleaned = sanitize_history(list(request.messages))
    parts = [f"{m.role}:{m.content.strip()}" for m in cleaned]
    if request.conversation_id:
        parts.insert(0, f"cid:{request.conversation_id.strip()}")
    uid = (request.user_id or "").strip() or "anon"
    parts.insert(0, f"uid:{uid}")
    return cache_key("hist", *parts)


def _chunk_text(text: str, size: int = 28) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def _guardrail_understanding(reason: str) -> RequestUnderstanding:
    return RequestUnderstanding(
        scope="out_of_scope",
        intent="out_of_scope",
        risk="read",
        freshness="static",
        data_need="none",
        complexity="single_step",
        route="refuse",
        reasons=(reason,),
        execution_class="out_of_scope",
    )


def _apply_output_guard(
    text: str,
    *,
    request: ChatRequest,
    messages: list | None,
) -> tuple[str, str | None]:
    """Return (safe_text, model_override). model_override is guardrail:output on hit."""
    ui = request.context.model_dump(exclude_none=True) if request.context else {}
    blob = grounding_from_messages(messages or [])
    safe, hit = apply_output_guardrail(
        text,
        user_text=latest_user_text(request.messages),
        role=(ui or {}).get("user_role"),
        tool_blob=blob or None,
        ui_blob=blob or None,
    )
    if hit is None:
        return text, None
    return safe, "guardrail:output"


def decide_turn(request: ChatRequest) -> TurnDecision:
    """Resolve follow-ups, then classify with conversation-aware scope."""
    request_id = uuid.uuid4().hex[:12]
    user_text = latest_user_text(request.messages)
    resolution = resolve_request(list(request.messages))

    input_hit = scan_user_text(user_text)
    if input_hit is not None:
        understanding = _guardrail_understanding("guardrail:input")
        _log_request_trace(
            request_id=request_id,
            request=request,
            resolution=resolution,
            understanding=understanding,
        )
        return TurnDecision(
            request_id=request_id,
            understanding=understanding,
            resolution=resolution,
            early_reply=INPUT_REFUSAL,
            early_model="guardrail:input",
            guardrail="input",
        )

    # Hard out-of-scope on the *raw* utterance always wins (weather, jokes, …),
    # even mid-conversation — do not let follow-up rewriting soften that.
    if is_hard_out_of_scope(user_text):
        understanding = classify_request(user_text)
        _log_request_trace(
            request_id=request_id,
            request=request,
            resolution=resolution,
            understanding=understanding,
        )
        return TurnDecision(
            request_id=request_id,
            understanding=understanding,
            resolution=resolution,
            early_reply=OUT_OF_SCOPE_REFUSAL,
            early_model="scope:refuse",
        )

    # Warm social / FAQ replies before product scope. Keeps hello / I'm fine /
    # bye interactive without treating them as out-of-scope.
    # Chat-history asks ("what was my first question?") must not hit canned FAQ.
    canned = (
        None
        if is_conversation_meta(user_text)
        else match_canned_reply(
            user_text,
            conversation_id=request.conversation_id,
        )
    )
    if canned is not None:
        understanding = classify_request(
            user_text,
            conversation_active=True,
        )
        # Force a friendly route for logging even if classifier was unsure.
        if understanding.route == "refuse":
            understanding = RequestUnderstanding(
                scope="in_scope",
                intent="chitchat",
                risk="read",
                freshness="static",
                data_need="none",
                complexity="single_step",
                route="canned_eligible",
                reasons=("canned_social", *understanding.reasons),
                execution_class="conversational",
            )
        _log_request_trace(
            request_id=request_id,
            request=request,
            resolution=resolution,
            understanding=understanding,
        )
        return TurnDecision(
            request_id=request_id,
            understanding=understanding,
            resolution=resolution,
            early_reply=canned.text,
            early_model=canned.model,
        )

    # Active Quizzer thread → classifier may continue without keyword matches.
    # Prefer resolver follow-up flag; also treat any prior Quizzer topic in-thread
    # as active so ordinals like "first" never cold-refuse mid-conversation.
    conversation_active = bool(
        resolution.is_follow_up
        or resolution.topic
        or resolution.thread_active
        or is_conversation_meta(user_text)
        or (
            resolution.prior_user_message
            and _has_quizzer_hint(resolution.prior_user_message)
        )
    )
    understanding = classify_request(
        resolution.resolved_query or user_text,
        conversation_active=conversation_active,
    )
    from app.orchestration.intent_catalog import (
        best_lexical_hit,
        finalize_understanding,
        render_workflow_card,
    )
    from app.orchestration.semantic_router import maybe_override_understanding

    understanding = maybe_override_understanding(
        resolution.resolved_query or user_text,
        understanding,
        settings=get_settings(),
    )
    prior_canonical = None
    if resolution.is_follow_up and resolution.prior_user_message:
        prior_hit = best_lexical_hit(resolution.prior_user_message)
        if prior_hit is not None and prior_hit.score >= 0.36:
            prior_canonical = prior_hit.intent_id
    semantic_hit = None
    if getattr(understanding, "canonical_intent", None) and float(understanding.confidence or 0) >= 0.78:
        from app.orchestration.intent_catalog import IntentHit

        semantic_hit = IntentHit(
            intent_id=str(understanding.canonical_intent),
            score=float(understanding.confidence or 0),
            source="semantic",
        )
    understanding = finalize_understanding(
        understanding,
        resolution.resolved_query or user_text,
        hit=semantic_hit,
        prior_canonical=prior_canonical,
    )

    # Classifier says social/meta but phrase matcher missed → still skip LLM.
    if understanding.route == "canned_eligible" or understanding.intent in {
        "chitchat",
        "meta",
    }:
        intent_id = "capabilities"
        if understanding.intent == "chitchat":
            intent_id = "greeting"
        fallback = pick_canned_intent(
            intent_id,
            conversation_id=request.conversation_id,
        )
        if fallback is not None:
            _log_request_trace(
                request_id=request_id,
                request=request,
                resolution=resolution,
                understanding=understanding,
            )
            return TurnDecision(
                request_id=request_id,
                understanding=understanding,
                resolution=resolution,
                early_reply=fallback.text,
                early_model=fallback.model,
            )

    _log_request_trace(
        request_id=request_id,
        request=request,
        resolution=resolution,
        understanding=understanding,
    )

    if (
        understanding.execution_class == "deterministic"
        and understanding.canonical_intent
        and understanding.route != "tool"
    ):
        ui = request.context.model_dump(exclude_none=True) if request.context else {}
        role = str((ui or {}).get("user_role") or "")
        title = str((ui or {}).get("current_exam_title") or "")
        cache_id = (
            f"workflow::{understanding.canonical_intent}::{role or 'any'}::{title or '-'}"
        )
        from app.core.que_cache import get_cached_intent, set_cached_intent

        cached_card = get_cached_intent(cache_id)
        reply = cached_card
        if not reply:
            reply = render_workflow_card(
                understanding.canonical_intent,
                user_role=role or None,
                exam_title=title or None,
                current_page=str((ui or {}).get("current_page") or "") or None,
            )
            if reply:
                set_cached_intent(cache_id, reply)
        if reply:
            return TurnDecision(
                request_id=request_id,
                understanding=understanding,
                resolution=resolution,
                early_reply=reply,
                early_model=f"workflow:{understanding.canonical_intent}",
            )

    if understanding.route == "refuse":
        return TurnDecision(
            request_id=request_id,
            understanding=understanding,
            resolution=resolution,
            early_reply=OUT_OF_SCOPE_REFUSAL,
            early_model="scope:refuse",
        )

    if understanding.route == "clarify":
        return TurnDecision(
            request_id=request_id,
            understanding=understanding,
            resolution=resolution,
            early_reply=CLARIFY_REPLY,
            early_model="scope:clarify",
        )

    if understanding.route == "tool":
        cfg = _get_settings_for_tools()
        # When tools are enabled, continue into the graph (insight workflows).
        if not cfg.que_tools_enabled or not (cfg.quizzer_internal_base_url or "").strip():
            ui = request.context.model_dump(exclude_none=True) if request.context else None
            return TurnDecision(
                request_id=request_id,
                understanding=understanding,
                resolution=resolution,
                early_reply=live_data_reply_with_context(ui) if ui else TOOL_NOT_READY_REPLY,
                early_model="route:tool_pending",
            )

    return TurnDecision(
        request_id=request_id,
        understanding=understanding,
        resolution=resolution,
    )


async def resolve_write_confirmation(
    decision: TurnDecision,
    request: ChatRequest,
    settings: Settings | None = None,
) -> TurnDecision:
    """Detect a yes/no reply to a pending write-tool confirmation.

    Runs after ``decide_turn`` for every turn (cheap dict lookup when there is
    no pending action). This is the *only* place a write tool is ever actually
    executed — deterministic, outside the LLM/graph, so a mutation's outcome
    is never left to model fidelity. Overrides whatever ``decide_turn`` picked
    (canned/guardrail/etc.) when a pending confirmation matches, since a
    publish/notify/delete confirmation is more specific than generic chitchat.
    """
    thread_key = make_thread_id(request.conversation_id, request.user_id)
    pending = get_pending(thread_key)
    if pending is None:
        return decision

    text = latest_user_text(request.messages)
    if is_affirmative_reply(text):
        clear_pending(thread_key)
        from app.tools.executor import execute_confirmed_write_action

        execution = await execute_confirmed_write_action(
            pending, request_id=decision.request_id, settings=settings
        )
        reply = execution.final_reply or "Something went wrong. Nothing was changed."
        logger.info(
            "que_write_action_resolved",
            request_id=decision.request_id,
            tool=pending.tool_name,
            ok=execution.error_code is None,
        )
        return dataclasses.replace(decision, early_reply=reply, early_model="tool:write_confirm")

    if is_negative_reply(text):
        clear_pending(thread_key)
        return dataclasses.replace(
            decision,
            early_reply="Cancelled — nothing was changed.",
            early_model="tool:write_cancel",
        )

    # Anything else: fail safe. Don't carry a stale confirmation forward onto
    # an unrelated message — drop it and process this turn normally.
    clear_pending(thread_key)
    return decision


def _log_turn(
    *,
    event: str,
    decision: TurnDecision,
    request: ChatRequest,
    latency_ms: float,
    model: str | None = None,
    cache_hit: bool = False,
    cache_layer: str | None = None,
    error: str | None = None,
    knowledge_packs: list[str] | None = None,
    knowledge_scores: dict[str, int] | None = None,
    knowledge_truncated: bool | None = None,
) -> None:
    logger.info(
        event,
        request_id=decision.request_id,
        conversation_id=request.conversation_id,
        user_hash=hash_user_id(request.user_id),
        latency_ms=round(latency_ms, 2),
        model=model,
        cache_hit=cache_hit,
        cache_layer=cache_layer,
        error=error,
        knowledge_packs=knowledge_packs or [],
        knowledge_scores=knowledge_scores or {},
        knowledge_truncated=knowledge_truncated,
        is_follow_up=decision.resolution.is_follow_up,
        response_mode=decision.resolution.response_mode,
        topic=decision.resolution.topic,
        resolve_intent=decision.resolution.intent,
        **decision.understanding.as_log_dict(),
    )


async def complete(request: ChatRequest, *, settings: Settings | None = None) -> ChatResponse:
    cfg = settings or get_settings()
    started = time.perf_counter()
    t_decide = time.perf_counter()
    decision = decide_turn(request)
    decision = await resolve_write_confirmation(decision, request, settings=cfg)
    decide_ms = (time.perf_counter() - t_decide) * 1000.0
    with _langsmith_turn(decision):
        return await _complete_after_decide(
            request, decision, cfg=cfg, started=started, decide_ms=decide_ms
        )


async def _complete_after_decide(
    request: ChatRequest,
    decision: TurnDecision,
    *,
    cfg: Settings,
    started: float,
    decide_ms: float,
) -> ChatResponse:
    thread_id, mem_config = _thread_config(request)
    trace = _begin_obs(decision, request)
    trace.add_span(
        "decide",
        decide_ms,
        extra={
            "route": decision.understanding.route,
            "execution_class": getattr(decision.understanding, "execution_class", None),
            "canonical_intent": getattr(decision.understanding, "canonical_intent", None),
        },
    )
    if decision.guardrail:
        trace.add_span("guardrail", 0.0, extra={"layer": decision.guardrail})

    if decision.early_reply is not None:
        memory_turns = await _persist_dialog_turn(request, decision.early_reply)
        _log_turn(
            event="que_chat_complete",
            decision=decision,
            request=request,
            latency_ms=(time.perf_counter() - started) * 1000,
            model=decision.early_model,
            knowledge_packs=[],
        )
        logger.info(
            "que_memory_saved",
            request_id=decision.request_id,
            thread_id=thread_id,
            memory_turns=memory_turns,
            path="early",
        )
        _maybe_online(
            decision=decision,
            request=request,
            model=decision.early_model,
            guardrail=decision.guardrail,
            settings=cfg,
        )
        _end_obs(trace, started=started, model=decision.early_model, settings=cfg)
        return ChatResponse(
            message=ChatMessage(role="assistant", content=decision.early_reply),
            conversation_id=request.conversation_id,
            model=decision.early_model or "unknown",
        )

    if user_hour_exceeded(request.user_id, settings=cfg):
        await _persist_dialog_turn(request, CAPACITY_REPLY)
        _end_obs(trace, started=started, model="budget:user", settings=cfg)
        return _capacity_response(request, decision, model="budget:user")

    fingerprint = _history_fingerprint(request)
    cached = None
    if allow_llm_reply_cache(decision.understanding):
        cached = get_cached_llm_reply(fingerprint)
    if cached is not None:
        model_name = f"cache:{cached.get('model') or cfg.llm_model}"
        packs = list(cached.get("knowledge_packs") or [])
        await _persist_dialog_turn(request, cached["content"])
        trace.add_span("cache", 0.0, extra={"hit": True})
        _log_turn(
            event="que_chat_complete",
            decision=decision,
            request=request,
            latency_ms=(time.perf_counter() - started) * 1000,
            model=model_name,
            cache_hit=True,
            cache_layer="llm",
            knowledge_packs=packs,
        )
        _maybe_online(
            decision=decision,
            request=request,
            model=model_name,
            cache_hit=True,
            cache_layer="llm",
            settings=cfg,
        )
        _end_obs(trace, started=started, model=model_name, settings=cfg)
        return ChatResponse(
            message=ChatMessage(role="assistant", content=cached["content"]),
            conversation_id=request.conversation_id,
            model=model_name,
            knowledge_packs=packs,
            sources_used=["cache", "knowledge", *[f"knowledge:{p}" for p in packs]],
        )

    # Knowledge packs come from the graph knowledge_node (no duplicate pre-retrieve).
    graph = get_que_graph()
    initial = _request_to_input(
        request,
        resolution=decision.resolution,
        understanding=decision.understanding,
        request_id=decision.request_id,
    )
    invoke_kwargs: dict = {}
    if mem_config is not None:
        invoke_kwargs["config"] = mem_config

    try:
        result = await graph.ainvoke(initial, **invoke_kwargs)
    except LLMError:
        _log_turn(
            event="que_chat_complete",
            decision=decision,
            request=request,
            latency_ms=(time.perf_counter() - started) * 1000,
            error="llm_error",
            knowledge_packs=[],
        )
        _end_obs(trace, started=started, error=True, settings=cfg)
        raise
    except ValueError:
        _log_turn(
            event="que_chat_complete",
            decision=decision,
            request=request,
            latency_ms=(time.perf_counter() - started) * 1000,
            error="bad_request",
            knowledge_packs=[],
        )
        _end_obs(trace, started=started, error=True, settings=cfg)
        raise
    except Exception as exc:  # noqa: BLE001
        _log_turn(
            event="que_chat_complete",
            decision=decision,
            request=request,
            latency_ms=(time.perf_counter() - started) * 1000,
            error=type(exc).__name__,
            knowledge_packs=[],
        )
        _end_obs(trace, started=started, error=True, settings=cfg)
        raise LLMError(str(exc)) from exc

    content = _assistant_text(result.get("messages") or [])
    model_name = result.get("model_name") or cfg.llm_model
    packs = list(result.get("knowledge_packs") or [])
    sources = list(result.get("sources_used") or [])
    content, out_model = _apply_output_guard(
        content, request=request, messages=result.get("messages") or []
    )
    if out_model:
        model_name = out_model
    cacheable = allow_llm_reply_cache(decision.understanding) and not str(model_name).startswith(
        "guardrail:"
    )
    if cacheable:
        set_cached_llm_reply(
            fingerprint,
            content=content,
            model=model_name,
            knowledge_packs=packs,
        )
    _log_turn(
        event="que_chat_complete",
        decision=decision,
        request=request,
        latency_ms=(time.perf_counter() - started) * 1000,
        model=model_name,
        knowledge_packs=packs,
    )
    _maybe_online(
        decision=decision,
        request=request,
        model=str(model_name),
        settings=cfg,
    )
    logger.info(
        "que_memory_saved",
        request_id=decision.request_id,
        thread_id=thread_id,
        memory_turns=result.get("memory_turns"),
        path="graph",
    )
    if out_model:
        trace.add_span("guardrail", 0.0, extra={"layer": "output"})
    _end_obs(trace, started=started, model=str(model_name), settings=cfg)
    return ChatResponse(
        message=ChatMessage(role="assistant", content=content),
        conversation_id=request.conversation_id,
        model=model_name,
        knowledge_packs=packs,
        sources_used=sources,
    )


async def stream_turn_events(
    request: ChatRequest,
    *,
    settings: Settings | None = None,
    decision: TurnDecision | None = None,
) -> AsyncIterator[dict]:
    """Yield SSE-ready dicts: status events then token events (same context as complete)."""
    from app.orchestration.agent_loop import iter_agent_loop
    from app.orchestration.agent_status import status_event, tool_status_label

    cfg = settings or get_settings()
    started = time.perf_counter()
    t_decide = time.perf_counter()
    decision = decision or decide_turn(request)
    decide_ms = (time.perf_counter() - t_decide) * 1000.0
    thread_id, mem_config = _thread_config(request)
    trace = _begin_obs(decision, request)
    trace.add_span("decide", decide_ms, extra={"route": decision.understanding.route})
    if decision.guardrail:
        trace.add_span("guardrail", 0.0, extra={"layer": decision.guardrail})
    model_used: str | None = None
    errored = False
    smith = _langsmith_turn(decision)
    smith.__enter__()
    try:
        yield status_event(stage="prepare", label="Reading your question…")

        if decision.early_reply is not None:
            memory_turns = await _persist_dialog_turn(request, decision.early_reply)
            _log_turn(
                event="que_chat_stream",
                decision=decision,
                request=request,
                latency_ms=(time.perf_counter() - started) * 1000,
                model=decision.early_model,
            )
            logger.info(
                "que_memory_saved",
                request_id=decision.request_id,
                thread_id=thread_id,
                memory_turns=memory_turns,
                path="early_stream",
            )
            _maybe_online(
                decision=decision,
                request=request,
                model=decision.early_model,
                guardrail=decision.guardrail,
                settings=cfg,
            )
            model_used = decision.early_model
            yield status_event(stage="generate", label="Writing answer…")
            for piece in _chunk_text(decision.early_reply):
                yield {"type": "token", "content": piece}
            return

        if user_hour_exceeded(request.user_id, settings=cfg):
            await _persist_dialog_turn(request, CAPACITY_REPLY)
            model_used = "budget:user"
            yield status_event(stage="generate", label="Writing answer…")
            for piece in _chunk_text(CAPACITY_REPLY):
                yield {"type": "token", "content": piece}
            return

        fingerprint = _history_fingerprint(request)
        cached = None
        if allow_llm_reply_cache(decision.understanding):
            cached = get_cached_llm_reply(fingerprint)
        if cached is not None:
            model_name = f"cache:{cached.get('model') or cfg.llm_model}"
            packs = list(cached.get("knowledge_packs") or [])
            await _persist_dialog_turn(request, cached["content"])
            trace.add_span("cache", 0.0, extra={"hit": True})
            _log_turn(
                event="que_chat_stream",
                decision=decision,
                request=request,
                latency_ms=(time.perf_counter() - started) * 1000,
                model=model_name,
                cache_hit=True,
                cache_layer="llm",
                knowledge_packs=packs,
            )
            _maybe_online(
                decision=decision,
                request=request,
                model=model_name,
                cache_hit=True,
                cache_layer="llm",
                settings=cfg,
            )
            model_used = model_name
            yield status_event(stage="generate", label="Writing answer…")
            for piece in _chunk_text(cached["content"]):
                yield {"type": "token", "content": piece}
            return

        existing_dialog: list = []
        if mem_config is not None:
            try:
                snap = await get_que_graph().aget_state(mem_config)
                existing_dialog = list((snap.values or {}).get("dialog") or [])
            except Exception:  # noqa: BLE001
                existing_dialog = []

        initial = _request_to_input(
            request,
            resolution=decision.resolution,
            understanding=decision.understanding,
            request_id=decision.request_id,
        )
        initial["dialog"] = existing_dialog
        state = prepare_node(initial)
        state = {**initial, **state}
        state = {**state, **context_node(state)}
        mode = (state.get("runtime_mode") or "knowledge").strip()
        tool_name: str | None = None
        packs: list[str] = []
        if mode == "agent":
            query = str(state.get("retrieval_query") or state.get("resolved_query") or "")
            raw = str(state.get("raw_user_message") or "")
            ui = state.get("ui_context") if isinstance(state.get("ui_context"), dict) else None
            agent_result = None
            async for event in iter_agent_loop(
                query=query,
                raw_query=raw or None,
                ui_context=ui,
                user_id=request.user_id,
                route=state.get("understanding_route"),
                request_id=decision.request_id,
                settings=cfg,
            ):
                if event.kind == "before":
                    yield status_event(
                        stage="tool",
                        label=tool_status_label(event.tool_name),
                        tool=event.tool_name,
                        step=event.step,
                    )
                elif event.kind == "after":
                    yield status_event(
                        stage="tool_done",
                        label="Got the numbers — drafting next steps…",
                        tool=event.tool_name,
                        step=event.step,
                    )
                elif event.kind == "done":
                    agent_result = event.result
            if agent_result is not None:
                state = {**state, **apply_agent_loop_result(state, agent_result)}
                tool_name = state.get("tool_name")
            packs = list(state.get("knowledge_packs") or [])
        elif mode == "workflow":
            from app.orchestration.runtime_mode import decide_runtime_mode_from_state

            _mode, _reason, tool_sel = decide_runtime_mode_from_state(state, settings=cfg)
            tool_name = tool_sel.tool.name if tool_sel and tool_sel.tool else None
            yield status_event(
                stage="tool",
                label=tool_status_label(tool_name),
                tool=tool_name,
            )
            state = {**state, **(await tools_node(state))}
            tool_name = state.get("tool_name") or tool_name
            if tool_name:
                yield status_event(
                    stage="tool_done",
                    label="Got the numbers — drafting next steps…",
                    tool=tool_name,
                )
            packs = list(state.get("knowledge_packs") or [])
        else:
            yield status_event(stage="knowledge", label="Searching Quizzer guides…")
            t_ret = time.perf_counter()
            state = knowledge_node(state)
            packs = list(state.get("knowledge_packs") or [])
            trace.add_span("retrieve", (time.perf_counter() - t_ret) * 1000.0)

        from app.graphs.nodes import _refresh_identity_pieces

        messages = _refresh_identity_pieces(state, list(state.get("messages") or []))
        state = {**state, "messages": messages}
        dialog_after_prepare = list(state.get("dialog") or existing_dialog)

        yield status_event(stage="generate", label="Writing answer…")

        ok_llm, deny = allow_llm_call(decision.request_id, messages=messages, settings=cfg)
        if not ok_llm:
            model_used = deny or "budget:turn"
            await _persist_dialog_turn(request, CAPACITY_REPLY)
            for piece in _chunk_text(CAPACITY_REPLY):
                yield {"type": "token", "content": piece}
            return

        collected: list[str] = []
        lane_used = None
        t_llm = time.perf_counter()
        try:
            async for piece, lane in astream_chat(
                messages,
                settings=cfg,
                complexity=state.get("understanding_complexity"),
                runtime_mode=state.get("runtime_mode"),
                intent=state.get("intent"),
                execution_class=state.get("execution_class")
                or getattr(decision.understanding, "execution_class", None),
            ):
                if not collected:
                    trace.add_span(
                        "ttft",
                        (time.perf_counter() - t_llm) * 1000.0,
                        extra={
                            "model": lane.model,
                            "attempt": 0,
                            "route": decision.understanding.route,
                        },
                    )
                collected.append(piece)
                lane_used = lane
                yield {"type": "token", "content": piece}
        except LLMError:
            errored = True
            _log_turn(
                event="que_chat_stream",
                decision=decision,
                request=request,
                latency_ms=(time.perf_counter() - started) * 1000,
                error="llm_error",
                knowledge_packs=packs,
                            )
            raise
        except ValueError:
            errored = True
            _log_turn(
                event="que_chat_stream",
                decision=decision,
                request=request,
                latency_ms=(time.perf_counter() - started) * 1000,
                error="bad_request",
                knowledge_packs=packs,
                            )
            raise
        except Exception as exc:  # noqa: BLE001
            errored = True
            _log_turn(
                event="que_chat_stream",
                decision=decision,
                request=request,
                latency_ms=(time.perf_counter() - started) * 1000,
                error=type(exc).__name__,
                knowledge_packs=packs,
                            )
            raise LLMError(str(exc)) from exc

        usage = last_llm_usage()
        usd = usd_for_usage(usage)
        note_llm_usage(
            decision.request_id,
            tokens=usage.total,
            usd=usd,
            user_id=request.user_id,
        )
        trace.add_span(
            "llm",
            (time.perf_counter() - t_llm) * 1000.0,
            extra={
                "stream": True,
                "model": lane_used.model if lane_used is not None else None,
                "key_index": lane_used.key_index if lane_used is not None else None,
            },
        )
        if usage.total:
            trace.prompt_tokens = usage.prompt_tokens
            trace.completion_tokens = usage.completion_tokens
            if usd is not None:
                trace.cost_usd = usd
            elif ":free" in (usage.model or "").casefold():
                trace.cost_usd = 0.0

        full = "".join(collected).strip()
        model_name = lane_used.model if lane_used is not None else cfg.llm_model
        if full:
            full, out_model = _apply_output_guard(full, request=request, messages=messages)
            if out_model:
                model_name = out_model
                trace.add_span("guardrail", 0.0, extra={"layer": "output"})
            cacheable = allow_llm_reply_cache(decision.understanding) and not str(
                model_name
            ).startswith("guardrail:")
            if cacheable:
                set_cached_llm_reply(
                    fingerprint,
                    content=full,
                    model=str(model_name),
                    knowledge_packs=packs,
                )
            if mem_config is not None:
                dialog = append_assistant(
                    dialog_after_prepare,
                    full,
                    max_turns=max_dialog_turns(),
                )
                try:
                    await get_que_graph().aupdate_state(
                        mem_config,
                        {
                            **_request_to_input(
                                request,
                                resolution=decision.resolution,
                                understanding=decision.understanding,
                                request_id=decision.request_id,
                            ),
                            "dialog": dialog,
                            "memory_turns": len(dialog),
                            "knowledge_packs": packs,
                        },
                        as_node="generate",
                    )
                    logger.info(
                        "que_memory_saved",
                        request_id=decision.request_id,
                        thread_id=thread_id,
                        memory_turns=len(dialog),
                        path="stream",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "que_memory_persist_failed",
                        request_id=decision.request_id,
                        thread_id=thread_id,
                        error=str(exc),
                        path="stream",
                    )
        model_used = str(model_name)
        trace.add_span("generate", (time.perf_counter() - t_llm) * 1000.0)
        _log_turn(
            event="que_chat_stream",
            decision=decision,
            request=request,
            latency_ms=(time.perf_counter() - started) * 1000,
            model=str(model_name),
            knowledge_packs=packs,
                    )
        _maybe_online(
            decision=decision,
            request=request,
            model=str(model_name),
            settings=cfg,
        )
    finally:
        try:
            _end_obs(trace, started=started, error=errored, model=model_used, settings=cfg)
        finally:
            smith.__exit__(None, None, None)


async def stream_tokens(
    request: ChatRequest,
    *,
    settings: Settings | None = None,
    decision: TurnDecision | None = None,
) -> AsyncIterator[str]:
    """Token-only stream (tests / callers that ignore status events)."""
    async for event in stream_turn_events(request, settings=settings, decision=decision):
        if event.get("type") == "token" and event.get("content"):
            yield str(event["content"])
