"""Print the chunks retrieval hands the generator for one query (no LLM call).

    uv run python scripts/show_chunks.py "How does grading work for short answers?"
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from evals.prod_route import route_for

    from app.knowledge.assemble import _MAX_CHUNK_CHARS, truncate_text
    from app.knowledge.hybrid import select_hybrid

    query = " ".join(sys.argv[1:])
    route = route_for(query)
    print(f"served_by={route.served_by} execution_class={route.execution_class} intent={route.canonical_intent}")
    sel = select_hybrid(query, execution_class=route.execution_class, canonical_intent=route.canonical_intent)
    if sel is None:
        print("no selection")
        return
    print(f"no_answer={sel.no_answer} hits={len(sel.hits)}\n")
    for i, h in enumerate(sel.hits, 1):
        body, cut = truncate_text(h.text, _MAX_CHUNK_CHARS)
        scores = {k: round(getattr(h, k), 3) for k in ("score", "dense", "bm25", "rrf") if isinstance(getattr(h, k, None), (int, float))}
        print(f"--- [{i}] {h.doc_id} | {h.section} | {scores} | {len(h.text)} chars{' (CUT)' if cut else ''}")
        print(body, "\n")


if __name__ == "__main__":
    main()
