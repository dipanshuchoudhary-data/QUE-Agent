"""LangGraph state for the QUE conversational agent."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from langchain_core.messages import BaseMessage


class QueGraphState(TypedDict):
    """Agent state shared across graph nodes.

    Topology: prepare → context → knowledge | tools | agent → generate.

    ``dialog`` is short-term memory (user/assistant turns) restored by the
    LangGraph checkpointer when ``thread_id`` is set. ``messages`` is the
    ephemeral prompt for this turn only (identity + UI context + knowledge + dialog).

    Conversational resolution fields (resolved_query, topic, …) are set by the
    orchestration layer before/during the graph so RAG and generation use the
    rewritten ask — not only the raw follow-up utterance.

    ``ui_context`` is structured Quizzer page/entity/role (Phase 3) — never
    concatenated into the user message.
    """

    # Raw role/content dicts from the HTTP request (pre-sanitize).
    input_messages: list[dict[str, str]]
    # Short-term conversation memory (Human/AI only) — checkpointed.
    dialog: NotRequired[list[BaseMessage]]
    # LangChain messages actually sent to / returned from the model this turn.
    messages: list[BaseMessage]
    sources_used: list[str]
    conversation_id: NotRequired[str | None]
    user_id: NotRequired[str | None]
    request_id: NotRequired[str | None]
    identity_version: NotRequired[str]
    model_name: NotRequired[str]
    knowledge_packs: NotRequired[list[str]]
    memory_turns: NotRequired[int]

    # --- Conversational resolution (checkpointed for continuity) ---
    raw_user_message: NotRequired[str | None]
    resolved_query: NotRequired[str | None]
    is_follow_up: NotRequired[bool]
    topic: NotRequired[str | None]
    current_task: NotRequired[str | None]
    intent: NotRequired[str | None]
    response_mode: NotRequired[str | None]
    retrieval_query: NotRequired[str | None]

    # --- Compact conversational state (Wave 3) ---
    active_topic: NotRequired[str | None]
    previous_intent: NotRequired[str | None]
    active_entity: NotRequired[str | None]
    unresolved_question: NotRequired[str | None]
    pending_action: NotRequired[str | None]

    # Structured Quizzer page/entity/role hint. Must be a declared channel: LangGraph
    # drops undeclared input keys, which silently removed the role before tool policy
    # checks (every graph-path tool call failed as "forbidden") and skipped UI injection.
    ui_context: NotRequired[dict[str, Any] | None]

    # --- Phase 4 tools ---
    understanding_route: NotRequired[str | None]
    data_need: NotRequired[str | None]
    understanding_complexity: NotRequired[str | None]
    understanding_freshness: NotRequired[str | None]
    execution_class: NotRequired[str | None]
    canonical_intent: NotRequired[str | None]
    understanding_confidence: NotRequired[float | None]
    runtime_mode: NotRequired[str | None]
    runtime_mode_reason: NotRequired[str | None]
    agent_steps: NotRequired[int]
    agent_termination_reason: NotRequired[str | None]
    tools_used: NotRequired[list[str]]
    tool_name: NotRequired[str | None]
    tool_args: NotRequired[dict[str, Any] | None]
    tool_error: NotRequired[str | None]
    tool_latency_ms: NotRequired[float | None]
    # Tool failure recovery: "knowledge" when a failed tool was replaced by KB
    # retrieval; ``direct_reply`` is a deterministic answer that skips the LLM
    # (live data that could not be fetched must never be paraphrased by a model).
    tool_fallback: NotRequired[str | None]
    direct_reply: NotRequired[str | None]
    # model_name reported for a `direct_reply` (defaults to the tool-unavailable tag).
    direct_model: NotRequired[str | None]
    # Retrieval missed and nothing else can ground the turn; `resolve_knowledge_miss` decides
    # (interpret + one retry, ask, or honest no-answer) before generation.
    knowledge_miss: NotRequired[bool]
