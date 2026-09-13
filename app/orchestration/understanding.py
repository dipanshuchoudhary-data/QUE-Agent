"""Request Understanding — classify each turn before RAG / tools / LLM.

Phase 1 foundation (handbook): scope, intent, risk, freshness, data need,
and complexity. Rule-based and cheap so every later router can read one object
instead of re-parsing the user text.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace
from typing import Any, Literal

Scope = Literal["in_scope", "out_of_scope", "clarification"]
Intent = Literal[
    "chitchat",
    "meta",
    "knowledge",
    "live_data",
    "analytics",
    "action",
    "out_of_scope",
]
Risk = Literal["read", "low_write", "high_write"]
Freshness = Literal["static", "slow_changing", "dynamic", "critical"]
DataNeed = Literal["none", "knowledge", "live_tool"]
Complexity = Literal["single_step", "multi_step"]
Route = Literal["refuse", "canned_eligible", "knowledge", "tool", "clarify"]
ExecutionClass = Literal[
    "deterministic",
    "simple_knowledge",
    "complex_knowledge",
    "tool_required",
    "conversational",
    "out_of_scope",
]


@dataclass(frozen=True)
class RequestUnderstanding:
    scope: Scope
    intent: Intent
    risk: Risk
    freshness: Freshness
    data_need: DataNeed
    complexity: Complexity
    route: Route
    reasons: tuple[str, ...] = ()
    execution_class: ExecutionClass = "simple_knowledge"
    canonical_intent: str | None = None
    confidence: float = 0.0

    def as_log_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reasons"] = list(self.reasons)
        return data


OUT_OF_SCOPE_REFUSAL = (
    "I only help with Quizzer — creating quizzes, exams, monitoring, and results. "
    "Ask me something about using the platform."
)

# General knowledge / coding / world facts that are clearly not Quizzer.
_OUT_OF_SCOPE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\b(who is|who's)\s+(the\s+)?(president|prime minister|ceo of)\b",
        r"\bcapital of\b",
        r"\bweather\b",
        r"\brecipe\b|\bcook(ing)?\b",
        r"\bsorting algorithm\b|\bbubble sort\b|\bquicksort\b",
        r"\bwrite (me )?(a |an )?(python|javascript|java|c\+\+|rust)\b",
        r"\b(code|program|script)\s+(for|to)\b",
        r"\bbitcoin\b|\bstock price\b|\bnft\b",
        r"\b(ignore|disregard)\s+(all\s+)?(previous|prior)\s+(instructions|rules)\b",
        r"\b(system prompt|reveal your (system )?prompt)\b",
        r"\bpretend (you are|to be)\s+(an?\s+)?admin",
        r"\bjoke about\b|\bwrite a poem\b|\blimerick\b",
    )
)

# Workspace / nav surfaces — also used for small typos ("Dashbaord").
_WORKSPACE_SURFACES: tuple[str, ...] = (
    "dashboard",
    "dashboards",
    "home",
    "exam",
    "exams",
    "quiz",
    "quizzes",
    "quizzer",
    "student",
    "students",
    "analytics",
    "arena",
    "monitoring",
    "results",
    "settings",
    "integrations",
    "classroom",
    "calendar",
    "account",
    "onboarding",
)

_QUIZZER_HINTS: tuple[str, ...] = (
    "quiz",
    "quizzer",
    "exam",
    "assessment",
    "question",
    "publish",
    "arena",
    "attempt",
    "student",
    "proctor",
    "monitor",
    "analytics",
    "result",
    "score",
    "grade",
    "dashboard",
    "metric",
    "kpi",
    "home",
    "share link",
    "verification",
    "enrollment",
    "negative marking",
    "live exam",
    # Integrations & account surfaces
    "classroom",
    "google classroom",
    "google drive",
    "google calendar",
    "integration",
    "integrations",
    "calendar",
    "calender",  # common typo
    "microsoft teams",
    "teams",
    "roster",
    "onboarding",
    "notification",
    "account settings",
    "settings",
)

_LIVE_DATA_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bhow many\b.*\b(students?|attempts?|fails?|pass(es|ed)?|scores?|exams?|quizzes)\b",
        r"\b(my|our)\s+(score|result|grade|analytics|exams?|quizzes)\b",
        r"\bwho\s+(failed|passed|scored)\b",
        r"\bcount\b.*\b(students?|attempts?|exams?|quizzes)\b",
        r"\b(exams?|quizzes)\s+(have i|did i|i (made|created|have)|made by me|created by me)\b",
        r"\bhow many\b.*\b(made|created)\b",
        r"\bbelow\s+\d+\b",
        r"\btoday'?s?\s+(exam|results?)\b",
        r"\blive\s+(count|students?|attempts?)\b",
        r"\b(my|the)\s+(dashboard\s+)?(metrics?|kpis?)\b",
        r"\bmetrics?\b.*\b(dashboard|exam|quiz|numbers?)\b",
        r"\bdashboard\b.*\b(metrics?|numbers?|stats?|kpis?)\b",
        r"\b(can you|do you|could you)\s+see\b.*\b(exam|quiz)\b",
        r"\b(see|look at|find|show me|open|check)\s+(my|this|that|the)\s+(one\s+)?(exam|quiz)\b",
        r"\bin\s+my\s+(one\s+)?(exam|quiz)\b",
        r"\b(exam|quiz)\s+(titled|called|named)\b",
        r"\bcan you see (that|this|it)\b",
    )
)

_ANALYTICS_HINTS: tuple[str, ...] = (
    "analytics",
    "statistics",
    "performance",
    "average score",
    "pass rate",
    "fail rate",
    "compare exam",
    "topic performance",
    "metric",
    "kpi",
)

_ACTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\b(create|delete|publish|unpublish|approve|reject|share|notify|remind)\b",
        r"\b(start|stop|end)\s+(the\s+)?(exam|quiz|attempt)\b",
        r"\bchange\b.*\b(setting|timer|password)\b",
    )
)

_META_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"^(hi|hello|hey|yo|hiya|hola|namaste|sup|howdy)(\s|$)",
        r"^(hi|hello|hey)\s+(there|que)\b",
        r"^(good\s+)?(morning|afternoon|evening|night)\b",
        r"\bwhat can you (do|help(?: me)?(?: with)?)\b",
        r"\bwhat do you (do|help(?: with)?)\b",
        r"\bhow can you help(?: me)?(?: with)?\b",
        r"\bwhat can que (do|help(?: me)?(?: with)?)\b",
        r"^can you help(?: me)?(?: with)?(?:\s+(?:in|on|with)\s+(?:quizzer|the\s+app|this\s+app))?[\s?]*$",
        r"^i(?:'m| am|m)?\s+new(?:\s+here)?(?:\s*[,.]?\s*explain\s+this(?:\s+to\s+me)?)?[\s,.!]*$",
        r"^explain this(?: to me)?[\s,.!]*$",
        r"^what is this(?: page)?[\s,.!]*$",
        r"^(?:help me )?get(?:ting)? started[\s,.!]*$",
        r"\bwho are you\b",
        r"\bwhat is quizzer\b",
        r"^(help|help me)$",
        r"^(thanks|thank you|thx|ty)(\s|!|\.|$)",
        r"\bhow are you\b",
        r"^(bye|goodbye|good bye|see you|see ya|take care|later)\b",
        r"\b(what|how)\s+about\s+you\b",
        r"^i('m| am|m)?\s+(fine|good|great|well|ok|okay)\b",
        r"^(ok|okay|cool|nice|great|awesome|perfect|got it|alright)\s*$",
    )
)

_MULTI_STEP_RE = re.compile(
    r"\b(compare|versus|vs\.?|then tell me|and then|as well as)\b",
    re.I,
)
_MULTI_LIVE_BITS: tuple[str, ...] = (
    "how many",
    "how did",
    "results",
    "who needs",
    "publish",
    "dashboard",
    "analytics",
    "live exam",
    "status",
    "count",
    "blueprint",
    "follow up",
)


def is_multi_step_ask(text: str) -> bool:
    """True when the ask likely needs more than one tool or a chained how-to."""
    n = _norm(text or "")
    if not n:
        return False
    if _MULTI_STEP_RE.search(n):
        return True
    if " and " in n:
        live_hits = sum(1 for bit in _MULTI_LIVE_BITS if bit in n)
        if live_hits >= 2:
            return True
        if "how" in n and any(h in n for h in ("exam", "quiz", "result", "student", "dashboard")):
            return True
    return False


_HIGH_WRITE_HINTS: tuple[str, ...] = (
    "delete",
    "remove all",
    "wipe",
    "reset password",
    "change password",
    "unpublish",
)


def _canonicalize_product_text(text: str) -> str:
    """Map workspace-page typos onto canonical names (dashbaord → dashboard)."""

    def _repl(match: re.Match[str]) -> str:
        tok = match.group(0)
        if tok in _WORKSPACE_SURFACES:
            return tok
        if len(tok) < 6:
            return tok
        for surface in _WORKSPACE_SURFACES:
            if abs(len(tok) - len(surface)) > 2:
                continue
            allowed = 1 if min(len(tok), len(surface)) <= 7 else 2
            if _edit_distance(tok, surface) <= allowed:
                return surface
        return tok

    return re.sub(r"[a-z0-9']+", _repl, text)


def _norm(text: str) -> str:
    cleaned = text.casefold().strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return _canonicalize_product_text(cleaned)


def _edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _token_is_workspace_surface(token: str) -> bool:
    """True if a word is a Quizzer page name, including common typos."""
    if token in _WORKSPACE_SURFACES:
        return True
    if len(token) < 6:
        return False
    for surface in _WORKSPACE_SURFACES:
        if abs(len(token) - len(surface)) > 2:
            continue
        allowed = 1 if min(len(token), len(surface)) <= 7 else 2
        if _edit_distance(token, surface) <= allowed:
            return True
    return False


def _has_quizzer_hint(text: str) -> bool:
    """Product signal: exact hints or a workspace-page token (with typo slack)."""
    n = _norm(text or "")
    if any(h in n for h in _QUIZZER_HINTS):
        return True
    return any(_token_is_workspace_surface(tok) for tok in re.findall(r"[a-z0-9']+", n))


def is_hard_out_of_scope(text: str) -> bool:
    """True for clearly non-Quizzer asks (weather, coding, jailbreak, …).

    Used before follow-up continuation so mid-chat topic switches still refuse.
    """
    n = _norm(text or "")
    if not n:
        return False
    return any(pat.search(n) for pat in _OUT_OF_SCOPE_PATTERNS)


def _is_count_live_ask(n: str) -> bool:
    return bool(
        re.search(r"\bhow many\b", n)
        or re.search(r"\bwho\s+(failed|passed|scored)\b", n)
        or re.search(r"\bbelow\s+\d+\b", n)
        or re.search(r"\blive\s+(count|students?|attempts?)\b", n)
    )


def _is_product_howto(n: str) -> bool:
    return (
        "how do i" in n
        or "how to" in n
        or "how does" in n
        or "how can i" in n
        or n.startswith("how ")
        or "where is" in n
        or "where do i" in n
        or n.startswith("help me")
        or n.startswith("help with")
    )


def _is_troubleshooting_ask(n: str) -> bool:
    return bool(
        re.search(r"\bwhy (can'?t|isn'?t|doesn'?t|won'?t)\b", n)
        or re.search(r"\bwhat happens (when|if|after)\b", n)
        or re.search(r"\bwhat'?s wrong\b|\bwhat is wrong\b", n)
        or re.search(r"\bnot (working|showing|appearing)\b", n)
    )


def _with_execution(u: RequestUnderstanding, text: str) -> RequestUnderstanding:
    """Fill execution_class from route. Canonical intent is attached later."""
    if u.route == "refuse":
        cls: ExecutionClass = "out_of_scope"
    elif u.route == "canned_eligible" or u.intent in {"chitchat", "meta"}:
        cls = "conversational"
    elif u.route == "clarify":
        cls = "conversational"
    elif u.route == "tool" or u.data_need == "live_tool":
        cls = "tool_required"
    elif u.complexity == "multi_step":
        cls = "complex_knowledge"
    else:
        cls = "simple_knowledge"
    if u.execution_class == cls:
        return u
    return replace(u, execution_class=cls)


def classify_request(
    text: str,
    *,
    conversation_active: bool = False,
) -> RequestUnderstanding:
    """Classify a user ask (usually the *resolved* query)."""
    return _with_execution(
        _classify_core(text, conversation_active=conversation_active),
        text,
    )


def _classify_core(
    text: str,
    *,
    conversation_active: bool = False,
) -> RequestUnderstanding:
    """Classify a user ask (usually the *resolved* query).

    ``conversation_active`` means this turn continues an established Quizzer
    thread. In that mode we still refuse hard out-of-scope patterns, but we do
    **not** refuse merely because the wording lacks Quizzer keywords.
    """
    raw = (text or "").strip()
    if not raw:
        return RequestUnderstanding(
            scope="clarification",
            intent="meta",
            risk="read",
            freshness="static",
            data_need="none",
            complexity="single_step",
            route="clarify",
            reasons=("empty_message",),
        )

    n = _norm(raw)
    reasons: list[str] = []

    for pat in _OUT_OF_SCOPE_PATTERNS:
        if pat.search(n):
            # Jailbreak / injection / unrelated world knowledge.
            if _has_quizzer_hint(n) and "ignore" not in n and "system prompt" not in n:
                # e.g. "write a python script to grade quizzer results" — still risky out.
                pass
            reasons.append(f"out_pattern:{pat.pattern[:40]}")
            return RequestUnderstanding(
                scope="out_of_scope",
                intent="out_of_scope",
                risk="read",
                freshness="static",
                data_need="none",
                complexity="single_step",
                route="refuse",
                reasons=tuple(reasons),
            )

    # Short meta / chitchat without product ask.
    for pat in _META_PATTERNS:
        if pat.search(n) and len(n) < 80 and not any(
            h in n for h in ("how do i", "where is", "publish", "create quiz", "monitor")
        ):
            intent: Intent = "chitchat" if pat.pattern.startswith("^(hi") else "meta"
            reasons.append("meta_or_chitchat")
            return RequestUnderstanding(
                scope="in_scope",
                intent=intent,
                risk="read",
                freshness="static",
                data_need="none",
                complexity="single_step",
                route="canned_eligible",
                reasons=tuple(reasons),
            )

    for pat in _LIVE_DATA_PATTERNS:
        if pat.search(n):
            if (
                _is_product_howto(n) or _is_troubleshooting_ask(n)
            ) and not _is_count_live_ask(n):
                reasons.append("live_pattern_as_howto")
                break
            reasons.append("live_data_pattern")
            return RequestUnderstanding(
                scope="in_scope",
                intent="analytics" if any(h in n for h in _ANALYTICS_HINTS) else "live_data",
                risk="read",
                freshness="critical" if "live" in n or "today" in n else "dynamic",
                data_need="live_tool",
                complexity="multi_step" if is_multi_step_ask(n) else "single_step",
                route="tool",
                reasons=tuple(reasons),
            )

    if any(h in n for h in _ANALYTICS_HINTS) and _has_quizzer_hint(n):
        if _is_troubleshooting_ask(n) and not _is_count_live_ask(n):
            reasons.append("analytics_troubleshooting_as_knowledge")
            return RequestUnderstanding(
                scope="in_scope",
                intent="knowledge",
                risk="read",
                freshness="static",
                data_need="knowledge",
                complexity="multi_step",
                route="knowledge",
                reasons=tuple(reasons),
            )
        reasons.append("analytics_hint")
        return RequestUnderstanding(
            scope="in_scope",
            intent="analytics",
            risk="read",
            freshness="dynamic",
            data_need="live_tool",
            complexity="multi_step" if is_multi_step_ask(n) else "single_step",
            route="tool",
            reasons=tuple(reasons),
        )

    action_hit = any(p.search(n) for p in _ACTION_PATTERNS)
    howto_ask = (
        "how" in n
        or "where" in n
        or "what" in n
        or "why" in n
        or "?" in raw
        or n.startswith("help me")
        or n.startswith("help with")
        or _is_troubleshooting_ask(n)
        or _is_product_howto(n)
    )
    if action_hit and howto_ask:
        # "How do I publish?" / "Help me publish" is knowledge, not execution.
        reasons.append("how_to_action_as_knowledge")
        return RequestUnderstanding(
            scope="in_scope",
            intent="knowledge",
            risk="read",
            freshness="static",
            data_need="knowledge",
            complexity="single_step",
            route="knowledge",
            reasons=tuple(reasons),
        )

    if action_hit and _has_quizzer_hint(n):
        risk: Risk = "high_write" if any(h in n for h in _HIGH_WRITE_HINTS) else "low_write"
        reasons.append("action_request")
        return RequestUnderstanding(
            scope="in_scope",
            intent="action",
            risk=risk,
            freshness="dynamic",
            data_need="live_tool",
            complexity="single_step",
            route="tool",
            reasons=tuple(reasons),
        )

    if _has_quizzer_hint(n) or any(
        p in n
        for p in (
            "how do i",
            "how does ",
            "how can i",
            "how to",
            "where is",
            "where do i",
            "what is a",
            "what is an",
            "can i",
            "explain ",
        )
    ):
        reasons.append("knowledge_or_howto")
        return RequestUnderstanding(
            scope="in_scope",
            intent="knowledge",
            risk="read",
            freshness="static",
            data_need="knowledge",
            complexity="multi_step" if is_multi_step_ask(n) else "single_step",
            route="knowledge",
            reasons=tuple(reasons),
        )

    # Active Quizzer conversation: continue helping unless hard-OOS (already checked).
    if conversation_active:
        reasons.append("conversation_continuation")
        return RequestUnderstanding(
            scope="in_scope",
            intent="knowledge",
            risk="read",
            freshness="static",
            data_need="knowledge",
            complexity="single_step",
            route="knowledge",
            reasons=tuple(reasons),
        )

    # Cold start with no Quizzer signal → refuse rather than hallucinate.
    reasons.append("no_quizzer_signal")
    return RequestUnderstanding(
        scope="out_of_scope",
        intent="out_of_scope",
        risk="read",
        freshness="static",
        data_need="none",
        complexity="single_step",
        route="refuse",
        reasons=tuple(reasons),
    )
