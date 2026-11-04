"""Refined claim-level judge.

Same principle as ``claim_judge``: the LLM makes the semantic decisions, code computes
every score. What changes:

* Reference claims are atomic (one checkable fact each), frozen once.
* Every label carries a verbatim quote. Code checks the quote exists in the cited text.
  A label with no real quote cannot stay ``supported`` / ``partial`` / ``contradicted``.
* ``partial`` must name the missing element, otherwise it is ``supported``.
* Relevancy and answer relevancy are judged per sentence/list-item unit. Code splits the
  text into units (mechanical splitting only), so the denominator never depends on the LLM.
* Each metric has its own criteria section in the prompt.
* Items that are borderline, ``partial``, quote-failed, or a ``contradicted`` negative claim
  go to one batched adjudication call that checks the claim element by element. The
  adjudicator does not see the first verdict. When the two disagree, the score is reported
  as a band and the row is marked uncertain.
"""

from __future__ import annotations

import difflib
import re
import statistics
from typing import Literal

from pydantic import BaseModel, Field

PROMPT_VERSION = "refined-v1"

# ---- schemas ---------------------------------------------------------------------------


class _Facts(BaseModel):
    claims: list[str]


class _SplitCheck(BaseModel):
    class Item(BaseModel):
        claim_index: int
        facts: list[str]  # the independent facts inside the claim; one entry if already atomic

    items: list[Item]


class _RefItem(BaseModel):
    claim_index: int
    label: Literal["supported", "partial", "unsupported", "contradicted"]
    chunk: int = 0
    quote: str = ""
    missing_element: str = ""
    borderline: bool = False
    reason: str = ""


class _ChunkEvidence(BaseModel):
    chunk: int
    holds_evidence: bool


class _UnitLabel(BaseModel):
    unit: str
    label: Literal["useful", "not_useful"]


class _RetrieverOut(BaseModel):
    reference_claims: list[_RefItem]
    chunk_evidence: list[_ChunkEvidence]
    chunk_units: list[_UnitLabel]


class _AnswerClaim(BaseModel):
    claim: str
    label: Literal["supported", "unsupported", "contradicted"]
    chunk: int = 0
    quote: str = ""
    borderline: bool = False
    reason: str = ""


class _AnswerUnit(BaseModel):
    unit: str
    label: Literal["addresses_question", "off_topic"]


class _CovItem(BaseModel):
    claim_index: int
    label: Literal["conveyed", "partial", "missing", "contradicted"]
    quote: str = ""
    missing_element: str = ""
    borderline: bool = False
    reason: str = ""


class _GeneratorOut(BaseModel):
    answer_claims: list[_AnswerClaim]
    answer_units: list[_AnswerUnit]
    reference_coverage: list[_CovItem]


class _AdjElement(BaseModel):
    element: str
    present: Literal["yes", "no", "opposite"]
    quote: str = ""


class _AdjItem(BaseModel):
    item_id: str
    elements: list[_AdjElement] = Field(min_length=1)


class _AdjOut(BaseModel):
    items: list[_AdjItem]


# ---- mechanical text units -------------------------------------------------------------

_LIST_START = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9*\"'(])")


def split_units(text: str, *, drop_header: bool = False) -> list[str]:
    """Sentence and list-item units. Pure string handling; no judgment."""
    lines = text.replace("\r", "").split("\n")
    if drop_header and lines and lines[0].startswith("["):
        lines = lines[1:]
    paragraphs: list[list[str]] = [[]]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            paragraphs.append([])
        elif stripped.startswith("#"):
            continue  # markdown headings carry no facts of their own
        elif _LIST_START.match(line):
            paragraphs.append([stripped])
        else:
            paragraphs[-1].append(stripped)
    units: list[str] = []
    for para in paragraphs:
        joined = " ".join(para).strip()
        if not joined:
            continue
        for sent in _SENT_SPLIT.split(joined):
            sent = sent.strip()
            if len(sent) >= 3:
                units.append(sent)
    return units


