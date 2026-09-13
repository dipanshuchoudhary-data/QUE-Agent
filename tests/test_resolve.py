"""Conversational request resolution tests."""

from __future__ import annotations

from tests.conftest import requires_knowledge

from app.knowledge.retrieve import select_knowledge
from app.orchestration.pipeline import decide_turn
from app.orchestration.resolve import resolve_request
from app.orchestration.understanding import classify_request
from app.schemas.chat import ChatMessage, ChatRequest


def _msgs(*pairs: tuple[str, str]) -> list[ChatMessage]:
    return [ChatMessage(role=role, content=text) for role, text in pairs]  # type: ignore[arg-type]


def test_resolve_step_by_step_follow_up():
    messages = _msgs(
        ("user", "Help me create an exam"),
        ("assistant", "Click Create Exam and follow the wizard."),
        ("user", "yes explain step by step"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert resolved.response_mode == "step_by_step"
    assert "exam" in resolved.resolved_query.casefold()
    assert "step" in resolved.resolved_query.casefold()
    u = classify_request(resolved.resolved_query)
    assert u.scope == "in_scope"
    assert u.route == "knowledge"


def test_decide_turn_does_not_refuse_follow_up():
    request = ChatRequest(
        messages=[
            {"role": "user", "content": "Help me create an exam"},
            {
                "role": "assistant",
                "content": "Open Create Exam and walk through the wizard.",
            },
            {"role": "user", "content": "yes explain step by step"},
        ],
        conversation_id="c-follow-1",
    )
    decision = decide_turn(request)
    assert decision.understanding.route == "knowledge"
    assert decision.resolution.is_follow_up is True
    assert (decision.early_model or "") != "scope:refuse"


def test_resolve_give_example():
    messages = _msgs(
        ("user", "How does scoring work?"),
        ("assistant", "Scoring uses marks and optional negative marking."),
        ("user", "Give me an example"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert resolved.response_mode == "example"
    assert "scor" in resolved.resolved_query.casefold()


def test_resolve_what_about():
    messages = _msgs(
        ("user", "How do I create an exam?"),
        ("assistant", "Use Create Exam."),
        ("user", "What about quizzes?"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert "quiz" in resolved.resolved_query.casefold()


def test_resolve_what_if_attempts():
    messages = _msgs(
        ("user", "How do I configure exam attempts?"),
        ("assistant", "Open exam settings and set attempts."),
        ("user", "What if I allow 3?"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert "3" in resolved.resolved_query or "three" in resolved.resolved_query.casefold()
    assert "attempt" in resolved.resolved_query.casefold()


def test_out_of_scope_still_refused():
    request = ChatRequest(
        messages=[
            {"role": "user", "content": "How do I create an exam?"},
            {"role": "assistant", "content": "Use Create Exam."},
            {"role": "user", "content": "What's the weather today?"},
        ],
        conversation_id="c-oos",
    )
    decision = decide_turn(request)
    assert decision.understanding.route == "refuse"
    assert decision.early_reply and "Quizzer" in decision.early_reply


@requires_knowledge
def test_rag_uses_resolved_query_not_raw_follow_up():
    messages = _msgs(
        ("user", "Help me create an exam"),
        ("assistant", "Start with Create Exam."),
        ("user", "yes explain step by step"),
    )
    resolved = resolve_request(messages)
    bad = select_knowledge([{"role": m.role, "content": m.content} for m in messages])
    good = select_knowledge(
        [{"role": m.role, "content": m.content} for m in messages],
        query=resolved.resolved_query,
    )
    assert good.pack_ids
    assert "creating-exams" in good.pack_ids or "core" in good.pack_ids
    assert resolved.resolved_query != messages[-1].content
    assert bad.pack_ids
    assert sum(good.scores.values()) >= sum(bad.scores.values())


def test_new_conversation_does_not_inherit_prior_messages():
    first = resolve_request(_msgs(("user", "Help me create an exam")))
    second = resolve_request(_msgs(("user", "make it clearer")))
    assert first.is_follow_up is False
    assert second.is_follow_up is False
    # Cold start of a style-only phrase with no prior → refuse.
    assert classify_request(second.resolved_query).route == "refuse"
    decision = decide_turn(
        ChatRequest(messages=[{"role": "user", "content": "make it clearer"}])
    )
    assert decision.understanding.route == "refuse"


def test_in_simple_language_follow_up_calendar():
    messages = _msgs(
        ("user", "Explain integrations"),
        (
            "assistant",
            "Integrations connect Google Classroom, Calendar, and Drive.",
        ),
        ("user", "explain calender one step by step"),
        ("assistant", "1. Open Integrations..."),
        ("user", "in simple language"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert resolved.response_mode == "brief"
    assert "calender" in resolved.resolved_query.casefold() or "calendar" in resolved.resolved_query.casefold()
    assert "simple" in resolved.resolved_query.casefold()
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-simple",
        )
    )
    assert decision.early_reply is None
    assert decision.understanding.route == "knowledge"


def test_short_follow_up_defaults_in_scope_without_keyword_patch():
    """Any short continuation after a Quizzer prior should not hit scope:refuse."""
    messages = _msgs(
        ("user", "How do I publish an exam?"),
        ("assistant", "Use the Links tab Publish button."),
        ("user", "make it clearer"),
    )
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-clearer",
        )
    )
    assert decision.understanding.route == "knowledge"
    assert decision.early_model != "scope:refuse"
    assert decision.resolution.is_follow_up is True


def test_weather_mid_conversation_still_refused():
    messages = _msgs(
        ("user", "How do I create an exam?"),
        ("assistant", "Open Create Exam."),
        ("user", "What's the weather today?"),
    )
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-weather",
        )
    )
    assert decision.understanding.route == "refuse"
    assert decision.early_reply and "Quizzer" in decision.early_reply


def test_ordinal_first_after_integration_list():
    """'first' must resolve to Google Classroom, not refuse mid-thread."""
    messages = _msgs(
        ("user", "Explain Integrations (especially calendar)"),
        (
            "assistant",
            "**Integrations** connect tools.\n"
            "- **Google Classroom**: Import courses.\n"
            "- **Google Calendar**: Schedule exams.\n"
            "- **Google Drive**: Import files.",
        ),
        ("user", "explain in more simple lang"),
        (
            "assistant",
            "**Integrations** help connect tools.\n"
            "- **Google Classroom**: Bring in classes.\n"
            "- **Google Calendar**: Set exam events.\n"
            "- **Google Drive**: Upload files.",
        ),
        ("user", "explain one by one"),
        (
            "assistant",
            "1. **Google Classroom**: Import courses and rosters.\n"
            "2. **Google Calendar**: Schedule exam events.\n"
            "3. **Google Drive**: Import source files.",
        ),
        ("user", "first"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert "classroom" in resolved.resolved_query.casefold()
    assert "integrat" in (resolved.topic or "")
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-first",
        )
    )
    assert decision.early_reply is None
    assert decision.understanding.route == "knowledge"


def test_one_by_one_walks_back_to_integrations_anchor():
    messages = _msgs(
        ("user", "Explain Integrations"),
        ("assistant", "Classroom, Calendar, Drive."),
        ("user", "explain in more simple lang"),
        ("assistant", "Simple overview of the three."),
        ("user", "explain one by one"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is True
    assert "integrat" in resolved.resolved_query.casefold()
    assert "one by one" in resolved.resolved_query.casefold()
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-obo",
        )
    )
    assert decision.understanding.route == "knowledge"


def test_new_topic_bug_report_not_glued_to_prior():
    messages = _msgs(
        ("user", "How do I analyze exam results in Quizzer?"),
        ("assistant", "Open Analytics or the exam Results tab."),
        ("user", "how to report a bug"),
    )
    resolved = resolve_request(messages)
    assert resolved.is_follow_up is False
    assert "report" in resolved.resolved_query.casefold()
    assert "analyze" not in resolved.resolved_query.casefold()
    assert resolved.topic == "feedback"
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-bug",
        )
    )
    assert decision.understanding.route == "knowledge"
    assert decision.early_reply is None
    from app.knowledge import knowledge_available
    from app.knowledge.retrieve import select_knowledge

    if knowledge_available():
        packs = select_knowledge(
            [{"role": m.role, "content": m.content} for m in messages],
            query=resolved.resolved_query,
        )
        assert "feedback" in packs.pack_ids


def test_dashboard_metrics_cold_start_not_refused():
    decision = decide_turn(
        ChatRequest(
            messages=[
                {
                    "role": "user",
                    "content": "I want to ask about my metrics numbers of my Dashbaord",
                }
            ],
            conversation_id="c-dash-metrics",
        )
    )
    assert decision.understanding.scope == "in_scope"
    assert decision.understanding.route != "refuse"
    assert decision.early_model != "scope:refuse"


def test_follow_up_after_dashboard_refuse_stays_in_scope():
    """A prior refuse must not lock the rest of the chat to out-of-scope."""
    messages = _msgs(
        ("user", "I want to ask about my Dashbaord"),
        (
            "assistant",
            "I only help with Quizzer — creating quizzes, exams, monitoring, and results.",
        ),
        ("user", "I want to ask about my metrics numbers of my Dashbaord"),
    )
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-dash-follow",
        )
    )
    assert decision.understanding.scope == "in_scope"
    assert decision.understanding.route != "refuse"
    assert decision.early_model != "scope:refuse"


