"""Fast FAQ replies — skip the LLM for common chit-chat / meta asks.

Multiple variants per intent so the same question does not always
return identical copy (better chat feel, zero token cost).

Social turns (hello, how are you, I'm fine, bye, thanks) stay warm even
when they are not Quizzer product questions — they keep the chat going.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from app.core.que_cache import (
    get_cached_intent,
    get_last_canned_variant,
    set_cached_intent,
    set_last_canned_variant,
)


@dataclass(frozen=True)
class CannedReply:
    intent: str
    text: str
    model: str = "canned"


def _norm(text: str) -> str:
    cleaned = text.casefold().strip()
    # Drop most punctuation / symbols; keep letters, numbers, spaces, apostrophes.
    cleaned = re.sub(r"[^\w\s']+", " ", cleaned, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _squash(text: str) -> str:
    """Collapse elongated letters so 'Heelllo' matches 'hello'.

    Applied to both the user text and FAQ phrases before compare.
    """
    cleaned = _norm(text)
    # heelllo → helo, hiiii → hi, thanksss → thanks
    cleaned = re.sub(r"(.)\1+", r"\1", cleaned)
    return cleaned


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Tiny strings only — FAQ path; keep DP small.
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


# Exact / near-exact phrases (after normalize). Longest match wins among equals.
_PHRASE_INTENTS: list[tuple[str, str]] = [
    # greetings
    ("hello", "greeting"),
    ("hello there", "greeting"),
    ("hello que", "greeting"),
    ("hi", "greeting"),
    ("hi there", "greeting"),
    ("hi que", "greeting"),
    ("hiya", "greeting"),
    ("hey", "greeting"),
    ("hey there", "greeting"),
    ("hey que", "greeting"),
    ("hey friend", "greeting"),
    ("good morning", "greeting"),
    ("good afternoon", "greeting"),
    ("good evening", "greeting"),
    ("morning", "greeting"),
    ("evening", "greeting"),
    ("yo", "greeting"),
    ("sup", "greeting"),
    ("what's up", "greeting"),
    ("whats up", "greeting"),
    ("wassup", "greeting"),
    ("howdy", "greeting"),
    ("namaste", "greeting"),
    ("hola", "greeting"),
    ("nice to meet you", "greeting"),
    ("pleased to meet you", "greeting"),
    # wellbeing / check-in
    ("how are you", "how_are_you"),
    ("how are you doing", "how_are_you"),
    ("how's it going", "how_are_you"),
    ("hows it going", "how_are_you"),
    ("how do you do", "how_are_you"),
    ("how have you been", "how_are_you"),
    ("are you ok", "how_are_you"),
    ("are you okay", "how_are_you"),
    ("are you fine", "how_are_you"),
    ("you okay", "how_are_you"),
    ("you good", "how_are_you"),
    # user shares how they feel / asks QUE back
    ("i am fine", "wellbeing_reply"),
    ("i'm fine", "wellbeing_reply"),
    ("im fine", "wellbeing_reply"),
    ("i am good", "wellbeing_reply"),
    ("i'm good", "wellbeing_reply"),
    ("im good", "wellbeing_reply"),
    ("i am well", "wellbeing_reply"),
    ("i'm well", "wellbeing_reply"),
    ("i am okay", "wellbeing_reply"),
    ("i'm okay", "wellbeing_reply"),
    ("i am ok", "wellbeing_reply"),
    ("i'm ok", "wellbeing_reply"),
    ("i am great", "wellbeing_reply"),
    ("i'm great", "wellbeing_reply"),
    ("doing fine", "wellbeing_reply"),
    ("doing good", "wellbeing_reply"),
    ("all good", "wellbeing_reply"),
    ("not bad", "wellbeing_reply"),
    ("what about you", "wellbeing_reply"),
    ("how about you", "wellbeing_reply"),
    ("and you", "wellbeing_reply"),
    ("i am fine what about you", "wellbeing_reply"),
    ("i'm fine what about you", "wellbeing_reply"),
    ("im fine what about you", "wellbeing_reply"),
    ("i am fine how about you", "wellbeing_reply"),
    ("i'm fine how about you", "wellbeing_reply"),
    ("i am good what about you", "wellbeing_reply"),
    ("i'm good what about you", "wellbeing_reply"),
    ("im good what about you", "wellbeing_reply"),
    ("i am good how about you", "wellbeing_reply"),
    ("i'm good how about you", "wellbeing_reply"),
    ("fine what about you", "wellbeing_reply"),
    ("good what about you", "wellbeing_reply"),
    ("i am fine and you", "wellbeing_reply"),
    ("i'm fine and you", "wellbeing_reply"),
    # light acknowledgements
    ("ok", "ack"),
    ("okay", "ack"),
    ("ok thanks", "thanks"),
    ("okay thanks", "thanks"),
    ("cool", "ack"),
    ("nice", "ack"),
    ("great", "ack"),
    ("awesome", "ack"),
    ("perfect", "ack"),
    ("got it", "ack"),
    ("alright", "ack"),
    ("sounds good", "ack"),
    ("makes sense", "ack"),
    # thanks
    ("thanks", "thanks"),
    ("thank you", "thanks"),
    ("thanks que", "thanks"),
    ("thank you que", "thanks"),
    ("thanks a lot", "thanks"),
    ("thank you so much", "thanks"),
    ("many thanks", "thanks"),
    ("thx", "thanks"),
    ("ty", "thanks"),
    ("appreciate it", "thanks"),
    ("much appreciated", "thanks"),
    # bye
    ("bye", "bye"),
    ("bye bye", "bye"),
    ("goodbye", "bye"),
    ("good bye", "bye"),
    ("good night", "bye"),
    ("goodnight", "bye"),
    ("see you", "bye"),
    ("see ya", "bye"),
    ("see you later", "bye"),
    ("catch you later", "bye"),
    ("talk later", "bye"),
    ("talk to you later", "bye"),
    ("later", "bye"),
    ("take care", "bye"),
    ("have a good day", "bye"),
    ("have a nice day", "bye"),
    ("signing off", "bye"),
    # what can you do / capabilities
    ("what can you do", "capabilities"),
    ("what do you do", "capabilities"),
    ("what do you help with", "capabilities"),
    ("what are you", "capabilities"),
    ("who are you", "capabilities"),
    ("help", "capabilities"),
    ("help me", "capabilities"),
    ("what can you help with", "capabilities"),
    ("what can you help me with", "capabilities"),
    ("how can you help", "capabilities"),
    ("how can you help me", "capabilities"),
    ("how can you help me with", "capabilities"),
    ("what can you help me with in quizzer", "capabilities"),
    ("what can you help with in quizzer", "capabilities"),
    ("how can you help me in quizzer", "capabilities"),
    ("what can que help with", "capabilities"),
    ("what can que do", "capabilities"),
    ("can you help me", "capabilities"),
    ("can you help me with", "capabilities"),
    ("can you help me with quizzer", "capabilities"),
    ("can you help with quizzer", "capabilities"),
    # New-user / vague orientation (UI context may refine the reply text)
    ("i am new here", "getting_started"),
    ("im new here", "getting_started"),
    ("i'm new here", "getting_started"),
    ("i am new", "getting_started"),
    ("im new", "getting_started"),
    ("i'm new", "getting_started"),
    ("i am new here explain this to me", "getting_started"),
    ("im new here explain this to me", "getting_started"),
    ("i am new here, explain this to me", "getting_started"),
    ("explain this to me", "getting_started"),
    ("explain this", "getting_started"),
    ("explain the page", "getting_started"),
    ("what is this page", "getting_started"),
    ("what is this", "getting_started"),
    ("help me get started", "getting_started"),
    ("how do i get started", "getting_started"),
    ("getting started", "getting_started"),
    # what is quizzer
    ("what is quizzer", "what_is_quizzer"),
    ("what's quizzer", "what_is_quizzer"),
    ("whats quizzer", "what_is_quizzer"),
    ("tell me about quizzer", "what_is_quizzer"),
    ("explain quizzer", "what_is_quizzer"),
    # who is que
    ("who is que", "who_is_que"),
    ("what is que", "who_is_que"),
    ("what's que", "who_is_que"),
    ("whats que", "who_is_que"),
]

# Trailing product location that users add after capability asks.
_PRODUCT_TAIL_RE = re.compile(
    r"\s+(?:in|on|with)\s+(?:quizzer|the\s+app|this\s+app)\s*$",
    re.I,
)
_CAPABILITIES_ASK_RE = re.compile(
    r"^(?:(?:what|how)\s+can\s+(?:you|que)\s+"
    r"(?:do|help(?:\s+me)?(?:\s+with)?)|"
    r"can\s+you\s+help(?:\s+me)?(?:\s+with)?)"
    r"(?:\s+(?:in|on|with)\s+(?:quizzer|the\s+app|this\s+app))?"
    r"\s*$",
    re.I,
)
_GETTING_STARTED_ASK_RE = re.compile(
    r"^(?:i(?:'m| am|m)?\s+new(?:\s+here)?"
    r"(?:\s*[,.]?\s*explain\s+this(?:\s+to\s+me)?)?|"
    r"explain\s+this(?:\s+to\s+me)?|"
    r"explain\s+(?:the\s+)?page|"
    r"what\s+is\s+this(?:\s+page)?|"
    r"(?:help\s+me\s+)?get(?:ting)?\s+started|"
    r"how\s+do\s+i\s+get\s+started)\s*$",
    re.I,
)


def _strip_product_tail(text: str) -> str:
    return _PRODUCT_TAIL_RE.sub("", text).strip()


def pick_canned_intent(
    intent: str,
    *,
    conversation_id: str | None = None,
    rng: random.Random | None = None,
) -> CannedReply | None:
    """Return a varied canned reply for a known intent id (no phrase matching)."""
    variants = _VARIANTS.get(intent) or ()
    if not variants:
        return None
    picker = rng or random.SystemRandom()
    last = get_last_canned_variant(conversation_id, intent)
    choices = [v for v in variants if v != last] or list(variants)
    text = picker.choice(choices)
    set_last_canned_variant(conversation_id, intent, text)
    return CannedReply(intent=intent, text=text)


_VARIANTS: dict[str, tuple[str, ...]] = {
    "greeting": (
        "Hey — I'm QUE, your Quizzer assistant. What do you want help with?",
        "Hi! Ask me anything about creating, publishing, or monitoring exams in Quizzer.",
        "Hello. I'm here for Quizzer how-tos — exams, links, monitoring, results, and more.",
        "Hey there. Tell me what you're trying to do in Quizzer and I'll point you there.",
        "Hi! Good to see you. Need a hand with a Quizzer exam, share link, or monitoring?",
        "Hello — ready when you are. What's on your Quizzer to-do list?",
        "Hey! I can walk you through Quizzer screens in plain language. Where should we start?",
    ),
    "how_are_you": (
        "Doing well — ready when you are. What do you need in Quizzer?",
        "All good on my side. Want help with an exam, link, or monitoring question?",
        "I'm fine, thanks. Ask me a Quizzer question whenever you're ready.",
        "Feeling helpful today. How can I make Quizzer clearer for you?",
        "Great, thanks for asking. What are you working on in Quizzer?",
    ),
    "wellbeing_reply": (
        "Glad you're doing well. I'm good too — what Quizzer thing can I help with?",
        "Nice to hear. I'm ready whenever you are — Quizzer exams, publish, monitoring, results?",
        "Good to know. I'm here if you want a quick Quizzer how-to.",
        "Awesome. Want help creating an exam, sharing a link, or checking results?",
        "Happy you're fine. Tell me what you're stuck on in Quizzer and I'll keep it simple.",
    ),
    "ack": (
        "Got it. Anything else about Quizzer I can clarify?",
        "Okay. Ask another Quizzer question anytime.",
        "Sounds good. I'm here if you need the next step.",
        "Cool. Want to dig into create, publish, or monitoring next?",
    ),
    "thanks": (
        "You're welcome. Ping me if you get stuck on another Quizzer step.",
        "Anytime. Happy to help with the next Quizzer question too.",
        "Glad that helped. Ask again anytime.",
        "My pleasure. Come back if another Quizzer screen is confusing.",
        "Happy to help. What else are you working on?",
    ),
    "bye": (
        "Bye — open QUE again whenever you need Quizzer help.",
        "See you. I'll be here for the next exam or monitoring question.",
        "Take care. Come back if something in Quizzer is unclear.",
        "Goodbye! Good luck with your exams — I'm here when you need me.",
        "Catch you later. QUE is one click away when you need a how-to.",
        "Night! Rest well — ask me about Quizzer anytime you're back.",
        "Have a good one. I'll be ready for your next Quizzer question.",
    ),
    "capabilities": (
        "I explain how Quizzer works — create and approve questions, publish, share links, "
        "monitoring, results, students, and analytics. I can't change settings or read live "
        "account numbers yet. What are you working on?",
        "Think of me as in-app Quizzer help: click paths, publish flow, link windows, LIVE "
        "monitoring, and similar how-tos. I don't take actions in your account. What should we cover?",
        "I can walk you through Quizzer screens and workflows. Live counts and edits still need "
        "you in the UI. Ask a specific question and I'll keep it short.",
    ),
    "what_is_quizzer": (
        "Quizzer is an AI assessment platform: create an exam from sources, review questions, "
        "publish, share a link, then monitor attempts and review results or analytics.",
        "Quizzer helps you go from upload → AI draft questions → human review → publish → "
        "students take the exam → monitoring and analytics.",
        "In short: Quizzer is where you build, publish, and watch graded exams — plus Arena "
        "for live competition games, which is separate from graded Results.",
    ),
    "who_is_que": (
        "I'm QUE — Quizzer's in-app assistant. I help with product how-tos; I don't edit your "
        "exams or see live student counts yet.",
        "QUE is your Quizzer guide built into the workspace. Ask how something works and I'll "
        "point you to the right place.",
        "I'm QUE. I answer Quizzer questions in plain language so you can keep moving without "
        "leaving the app.",
    ),
    "getting_started": (
        "Welcome — you're on **Exams**, your exam list. Click **Create Exam** (emerald) to "
        "start, approve questions, then **Publish** and share the link. Ask me any step.",
        "New here: create → approve questions → publish → share link → watch **Monitoring** / "
        "**Results**. Open **Create Exam** when you're ready, or ask me about one step.",
        "You're in the teacher workspace. **Dashboard** is the overview; **Exams** is where "
        "exams live. Start with **Create Exam**, then ask me about publish, links, or monitoring.",
    ),
}


_WELLBEING_REPLY_RE = re.compile(
    r"^(?:(?:yes|yeah|yep|sure)[,.]?\s+)?"
    r"(?:i(?:'m| am|m)\s+)?"
    r"(?:doing\s+)?"
    r"(?:fine|good|great|well|ok|okay|alright|all good|not bad)"
    r"(?:\s*(?:,|and|&)?\s*(?:what|how)\s+about\s+you|\s+and\s+you)?"
    r"\s*$",
    re.I,
)
_HOW_ABOUT_YOU_RE = re.compile(
    r"^(?:what|how)\s+about\s+you\s*$|^(?:and\s+)?you\s*\??$",
    re.I,
)


def match_canned_reply(
    user_text: str,
    *,
    conversation_id: str | None = None,
    rng: random.Random | None = None,
) -> CannedReply | None:
    """Return a varied canned reply if the latest user turn is a known FAQ.

    Tolerates casing, punctuation, elongated letters (``Heelllo``), and small typos.
    Uses QUE-local cache for intent reuse and to avoid repeating the same variant
    back-to-back in a conversation.
    """
    query = _norm(user_text)
    if not query or len(query) > 120:
        return None

    squashed = _squash(query)
    stripped = _strip_product_tail(squashed)
    intent: str | None = get_cached_intent(squashed) or get_cached_intent(stripped)

    # 1) Exact after squash (handles Heelllo / hellloooo / Hi!!!!).
    if intent is None:
        for candidate in (squashed, stripped):
            if not candidate:
                continue
            for phrase, name in sorted(_PHRASE_INTENTS, key=lambda item: len(item[0]), reverse=True):
                if candidate == _squash(phrase):
                    intent = name
                    break
            if intent is not None:
                break

    # 1b) Capability paraphrases with optional "in Quizzer" tail.
    if intent is None and _CAPABILITIES_ASK_RE.match(query):
        intent = "capabilities"
    if intent is None and _GETTING_STARTED_ASK_RE.match(query):
        intent = "getting_started"

    # 2) Tiny typo tolerance on short turns only (avoid stealing real questions).
    if intent is None and len(stripped) <= 36:
        best: tuple[int, str] | None = None
        for phrase, name in _PHRASE_INTENTS:
            target = _squash(phrase)
            # Only compare similar-length phrases (don't map "hi" → "what is quizzer").
            if abs(len(stripped) - len(target)) > 2:
                continue
            dist = _levenshtein(stripped, target)
            # Allow 1 edit for short, 2 for slightly longer FAQ lines.
            allowed = 1 if len(target) <= 8 else 2
            if dist <= allowed and (best is None or dist < best[0]):
                best = (dist, name)
        if best is not None:
            intent = best[1]

    if intent is None:
        # Elongated greeting tokens: hiiii, heeey, helllo que
        if re.fullmatch(r"h+i+( que)?", squashed) or re.fullmatch(
            r"h+e+y+( que)?", squashed
        ) or re.fullmatch(r"h+e+l+o+( que)?", squashed):
            intent = "greeting"

    if intent is None and len(query) <= 80:
        if _WELLBEING_REPLY_RE.match(query) or _HOW_ABOUT_YOU_RE.match(query):
            intent = "wellbeing_reply"

    if intent is None:
        return None

    set_cached_intent(squashed, intent)
    if stripped and stripped != squashed:
        set_cached_intent(stripped, intent)

    return pick_canned_intent(intent, conversation_id=conversation_id, rng=rng)


def latest_user_text(messages: list) -> str:
    """Best-effort extract of the latest user string from ChatMessage or dicts."""
    for item in reversed(messages or []):
        role = getattr(item, "role", None)
        content = getattr(item, "content", None)
        if role is None and isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
        if role == "user" and isinstance(content, str) and content.strip():
            return content
    return ""
