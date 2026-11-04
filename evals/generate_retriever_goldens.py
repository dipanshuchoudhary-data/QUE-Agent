"""Generate candidate retriever goldens from knowledge/ with DeepEval Synthesizer.

Each candidate is built from one real guide chunk, so its expected_output and
expected guide id come from known source text. Candidates are NOT trusted until
a human sets ``human_verified`` in evals/retriever_goldens.json.

    uv run python -m evals.generate_retriever_goldens --num 40
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import EvolutionConfig, FiltrationConfig, StylingConfig

from app.knowledge.ingest import _chunk_doc, _is_retrievable, _load_manifest
from evals.judge import QueJudge

_ROOT = Path(__file__).resolve().parents[1]
OUT = _ROOT / "tests" / "evals" / ".dataset.json"
MIN_CHARS = 250


def _candidate_contexts(num: int, seed: int) -> list[tuple[str, str, str]]:
    manifest = _load_manifest()
    version = str(manifest.get("version") or "0")
    by_doc: dict[str, list[tuple[str, str, str]]] = {}
    for doc in manifest.get("documents") or []:
        if not _is_retrievable(doc):
            continue
        for chunk in _chunk_doc(doc, corpus_version=version):
            if chunk.char_count >= MIN_CHARS:
                by_doc.setdefault(chunk.doc_id, []).append(
                    (chunk.doc_id, chunk.section, f"{chunk.section}\n{chunk.text}")
                )
    rng = random.Random(seed)
    for items in by_doc.values():
        rng.shuffle(items)
    picked: list[tuple[str, str, str]] = []
    # Round-robin across guides so no single guide dominates the set.
    while len(picked) < num and any(by_doc.values()):
        for doc_id in sorted(by_doc):
            if by_doc[doc_id] and len(picked) < num:
                picked.append(by_doc[doc_id].pop())
    return picked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    picked = _candidate_contexts(args.num, args.seed)
    judge = QueJudge()
    synth = Synthesizer(
        model=judge,
        async_mode=False,
        # Keep questions close to what a user types; evolutions rewrite them away from the source chunk.
        evolution_config=EvolutionConfig(num_evolutions=0),
        filtration_config=FiltrationConfig(max_quality_retries=1, critic_model=judge),
        styling_config=StylingConfig(
            scenario="Teachers and students asking the Quizzer help assistant how to do something in the product",
            task="Answer product-help questions accurately from Quizzer guides, with click paths",
            input_format="One short natural question a real user would type, without quoting guide headings",
            expected_output_format="Concise, actionable answer grounded only in the provided guide text",
        ),
    )
    rows: list[dict] = []
    batch = 5
    for start in range(0, len(picked), batch):
        part = picked[start : start + batch]
        try:
            goldens = synth.generate_goldens_from_contexts(
                contexts=[[text] for _doc, _sec, text in part],
                include_expected_output=True,
                max_goldens_per_context=1,
                source_files=[doc for doc, _sec, _text in part],
            )
        except Exception as exc:  # noqa: BLE001 - keep finished batches when the judge flakes
            print(f"batch at {start} failed: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
            continue
        for golden in goldens:
            source = golden.source_file or ""
            rows.append(
                {
                    "id": f"s{len(rows) + 1:02d}",
                    "query": golden.input,
                    "expected_output": golden.expected_output,
                    "expected_doc_ids": [source] if source else [],
                    "source_context": list(golden.context or []),
                    "origin": "synthesizer",
                    "human_verified": False,
                }
            )
        # Save after every batch so a later failure does not lose finished rows.
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"goldens": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{len(rows)} candidates so far -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
