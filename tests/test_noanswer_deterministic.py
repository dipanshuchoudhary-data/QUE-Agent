"""QUE_NOANSWER_DETERMINISTIC: fixed honest reply when retrieval finds nothing."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.graphs import nodes
from app.orchestration.clarify import NO_ANSWER_REPLIES, no_answer_reply


@pytest.fixture
def flag(monkeypatch):
    def set_flag(value: bool) -> None:
        monkeypatch.setattr(nodes, "get_settings", lambda: SimpleNamespace(que_noanswer_deterministic=value))

    return set_flag


MISS = SimpleNamespace(no_answer=True)
HIT = SimpleNamespace(no_answer=False)


def test_off_by_default_never_replies(flag):
    flag(False)
    assert nodes._should_answer_no_match({}, MISS) is False


def test_miss_with_flag_on_replies(flag):
    flag(True)
    assert nodes._should_answer_no_match({}, MISS) is True


def test_hit_never_replies(flag):
    flag(True)
    assert nodes._should_answer_no_match({}, HIT) is False


def test_follow_up_and_tool_fallback_keep_llm(flag):
    flag(True)
    assert nodes._should_answer_no_match({"is_follow_up": True}, MISS) is False
    assert nodes._should_answer_no_match({"tool_fallback": "knowledge"}, MISS) is False


def test_ui_context_keeps_llm(flag):
    flag(True)
    assert nodes._should_answer_no_match({"ui_context": {"current_exam_id": "abc"}}, MISS) is False
    assert nodes._should_answer_no_match({"ui_context": {"current_page": "results"}}, MISS) is False
    assert nodes._should_answer_no_match({"ui_context": {"current_page": "unknown"}}, MISS) is True


def test_reply_is_deterministic_and_never_invents_features():
    assert no_answer_reply("marks badhane hain") == no_answer_reply("  Marks badhane hain ")
    for reply in NO_ANSWER_REPLIES:
        assert "Release" not in reply and "click" not in reply.lower()
