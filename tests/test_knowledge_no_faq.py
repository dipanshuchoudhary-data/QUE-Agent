"""Guard: knowledge guides must not contain FAQ-style Q&A blocks.

Bundled "Common Questions" chunks match many queries by keywords but answer
none of them, so they pollute retrieval. Answers belong in topical sections.
"""

from __future__ import annotations

import re
from pathlib import Path

KNOWLEDGE = Path(__file__).resolve().parents[1] / "knowledge"
_QUESTION_LINE = re.compile(r"^[A-Z][^\n]{6,110}\?\s*$")


def _guides() -> list[Path]:
    return [
        p
        for p in KNOWLEDGE.rglob("*.md")
        if p.name != "README.md" and "intents" not in p.parts
    ]


def test_guides_exist() -> None:
    assert _guides()


def test_no_common_questions_heading() -> None:
    bad = [
        str(p.relative_to(KNOWLEDGE))
        for p in _guides()
        if re.search(r"^#{1,6}\s+(Common Questions|FAQ)\b", p.read_text(encoding="utf-8"), re.M | re.I)
    ]
    assert not bad, f"FAQ headings found: {bad}"


def test_no_consecutive_question_lines() -> None:
    bad: list[str] = []
    for p in _guides():
        lines = p.read_text(encoding="utf-8").splitlines()
        count = 0
        for i, ln in enumerate(lines):
            if ln.startswith("#"):
                count = 0  # question lines are counted per section
            elif _QUESTION_LINE.match(ln):
                count += 1
                if count >= 3:
                    bad.append(f"{p.relative_to(KNOWLEDGE)}:{i + 1}")
                    break
    assert not bad, f"Q&A runs found: {bad}"