def _norm(text: str) -> str:
    return re.sub(r"[\s*_`>#]+", " ", text).casefold().strip(" .\"'")


def quote_in(quote: str, text: str) -> bool:
    q = _norm(quote)
    return bool(q) and q in _norm(text)


# ---- prompts ---------------------------------------------------------------------------

_EXTRACT = """Split the reference answer into atomic claims.

An atomic claim states ONE checkable fact or ONE step. Test for every claim: could one part
be present in a source while another part is absent? If yes, split it.
Examples of what to split:
- "generates a six-character room code and a join URL" -> "generates a six-character room code" and "generates a join URL"
- "export to CSV, JSON, or Google Sheets" -> three claims, one per format
- "click Settings, then scroll to Proctoring" -> two steps

Keep the original wording as far as possible. Add nothing. Drop greetings. Keep the order.

Reference answer:
{text}

Return JSON: {{"claims": ["...", "..."]}}"""

_SPLIT_CHECK = """Each numbered claim below should state ONE checkable fact or step. For each claim, list the
independent facts it contains. If it already holds exactly one fact, list that one fact (the claim itself).
Two facts are independent when one could be present in a source while the other is absent.

Claims:
{claims}

Return JSON: {{"items": [{{"claim_index": 0, "facts": ["..."]}}]}} with one item per claim, in order."""

_RETRIEVER = """You check retrieved text for a product-help assistant. Use ONLY the text below. Write no scores.
Answer each task with its own criteria. Do not let one task influence another.

Question:
{query}

Reference claims (numbered from 0; each is one fact):
{claims}

Retrieved chunks (numbered from 1, rank 1 first):
{chunks}

TASK A, recall. For EVERY reference claim, in order, decide whether the chunks contain it.
Missing information is a finding, not an error. Labels:
- supported: every element of the claim is stated in, or directly follows from, a quote.
- partial: the claim's subject is stated but with a weaker scope or qualifier, OR the claim lists items and only some appear.
  You MUST name the exact missing element in "missing_element". If you cannot name one, the label is supported.
  Sharing only the topic or a keyword with the claim is never partial; that is unsupported.
- unsupported: no quote in the chunks states it.
- contradicted: a quote states the opposite. A source that is merely silent is never a contradiction.
  If the claim says something is absent ("X is not in Y") and a quote says it is absent, that is supported.
For supported, partial and contradicted give the chunk number and a VERBATIM quote copied from that chunk.
Set borderline=true only if a careful reader could reasonably choose a different label, and say why in "reason".

TASK B, precision. For EVERY chunk, in order, set holds_evidence=true if it contains a quote that supports or
contradicts at least one reference claim. This is about evidence for the claims, not about topic.

TASK C, contextual relevancy. Below, every chunk is cut into units with ids. For EVERY unit decide:
- useful: the unit contains information that helps answer the question.
- not_useful: it does not. A unit is not useful just because it is about the same product area.
Do not consider whether the chunk answers the whole question; judge each unit by itself.

Units:
{units}

Return JSON with keys "reference_claims", "chunk_evidence", "chunk_units"."""

_GENERATOR = """You check one answer from a product-help assistant. Use ONLY the text below. Write no scores.
Answer each task with its own criteria. Do not let one task influence another.

Question:
{query}

Retrieved chunks (numbered from 1):
{chunks}

Reference claims (numbered from 0; each is one fact):
{claims}

Answer to check:
{answer}

TASK A, faithfulness. Ignore the reference claims here. Split the answer into its factual claims. For each:
- supported: a chunk states it. Give chunk number and a VERBATIM quote from that chunk.
- unsupported: no chunk states it and none conflicts with it.
- contradicted: a chunk states the opposite. Give chunk number and quote.
Set borderline=true only if a careful reader could reasonably choose a different label, and say why in "reason".

TASK B, answer relevancy. The answer is cut into units with ids. For EVERY unit:
- addresses_question: it helps answer the question asked.
- off_topic: it does not (greetings, offers of more help, unrelated advice).

Answer units:
{units}

TASK C, correctness. Ignore the chunks here. For EVERY reference claim, in order, decide whether the answer gives it:
- conveyed: the answer states the same fact or step. Give a VERBATIM quote from the answer.
- partial: the answer states it with a weaker scope, or states only some listed items.
  You MUST name the exact missing element in "missing_element". If you cannot, the label is conveyed.
- missing: the answer does not state it. Topic overlap is not partial.
- contradicted: the answer states the opposite. Give a VERBATIM quote from the answer.
Set borderline=true only if a careful reader could reasonably choose a different label.

Return JSON with keys "answer_claims", "answer_units", "reference_coverage"."""

