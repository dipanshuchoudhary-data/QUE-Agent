"""Hinglish how-to asks are guidance (never a live tool); interpret-on-miss parsing."""

from __future__ import annotations

import pytest

from app.knowledge.interpret import parse
from app.orchestration.understanding import classify_request, is_guidance_ask


@pytest.mark.parametrize(
    "query",
    ["exam publish kese kru", "exam publish krna h kaise", "Students ki performance kaise improve kru?"],
)
def test_hinglish_howto_is_knowledge_not_tool(query):
    assert is_guidance_ask(query)
    assert classify_request(query).route == "knowledge"


@pytest.mark.parametrize(
    "query",
    ["publish my exam", "how many students passed", "show me my results"],
)
def test_english_routing_unchanged(query):
    # not guidance-shaped (quantity / imperative asks want data or an action)
    assert not is_guidance_ask(query)


def test_parse_rewrite():
    got = parse('{"english": "How to publish my exam", "ambiguous": false, "clarify": ""}')
    assert got and got.english == "How to publish my exam" and not got.ambiguous


def test_parse_ambiguous_needs_question():
    got = parse('{"english": "", "ambiguous": true, "clarify": "Do you mean raise or edit scores?"}')
    assert got and got.ambiguous and got.clarify.endswith("?")
    no_q = parse('{"english": "x", "ambiguous": true, "clarify": ""}')
    assert no_q and not no_q.ambiguous


def test_parse_rejects_links_and_garbage():
    assert parse("not json") is None
    bad = parse('{"english": "x", "ambiguous": true, "clarify": "See https://evil.example now?"}')
    assert bad and not bad.ambiguous and bad.clarify == ""