def test_exam_thread_first_query_is_not_refused():
    """After a named-exam thread, chat-history asks must reach the model."""
    messages = _msgs(
        ("user", "Did you see one exam maded by me ,AI vs ML"),
        (
            "assistant",
            "I can see your exam titled AI vs ML, which is currently PUBLISHED.",
        ),
        ("user", "How to chnage the verification schema of this exam"),
        ("assistant", "Open Exams, then Settings, then Verification Schema."),
        ("user", "How to enhance the experince of mine on this website"),
        ("assistant", "Explore Create Exam, review questions, then check Analytics."),
        ("user", "what is my first query ?,starting message tell me"),
    )
    resolved = resolve_request(messages)
    assert resolved.thread_active is True
    assert resolved.is_follow_up is True
    assert "conversation_meta" in resolved.reasons
    assert "first query" in resolved.resolved_query.casefold()
    assert "verification" not in resolved.resolved_query.casefold()

    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-exam-memory",
        )
    )
    assert decision.early_reply is None
    assert decision.early_model != "scope:refuse"
    assert decision.understanding.scope == "in_scope"
    assert decision.understanding.route != "refuse"


def test_which_exam_after_generic_mid_thread_stays_in_scope():
    messages = _msgs(
        ("user", "Did you see one exam maded by me ,AI vs ML"),
        (
            "assistant",
            "I can see your exam titled AI vs ML, which is currently PUBLISHED.",
        ),
        ("user", "How to enhance the experince of mine on this website"),
        ("assistant", "Use Create Exam and Analytics."),
        ("user", "I am talking about one exam ,which one ?"),
    )
    resolved = resolve_request(messages)
    assert resolved.thread_active is True
    assert resolved.is_follow_up is True
    decision = decide_turn(
        ChatRequest(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            conversation_id="c-which-exam",
        )
    )
    assert decision.early_model != "scope:refuse"
    assert decision.understanding.scope == "in_scope"