_ADJUDICATE = """You verify claims against evidence, one claim at a time. Use ONLY the evidence given with each item.
For each item:
1. List the separate elements the claim asserts (one element if it asserts one thing).
2. For each element say: "yes" if the evidence states it (give a VERBATIM quote), "no" if the evidence does not
   state it, or "opposite" if the evidence states the opposite (give the quote).
Do not guess what the evidence might imply beyond what it states.

{items}

Return JSON: {{"items": [{{"item_id": "...", "elements": [{{"element": "...", "present": "yes|no|opposite", "quote": ""}}]}}]}}"""


def _numbered(items: list[str], start: int) -> str:
    return "\n".join(f"[{i}] {t}" for i, t in enumerate(items, start=start)) or "(none)"


def _chunks_text(chunks: list[str]) -> str:
    return "\n\n".join(f"[{i}] {c}" for i, c in enumerate(chunks, start=1)) or "(none)"


# ---- atomic claim freezing -------------------------------------------------------------


def extract_atomic(judge, text: str) -> list[dict]:
    """Two judge calls: extract, then split-check. Returns [{text, parent_id}]."""
    first = judge.generate(_EXTRACT.format(text=text), schema=_Facts)
    claims = [c.strip() for c in first.claims if c.strip()]
    if not claims:
        return []
    checked = judge.generate(_SPLIT_CHECK.format(claims=_numbered(claims, 0)), schema=_SplitCheck)
    by_index = {i.claim_index: [f.strip() for f in i.facts if f.strip()] for i in checked.items}
    out: list[dict] = []
    for idx, claim in enumerate(claims):
        facts = by_index.get(idx) or [claim]
        if len(facts) == 1:
            out.append({"text": claim, "parent_id": None})
        else:
            out.extend({"text": f, "parent_id": idx} for f in facts)
    return out


def claim_set_agreement(a: list[str], b: list[str]) -> float:
    """Share of claims in ``a`` that have a close match in ``b`` (text similarity >= 0.6)."""
    if not a:
        return 1.0 if not b else 0.0
    hits = 0
    for x in a:
        best = max((difflib.SequenceMatcher(None, _norm(x), _norm(y)).ratio() for y in b), default=0.0)
        hits += best >= 0.6
    return hits / len(a)


# ---- verification and normalization ----------------------------------------------------


def _chunk_text(chunks: list[str], index: int) -> str:
    return chunks[index - 1] if 1 <= index <= len(chunks) else ""


def _cleanup_ref(items: list[_RefItem], chunks: list[str]) -> list[dict]:
    """Apply the rubric's own consistency rules to what the judge wrote. Records every change."""
    out = []
    for it in items:
        d = it.model_dump()
        d["flags"] = []
        if d["label"] in ("supported", "partial", "contradicted"):
            text = _chunk_text(chunks, d["chunk"]) or "\n".join(chunks)
            if not quote_in(d["quote"], text):
                d["flags"].append("quote_failed")
                d["label"] = "unsupported"
        if d["label"] == "partial" and not d["missing_element"].strip():
            d["flags"].append("partial_without_missing_element")
            d["label"] = "supported"
        out.append(d)
    return out


