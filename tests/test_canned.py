"""Canned FAQ fast-path — no LLM."""

from __future__ import annotations

import random

import pytest

from app.orchestration.canned import match_canned_reply
from app.orchestration.pipeline import complete
from app.schemas.chat import ChatMessage, ChatRequest


@pytest.mark.parametrize(
    "text,intent",
    [
        ("hello", "greeting"),
        ("Hi!", "greeting"),
        ("hey QUE", "greeting"),
        ("Heelllo", "greeting"),
        ("hellloooo", "greeting"),
        ("hiiii", "greeting"),
        ("HEY!!!", "greeting"),
        ("good morning", "greeting"),
        ("what's up", "greeting"),
        ("how are you", "how_are_you"),
        ("howw are youu", "how_are_you"),
        ("I am fine what about you", "wellbeing_reply"),
        ("i'm good how about you", "wellbeing_reply"),
        ("im fine", "wellbeing_reply"),
        ("what about you", "wellbeing_reply"),
        ("ok", "ack"),
        ("got it", "ack"),
        ("what can you do", "capabilities"),
        ("what can you help me with", "capabilities"),
        ("What can you help me with in Quizzer?", "capabilities"),
        ("how can you help me with", "capabilities"),
        ("I am new here ,explain this to me", "getting_started"),
        ("explain this to me", "getting_started"),
        ("What is Quizzer?", "what_is_quizzer"),
        ("what is quizer", "what_is_quizzer"),  # small typo
        ("who are you", "capabilities"),
        ("thanks", "thanks"),
        ("thankssss", "thanks"),
        ("thank you so much", "thanks"),
        ("bye", "bye"),
        ("good night", "bye"),
        ("take care", "bye"),
        ("see you later", "bye"),
    ],
)
def test_canned_matches_common_asks(text, intent):
    hit = match_canned_reply(text, rng=random.Random(0))
    assert hit is not None
    assert hit.intent == intent
    assert hit.text.strip()
    assert hit.model == "canned"


def test_wellbeing_reply_not_refused_after_hello():
    from app.orchestration.pipeline import decide_turn
    from app.schemas.chat import ChatRequest

    decision = decide_turn(
        ChatRequest(
            messages=[
                {"role": "user", "content": "Hello"},
                {
                    "role": "assistant",
                    "content": "Hi! Ask me anything about Quizzer.",
                },
                {"role": "user", "content": "I am fine what about you"},
            ],
            conversation_id="c-social",
        )
    )
    assert decision.early_reply is not None
    assert decision.early_model == "canned"
    assert decision.understanding.route != "refuse"
    assert "I only help with Quizzer" not in decision.early_reply


def test_canned_skips_real_product_questions():
    assert match_canned_reply("Where is Monitoring for my exam?") is None
    assert match_canned_reply("How do I publish?") is None


def test_canned_variants_differ_across_seeds():
    a = match_canned_reply("hello", rng=random.Random(1))
    b = match_canned_reply("hello", rng=random.Random(2))
    c = match_canned_reply("hello", rng=random.Random(3))
    assert a and b and c
    # At least two distinct strings across a few seeds (4 variants available).
    assert len({a.text, b.text, c.text}) >= 2


@pytest.mark.asyncio
async def test_complete_uses_canned_without_llm():
    request = ChatRequest(messages=[ChatMessage(role="user", content="hello")])
    response = await complete(request)
    assert response.model == "canned"
    assert "Quizzer" in response.message.content or "QUE" in response.message.content
