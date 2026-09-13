"""Short-term memory (LangGraph checkpointer) unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.llm import ChatLane
from app.graphs.memory import (
    append_assistant,
    make_thread_id,
    merge_dialog_with_incoming,
    runnable_config,
)
from app.graphs.nodes import prepare_node
from app.graphs.que_graph import get_que_graph
from app.orchestration.pipeline import complete
from app.schemas.chat import ChatMessage, ChatRequest


def test_make_thread_id_scopes_user_and_conversation():
    assert make_thread_id("conv-1", "user-9") == "user-9:conv-1"
    assert make_thread_id("conv-1", None) == "anon:conv-1"
    assert make_thread_id(None, "user-9") is None
    assert make_thread_id("  ", "user-9") is None


def test_merge_seeds_then_appends_new_user_only():
    seed = merge_dialog_with_incoming(
        [],
        [
            ChatMessage(role="user", content="How do I publish?"),
            ChatMessage(role="assistant", content="Open Links and publish."),
        ],
        max_turns=20,
    )
    assert len(seed) == 2
    assert isinstance(seed[0], HumanMessage)

    nxt = merge_dialog_with_incoming(
        seed,
        [
            ChatMessage(role="user", content="How do I publish?"),
            ChatMessage(role="assistant", content="Open Links and publish."),
            ChatMessage(role="user", content="And where are results?"),
        ],
        max_turns=20,
    )
    assert len(nxt) == 3
    assert nxt[-1].content == "And where are results?"


def test_merge_keeps_canned_turns_missing_from_checkpoint():
    """Refuse/canned replies skip the graph, so client history must fill the gap."""
    existing = merge_dialog_with_incoming(
        [],
        [
            ChatMessage(role="user", content="Did you see my exam AI vs ML"),
            ChatMessage(role="assistant", content="Yes, it is published."),
        ],
        max_turns=20,
    )
    merged = merge_dialog_with_incoming(
        existing,
        [
            ChatMessage(role="user", content="Did you see my exam AI vs ML"),
            ChatMessage(role="assistant", content="Yes, it is published."),
            ChatMessage(role="user", content="How to enhance the experience on this website"),
            ChatMessage(
                role="assistant",
                content="I only help with Quizzer — creating quizzes, exams, monitoring, and results.",
            ),
            ChatMessage(role="user", content="what is my first query?"),
        ],
        max_turns=20,
    )
    texts = [str(m.content) for m in merged]
    assert "How to enhance the experience on this website" in texts
    assert any("only help with Quizzer" in t for t in texts)
    assert texts[-1] == "what is my first query?"


def test_append_assistant_trims():
    dialog = [HumanMessage(content=f"u{i}") for i in range(10)]
    dialog = append_assistant(dialog, "answer", max_turns=4)
    assert len(dialog) == 4
    assert isinstance(dialog[-1], AIMessage)


def test_prepare_uses_dialog_memory():
    state = prepare_node(
        {
            "input_messages": [{"role": "user", "content": "Where are results?"}],
            "dialog": [
                HumanMessage(content="How do I publish?"),
                AIMessage(content="Use Publish on the Links tab."),
            ],
            "messages": [],
            "sources_used": [],
        }
    )
    texts = [str(m.content) for m in state["messages"]]
    assert any("QUE" in t for t in texts)
    assert any("publish" in t.casefold() for t in texts)
    assert any("results" in t.casefold() for t in texts)
    assert "memory" in state["sources_used"]
    assert state["memory_turns"] >= 2


@pytest.mark.asyncio
async def test_complete_persists_dialog_across_turns():
    get_que_graph.cache_clear()
    lane = ChatLane(model="test-model", key_index=0, api_key="test")
    fake_ainvoke = AsyncMock(
        side_effect=[
            (AIMessage(content="Publish from the Links tab."), lane),
            (AIMessage(content="Results are under the Results tab — related to publishing."), lane),
        ]
    )
    cid = "mem-test-convo-1"

    with patch("app.graphs.nodes.ainvoke_chat", fake_ainvoke):
        first = await complete(
            ChatRequest(
                messages=[{"role": "user", "content": "What's the difference between exam duration and link window?"}],
                conversation_id=cid,
                user_id="u1",
            )
        )
        second = await complete(
            ChatRequest(
                messages=[
                    {"role": "user", "content": "What's the difference between exam duration and link window?"},
                    {"role": "assistant", "content": first.message.content},
                    {"role": "user", "content": "Give an example of that distinction."},
                ],
                conversation_id=cid,
                user_id="u1",
            )
        )

    assert fake_ainvoke.await_count == 2
    assert first.message.content
    assert second.message.content

    # Second call's prompt should include prior dialog from checkpointer.
    second_prompt = fake_ainvoke.await_args_list[1].args[0]
    blob = " ".join(str(m.content) for m in second_prompt)
    assert "duration" in blob.casefold() or "window" in blob.casefold()

    config = runnable_config(make_thread_id(cid, "u1") or "")
    snap = await get_que_graph().aget_state(config)
    dialog = list((snap.values or {}).get("dialog") or [])
    assert len(dialog) >= 3
    get_que_graph.cache_clear()