def _cleanup_cov(items: list[_CovItem], answer: str) -> list[dict]:
    out = []
    for it in items:
        d = it.model_dump()
        d["flags"] = []
        if d["label"] in ("conveyed", "partial", "contradicted") and not quote_in(d["quote"], answer):
            d["flags"].append("quote_failed")
            d["label"] = "missing"
        if d["label"] == "partial" and not d["missing_element"].strip():
            d["flags"].append("partial_without_missing_element")
            d["label"] = "conveyed"
        out.append(d)
    return out


def _cleanup_answer_claims(items: list[_AnswerClaim], chunks: list[str]) -> list[dict]:
    out = []
    for it in items:
        d = it.model_dump()
        d["flags"] = []
        if d["label"] in ("supported", "contradicted"):
            text = _chunk_text(chunks, d["chunk"]) or "\n".join(chunks)
            if not quote_in(d["quote"], text):
                d["flags"].append("quote_failed")
                d["label"] = "unsupported"
        out.append(d)
    return out


# ---- scores: pure functions of labels --------------------------------------------------

_REF_W = {"supported": 1.0, "partial": 0.5, "unsupported": 0.0, "contradicted": 0.0}
_COV_W = {"conveyed": 1.0, "partial": 0.5, "missing": 0.0, "contradicted": -1.0}


def _precision(flags: list[bool]) -> float:
    if not any(flags):
        return 0.0
    total, hits = 0.0, 0
    for k, flag in enumerate(flags, start=1):
        hits += flag
        total += (hits / k) * flag
    return total / sum(flags)


def compute_scores(state: dict) -> dict:
    ref, cov, ans = state["ref"], state["cov"], state["answer_claims"]
    chunk_flags = [c["holds_evidence"] for c in sorted(state["chunk_evidence"], key=lambda c: c["chunk"])]
    units_r, units_a = state["chunk_units"], state["answer_units"]
    return {
        "recall": statistics.mean(_REF_W[r["label"]] for r in ref),
        "precision": _precision(chunk_flags),
        "relevancy": (sum(u["label"] == "useful" for u in units_r) / len(units_r)) if units_r else 0.0,
        "faithfulness": (sum(c["label"] == "supported" for c in ans) / len(ans)) if ans else 1.0,
        "answer_relevancy": (sum(u["label"] == "addresses_question" for u in units_a) / len(units_a)) if units_a else 0.0,
        "correctness": max(0.0, statistics.mean(_COV_W[c["label"]] for c in cov)),
        "unsupported_share": (sum(c["label"] == "unsupported" for c in ans) / len(ans)) if ans else 0.0,
        "contradicted_claims": sum(c["label"] == "contradicted" for c in ans),
    }


# ---- judge passes ----------------------------------------------------------------------


def _check_indexes(items, n: int, key: str, start: int, what: str) -> None:
    got = [getattr(i, key) if not isinstance(i, dict) else i[key] for i in items]
    if got != list(range(start, start + n)):
        raise ValueError(f"{what}: expected {start}..{start + n - 1} once each, got {got}")


def _units_for_chunks(chunks: list[str]) -> dict[str, str]:
    units: dict[str, str] = {}
    for ci, chunk in enumerate(chunks, start=1):
        for ui, text in enumerate(split_units(chunk, drop_header=True), start=1):
            units[f"{ci}.{ui}"] = text
    return units


def _retriever_pass(judge, query: str, claims: list[str], chunks: list[str]) -> dict:
    units = _units_for_chunks(chunks)
    prompt = _RETRIEVER.format(
        query=query,
        claims=_numbered(claims, 0),
        chunks=_chunks_text(chunks),
        units="\n".join(f"[{k}] {v}" for k, v in units.items()) or "(none)",
    )
    last: Exception | None = None
    for _ in range(2):
        out = judge.generate(prompt, schema=_RetrieverOut)
        try:
            _check_indexes(out.reference_claims, len(claims), "claim_index", 0, "reference_claims")
            _check_indexes(out.chunk_evidence, len(chunks), "chunk", 1, "chunk_evidence")
            if [u.unit for u in out.chunk_units] != list(units):
                if len(out.chunk_units) != len(units):
                    raise ValueError(f"chunk_units: unit ids do not match the units given: got {[u.unit for u in out.chunk_units]} want {list(units)}")
                for u, key in zip(out.chunk_units, units, strict=True):
                    u.unit = key
            return {
                "ref": _cleanup_ref(out.reference_claims, chunks),
                "chunk_evidence": [c.model_dump() for c in out.chunk_evidence],
                "chunk_units": [{**u.model_dump(), "text": units[u.unit]} for u in out.chunk_units],
            }
        except ValueError as exc:
            last = exc
    raise last  # type: ignore[misc]


