"""Paired comparison of multilingual eval runs: only rows that completed in every arm count.

    uv run python scripts/compare_multilingual.py base=evals/baselines/ml_full_base.json e1=...
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

METRICS = ("routing_ok", "evidence_hit", "cross_language", "ambiguity_ok", "grounded", "intent_preserved")


def _val(row: dict, key: str):
    v = row.get(key)
    return None if v is None else float(v)


def main() -> None:
    arms = {}
    for arg in sys.argv[1:]:
        name, path = arg.split("=", 1)
        arms[name] = json.loads(Path(path).read_text(encoding="utf-8"))["rows"]
    names = list(arms)
    n_rows = len(arms[names[0]])
    complete = [
        i for i in range(n_rows)
        if all(("grounded" in arms[n][i] or arms[n][i].get("llm_called") is False) and not arms[n][i].get("generate_error") for n in names)
    ]
    print(f"rows in every arm: {len(complete)} of {n_rows}  (others hit provider errors in at least one arm)")
    print("metric".ljust(18) + "".join(n.rjust(10) for n in names))
    for m in METRICS:
        cells = []
        for n in names:
            vals = [_val(arms[n][i], m) for i in complete]
            vals = [v for v in vals if v is not None]
            cells.append(f"{statistics.mean(vals):.3f}" if vals else "n/a")
        print(m.ljust(18) + "".join(c.rjust(10) for c in cells))
    for key in ("latency_ms", "prompt_tokens", "completion_tokens"):
        cells = [f"{statistics.mean(arms[n][i].get(key, 0) for i in complete):.0f}" for n in names]
        print(key.ljust(18) + "".join(c.rjust(10) for c in cells))
    llm = [sum(int(bool(arms[n][i].get("llm_called"))) + int(bool((arms[n][i].get("interpret") or {}).get("tokens"))) for i in complete) for n in names]
    print("llm_calls".ljust(18) + "".join(str(c).rjust(10) for c in llm))


if __name__ == "__main__":
    main()
