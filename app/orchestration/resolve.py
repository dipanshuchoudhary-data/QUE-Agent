"""Conversational request resolution — rewrite follow-ups into full Quizzer asks.

Runs *before* scope/intent routing so short continuations like
\"yes explain step by step\" are not refused as out-of-scope.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.orchestration.understanding import _has_quizzer_hint, is_hard_out_of_scope
from app.schemas.chat import ChatMessage

ResponseMode = Literal[
    "brief",
    "normal",
    "detailed",
    "step_by_step",
    "example",
    "comparison",
    "troubleshooting",
    "summary",
]

ResolveIntent = Literal[
    "explanation",
    "how_to",
    "follow_up",
    "troubleshooting",
    "comparison",
    "example",
    "clarification",
    "summary",
    "general_product_question",
    "tool_request",
    "out_of_scope",
]


class ResolvedRequest(BaseModel):
    """Structured outcome of the conversation resolver."""

    raw_message: str
    resolved_query: str
    is_follow_up: bool = False
    topic: str | None = None
    intent: ResolveIntent = "general_product_question"
    response_mode: ResponseMode = "normal"
    prior_user_message: str | None = None
    prior_assistant_summary: str | None = None
    thread_active: bool = False
    reasons: tuple[str, ...] = ()

    def as_log_dict(self) -> dict[str, Any]:
        return self.model_dump()


# Short continuations that only make sense with prior context.
_FOLLOW_UP_EXACT: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"^(yes|yeah|yep|yup|sure|ok|okay|please)([,.!]|\s|$)",
        r"^(explain more|more detail|more details|go deeper|tell me more|elaborate)([.!?]|\s|$)",
        r"^(explain|show|tell)\s+(me\s+)?(step[- ]?by[- ]?step|in steps)([.!?]|\s|$)",
        r"^(step[- ]?by[- ]?step|in steps)([.!?]|\s|$)",
        r"^(give|show)\s+(me\s+)?(an\s+)?example([.!?]|\s|$)",
        r"^(for example|show me|demonstrate)([.!?]|\s|$)",
        r"^(explain\s+)?(it|this|that)?\s*(simply|simpler|briefly|in detail|in brief)([.!?]|\s|$)",
        r"^(keep it )?(short|brief|simple)([.!?]|\s|$)",
        r"^(in\s+)?simple(\s+language|\s+words|\s+terms)?([.!?]|\s|$)",
        r"^(make it )?(simpler|easier|simpler to (read|understand)|plain(er)?( english)?)([.!?]|\s|$)",
        r"^(eli5|like i'?m (five|5)|for beginners|in plain english)([.!?]|\s|$)",
        r"^(shorter|longer|again|rephrase|reword|rewrite)([.!?]|\s|$)",
        r"^(what about|how about|and what about)\b",
        r"^(what if|and if)\b",
        # Bare "why?" / "how?" only — not "how many exams…" / "how do I publish"
        r"^(why|how)\s*\??$",
        r"^(can i|is it possible)\s*\??$",
        r"^(and|also|then)\b.{0,80}$",
        r"^(continue|go on|next|more)([.!?]|\s|$)",
        r"^(same for|now for|now about|now tell me about)\b",
        # List / ordinal continuations ("first", "the second one", "explain one by one")
        r"^(the\s+)?(first|second|third|fourth|fifth|last|1st|2nd|3rd|4th|5th)(\s+one)?([.!?]|\s|$)",
        r"^(explain|tell me about|describe|cover|start with)\s+(the\s+)?"
        r"(first|second|third|fourth|fifth|last|1st|2nd|3rd|4th|5th)(\s+one)?([.!?]|\s|$)",
        r"^#?\d{1,2}([.!?]|\s|$)",
        r"^(explain\s+)?(them\s+)?(one by one|each one|one at a time|separately)([.!?]|\s|$)",
        r"^(go through|walk through)\s+(them|each|each one)([.!?]|\s|$)",
        r"\bwhich (exam|quiz|one)\b",
        r"\bwhat (was|is) my (first|last|original|starting|previous) (query|question|message|ask)\b",
        r"\b(starting message|first (query|question|message))\b",
        r"\bwhat did i (just )?(ask|say|type)\b",
        r"\bwhat were we talking about\b",
        r"\bi('m| am) talking about\b",
    )
)

_ORDINAL_WORDS: dict[str, int] = {
    "first": 1,
    "1st": 1,
    "one": 1,
    "second": 2,
    "2nd": 2,
    "two": 2,
    "third": 3,
    "3rd": 3,
    "three": 3,
    "fourth": 4,
    "4th": 4,
    "four": 4,
    "fifth": 5,
    "5th": 5,
    "five": 5,
}

_ORDINAL_RE = re.compile(
    r"^(?:explain|tell me about|describe|cover|start with)?\s*"
    r"(?:the\s+)?"
    r"(?P<word>first|second|third|fourth|fifth|last|1st|2nd|3rd|4th|5th|"
    r"one|two|three|four|five)"
    r"(?:\s+one)?\s*[.!]?\s*$",
    re.I,
)
_NUM_ORDINAL_RE = re.compile(r"^#?(?P<num>\d{1,2})\s*[.!]?\s*$")
_ONE_BY_ONE_RE = re.compile(
    r"\b(one by one|each one|one at a time|separately|go through them|walk through them)\b",
    re.I,
)

_STEP_BY_STEP = re.compile(r"\bstep[- ]?by[- ]?step\b|\bin steps\b|\bwalk me through\b", re.I)
_EXAMPLE = re.compile(r"\b(give|show)\b.*\bexample\b|\bfor example\b|\bdemonstrate\b", re.I)
_MORE = re.compile(r"\b(explain more|more detail|elaborate|go deeper|tell me more)\b", re.I)
_BRIEF = re.compile(
    r"\b(briefly|in brief|keep it short|keep it brief|simply|simpler|"
    r"in simple language|in simple words|in simple terms|simple language|"
    r"plain english|eli5|like i'?m (five|5)|for beginners)\b",
    re.I,
)
_DETAILED = re.compile(r"\b(in detail|more thoroughly|detailed)\b", re.I)
_WHAT_ABOUT = re.compile(r"^(?:yes[,.]?\s*)?(?:what|how)\s+about\s+(.+?)([.!?]|$)", re.I)
_NOW_ABOUT = re.compile(
    r"^(?:now\s+)?(?:tell me about|same for|now for|now about)\s+(.+?)([.!?]|$)",
    re.I,
)
_WHAT_IF = re.compile(r"^(?:and\s+)?what if\s+(.+?)([.!?]|$)", re.I)
_YES_PREFIX = re.compile(r"^(yes|yeah|yep|yup|sure|ok|okay|please)[,.!]?\s*", re.I)

_HELP_PREFIX = re.compile(
    r"^(help me|help with|can you|could you|please|i want to|i need to|how do i|how to|how can i)\s+",
    re.I,
)


def _norm(text: str) -> str:
    cleaned = (text or "").casefold().strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _looks_like_follow_up(
    text: str,
    *,
    prior: str | None = None,
    thread_active: bool = False,
) -> bool:
    """Detect continuations. Prefer explicit patterns; else short asks after Quizzer prior."""
    n = _norm(text)
    if not n:
        return False
    # Explicit topic switch to non-Quizzer is never a follow-up.
    if is_hard_out_of_scope(text):
        return False
    # Greetings / thanks are their own turns (canned), not product follow-ups.
    if re.match(r"^(hi|hello|hey|yo|thanks|thank you|thx)\b", n):
        return False
    if _is_conversation_meta(text) and thread_active:
        return True
    # Fresh product / live-data asks are standalone even mid-thread.
    if _looks_like_new_topic_ask(text):
        return False
    if len(n) > 160 and not _YES_PREFIX.match(n):
        return False
    if any(p.search(n) for p in _FOLLOW_UP_EXACT):
        return True
    if _STEP_BY_STEP.search(n) and len(n) < 100:
        return True
    if _BRIEF.search(n) and len(n) < 80:
        return True
    if _ONE_BY_ONE_RE.search(n) and len(n) < 100:
        return True
    # Immediate prior was a Quizzer ask → short continuation stays attached.
    if prior and len(n) <= 120 and _prior_is_quizzer_context(prior):
        return True
    # Earlier in-thread Quizzer topic, but immediate prior was style-only
    # (e.g. "explain one by one" then "first") — still a continuation.
    if thread_active and len(n) <= 120 and _is_style_or_ordinal_only(text):
        return True
    return False


def _prior_is_quizzer_context(prior: str) -> bool:
    n = _norm(prior)
    if _has_quizzer_hint(n):
        return True
    return _infer_topic(prior) is not None


def _is_style_or_ordinal_only(text: str) -> bool:
    """True when a user turn is only a style / list continuation, not a topic ask."""
    n = _norm(text)
    if not n:
        return True
    if _prior_is_quizzer_context(text):
        return False
    if _ORDINAL_RE.match(n) or _NUM_ORDINAL_RE.match(n):
        return True
    if _ONE_BY_ONE_RE.search(n) and len(n) < 80:
        return True
    if any(p.search(n) for p in _FOLLOW_UP_EXACT) and len(n) < 80:
        return True
    if _BRIEF.search(n) and len(n) < 80:
        return True
    if _STEP_BY_STEP.search(n) and len(n) < 80:
        return True
    return False


def _thread_has_quizzer_context(messages: list[ChatMessage]) -> bool:
    """True if any earlier user turn established a Quizzer topic."""
    users = [m.content.strip() for m in messages if m.role == "user" and m.content.strip()]
    if len(users) < 2:
        return False
    return any(_prior_is_quizzer_context(u) for u in users[:-1])


def _find_topic_anchor(messages: list[ChatMessage]) -> str | None:
    """Walk back user turns (skip current) to the last Quizzer topic ask.

    Style-only / ordinal turns like \"in simple language\" or \"first\" are skipped
    so follow-ups keep resolving against the real product question.
    """
    users = [m.content.strip() for m in messages if m.role == "user" and m.content.strip()]
    if len(users) < 2:
        return None
    for prior in reversed(users[:-1]):
        if _prior_is_quizzer_context(prior):
            return prior
    # Fall back to immediate prior even if style-only (compose still needs something).
    return users[-2]


def _nth_listed_item(assistant: str | None, n: int) -> str | None:
    """Pull the Nth bold / numbered label from the last assistant reply."""
    if not assistant or n < 1:
        return None
    bold = re.findall(r"\*\*([^*]+)\*\*", assistant)
    # Prefer bold labels that look like product terms (skip tiny words).
    items = [b.strip() for b in bold if len(b.strip()) >= 3]
    if not items:
        numbered = re.findall(
            r"(?m)^\s*\d+[.)]\s+(?:\*\*)?([^*\n:]+?)(?:\*\*)?\s*:",
            assistant,
        )
        items = [x.strip() for x in numbered if x.strip()]
    if n == -1 and items:
        return items[-1]
    if 1 <= n <= len(items):
        return items[n - 1]
    return None


def _parse_ordinal(raw: str) -> int | None:
    n = _norm(raw)
    m = _ORDINAL_RE.match(n)
    if m:
        word = m.group("word").casefold()
        if word == "last":
            return -1
        return _ORDINAL_WORDS.get(word)
    m2 = _NUM_ORDINAL_RE.match(n)
    if m2:
        return int(m2.group("num"))
    return None


def _anchor_phrase(prior: str) -> str:
    """Turn a prior user ask into a compact topic phrase."""
    text = (prior or "").strip()
    text = _HELP_PREFIX.sub("", text).strip()
    text = text.rstrip("?.! ").strip()
    # Common typos / shorthand → product terms for retrieval + scope.
    text = re.sub(r"\bcalender\b", "calendar", text, flags=re.I)
    text = re.sub(r"\bdashbaord\b", "dashboard", text, flags=re.I)
    text = re.sub(r"\bexplain\s+", "", text, count=1, flags=re.I).strip() or text
    if not text:
        return (prior or "").strip()
    lower = text.casefold()
    # Expand bare "calendar" / "classroom" asks into Quizzer integration phrasing.
    if re.fullmatch(r"(google\s+)?calendar(\s+one)?(\s+step[- ]?by[- ]?step)?", lower):
        return "how Google Calendar integration works in Quizzer"
    if "calendar" in lower and "quizzer" not in lower and "integrat" not in lower:
        text = re.sub(
            r"\b(google\s+)?calendar\b",
            "Google Calendar integration in Quizzer",
            text,
            count=1,
            flags=re.I,
        )
    if lower.startswith(("create ", "publish ", "configure ", "share ", "monitor ")):
        return f"how to {text}"
    if lower.startswith("how "):
        return text
    return text


def _infer_topic(anchor: str) -> str | None:
    n = _norm(anchor)
    if "creat" in n and ("exam" in n or "quiz" in n or "assessment" in n):
        return "exam_creation" if "exam" in n else "quiz_creation"
    if "publish" in n or "share" in n:
        return "publishing"
    if "score" in n or "grad" in n or "mark" in n:
        return "scoring"
    if "attempt" in n:
        return "attempts"
    if "monitor" in n or "proctor" in n or "live" in n:
        return "monitoring"
    if "result" in n or "analytics" in n:
        return "results"
    if "feedback" in n or ("bug" in n and "report" in n) or "feature request" in n:
        return "feedback"
    if "setting" in n:
        return "exam_settings"
    if "arena" in n:
        return "arena"
    if "dashboard" in n or "metric" in n or "kpi" in n:
        return "dashboard"
    if "integrat" in n or "classroom" in n or "drive" in n or "calendar" in n or "calender" in n:
        return "integrations"
    if "exam" in n:
        return "exams"
    if "quiz" in n:
        return "quizzes"
    return None


_NEW_TOPIC_ASK = re.compile(
    r"\b("
    r"how (do|to|can|many) i?\b|how does\b|where (is|do|can)\b|what is (a|an|the)\b|"
    r"how many\b|count (my|the)?\b|"
    r"report (a )?bug|send feedback|contact support|feature request|"
    r"explain\b|help me\b"
    r")",
    re.I,
)

_CONVO_META_RE = re.compile(
    r"\b("
    r"what (was|is) my (first|last|original|starting|previous) (query|question|message|ask)|"
    r"what did i (just )?(ask|say|type)|"
    r"starting message|first (query|question|message)|"
    r"which (exam|quiz|one)|"
    r"what were we talking about|"
    r"i('m| am) talking about"
    r")\b",
    re.I,
)


def is_conversation_meta(text: str) -> bool:
    """True when the user is asking about this chat, not a new product topic."""
    return bool(_CONVO_META_RE.search(_norm(text)))


def _is_conversation_meta(text: str) -> bool:
    return is_conversation_meta(text)


def _looks_like_new_topic_ask(text: str) -> bool:
    """True when the user starts a fresh product ask mid-thread (not style/ordinal)."""
    n = _norm(text)
    if len(n) < 10 or len(n) > 160:
        return False
    if _is_conversation_meta(text):
        return False
    if _is_style_or_ordinal_only(text):
        return False
    if is_hard_out_of_scope(text):
        return False
    return bool(_NEW_TOPIC_ASK.search(n))


def _prior_user_message(messages: list[ChatMessage]) -> str | None:
    users = [m.content.strip() for m in messages if m.role == "user" and m.content.strip()]
    if len(users) < 2:
        return None
    return users[-2]


def _prior_assistant_snippet(messages: list[ChatMessage], *, limit: int = 900) -> str | None:
    assistants = [
        m.content.strip() for m in messages if m.role == "assistant" and m.content.strip()
    ]
    if not assistants:
        return None
    text = assistants[-1]
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _detect_mode(raw: str) -> ResponseMode:
    if _STEP_BY_STEP.search(raw):
        return "step_by_step"
    if _EXAMPLE.search(raw):
        return "example"
    if _BRIEF.search(raw):
        return "brief"
    if _DETAILED.search(raw) or _MORE.search(raw):
        return "detailed"
    if re.search(r"\bcompare\b|\bversus\b|\bvs\.?\b|\bdifference\b", raw, re.I):
        return "comparison"
    if re.search(r"\b(fix|troubleshoot|not working|broken|empty)\b", raw, re.I):
        return "troubleshooting"
    if re.search(r"\b(summarize|summary|tldr|tl;dr)\b", raw, re.I):
        return "summary"
    return "normal"


def _detect_intent(raw: str, *, is_follow_up: bool, mode: ResponseMode) -> ResolveIntent:
    if mode == "example":
        return "example"
    if mode == "comparison":
        return "comparison"
    if mode == "troubleshooting":
        return "troubleshooting"
    if mode == "summary":
        return "summary"
    if mode == "step_by_step" or re.search(r"\bhow (do|to|can) i\b|\bhelp me\b", raw, re.I):
        return "follow_up" if is_follow_up else "how_to"
    if is_follow_up:
        return "follow_up"
    if re.search(r"\bwhat is\b|\bexplain\b|\bmean\b", raw, re.I):
        return "explanation"
    return "general_product_question"


def _compose_resolved(
    raw: str,
    *,
    prior: str,
    mode: ResponseMode,
    assistant_summary: str | None = None,
) -> str:
    anchor = _anchor_phrase(prior)
    stripped = _YES_PREFIX.sub("", raw).strip() or raw.strip()

    about = _WHAT_ABOUT.match(stripped) or _NOW_ABOUT.match(stripped)
    if about:
        subject = about.group(1).strip().rstrip("?.!")
        return f"How does {subject} work in Quizzer, in relation to {anchor}?"

    what_if = _WHAT_IF.match(stripped)
    if what_if:
        cond = what_if.group(1).strip().rstrip("?.!")
        return f"For {anchor}: what happens if {cond}?"

    ordinal = _parse_ordinal(stripped)
    if ordinal is not None:
        item = _nth_listed_item(assistant_summary, ordinal)
        if item:
            return f"Explain {item} in Quizzer in more detail (from: {anchor})"
        label = "last" if ordinal == -1 else f"#{ordinal}"
        return f"Explain the {label} item from the previous answer about {anchor}"

    if _ONE_BY_ONE_RE.search(stripped):
        return (
            f"Explain each part of {anchor} one by one, "
            "starting with the first item from the previous answer"
        )

    if mode == "step_by_step":
        if re.search(r"^how\b", anchor, re.I):
            return f"{anchor} — explain step by step"
        return f"Explain {anchor} step by step"

    if mode == "example":
        return f"Give a concrete Quizzer example for: {anchor}"

    if mode == "brief":
        if re.search(r"simple language|simple words|simple terms|plain english|eli5", raw, re.I):
            return f"Explain in simple language: {anchor}"
        return f"Briefly explain: {anchor}"

    if mode == "detailed" or _MORE.search(raw):
        return f"Explain in more detail: {anchor}"

    if re.fullmatch(r"why\??", _norm(stripped)):
        return f"Why does this matter / why is it done this way for: {anchor}?"

    if re.fullmatch(r"how\??", _norm(stripped)):
        return f"How does this work for: {anchor}?"

    if re.match(r"^(can i|is it possible)\b", stripped, re.I):
        return f"Regarding {anchor}: {stripped}"

    # Generic short continuation — attach to prior ask.
    if len(stripped) < 80:
        return f"{anchor} — {stripped}"

    return stripped


def resolve_request(
    messages: list[ChatMessage],
    *,
    prior_topic: str | None = None,
    prior_task: str | None = None,
    previous_intent: str | None = None,
) -> ResolvedRequest:
    """Resolve the latest user turn against recent conversation context."""
    users = [m for m in messages if m.role == "user" and (m.content or "").strip()]
    raw = users[-1].content.strip() if users else ""
    if not raw:
        return ResolvedRequest(
            raw_message="",
            resolved_query="",
            intent="clarification",
            response_mode="normal",
            reasons=("empty_message",),
        )

    immediate_prior = _prior_user_message(messages)
    if not immediate_prior and prior_task:
        immediate_prior = prior_task
    anchor = _find_topic_anchor(messages) or immediate_prior or prior_task
    thread_active = _thread_has_quizzer_context(messages) or bool(
        prior_task and _prior_is_quizzer_context(prior_task)
    )
    assistant_snip = _prior_assistant_snippet(messages)
    mode = _detect_mode(raw)
    is_follow = bool(anchor) and _looks_like_follow_up(
        raw,
        prior=immediate_prior or anchor,
        thread_active=thread_active,
    )
    reasons: list[str] = []

    if is_follow:
        reasons.append("follow_up_pattern")
        if thread_active and immediate_prior and _is_style_or_ordinal_only(immediate_prior or ""):
            reasons.append("anchor_walkback")
        # Fresh how-to / where-is mid-thread should not stay glued to the old topic
        # (e.g. "how to report a bug" after an analytics question).
        if _looks_like_new_topic_ask(raw):
            resolved = raw.strip()
            topic = _infer_topic(raw) or _infer_topic(resolved) or prior_topic or previous_intent
            reasons.append("new_topic_override")
        elif _is_conversation_meta(raw):
            # Keep the chat-history question intact — do not rewrite it into a how-to.
            resolved = raw.strip()
            topic = _infer_topic(anchor or "") or prior_topic or previous_intent
            reasons.append("conversation_meta")
        else:
            resolved = _compose_resolved(
                raw,
                prior=anchor or "",
                mode=mode,
                assistant_summary=assistant_snip,
            )
            topic = (
                _infer_topic(resolved)
                or _infer_topic(anchor or "")
                or prior_topic
                or previous_intent
            )
        intent = _detect_intent(raw, is_follow_up=True, mode=mode)
        reasons.append("resolved_against_prior")
        return ResolvedRequest(
            raw_message=raw,
            resolved_query=resolved,
            is_follow_up=True,
            topic=topic,
            intent=intent,
            response_mode=mode,
            prior_user_message=anchor or immediate_prior,
            prior_assistant_summary=assistant_snip,
            thread_active=thread_active,
            reasons=tuple(reasons),
        )

    # Standalone turn — may still set response mode from phrasing.
    topic = _infer_topic(raw) or prior_topic or previous_intent
    intent = _detect_intent(raw, is_follow_up=False, mode=mode)
    if mode != "normal":
        reasons.append(f"mode:{mode}")
    reasons.append("standalone")
    return ResolvedRequest(
        raw_message=raw,
        resolved_query=raw,
        is_follow_up=False,
        topic=topic,
        intent=intent,
        response_mode=mode,
        prior_user_message=immediate_prior,
        prior_assistant_summary=assistant_snip,
        thread_active=thread_active,
        reasons=tuple(reasons),
    )


def build_turn_instruction(resolution: ResolvedRequest) -> str:
    """Compact structured turn state for the generator (one copy only)."""
    lines = [
        "TURN_STATE (answer THIS ask):",
        f"resolved_ask: {resolution.resolved_query}",
        f"intent: {resolution.intent}",
        f"response_mode: {resolution.response_mode}",
        f"follow_up: {str(resolution.is_follow_up).lower()}",
    ]
    if resolution.topic:
        lines.append(f"topic: {resolution.topic}")
    if "new_topic_override" in resolution.reasons:
        lines.append("note: user switched topics — answer the new ask")
    if _is_conversation_meta(resolution.raw_message):
        lines.append("note: answer from this chat's messages (conversation meta)")

    mode = resolution.response_mode
    if mode == "step_by_step":
        lines.append("format: numbered steps 1. 2. 3.; bold UI labels")
    elif mode == "example":
        lines.append("format: one concrete Quizzer example")
    elif mode == "brief":
        lines.append("format: 2–5 short plain sentences")
    elif mode == "detailed":
        lines.append("format: fuller how-to; bold key UI labels")
    elif mode == "comparison":
        lines.append("format: clear comparison; bold product terms")
    elif mode == "troubleshooting":
        lines.append("format: likely cause first, then UI checks")
    return "\n".join(lines)
