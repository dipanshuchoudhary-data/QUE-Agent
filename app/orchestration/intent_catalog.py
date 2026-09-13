"""Canonical workflow intents and lexical/semantic matching.

Prototype texts (not a synonym dictionary) map paraphrases onto ids like
``exam.publish``. Embeddings overlay when ``QUE_SEMANTIC_ROUTER`` is on;
lexical Jaccard on the same texts is the offline fallback.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.orchestration.understanding import RequestUnderstanding

logger = logging.getLogger(__name__)

_PROTOTYPES_PATH = Path(__file__).resolve().parent / "intent_prototypes.json"
_CARDS_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "intents"

_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "do",
        "i",
        "me",
        "my",
        "in",
        "on",
        "of",
        "for",
        "and",
        "or",
        "is",
        "it",
        "this",
        "that",
        "with",
        "can",
        "you",
        "please",
        "how",
        "where",
        "what",
        "when",
        "does",
        "did",
        "a",
    }
)

_DIAGNOSE_RE = re.compile(
    r"\b(why (can'?t|isn'?t|doesn'?t|won'?t)|what'?s wrong|what is wrong|"
    r"not (working|showing|appearing)|missing|diagnose)\b",
    re.I,
)
_COMPARE_RE = re.compile(r"\b(difference between|versus|vs\.?|compare)\b", re.I)
_WHAT_HAPPENS_RE = re.compile(r"\bwhat happens (when|if|after)\b", re.I)

ExecutionClass = str


@dataclass(frozen=True)
class IntentHit:
    intent_id: str
    score: float
    source: str  # lexical | semantic


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").casefold())
    out: set[str] = set()
    for word in words:
        if word in _STOP:
            continue
        out.add(word)
        for suffix in ("ing", "ed", "es", "ies", "s"):
            if len(word) > len(suffix) + 2 and word.endswith(suffix):
                stem = word[: -len(suffix)]
                if suffix == "ies":
                    stem = word[:-3] + "y"
                if stem and stem not in _STOP:
                    out.add(stem)
    return out


def _content_tokens(text: str) -> set[str]:
    return {t for t in _tokens(text) if t not in _STOP and len(t) > 1}


_GENERIC = frozenset(
    {
        "exam",
        "exams",
        "quiz",
        "quizzes",
        "test",
        "tests",
        "student",
        "students",
        "question",
        "questions",
        "quizzer",
        "page",
        "tab",
        "teacher",
    }
)


def _distinctive(tokens: set[str]) -> set[str]:
    return {t for t in tokens if t not in _GENERIC and t not in _STOP and len(t) > 2}


def lexical_score(query: str, prototype: str) -> float:
    q = _content_tokens(query)
    p = _content_tokens(prototype)
    if not q or not p:
        return 0.0
    inter = q & p
    if not inter:
        return 0.0
    p_dist = _distinctive(p)
    q_dist = _distinctive(q)
    if (p_dist or q_dist) and not (p_dist & q_dist):
        return 0.0
    jaccard = len(inter) / len(q | p)
    coverage = len(inter) / max(1, len(p))
    q_cover = len(inter) / max(1, len(q))
    return min(1.0, 0.35 * jaccard + 0.65 * max(coverage, q_cover))


@lru_cache
def load_prototypes_meta() -> dict[str, Any]:
    return json.loads(_PROTOTYPES_PATH.read_text(encoding="utf-8"))


@lru_cache
def load_cards() -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    if not _CARDS_DIR.is_dir():
        return cards
    for path in sorted(_CARDS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cid = str(data.get("id") or path.stem)
        cards[cid] = data
    return cards


def reset_intent_catalog_cache() -> None:
    load_prototypes_meta.cache_clear()
    load_cards.cache_clear()


def card_for(intent_id: str | None) -> dict[str, Any] | None:
    if not intent_id:
        return None
    return load_cards().get(intent_id)


def has_workflow_card(intent_id: str | None) -> bool:
    card = card_for(intent_id)
    return bool(card) and not card.get("requires_tool") and not card.get("requires_live_data")


def best_lexical_hit(query: str) -> IntentHit | None:
    meta = load_prototypes_meta()
    best: IntentHit | None = None
    for proto in meta.get("prototypes") or []:
        pid = str(proto.get("id") or "")
        if not pid or pid in {"greeting", "capabilities", "what_is_quizzer", "oos", "analytics_live"}:
            continue
        texts = list(proto.get("texts") or [])
        score = max((lexical_score(query, str(t)) for t in texts), default=0.0)
        if best is None or score > best.score:
            best = IntentHit(intent_id=pid, score=score, source="lexical")
    return best


def related_followup_intent(raw: str, prior_intent: str | None) -> str | None:
    """Map 'what about sharing it?' onto a related card without a synonym dictionary."""
    if not prior_intent:
        return None
    card = card_for(prior_intent)
    if not card:
        return None
    related = [str(r) for r in (card.get("related") or [])]
    if not related:
        return None
    best_id: str | None = None
    best_score = 0.0
    meta = load_prototypes_meta()
    by_id = {str(p.get("id")): p for p in (meta.get("prototypes") or [])}
    for rid in related:
        proto = by_id.get(rid) or {}
        texts = list(proto.get("texts") or [])
        score = max((lexical_score(raw, str(t)) for t in texts), default=0.0)
        if score > best_score:
            best_score = score
            best_id = rid
    if best_id and best_score >= 0.28:
        return best_id
    return None


def is_diagnostic_ask(text: str) -> bool:
    return bool(_DIAGNOSE_RE.search(text or "") or _WHAT_HAPPENS_RE.search(text or ""))


def is_comparison_ask(text: str) -> bool:
    return bool(_COMPARE_RE.search(text or ""))


def execution_class_from_route(
    understanding: RequestUnderstanding,
    *,
    query: str,
) -> str:
    if understanding.route == "refuse":
        return "out_of_scope"
    if understanding.route in {"canned_eligible"} or understanding.intent in {"chitchat", "meta"}:
        return "conversational"
    if understanding.route == "clarify":
        return "conversational"
    if understanding.route == "tool" or understanding.data_need == "live_tool":
        return "tool_required"
    if (
        understanding.complexity == "multi_step"
        or is_diagnostic_ask(query)
        or is_comparison_ask(query)
        or understanding.intent == "troubleshooting"
    ):
        return "complex_knowledge"
    return "simple_knowledge"


def finalize_understanding(
    base: RequestUnderstanding,
    query: str,
    *,
    hit: IntentHit | None = None,
    prior_canonical: str | None = None,
) -> RequestUnderstanding:
    """Attach execution_class / canonical_intent. Never sent to the LLM as JSON."""
    q = (query or "").strip()
    execution = execution_class_from_route(base, query=q)
    canonical: str | None = None
    confidence = 0.0

    related = related_followup_intent(q, prior_canonical)
    if related and execution not in {"out_of_scope", "tool_required", "conversational"}:
        canonical = related
        confidence = max(confidence, 0.8)
        hit = IntentHit(intent_id=related, score=0.8, source="followup")

    if hit is None and execution not in {"out_of_scope", "conversational"}:
        hit = best_lexical_hit(q)

    if hit is not None and hit.score >= 0.32:
        # Never let a how-to prototype demote a live/write tool turn.
        if base.route == "tool" and hit.intent_id not in {"analytics_live"}:
            pass
        elif execution != "tool_required":
            canonical = hit.intent_id
            confidence = max(confidence, float(hit.score))

    if (
        execution in {"simple_knowledge", "complex_knowledge"}
        and canonical
        and has_workflow_card(canonical)
        and not is_diagnostic_ask(q)
        and not is_comparison_ask(q)
        and confidence >= 0.36
        and execution != "complex_knowledge"
    ):
        execution = "deterministic"

    reasons = base.reasons
    if hit is not None:
        reasons = (*reasons, f"intent:{hit.source}:{hit.intent_id}:{hit.score:.2f}")
    if related:
        reasons = (*reasons, f"related_followup:{related}")

    return replace(
        base,
        execution_class=execution,  # type: ignore[arg-type]
        canonical_intent=canonical,
        confidence=round(confidence, 3),
        reasons=reasons,
    )


def render_workflow_card(
    intent_id: str,
    *,
    user_role: str | None = None,
    exam_title: str | None = None,
    current_page: str | None = None,
) -> str | None:
    card = card_for(intent_id)
    if not card:
        return None
    role = (user_role or "").strip().casefold()
    if role == "student" and card.get("teacher_only", True):
        return str(
            card.get("student_reply")
            or "That's a teacher action. Ask your teacher for the exam link."
        ).strip()

    cached_bits: list[str] = []
    title = (exam_title or "").strip()
    if title and current_page not in {None, "", "unknown"}:
        cached_bits.append(f"For **{title}**:")
    elif title:
        cached_bits.append(f"For **{title}**:")

    steps = [str(s).strip() for s in (card.get("steps") or []) if str(s).strip()]
    if len(steps) == 1:
        cached_bits.append(steps[0])
    elif steps:
        for i, step in enumerate(steps, 1):
            cached_bits.append(f"{i}. {step}")
    result = str(card.get("resulting_state") or "").strip()
    if result:
        cached_bits.append(result)
    for extra in list(card.get("restrictions") or [])[:1]:
        text = str(extra).strip()
        if text:
            cached_bits.append(text)
    body = " ".join(cached_bits).strip()
    if not body:
        return None
    # Single short paragraph when we only had one step + result.
    if len(steps) <= 1:
        return " ".join(cached_bits)
    return "\n".join(cached_bits)


def smith_route_tag(execution_class: str | None, route: str | None) -> str:
    mapping = {
        "deterministic": "deterministic",
        "simple_knowledge": "simple",
        "complex_knowledge": "complex",
        "tool_required": "tool",
        "conversational": "simple",
        "out_of_scope": "simple",
    }
    if execution_class in mapping:
        return mapping[execution_class]
    if route == "tool":
        return "tool"
    if route == "knowledge":
        return "knowledge"
    return "simple"
