"""Ask-back for questions that name nothing ("Can I change it after?")."""

from __future__ import annotations

import pytest

from app.orchestration.clarify import (
    CLARIFY_REFERENT_REPLIES,
    is_referent_reply,
    merge_with_answer,
    needs_referent,
    referent_reply,
)
from app.orchestration.pipeline import decide_turn
from app.orchestration.resolve import resolve_request
from app.schemas.chat import ChatMessage, ChatRequest


@pytest.mark.parametrize(
    "text",
    [
        "Can I change it after?",
        "How do I share this?",
        "can i undo that",
        "How do I turn this off?",
        "It's not working",
        "this isn't loading",
        "How do I use it?",
        "Can I edit them later?",
    ],
)
def test_needs_referent_true(text: str) -> None:
    assert needs_referent(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Can I change the exam timer after publishing?",  # names the exam
        "How do I share this exam?",  # names a Quizzer noun
        "How do I share this page?",  # pronoun is not the object
        "Is it possible to reset my password?",  # idiom, not a referent
        "How do I publish my exam?",
        "Hello",
        "What can you do?",
        "explain this",  # canned meta, handled elsewhere
        "What is the weather like, can you check it?",  # hard out-of-scope
        "I want to share that with my students and also add them to the class roster",  # too long
        "",
    ],
)
def test_needs_referent_false(text: str) -> None:
    assert needs_referent(text) is False


def test_reply_is_deterministic_and_recognised() -> None:
    reply = referent_reply("Can I change it after?")
    assert reply in CLARIFY_REFERENT_REPLIES
    assert referent_reply("Can I change it after?") == reply
    assert is_referent_reply(reply)
    assert is_referent_reply(f"  {reply}  ")
    assert not is_referent_reply("Open Exams and click Settings.")
    assert not is_referent_reply(None)


def _req(*pairs: tuple[str, str], context: dict | None = None) -> ChatRequest:
    return ChatRequest(
        messages=[{"role": r, "content": t} for r, t in pairs],
        conversation_id="c-clarify",
        context=context,
    )


def test_first_message_with_no_referent_asks_back() -> None:
    decision = decide_turn(_req(("user", "Can I change it after?")))
    assert decision.understanding.route == "clarify"
    assert decision.early_model == "scope:clarify_referent"
    assert decision.early_reply in CLARIFY_REFERENT_REPLIES


def test_prior_quizzer_topic_is_not_clarified() -> None:
    decision = decide_turn(
        _req(
            ("user", "How do I publish my exam?"),
            ("assistant", "Open the exam and click Publish."),
            ("user", "Can I change it after?"),
        )
    )
    assert decision.early_model != "scope:clarify_referent"
    assert decision.resolution.is_follow_up is True


@pytest.mark.parametrize(
    "context",
    [
        {"current_page": "exam_workspace"},
        {"current_page": "unknown", "current_exam_id": "exam-1"},
        {"current_page": "unknown", "current_exam_title": "Physics Midterm"},
    ],
)
def test_ui_context_gives_the_pronoun_a_referent(context: dict) -> None:
    decision = decide_turn(_req(("user", "Can I change it after?"), context=context))
    assert decision.early_model != "scope:clarify_referent"


def test_unknown_page_context_does_not_count_as_referent() -> None:
    decision = decide_turn(
        _req(("user", "How do I share this?"), context={"current_page": "unknown"})
    )
    assert decision.early_model == "scope:clarify_referent"


def test_answer_to_clarification_is_merged_with_original_ask() -> None:
    ask = "Can I change it after?"
    reply = referent_reply(ask)
    request = _req(("user", ask), ("assistant", reply), ("user", "the exam timer"))
    resolved = resolve_request(list(request.messages))
    assert resolved.is_follow_up is True
    assert resolved.resolved_query == merge_with_answer(ask, "the exam timer")
    assert "Can I change it after?" in resolved.resolved_query
    assert "the exam timer" in resolved.resolved_query
    assert "referent_clarification_answered" in resolved.reasons

    decision = decide_turn(request)
    assert decision.early_model != "scope:clarify_referent"
    assert decision.early_model != "scope:refuse"
    assert decision.understanding.route == "knowledge"


def test_new_question_after_clarification_is_not_merged() -> None:
    ask = "Can I change it after?"
    request = _req(
        ("user", ask),
        ("assistant", referent_reply(ask)),
        ("user", "How do I publish my exam?"),
    )
    resolved = resolve_request(list(request.messages))
    assert "referent_clarification_answered" not in resolved.reasons
    assert "They are asking about" not in resolved.resolved_query


def test_unrelated_assistant_message_is_never_treated_as_clarification() -> None:
    messages = [
        ChatMessage(role="user", content="Can I change it after?"),
        ChatMessage(role="assistant", content="Open Exams and pick the exam."),
        ChatMessage(role="user", content="the exam timer"),
    ]
    resolved = resolve_request(messages)
    assert "referent_clarification_answered" not in resolved.reasons


def test_out_of_scope_answer_is_not_merged() -> None:
    ask = "How do I share this?"
    messages = [
        ChatMessage(role="user", content=ask),
        ChatMessage(role="assistant", content=referent_reply(ask)),
        ChatMessage(role="user", content="what is the weather today"),
    ]
    resolved = resolve_request(messages)
    assert "referent_clarification_answered" not in resolved.reasons
