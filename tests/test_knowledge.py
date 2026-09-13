"""Product knowledge selection tests (no LLM)."""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from tests.conftest import requires_knowledge

from app.graphs.nodes import knowledge_node, prepare_node
from app.graphs.que_graph import build_que_graph, get_que_graph
from app.knowledge import select_knowledge, validate_knowledge_manifest
from app.orchestration.pipeline import prepare_turn
from app.schemas.chat import ChatRequest


@requires_knowledge
def test_manifest_files_all_exist():
    problems = validate_knowledge_manifest()
    assert problems == [], problems


@requires_knowledge
def test_core_always_selected():
    selection = select_knowledge([{"role": "user", "content": "hello"}])
    assert "core" in selection.pack_ids or "quizzer map" in selection.content.casefold()
    assert "quizzer" in selection.content.casefold()
    # Frontmatter should not be injected into the model context.
    assert not selection.content.lstrip().startswith("---")
    assert "Always inject this pack" not in selection.content


@requires_knowledge
def test_selects_creating_exams():
    selection = select_knowledge([{"role": "user", "content": "How do I create a quiz?"}])
    assert "creating-exams" in selection.pack_ids
    assert "Create Exam" in selection.content or "create" in selection.content.casefold()


@requires_knowledge
def test_selects_live_monitoring_for_monitoring_question():
    selection = select_knowledge([{"role": "user", "content": "Where is Monitoring?"}])
    assert "live-monitoring" in selection.pack_ids or "navigation" in selection.pack_ids
    assert "Monitoring" in selection.content


@requires_knowledge
def test_selects_empty_states_for_analytics_empty():
    selection = select_knowledge(
        [{"role": "user", "content": "Why is my Analytics empty with no data?"}]
    )
    assert "empty-states" in selection.pack_ids or "analytics" in selection.pack_ids
    assert "empty" in selection.content.casefold() or "Analytics" in selection.content


@requires_knowledge
def test_selects_publishing_guide():
    selection = select_knowledge(
        [{"role": "user", "content": "I cannot publish my exam, questions stuck in draft"}]
    )
    assert "publishing" in selection.pack_ids or "questions" in selection.pack_ids
    assert "publish" in selection.content.casefold() or "Approve" in selection.content


@requires_knowledge
def test_selects_verification_guide():
    selection = select_knowledge(
        [{"role": "user", "content": "what is the meaning of verification schema in exams"}]
    )
    assert "verification" in selection.pack_ids
    assert "verification" in selection.content.casefold() or "identity" in selection.content.casefold()


@requires_knowledge
def test_selects_arena():
    selection = select_knowledge(
        [{"role": "user", "content": "How do I host an Arena battle with a room code?"}]
    )
    assert "arena" in selection.pack_ids


@requires_knowledge
def test_selects_google_classroom():
    selection = select_knowledge(
        [{"role": "user", "content": "How do I connect Google Classroom and push grades?"}]
    )
    assert "google-classroom" in selection.pack_ids


@requires_knowledge
def test_fallback_when_no_keywords():
    selection = select_knowledge(
        [{"role": "user", "content": "zzzqqq unrelated producty gibberish xyz"}]
    )
    assert "core" in selection.pack_ids
    # Still injects one general guide so the model is not CORE-only silent.
    assert len(selection.pack_ids) >= 2


def test_graph_has_knowledge_node():
    get_que_graph.cache_clear()
    node_ids = set(build_que_graph().get_graph().nodes)
    assert {"prepare", "knowledge", "generate", "context", "tools"} <= node_ids
    get_que_graph.cache_clear()


@requires_knowledge
def test_knowledge_node_injects_system_pack():
    prepared = prepare_node(
        {
            "input_messages": [{"role": "user", "content": "Where is the Results tab?"}],
            "messages": [],
            "sources_used": [],
        }
    )
    state = {
        "input_messages": [{"role": "user", "content": "Where is the Results tab?"}],
        **prepared,
    }
    enriched = knowledge_node(state)
    assert "knowledge" in enriched["sources_used"]
    assert any(pid.startswith("knowledge:") for pid in enriched["sources_used"])
    system_texts = [m.content for m in enriched["messages"] if isinstance(m, SystemMessage)]
    assert len(system_texts) >= 2
    assert any("Results" in text or "results" in text.casefold() for text in system_texts)


@requires_knowledge
def test_prepare_turn_includes_knowledge_source():
    prepared = prepare_turn(
        ChatRequest(messages=[{"role": "user", "content": "Where is Monitoring?"}])
    )
    assert "identity" in prepared.sources_used
    assert "knowledge" in prepared.sources_used
    assert any("Monitoring" in m.content for m in prepared.messages if m.role == "system")
