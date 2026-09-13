"""Phase 3 UI context — schema, context_node injection, live-data grounding."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.graphs.nodes import context_node, prepare_node
from app.graphs.que_graph import build_que_graph, get_que_graph
from app.orchestration.pipeline import decide_turn, prepare_turn
from app.orchestration.ui_context import format_ui_context_system_message, live_data_reply_with_context
from app.schemas.chat import ChatRequest, QueUiContext


def test_graph_includes_context_node():
    get_que_graph.cache_clear()
    node_ids = set(build_que_graph().get_graph().nodes)
    assert {"prepare", "context", "knowledge", "generate"} <= node_ids
    get_que_graph.cache_clear()


def test_que_ui_context_rejects_oversized_route_path():
    with pytest.raises(ValidationError):
        QueUiContext(current_page="dashboard", route_path="x" * 300)


def test_que_ui_context_rejects_oversized_exam_id():
    with pytest.raises(ValidationError):
        QueUiContext(current_page="exam_workspace", current_exam_id="e" * 80)


def test_context_node_noop_without_ui_context():
    prepared = prepare_node(
        {
            "input_messages": [{"role": "user", "content": "How do I export this?"}],
            "messages": [],
            "sources_used": [],
        }
    )
    out = context_node({**prepared, "ui_context": None})
    assert not any(
        isinstance(m, SystemMessage) and "QUIZZER_UI_CONTEXT" in str(m.content)
        for m in out["messages"]
    )


def test_context_node_injects_structured_system_not_user_message():
    prepared = prepare_node(
        {
            "input_messages": [{"role": "user", "content": "How do I export this?"}],
            "messages": [],
            "sources_used": [],
            "ui_context": {
                "current_page": "exam_results",
                "current_exam_id": "quiz-123",
                "user_role": "teacher",
            },
        }
    )
    out = context_node(
        {
            **prepared,
            "ui_context": {
                "current_page": "exam_results",
                "current_exam_id": "quiz-123",
                "user_role": "teacher",
            },
        }
    )
    system_blobs = [str(m.content) for m in out["messages"] if isinstance(m, SystemMessage)]
    assert any("QUIZZER_UI_CONTEXT" in b for b in system_blobs)
    assert any("quiz-123" in b for b in system_blobs)
    assert any("exam_results" in b for b in system_blobs)
    assert any("Untrusted" in b or "untrusted" in b for b in system_blobs)
    # Must not append context into the human message.
    humans = [m for m in out["messages"] if isinstance(m, HumanMessage)]
    assert humans
    assert "QUIZZER_UI_CONTEXT" not in humans[-1].content
    assert "ui_context" in out["sources_used"]
    assert "ui_context:exam_results" in out["sources_used"]


def test_prepare_turn_includes_ui_context_source():
    prepared = prepare_turn(
        ChatRequest(
            messages=[{"role": "user", "content": "What does this tab mean?"}],
            context=QueUiContext(
                current_page="exam_workspace",
                current_exam_id="abc",
                user_role="teacher",
            ),
        )
    )
    assert "ui_context" in prepared.sources_used
    assert any("QUIZZER_UI_CONTEXT" in m.content for m in prepared.messages if m.role == "system")
    assert any("abc" in m.content for m in prepared.messages if m.role == "system")


def test_ambiguous_ask_without_context_has_no_invented_exam_id():
    prepared = prepare_turn(
        ChatRequest(messages=[{"role": "user", "content": "How do I export this?"}])
    )
    blob = "\n".join(m.content for m in prepared.messages if m.role == "system")
    assert "QUIZZER_UI_CONTEXT" not in blob
    assert "current_exam_id" not in blob


def test_format_ui_context_is_json_not_free_text_concat():
    text = format_ui_context_system_message(
        {"current_page": "analytics", "current_exam_id": "e1", "user_role": "teacher"}
    )
    assert text.startswith("QUIZZER_UI_CONTEXT")
    assert '"current_page":"analytics"' in text or '"current_page": "analytics"' in text.replace(
        " ", ""
    )


def test_live_data_reply_mentions_page_and_exam():
    reply = live_data_reply_with_context(
        {"current_page": "exam_results", "current_exam_id": "quiz-9"}
    )
    assert "exam_results" in reply
    assert "quiz-9" in reply
    assert "can't read live" in reply.casefold() or "can't read live" in reply.lower()


def test_decide_turn_tool_route_uses_context_grounded_reply(monkeypatch):
    monkeypatch.setenv("QUE_TOOLS_ENABLED", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": "user", "content": "How many students failed this exam today?"}],
            context=QueUiContext(
                current_page="exam_results",
                current_exam_id="exam-42",
                user_role="teacher",
            ),
        )
    )
    assert decision.early_reply is not None
    assert "exam-42" in decision.early_reply or decision.early_model == "route:tool_pending"
    if decision.early_model == "route:tool_pending":
        assert "exam-42" in (decision.early_reply or "")
