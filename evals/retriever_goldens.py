"""Load the retriever golden set. Only human-verified rows count."""

from __future__ import annotations

import json
from pathlib import Path

GOLDENS_PATH = Path(__file__).resolve().parent / "retriever_goldens.json"


def load_all() -> list[dict]:
    if not GOLDENS_PATH.is_file():
        return []
    return json.loads(GOLDENS_PATH.read_text(encoding="utf-8")).get("goldens", [])


def load_verified() -> list[dict]:
    return [row for row in load_all() if row.get("human_verified")]
