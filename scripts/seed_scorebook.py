"""Fill the scorebook from the saved baselines (oldest first, so newer runs win).

    uv run python scripts/seed_scorebook.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.scorebook import update  # noqa: E402

B = ROOT / "evals" / "baselines"


def _j(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    retr = _j(B / "retriever_judged_k3_c5_large_rerank.json")["cases"]
    print("retriever", update("retriever:retriever_judged_k3_c5_large_rerank", [
        {"id": c["id"], "query": c["query"], "scores": {
            k: (c.get(k) or {}).get("score")
            for k in ("ContextualRecallMetric", "ContextualPrecisionMetric", "ContextualRelevancyMetric")}}
        for c in retr]))
    prov = _j(B / "deepeval_pipeline_provenance.json")["rows"]
    print("pipeline", update("deepeval_pipeline:deepeval_pipeline_provenance", [
        {"id": r["id"], "query": r["query"], "scores": {k: v.get("score") for k, v in r["scores"].items()}}
        for r in prov]))
    faith = _j(B / "faithfulness_all.json")["rows"]
    print("faithfulness", update("faithfulness_all:faithfulness_all", [
        {"id": r["id"], "query": r["query"], "scores": {"faithfulness": r.get("faithfulness")}} for r in faith]))


if __name__ == "__main__":
    main()
