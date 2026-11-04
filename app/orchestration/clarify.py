"""Ask-back for questions that name nothing ("Can I change it after?").

A turn like "How do I share this?" or "It's not working" has a pronoun where the
topic should be. Retrieval then matches on filler words and returns unrelated
guides, and any answer would be a guess. When there is truly no referent we ask
what the user means (deterministic reply, no LLM), then answer the original ask
with the user's reply attached (see ``merge_with_answer`` / ``resolve_request``).

This is deliberately conservative: it only fires on short asks where a
pronoun is the *object* of an action (or the subject of "isn't working") and
there is nothing else to anchor it — no Quizzer noun, no earlier Quizzer topic in
the thread, and no UI context (page/exam) the pronoun could point at. Anything
doubtful falls through to the normal route.
"""

from __future__ import annotations

import hashlib
import re

from app.knowledge.query_normalize import _DOMAIN as _KNOWN_NOUNS
from app.orchestration.understanding import _has_quizzer_hint, is_hard_out_of_scope

# Fixed set so a later turn can recognise that the previous assistant message was
# our question (exact match). Do not edit wording without keeping old strings
# live for in-flight chats.
CLARIFY_REFERENT_REPLIES: tuple[str, ...] = (
    "Sure, happy to help. Can you tell me what you are referring to, for example "
    "an exam setting, the publish link, results, or a student? Once I know, I can "
    "give you a more accurate answer.",
    "Sure. Could you specify what you mean, such as the exam timer, the share "
    "link, or a question? Then I can answer properly.",
    "Happy to help. What are you talking about, an exam, a setting, results, or "
    "something else in Quizzer? Tell me and I will give you a better answer.",
)
_REPLY_SET = frozenset(CLARIFY_REFERENT_REPLIES)

# A reply this long is a new question, not the answer to "what do you mean".
_MAX_ANSWER_WORDS = 14
_MAX_ASK_WORDS = 9

_PRONOUN = r"(?:it|this|that|them|these|those)"
_ACTIONS = (
    "change|edit|update|modify|delete|remove|undo|cancel|share|send|export|download|"
    "publish|unpublish|add|move|copy|duplicate|rename|reset|restore|archive|print|"
    "find|open|close|start|stop|enable|disable|use|fix|set|turn|see|view|check"
)
# Pronoun is the object: "change it", "share this?", "edit it later", "turn this off".
_OBJECT_PRONOUN = re.compile(
    rf"\b(?:{_ACTIONS})\b(?:\s+\w+){{0,2}}?\s+{_PRONOUN}"
    r"(?=\s*(?:after|afterwards|later|before|again|now|anymore|too|first|please|"
    r"on|off|up|down|out|back|[?!.,]|$))"
)
# Pronoun is the subject of a complaint: "it's not working", "this isn't loading".
_SUBJECT_PRONOUN = re.compile(
    r"^(?:it|this|that)(?:'s|\s+is|\s+isn'?t|\s+isnt|\s+does(?:n'?t|nt)|"
    r"\s+won'?t|\s+wont|\s+not|\s+stopped|\s+keeps)\b"
)


def _norm(text: str) -> str:
    cleaned = (text or "").replace("\u2019", "'").casefold().strip()
    return re.sub(r"\s+", " ", cleaned)


def _words(n: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", n)


def needs_referent(text: str) -> bool:
    """True when a short ask points at "it/this/that" and names nothing else."""
    n = _norm(text)
    words = _words(n)
    if not words or len(words) > _MAX_ASK_WORDS:
        return False
    if is_hard_out_of_scope(text):
        return False
    if _has_quizzer_hint(n) or any(w in _KNOWN_NOUNS for w in words):
        return False
    return bool(_OBJECT_PRONOUN.search(n) or _SUBJECT_PRONOUN.search(n))


def referent_reply(text: str) -> str:
    """Pick a clarifying reply deterministically from the ask (stable, testable)."""
    digest = hashlib.sha1(_norm(text).encode("utf-8")).digest()[0]
    return CLARIFY_REFERENT_REPLIES[digest % len(CLARIFY_REFERENT_REPLIES)]


def is_referent_reply(text: str | None) -> bool:
    """True when an assistant message is exactly one of our clarifying questions."""
    return (text or "").strip() in _REPLY_SET


def answer_is_usable(text: str) -> bool:
    """A short, on-topic-looking reply to "what do you mean?" (not a new question)."""
    n = _norm(text)
    words = _words(n)
    if not words or len(words) > _MAX_ANSWER_WORDS:
        return False
    if is_hard_out_of_scope(text):
        return False
    return True


def merge_with_answer(vague_ask: str, answer: str) -> str:
    """Attach the user's clarification to the original ask for retrieval + the LLM."""
    clean = (answer or "").strip().rstrip("?.! ")
    return f"{vague_ask.strip()} (They are asking about: {clean})"

# Fixed honest replies when retrieval finds nothing for an in-scope ask
# (QUE_NOANSWER_DETERMINISTIC). No LLM, so nothing can be invented. Variant is
# picked from a hash of the normalized ask, so the same ask gets the same reply.
NO_ANSWER_REPLIES: tuple[str, ...] = (
    "I could not find that in the Quizzer guides, so I will not guess. Could you "
    "rephrase it, or tell me which part of Quizzer it is about, such as exams, "
    "results, or settings?",
    "I do not have a guide that covers that yet. Try asking in a different way, "
    "or name the feature you mean, and I will look again.",
    "I am not sure what you are asking about. Can you say which Quizzer feature "
    "it relates to, for example creating an exam, sharing it, or viewing results?",
)


def no_answer_reply(text: str) -> str:
    digest = hashlib.sha1(_norm(text).encode("utf-8")).digest()[0]
    return NO_ANSWER_REPLIES[digest % len(NO_ANSWER_REPLIES)]