def _generator_pass(judge, query: str, claims: list[str], chunks: list[str], answer: str) -> dict:
    answer = answer[:3000]
    units = {f"a{i}": t for i, t in enumerate(split_units(answer), start=1)}
    prompt = _GENERATOR.format(
        query=query,
        chunks=_chunks_text(chunks),
        claims=_numbered(claims, 0),
        answer=answer,
        units="\n".join(f"[{k}] {v}" for k, v in units.items()) or "(none)",
    )
    last: Exception | None = None
    for _ in range(2):
        out = judge.generate(prompt, schema=_GeneratorOut)
        try:
            _check_indexes(out.reference_coverage, len(claims), "claim_index", 0, "reference_coverage")
            repaired = False
            if [u.unit for u in out.answer_units] != list(units):
                # Only the id text is wrong (e.g. the unit text echoed back). Align by order when the count
                # is right; a different count means the judge skipped or merged units, which stays a failure.
                if len(out.answer_units) != len(units):
                    raise ValueError(f"answer_units: unit ids do not match the units given: got {[u.unit for u in out.answer_units]} want {list(units)}")
                for u, key in zip(out.answer_units, units, strict=True):
                    u.unit = key
                repaired = True
            return {
                "cov": _cleanup_cov(out.reference_coverage, answer),
                "answer_claims": _cleanup_answer_claims(out.answer_claims, chunks),
                "answer_units": [{**u.model_dump(), "text": units[u.unit]} for u in out.answer_units],
                "ids_repaired": repaired,
            }
        except ValueError as exc:
            last = exc
    raise last  # type: ignore[misc]


# ---- adjudication ----------------------------------------------------------------------

_NEG = re.compile(r"\b(not|no|never|cannot|can't|isn't|aren't|without|there is no)\b", re.IGNORECASE)


def _triggers(state: dict, claims: list[str]) -> list[dict]:
    """Items that need a second look. Everything else keeps its first label."""
    items = []
    for r in state["ref"]:
        negative = r["label"] == "contradicted" and bool(_NEG.search(claims[r["claim_index"]]))
        if r["label"] == "partial" or r["borderline"] or r["flags"] or negative:
            items.append({"id": f"ref{r['claim_index']}", "kind": "ref", "index": r["claim_index"]})
    for c in state["cov"]:
        negative = c["label"] == "contradicted" and bool(_NEG.search(claims[c["claim_index"]]))
        if c["label"] == "partial" or c["borderline"] or c["flags"] or negative:
            items.append({"id": f"cov{c['claim_index']}", "kind": "cov", "index": c["claim_index"]})
    for i, c in enumerate(state["answer_claims"]):
        if c["borderline"] or c["flags"]:
            items.append({"id": f"ans{i}", "kind": "ans", "index": i})
    return items


def _label_from_elements(kind: str, elements: list[_AdjElement]) -> str:
    present = [e.present for e in elements]
    if "opposite" in present:
        return "contradicted"
    yes = present.count("yes")
    if yes == len(present):
        return {"ref": "supported", "cov": "conveyed", "ans": "supported"}[kind]
    if yes == 0:
        return {"ref": "unsupported", "cov": "missing", "ans": "unsupported"}[kind]
    return {"ref": "partial", "cov": "partial", "ans": "unsupported"}[kind]  # answer claims have no partial


