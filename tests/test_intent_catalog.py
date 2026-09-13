"""Canonical intents, execution class, and workflow cards (no LLM)."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.llm import (
    max_tokens_for_turn,
    reasoning_enabled_for_turn,
)
from app.core.config import Settings
from app.orchestration.intent_catalog import (
    finalize_understanding,
    has_workflow_card,
    render_workflow_card,
)
from app.orchestration.pipeline import decide_turn
from app.orchestration.prompt_pack import compose_leading_systems
from app.orchestration.resolve import ResolvedRequest
from app.orchestration.understanding import classify_request
from app.orchestration.ui_context import ui_context_needed
from app.schemas.chat import ChatRequest, QueUiContext

ROOT = Path(__file__).resolve().parents[1]


def test_publish_howto_is_deterministic_card():
    query = "how to published the draft exam"
    u = finalize_understanding(classify_request(query), query)
    assert u.route == "knowledge"
    assert u.canonical_intent == "exam.publish"
    assert u.execution_class == "deterministic"
    decision = decide_turn(ChatRequest(messages=[{"role": "user", "content": query}]))
    assert decision.early_model == "workflow:exam.publish"
    assert decision.early_reply
    assert "Publish" in (decision.early_reply or "")
    assert "Hi!" not in (decision.early_reply or "")


def test_publish_this_exam_stays_write_tool():
    query = "Publish this exam"
    u = finalize_understanding(classify_request(query), query)
    assert u.route == "tool"
    assert u.execution_class == "tool_required"
    decision = decide_turn(ChatRequest(messages=[{"role": "user", "content": query}]))
    assert decision.understanding.execution_class == "tool_required"
    assert not (decision.early_model or "").startswith("workflow:")


def test_resume_is_not_exam_publish():
    query = "Can students resume an exam?"
    u = finalize_understanding(classify_request(query), query)
    assert u.canonical_intent != "exam.publish"
    assert u.execution_class == "simple_knowledge"


def test_archive_what_happens_stays_complex():
    query = "What happens when I archive an exam?"
    u = finalize_understanding(classify_request(query), query)
    assert u.canonical_intent == "exam.archive"
    assert u.execution_class == "complex_knowledge"
    decision = decide_turn(ChatRequest(messages=[{"role": "user", "content": query}]))
    assert decision.early_reply is None


def test_share_followup_after_publish_card():
    request = ChatRequest(
        messages=[
            {"role": "user", "content": "How do I publish an exam?"},
            {"role": "assistant", "content": "Approve questions, then click **Publish**."},
            {"role": "user", "content": "what about sharing it?"},
        ]
    )
    decision = decide_turn(request)
    assert decision.understanding.canonical_intent == "exam.share"
    assert decision.early_model == "workflow:exam.share"


def test_student_publish_card_is_role_safe():
    body = render_workflow_card("exam.publish", user_role="student")
    assert body
    assert "teacher" in body.casefold() or "link" in body.casefold()
    teacher = render_workflow_card("exam.publish", user_role="teacher", exam_title="Midterm")
    assert teacher and "Midterm" in teacher
    assert has_workflow_card("exam.publish")


def test_efficiency_cases_offline_intents():
    payload = json.loads((ROOT / "evals" / "efficiency_cases.json").read_text(encoding="utf-8"))
    misses: list[str] = []
    for case in payload["cases"]:
        query = str(case["query"])
        u = finalize_understanding(classify_request(query), query)
        expected_cls = case.get("expected_execution_class")
        if expected_cls and u.execution_class != expected_cls:
            misses.append(f"{case['id']}: class {u.execution_class} != {expected_cls}")
        expected_intent = case.get("expected_canonical_intent")
        if expected_intent and u.canonical_intent != expected_intent:
            misses.append(f"{case['id']}: intent {u.canonical_intent} != {expected_intent}")
    assert misses == [], misses


def test_prompt_pack_skips_howto_duplicate():
    resolution = ResolvedRequest(raw_message="q", resolved_query="How do I publish?")
    messages = compose_leading_systems(
        resolution=resolution,
        execution_class="simple_knowledge",
        route="knowledge",
        pieces={"howto"},
    )
    blob = "\n".join(str(m.content) for m in messages)
    assert "few sentences" in blob
    assert blob.lower().count("step-by-step") <= 1


def test_ui_skipped_for_non_deictic_how_to():
    ui = {"current_page": "exam_workspace", "current_exam_id": "quiz-1"}
    assert (
        ui_context_needed(
            ui,
            route="knowledge",
            query="What is negative marking?",
            execution_class="simple_knowledge",
        )
        is False
    )
    assert (
        ui_context_needed(
            ui,
            route="knowledge",
            query="How do I publish this?",
            execution_class="deterministic",
        )
        is True
    )


def test_deictic_publish_uses_exam_title():
    request = ChatRequest(
        messages=[{"role": "user", "content": "How do I publish this?"}],
        context=QueUiContext(current_page="exam_workspace", current_exam_title="Midterm"),
    )
    decision = decide_turn(request)
    assert decision.early_model == "workflow:exam.publish"
    assert "Midterm" in (decision.early_reply or "")


def test_reasoning_off_for_simple_on_for_agent():
    assert reasoning_enabled_for_turn(execution_class="simple_knowledge") is False
    assert reasoning_enabled_for_turn(execution_class="complex_knowledge") is False
    assert reasoning_enabled_for_turn(execution_class="tool_required") is True
    assert reasoning_enabled_for_turn(runtime_mode="agent") is True
    cfg = Settings(
        APP_ENV="local",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
    )
    assert max_tokens_for_turn(cfg, execution_class="simple_knowledge") == cfg.llm_max_tokens_simple
    assert max_tokens_for_turn(cfg, execution_class="complex_knowledge") == cfg.llm_max_tokens_moderate
