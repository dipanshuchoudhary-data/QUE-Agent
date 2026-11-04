"""Benchmark chunk-size floor and ceiling on retrieval quality.

    uv run python scripts/benchmark_chunk_size.py            # all variants
    uv run python scripts/benchmark_chunk_size.py --only f400_m900

Each variant gets its own index under ``data/chroma_bench/<name>`` (production
``data/chroma`` is never touched): it re-chunks the guides with that floor
(``QUE_CHUNK_TARGET_CHARS``: neighbouring pieces below it are joined) and ceiling
(``QUE_CHUNK_MAX_CHARS``: the split limit; the injection cap follows it), rebuilds the
index, then runs the same judged retriever eval (production mode, same rows, top-k 2 /
pool 4). Writes ``evals/diagnostics/CHUNK_SIZE_BENCH.md``.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# name: (floor, ceiling). floor 0 = no merging (one chunk per heading section).
VARIANTS: dict[str, tuple[int, int]] = {
    "f0_m900": (0, 900),
    "f400_m900": (400, 900),
    "f400_m700": (400, 700),
    "f400_m1200": (400, 1200),
    "f600_m900": (600, 900),
}
OUT = ROOT / "evals" / "baselines"
BENCH = ROOT / "data" / "chroma_bench"


def _run(cmd: list[str], env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _chunk_stats(chroma: Path) -> dict:
    corpus = json.loads((chroma / "bm25_corpus.json").read_text(encoding="utf-8"))
    entries = corpus["chunks"] if isinstance(corpus, dict) and "chunks" in corpus else corpus
    lens = sorted(len(e["text"]) for e in entries)
    return {
        "chunks": len(lens),
        "median": int(statistics.median(lens)),
        "under_400": sum(x < 400 for x in lens),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    names = [n for n in VARIANTS if not args.only or n in args.only]

    for name in names:
        floor, ceil = VARIANTS[name]
        chroma = BENCH / name
        env = {
            **os.environ,
            "QUE_SCOREBOOK_OFF": "1",
            "QUE_CHROMA_PATH": str(chroma),
            "QUE_CHUNK_TARGET_CHARS": str(floor),
            "QUE_CHUNK_MAX_CHARS": str(ceil),
        }
        out = OUT / f"chunkbench_{name}.json"
        if not out.exists() or "summary" not in json.loads(out.read_text(encoding="utf-8")):
            print("building + judging", name, flush=True)
            _run([sys.executable, "-m", "app.knowledge", "--force"], env)
            _run(
                [sys.executable, "scripts/run_retriever_judged_eval.py", "--mode", "production",
                 "--include-unverified", "--out", str(out)],
                env,
            )
        else:
            print("reusing", name, flush=True)

    rows = []
    for name, (floor, ceil) in VARIANTS.items():
        out = OUT / f"chunkbench_{name}.json"
        if not out.exists():
            continue
        data = json.loads(out.read_text(encoding="utf-8"))
        if "summary" not in data:
            continue
        s = data["summary"]
        st = _chunk_stats(BENCH / name) if (BENCH / name / "bm25_corpus.json").exists() else {}
        rows.append((name, floor, ceil, s, st))

    lines = [
        "# Chunk size benchmark (floor = join pieces below it; ceiling = split above it)",
        "",
        "Same rows, top-k 2, pool 4, judged retriever eval (production mode). One judge run per "
        "variant, so differences under about 0.02 are noise.",
        "",
        "| variant | floor | ceiling | chunks | median chars | chunks <400 | recall | precision | relevancy | average | recall<=0.5 | injected chars |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, floor, ceil, s, st in rows:
        lines.append(
            f"| {name} | {floor} | {ceil} | {st.get('chunks', '')} | {st.get('median', '')} | {st.get('under_400', '')} "
            f"| {s['contextual_recall_mean']:.3f} | {s['contextual_precision_mean']:.3f} | "
            f"{s['contextual_relevancy_mean']:.3f} | {s['metrics_average']:.3f} | "
            f"{len(s['recall_cases_below_0_5'])} | {s['injected_chars_mean']:.0f} |"
        )
    path = ROOT / "evals" / "diagnostics" / "CHUNK_SIZE_BENCH.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    main()