def _adjudicate(
    judge,
    state: dict,
    claims: list[str],
    chunks: list[str],
    answer: str,
    trig: list[dict],
    generator_chunks: list[str] | None = None,
) -> dict:
    blocks, meta = [], {}
    gen_chunks = chunks if generator_chunks is None else generator_chunks
    all_chunks = _chunks_text(chunks)
    for t in trig:
        if t["kind"] == "ref":
            r = state["ref"][t["index"]]
            claim, evidence, where = claims[t["index"]], _chunk_text(chunks, r["chunk"]) or all_chunks, "retrieved chunks"
        elif t["kind"] == "cov":
            claim, evidence, where = claims[t["index"]], answer, "answer"
        else:
            c = state["answer_claims"][t["index"]]
            claim = c["claim"]
            evidence = _chunk_text(gen_chunks, c["chunk"]) or _chunks_text(gen_chunks)
            where = "context given to the generator"
        blocks.append(f"ITEM {t['id']}\nClaim: {claim}\nEvidence ({where}):\n{evidence}\n")
        meta[t["id"]] = t
    out = judge.generate(_ADJUDICATE.format(items="\n".join(blocks)), schema=_AdjOut)
    verdicts = {}
    for item in out.items:
        t = meta.get(item.item_id)
        if not t:
            continue
        # An element only counts as present/opposite if its quote exists in the evidence.
        text = answer if t["kind"] == "cov" else ("\n".join(gen_chunks if t["kind"] == "ans" else chunks))
        checked = []
        for e in item.elements:
            if e.present != "no" and not quote_in(e.quote, text):
                e = e.model_copy(update={"present": "no"})
            checked.append(e)
        verdicts[item.item_id] = {
            "label": _label_from_elements(t["kind"], checked),
            "elements": [e.model_dump() for e in checked],
        }
    return verdicts


def _apply(state: dict, trig: list[dict], verdicts: dict) -> dict:
    new = {k: [dict(x) for x in v] if isinstance(v, list) else v for k, v in state.items()}
    for t in trig:
        v = verdicts.get(t["id"])
        if not v:
            continue
        target = {"ref": "ref", "cov": "cov", "ans": "answer_claims"}[t["kind"]]
        new[target][t["index"]]["label"] = v["label"]
    return new


# ---- public entry ----------------------------------------------------------------------


def judge_row(
    judge,
    query: str,
    claims: list[str],
    chunks: list[str],
    answer: str,
    *,
    adjudicate: bool = True,
    generator_chunks: list[str] | None = None,
) -> dict:
    """Retriever scores use ``chunks`` (what retrieval returned). Faithfulness uses
    ``generator_chunks`` (what the LLM was actually given) when supplied; omitting it
    keeps the old behaviour of scoring both against the same list."""
    gen_chunks = chunks if generator_chunks is None else generator_chunks
    r = _retriever_pass(judge, query, claims, chunks)
    g = _generator_pass(judge, query, claims, gen_chunks, answer)
    state = {**r, **g}
    first = compute_scores(state)
    trig = _triggers(state, claims) if adjudicate else []
    verdicts: dict = {}
    final_state = state
    if trig:
        verdicts = _adjudicate(judge, state, claims, chunks, answer, trig, gen_chunks)
        final_state = _apply(state, trig, verdicts)
    final = compute_scores(final_state)
    changed = [t["id"] for t in trig if verdicts.get(t["id"]) and verdicts[t["id"]]["label"] != _first_label(state, t)]
    band = {k: (min(first[k], final[k]), max(first[k], final[k])) for k in final}
    return {
        "scores": final,
        "scores_first": first,
        "band": band,
        "uncertain": bool(changed),
        "adjudicated": [t["id"] for t in trig],
        "adjudication_changed": changed,
        "state_first": state,
        "state_final": final_state,
        "adjudication": verdicts,
    }


def _first_label(state: dict, t: dict) -> str:
    target = {"ref": "ref", "cov": "cov", "ans": "answer_claims"}[t["kind"]]
    return state[target][t["index"]]["label"]
