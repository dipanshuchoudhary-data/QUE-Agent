"""Guidance-vs-live routing, tool-failure recovery, and evidence provenance.

Regression coverage for the ``r02`` failure ("Where is Monitoring in the sidebar?"
was sent to a live-exam tool, the tool failed, and the model answered with no
evidence). Nothing here asserts one exact reply: tests check the *route taken*, the
*evidence the generator received*, and that failures never become invented answers.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.llm import ChatLane
from app.graphs import nodes
from app.knowledge.assemble import assemble_selection, preamble
from app.knowledge.retrieve import KnowledgeSelection
from app.knowledge.store import RetrievedChunk
from app.obs.evidence import capture_evidence, record_generator_context, split_documents
from app.orchestration.intent_catalog import finalize_understanding
from app.orchestration.pipeline import complete
from app.orchestration.runtime_mode import decide_runtime_mode
from app.orchestration.understanding import classify_request, is_guidance_ask
from app.schemas.chat import ChatMessage, ChatRequest, QueUiContext
from app.tools.executor import ToolExecution
from app.tools.quizzer_client import ToolClientError
from app.tools.registry import get_tool
from app.tools.select import ToolSelection

_LANE = ChatLane(model="test-model", key_index=0, api_key="test")
ROOT = Path(__file__).resolve().parents[1]

NAV_CHUNK = RetrievedChunk(
    chunk_id="live-monitoring::where-to-find-it::0::x",
    doc_id="live-monitoring",
    path="monitoring/live-and-monitoring.md",
    title="LIVE, Monitoring, and Real-Time Tracking",
    section="Where to Find It",
    text=(
        "Monitoring tab: open Exams from the sidebar, open a specific exam, then select "
        "the Monitoring tab.\n\nThere is no top-level Monitoring or LIVE item in the sidebar."
    ),
    score=0.82,
    corpus_version="t",
)


def _selection(chunks: list[RetrievedChunk]) -> KnowledgeSelection:
    asm = assemble_selection(chunks, score_label="rrf")
    return KnowledgeSelection(
        pack_ids=list(asm.pack_ids),
        content=asm.content,
        scores=dict(asm.scores),
        mode="hybrid",
        no_answer=asm.no_answer,
        chunk_ids=list(asm.chunk_ids),
    )


def _mode(query: str, *, tools: bool = True):
    u = finalize_understanding(classify_request(query), query)
    return decide_runtime_mode(
        query=query,
        raw_query=query,
        route=str(u.route),
        data_need=str(u.data_need),
        complexity=str(u.complexity),
        tools_enabled=tools,
    )


# --- 1. routing: guidance vs live data -------------------------------------------------

GUIDANCE_PARAPHRASES = [
    "Where is Monitoring in the sidebar?",
    "Where do I find the live exam monitor?",
    "How do I see who is taking my exam in progress?",
    "What does the Monitoring tab show?",
    "Where is Analytics in the menu?",
    "Where can I see my exam status?",
    "Where do I find the blueprint of an exam?",
    "How do I check my results after the exam?",
    "How do I coach struggling students?",
]


@pytest.mark.parametrize("query", GUIDANCE_PARAPHRASES)
def test_guidance_asks_never_become_tool_calls(query):
    mode, _reason, selection = _mode(query)
    assert mode == "knowledge"
    assert selection is None or selection.tool is None


@pytest.mark.parametrize(
    ("query", "tool"),
    [
        ("Show me live exam health", "summarize_live_exam_health"),
        ("What are my dashboard metrics?", "summarize_dashboard_metrics"),
        ("How many exams have I created?", "summarize_my_exams"),
    ],
)
def test_real_data_requests_keep_their_tool(query, tool):
    mode, _reason, selection = _mode(query)
    assert mode == "workflow"
    assert selection is not None and selection.tool is not None
    assert selection.tool.name == tool


def test_chained_how_and_live_ask_keeps_tools():
    mode, _reason, _sel = decide_runtime_mode(
        query="How many students are live right now and how do I message them?",
        raw_query="How many students are live right now and how do I message them?",
        route="tool",
        data_need="live_tool",
        complexity="multi_step",
        tools_enabled=True,
    )
    assert mode in {"agent", "workflow"}


def test_quantity_questions_are_not_guidance():
    assert not is_guidance_ask("How many students are live right now?")
    assert not is_guidance_ask("How much time is left on my exam?")
    assert is_guidance_ask("How do I publish my exam?")
    assert is_guidance_ask("Where is the Results tab?")


# --- 2. tool failure recovery ----------------------------------------------------------


def _failed_execution(code: str = "unavailable") -> ToolExecution:
    spec = get_tool("summarize_live_exam_health")
    selection = ToolSelection(tool=spec, args={}, reason="live_health")
    return ToolExecution(
        selection=selection,
        error_code=code,
        error_message="down",
        system_message="TOOL_ERROR (untrusted; do not invent numbers):\n{}",
    )


def _state(*, live: bool) -> dict:
    ask = "Show me live exam health" if live else "Where is Monitoring in the sidebar?"
    return {
        "raw_user_message": ask,
        "resolved_query": ask,
        "retrieval_query": ask,
        "messages": [SystemMessage(content="identity")],
        "sources_used": ["identity"],
        "understanding_route": "tool" if live else "knowledge",
        "data_need": "live_tool" if live else "knowledge",
        "input_messages": [{"role": "user", "content": ask}],
    }


@pytest.mark.asyncio
async def test_tool_error_on_navigation_ask_recovers_through_knowledge():
    knowledge = AsyncMock()  # sync function patched below; used only to count calls
    del knowledge
    with (
        patch("app.graphs.nodes.execute_selected_tool", AsyncMock(return_value=_failed_execution())),
        patch("app.graphs.nodes.select_knowledge", return_value=_selection([NAV_CHUNK])) as sk,
    ):
        out = await nodes.tools_node(_state(live=False))
    assert sk.call_count == 1
    assert out["tool_fallback"] == "knowledge"
    assert not out.get("direct_reply")
    blob = "\n".join(str(m.content) for m in out["messages"])
    assert "RETRIEVED_DOCUMENT" in blob
    assert "TOOL_ERROR" not in blob  # a tool that was never needed must not pollute the prompt
    assert "tool_fallback:knowledge" in out["sources_used"]


@pytest.mark.asyncio
@pytest.mark.parametrize("code", ["unavailable", "upstream_timeout", "forbidden"])
async def test_tool_error_on_live_ask_never_falls_back_to_docs(code):
    with (
        patch("app.graphs.nodes.execute_selected_tool", AsyncMock(return_value=_failed_execution(code))),
        patch("app.graphs.nodes.select_knowledge", side_effect=AssertionError("docs must not stand in for live data")),
    ):
        out = await nodes.tools_node(_state(live=True))
    reply = out["direct_reply"]
    assert reply and out["tool_fallback"] == "none"
    assert not re.search(r"\d", reply), "a failure reply must not contain numbers"
    assert "tool_error" in out["sources_used"]


@pytest.mark.asyncio
async def test_direct_reply_skips_the_llm():
    state = {**_state(live=True), "direct_reply": "I couldn't reach your live Quizzer data just now."}
    llm = AsyncMock(side_effect=AssertionError("LLM must not be called"))
    with patch("app.graphs.nodes.ainvoke_chat", llm), capture_evidence() as rec:
        out = await nodes.generate_node(state)
    assert llm.await_count == 0
    assert out["model_name"].startswith("deterministic:")
    assert isinstance(out["messages"][-1], AIMessage)
    assert rec["llm_called"] is False


# --- 3/6. evidence reaches the generator, end to end through the real pipeline ----------


def _env(monkeypatch, *, tools: bool) -> None:
    monkeypatch.setenv("QUE_TOOLS_ENABLED", "true" if tools else "false")
    monkeypatch.setenv("QUIZZER_INTERNAL_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("QUE_BUDGET_USD_PER_USER_HOUR", "0")
    get_settings.cache_clear()


def _request(query: str, cid: str, role: str | None = "teacher") -> ChatRequest:
    return ChatRequest(
        messages=[ChatMessage(role="user", content=query)],
        conversation_id=cid,
        user_id="teacher-1",
        context=QueUiContext(user_role=role) if role else None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    ["Where is Monitoring in the sidebar?", "Where do I find the live exam monitor?"],
)
async def test_navigation_ask_reaches_generator_with_kb_evidence(monkeypatch, query):
    _env(monkeypatch, tools=True)
    seen: dict = {}

    async def fake_llm(messages, **_kw):
        seen["messages"] = list(messages)
        return AIMessage(content="Open Exams, then the exam's Monitoring tab."), _LANE

    tool = AsyncMock(side_effect=AssertionError("navigation must not call a live tool"))
    with (
        patch("app.graphs.nodes.ainvoke_chat", fake_llm),
        patch("app.graphs.nodes.select_knowledge", return_value=_selection([NAV_CHUNK])),
        patch("app.tools.executor.invoke_quizzer_tool", tool),
        capture_evidence() as rec,
    ):
        response = await complete(_request(query, f"nav-{abs(hash(query))}"))

    assert tool.await_count == 0
    assert rec["route"]["runtime_mode"] == "knowledge"
    assert rec["route"]["tool"] is None
    docs = rec["generator_context"]["documents"]
    assert docs and "no top-level Monitoring" in docs[0]["text"]  # the negative fact is in the prompt
    prompt = "\n".join(str(m.content) for m in seen["messages"])
    assert "RETRIEVED_DOCUMENT" in prompt
    assert not any(
        str(m.content).startswith(("TOOL_RESULT", "TOOL_ERROR", "TOOL_CLARIFY")) for m in seen["messages"]
    )
    assert "knowledge:live-monitoring" in response.sources_used


@pytest.mark.asyncio
async def test_live_ask_with_failing_tool_answers_deterministically(monkeypatch):
    _env(monkeypatch, tools=True)
    llm = AsyncMock(side_effect=AssertionError("LLM must not paraphrase a tool failure"))
    with (
        patch("app.graphs.nodes.ainvoke_chat", llm),
        patch("app.graphs.nodes.select_knowledge", side_effect=AssertionError("no docs for live data")),
        patch(
            "app.tools.executor.invoke_quizzer_tool",
            AsyncMock(side_effect=ToolClientError("upstream_timeout", "timed out")),
        ),
        capture_evidence() as rec,
    ):
        response = await complete(_request("Show me live exam health", "live-fail-1"))

    assert llm.await_count == 0
    assert response.model.startswith("deterministic:")
    assert not re.search(r"\d", response.message.content)
    assert rec["route"]["tool_error"] == "upstream_timeout"
    assert rec["llm_called"] is False
    assert rec["generator_context"]["documents"] == []


# --- 5. explicit negative KB facts are preserved ----------------------------------------


def test_negative_kb_statements_survive_assembly_and_are_marked_authoritative():
    asm = assemble_selection([NAV_CHUNK], score_label="rrf")
    assert "There is no top-level Monitoring or LIVE item in the sidebar." in asm.content
    text = preamble(no_answer=False).casefold()
    assert "denial" in text and "never contradict" in text


def test_split_documents_recovers_what_was_in_the_prompt():
    asm = assemble_selection([NAV_CHUNK], score_label="rrf")
    docs = split_documents(asm.content)
    assert len(docs) == 1
    assert docs[0]["score"] == pytest.approx(0.82)
    assert "select the Monitoring tab" in docs[0]["text"]


@pytest.mark.skipif(not (ROOT / "knowledge").is_dir(), reason="knowledge/ not present")
def test_kb_never_places_exam_tabs_in_the_sidebar():
    """KB consistency: every doc agrees Monitoring/Results/Links are exam tabs, not sidebar items."""
    bad = re.compile(r"(?<!not )(?<!no )\b(monitoring|results)\b (is|are) (located )?(in|under) the (left )?sidebar", re.I)
    offenders = []
    for path in (ROOT / "knowledge").rglob("*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if bad.search(line) and "not" not in line.casefold() and "no " not in line.casefold():
                offenders.append(f"{path.name}: {line.strip()}")
    assert not offenders, offenders


# --- 4/8. evaluation provenance ----------------------------------------------------------


def test_record_generator_context_separates_documents_and_tool_blocks():
    messages = [
        SystemMessage(content="identity"),
        SystemMessage(content=_selection([NAV_CHUNK]).content),
        SystemMessage(content="TOOL_ERROR (untrusted; do not invent numbers):\n{}"),
        HumanMessage(content="q"),
    ]
    with capture_evidence() as rec:
        record_generator_context({"runtime_mode": "workflow", "tool_error": "unavailable"}, messages)
    ctx = rec["generator_context"]
    assert len(ctx["documents"]) == 1
    assert ctx["tool_blocks"] and ctx["tool_blocks"][0].startswith("TOOL_ERROR")
    assert rec["route"]["tool_error"] == "unavailable"


def test_nothing_is_captured_without_an_open_capture():
    record_generator_context({"runtime_mode": "knowledge"}, [SystemMessage(content="x")])  # must not raise


def test_faithfulness_prompt_uses_generator_context_not_a_second_retrieval():
    import importlib.util
    import sys

    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("run_deepeval_pipeline", ROOT / "scripts" / "run_deepeval_pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    prompts: list[str] = []

    class FakeJudge:
        def generate(self, prompt, schema):
            prompts.append(prompt)
            item = {"score": 1.0, "reason": "ok"}
            return schema.model_validate({k: item for k in mod.METRIC_KEYS})

    mod._judge_combined(
        FakeJudge(),
        "q",
        "ref",
        ["RERUN-CHUNK retrieval only"],
        "answer",
        use_cache=False,
        generator_chunks=["GENERATOR-DOC the model saw"],
    )
    prompt = prompts[0]
    retriever_part, generator_part = prompt.split("Generator context:")
    assert "RERUN-CHUNK" in retriever_part and "RERUN-CHUNK" not in generator_part
    assert "GENERATOR-DOC" in generator_part

    prompts.clear()
    mod._judge_combined(FakeJudge(), "q", "ref", ["x"], "answer", use_cache=False, generator_chunks=[])
    assert "received no retrieved evidence" in prompts[0]


def test_refined_judge_scores_faithfulness_against_generator_chunks():
    from evals import refined_judge as rj

    seen: dict = {}

    def fake_generator_pass(judge, query, claims, chunks, answer):
        seen["gen"] = list(chunks)
        return {}

    def fake_retriever_pass(judge, query, claims, chunks):
        seen["ret"] = list(chunks)
        return {}

    with (
        patch.object(rj, "_retriever_pass", fake_retriever_pass),
        patch.object(rj, "_generator_pass", fake_generator_pass),
        patch.object(rj, "compute_scores", lambda state: {"faithfulness": 1.0}),
        patch.object(rj, "_triggers", lambda state, claims: []),
    ):
        rj.judge_row(None, "q", ["c"], ["retriever chunk"], "a", generator_chunks=["generator chunk"])
        assert seen == {"ret": ["retriever chunk"], "gen": ["generator chunk"]}
        rj.judge_row(None, "q", ["c"], ["same"], "a")
        assert seen["gen"] == ["same"]  # default keeps the old single-list behaviour


@pytest.mark.asyncio
async def test_capture_artifact_records_route_and_evidence(monkeypatch):
    from evals.provenance import capture, evidence_summary, generator_chunks

    _env(monkeypatch, tools=False)

    async def fake_llm(messages, **_kw):
        return AIMessage(content="Open Exams, open the exam, select Monitoring."), _LANE

    with (
        patch("app.graphs.nodes.ainvoke_chat", fake_llm),
        patch("app.graphs.nodes.select_knowledge", return_value=_selection([NAV_CHUNK])),
    ):
        out = await capture("Where is Monitoring in the sidebar?", conversation_id="artifact-1", role="teacher")

    assert out["executed_path"]["runtime_mode"] == "knowledge"
    chunks = generator_chunks(out["evidence"])
    assert chunks and "no top-level Monitoring" in chunks[0]
    summary = evidence_summary(out["evidence"])
    assert summary["retrieved_chunk_ids"] == [NAV_CHUNK.chunk_id]
    assert summary["generator_documents"] and summary["llm_called"] is True
    assert generator_chunks(None) is None and generator_chunks({}) is None  # legacy rows are detectable


# --- graph state must declare every key the pipeline feeds it --------------------------


def test_graph_state_declares_every_input_channel():
    """LangGraph silently drops undeclared input keys (ui_context was one: the role vanished)."""
    from app.graphs.state import QueGraphState
    from app.orchestration.pipeline import _request_to_input
    from app.orchestration.resolve import resolve_request
    from app.orchestration.understanding import classify_request

    request = _request("Where is Monitoring in the sidebar?", "state-keys")
    resolution = resolve_request([m for m in request.messages])
    payload = _request_to_input(
        request,
        resolution=resolution,
        understanding=finalize_understanding(classify_request("x"), "x"),
        request_id="rid",
    )
    undeclared = set(payload) - set(QueGraphState.__annotations__)
    assert not undeclared, undeclared


@pytest.mark.asyncio
async def test_ui_role_reaches_tool_policy_through_the_graph(monkeypatch):
    """A teacher's live ask must be authorised from the request context, not fail as 'forbidden'."""
    _env(monkeypatch, tools=True)
    seen: dict = {}

    async def fake_invoke(**kwargs):
        seen["called"] = True
        raise ToolClientError("upstream_timeout", "timed out")

    with (
        patch("app.graphs.nodes.ainvoke_chat", AsyncMock(side_effect=AssertionError("no llm"))),
        patch("app.tools.executor.invoke_quizzer_tool", fake_invoke),
        capture_evidence() as rec,
    ):
        await complete(_request("Show me live exam health", "role-graph-1", role="teacher"))
    assert seen.get("called") is True
    assert rec["route"]["tool_error"] == "upstream_timeout"


