"""Human review of retriever goldens.

Only rows with ``human_verified: true`` enter the gate. Run:

    uv run python -m evals.review_goldens list
    uv run python -m evals.review_goldens approve r01 r03 s05
    uv run python -m evals.review_goldens reject s04 --note "question too vague"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / "retriever_goldens.json"


def _load() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def _save(payload: dict) -> None:
    PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["list", "approve", "reject"])
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    payload = _load()
    rows = payload["goldens"]
    if args.action == "list":
        for row in rows:
            flag = "OK " if row.get("human_verified") else ("REJ" if row.get("rejected") else "...")
            print(f"[{flag}] {row['id']} {row.get('expected_doc_ids')} :: {row['query']}")
            print(f"        expected: {(row.get('expected_output') or '(abstain)')[:160]}")
        verified = sum(1 for r in rows if r.get("human_verified"))
        print(f"\n{verified}/{len(rows)} verified")
        return

    wanted = set(args.ids)
    found = 0
    for row in rows:
        if row["id"] in wanted:
            found += 1
            if args.action == "approve":
                row["human_verified"] = True
                row.pop("rejected", None)
            else:
                row["human_verified"] = False
                row["rejected"] = True
                row["review_note"] = args.note
    missing = wanted - {row["id"] for row in rows}
    if missing:
        raise SystemExit(f"unknown ids: {sorted(missing)}")
    _save(payload)
    print(f"{args.action}d {found} rows")


if __name__ == "__main__":
    main()
