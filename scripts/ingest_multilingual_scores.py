"""Load the latest multilingual diagnostics into the scorebook. Runs nothing: reads saved result files.

    uv run python scripts/ingest_multilingual_scores.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.scorebook import update  # noqa: E402

B = ROOT / "evals" / "baselines"


def main() -> None:
    after = json.loads((B / "ml_stageA_local_after.json").read_text(encoding="utf-8"))["rows"]
    gen = {r["id"]: r for r in json.loads((B / "ml_full_e1e2.json").read_text(encoding="utf-8"))["rows"]}
    rows = []
    for r in after:
        scores = {
            "routing_ok": float(r["routing_ok"]),
            "evidence_hit": None if r["evidence_hit"] is None else float(r["evidence_hit"]),
            "cross_language": r.get("cross_language"),
            "ambiguity_ok": None if r["ambiguity_ok"] is None else float(r["ambiguity_ok"]),
        }
        g = gen.get(r["id"])
        # Generation scores only count when that run took the same route as the current code.
        if g and g.get("outcome") == r["outcome"] and "grounded" in g:
            scores["grounded"] = g.get("grounded")
            scores["intent_preserved"] = g.get("intent_preserved")
        rows.append({"id": f"ml-{r['id']}", "query": r["query"], "scores": scores})
    print("changed values:", update("multilingual:stageA_local_after+e1e2", rows))


if __name__ == "__main__":
    main()