# --- workflow cards answer whole workflows, not facets of them -----------------------------


@pytest.mark.parametrize(
    "query",
    [
        "Negative marking settings",
        "Integrity events and live proctoring",
        "How do I change my exam settings after it's already been published?",
    ],
)
def test_facet_questions_are_not_served_a_generic_card(query):
    u = finalize_understanding(classify_request(query), query)
    assert u.execution_class != "deterministic", (query, u.canonical_intent)


@pytest.mark.parametrize(
    ("query", "intent"),
    [
        ("How do I create a quiz?", "exam.create"),
        ("How do I publish my exam quickly?", "exam.publish"),
        ("How do I share the exam link with students?", "exam.share"),
        ("What are the exam settings?", "exam.settings"),
    ],
)
def test_plain_workflow_questions_still_get_their_card(query, intent):
    u = finalize_understanding(classify_request(query), query)
    assert u.execution_class == "deterministic"
    assert u.canonical_intent == intent


@pytest.mark.parametrize(
    "query",
    [
        "Is the LIVE badge the same as Monitoring?",
        "Is Monitoring different from Results?",
        "What's the difference between Monitoring and Analytics?",
    ],
)
def test_comparison_questions_are_guidance(query):
    assert is_guidance_ask(query)
    mode, _reason, _sel = _mode(query)
    assert mode == "knowledge"
