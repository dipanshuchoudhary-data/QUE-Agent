"""Retrieval-only query normalization and a should-clarify check.

Normalization rewrites the string used for dense + BM25 lookup only. The user's
message, the intent classifier and the LLM prompt never see the rewritten text.
It is deliberately a small deterministic glossary (common typos and Hinglish
function words seen in the golden set), not an LLM rewrite.
"""

from __future__ import annotations

import re

_TYPOS = {
    "publsh": "publish",
    "publis": "publish",
    "negetive": "negative",
    "negtive": "negative",
    "analytcs": "analytics",
    "analtics": "analytics",
    "reults": "results",
    "resuts": "results",
    "excercise": "exam",
}

# Romanised Hindi seen in student/teacher asks -> English product words.
_HINGLISH = {
    "kaise": "how to",
    "kese": "how to",
    "kaisey": "how to",
    "banaye": "create",
    "banaen": "create",
    "banao": "create",
    "bhejna": "send",
    "bheje": "send",
    "bhejo": "send",
    "dekhe": "view",
    "dekhna": "view",
    "dikhao": "show",
    "chalu": "start",
    "kare": "do",
    "karna": "do",
    "karein": "do",
    "ko": "to",
    "ka": "of",
    "ki": "of",
    "mein": "in",
    "nahi": "not",
    "nhi": "not",
    "kyun": "why",
    "kyu": "why",
    "kya": "what",
}
_WORD = re.compile(r"[A-Za-z']+")


def normalize_for_retrieval(query: str) -> str:
    """Return the query with known typos fixed and Hinglish function words translated.

    Everything else (punctuation, hyphens, digits, product words) is left untouched.
    """

    def swap(match: re.Match[str]) -> str:
        low = match.group(0).casefold()
        return _TYPOS.get(low) or _HINGLISH.get(low) or match.group(0)

    return _WORD.sub(swap, query or "").strip()


_VAGUE = {"it", "this", "that", "them", "these", "those", "here", "there", "start", "working"}
_DOMAIN = {
    "exam", "exams", "quiz", "quizzes", "result", "results", "student", "students", "question",
    "questions", "publish", "grade", "grades", "grading", "arena", "analytics", "classroom",
    "settings", "link", "export", "template", "proctoring", "webcam", "attempt", "attempts",
}


def should_clarify(query: str) -> bool:
    """True for short asks that name no Quizzer object and lean on a pronoun ("share this").

    Pure heuristic for the eval and a future clarify route. Production routing does
    not call it yet.
    """
    words = [w.casefold() for w in re.findall(r"[A-Za-z']+", query or "")]
    if not words or len(words) > 6:
        return False
    if any(w in _DOMAIN for w in words):
        return False
    return any(w in _VAGUE for w in words)
