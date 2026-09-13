"""Phase 11 unified eval suite — per-category scores, never a blended number."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "evals" / "catalog.json"
BASELINE_PATH = ROOT / "evals" / "baselines" / "offline.json"


@dataclass
class CategoryScore:
    id: str
    metric: str
    score: float
    hits: int
    n: int
    threshold: float
    misses: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.score + 1e-12 >= self.threshold

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return list(payload)
    return list(payload.get("cases") or [])


def score_scope(threshold: float) -> CategoryScore:
    from app.orchestration.understanding import classify_request

    cases = _load_cases(ROOT / "evals" / "scope_golden.json")
    hits = 0
    misses: list[str] = []
    for case in cases:
        result = classify_request(case["question"])
        ok = result.scope == case["expected_scope"] and result.route == case["expected_route"]
        if ok:
            hits += 1
        else:
            misses.append(
                f"{case['id']}: got {result.scope}/{result.route} "
                f"expected {case['expected_scope']}/{case['expected_route']}"
            )
    n = len(cases) or 1
    return CategoryScore(
        id="scope",
        metric="scope_and_route_accuracy",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_tools(threshold: float) -> CategoryScore:
    from app.tools.select import select_tool

    cases = _load_cases(ROOT / "evals" / "tool_cases.json")
    hits = 0
    misses: list[str] = []
    for case in cases:
        ui = {"current_page": case.get("page") or "unknown"}
        if case.get("exam_id"):
            ui["current_exam_id"] = case["exam_id"]
        sel = select_tool(query=case["query"], ui_context=ui)
        got = sel.tool.name if sel.tool else None
        if got == case["expected_tool"]:
            hits += 1
        else:
            misses.append(f"{case['id']}: expected={case['expected_tool']} got={got}")
    n = len(cases) or 1
    return CategoryScore(
        id="tools",
        metric="selection_accuracy",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_permissions(threshold: float) -> CategoryScore:
    from app.tools.select import select_tool

    cases = _load_cases(ROOT / "evals" / "permission_cases.json")
    hits = 0
    misses: list[str] = []
    for case in cases:
        ui = {"current_page": case.get("page") or "unknown"}
        if case.get("exam_id"):
            ui["current_exam_id"] = case["exam_id"]
        if case.get("role"):
            ui["user_role"] = case["role"]
        sel = select_tool(query=case["query"], ui_context=ui)
        denied = sel.reason.startswith("policy_denied")
        tool_name = sel.tool.name if sel.tool else None
        ok = denied == bool(case.get("expect_policy_denied")) and tool_name == case.get(
            "expect_tool"
        )
        if ok:
            hits += 1
        else:
            misses.append(
                f"{case['id']}: expected denied={case.get('expect_policy_denied')} "
                f"tool={case.get('expect_tool')} got denied={denied} tool={tool_name}"
            )
    n = len(cases) or 1
    return CategoryScore(
        id="permissions",
        metric="gate_accuracy",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_agent(threshold: float) -> CategoryScore:
    from app.core.config import Settings
    from app.orchestration.runtime_mode import decide_runtime_mode
    from app.orchestration.understanding import classify_request

    settings = Settings(
        APP_ENV="local",
        QUE_TOOLS_ENABLED=True,
        QUIZZER_INTERNAL_BASE_URL="http://127.0.0.1:9",
        QUE_SERVICE_KEY="test-service-key-not-for-production",
        QUE_JWT_SECRET="test-que-jwt-secret-not-for-production-32c",
    )
    cases = _load_cases(ROOT / "evals" / "agent_cases.json")
    hits = 0
    misses: list[str] = []
    for case in cases:
        ui = {"current_page": case.get("page") or "unknown"}
        if case.get("exam_id"):
            ui["current_exam_id"] = case["exam_id"]
        if case.get("role"):
            ui["user_role"] = case["role"]
        u = classify_request(case["query"])
        mode, reason, _sel = decide_runtime_mode(
            query=case["query"],
            ui_context=ui,
            route=u.route,
            data_need=u.data_need,
            complexity=u.complexity,
            settings=settings,
        )
        if mode == case["expected_mode"]:
            hits += 1
        else:
            misses.append(
                f"{case['id']}: expected={case['expected_mode']} got={mode} reason={reason}"
            )
    n = len(cases) or 1
    return CategoryScore(
        id="agent",
        metric="runtime_mode_accuracy",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_injection(threshold: float) -> CategoryScore:
    from app.guardrails.input import scan_user_text
    from app.guardrails.output import scan_output
    from app.guardrails.sanitize import neutralize_untrusted_text
    from app.orchestration.pipeline import decide_turn
    from app.schemas.chat import ChatMessage, ChatRequest

    cases = _load_cases(ROOT / "evals" / "injection_cases.json")
    hits = 0
    misses: list[str] = []
    for case in cases:
        kind = case.get("kind") or "direct"
        expected = case.get("expected")
        ok = False
        if kind == "indirect":
            cleaned = neutralize_untrusted_text(case.get("retrieved_payload") or "")
            ok = "[untrusted line omitted]" in cleaned and "ignore previous" not in cleaned.casefold()
        elif kind == "output":
            hit = scan_output(
                case.get("candidate_answer") or "",
                user_text=case.get("query") or "",
                role=case.get("role"),
                tool_blob=case.get("tool_blob"),
            )
            ok = hit is not None
        else:
            query = case.get("query") or ""
            decision = decide_turn(
                ChatRequest(messages=[ChatMessage(role="user", content=query)])
            )
            blocked = decision.early_model in {"guardrail:input", "scope:refuse"}
            scanned = scan_user_text(query) is not None
            ok = blocked and (expected in {"guardrail:input", "block", "refuse"} or scanned)
        if ok:
            hits += 1
        else:
            misses.append(f"{case['id']}: kind={kind} expected={expected}")
    n = len(cases) or 1
    return CategoryScore(
        id="injection",
        metric="block_rate",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_guardrail_fp(threshold: float) -> CategoryScore:
    from app.guardrails.input import scan_user_text

    cases = [
        c
        for c in _load_cases(ROOT / "evals" / "scope_golden.json")
        if c.get("expected_scope") == "in_scope"
    ]
    hits = 0
    misses: list[str] = []
    for case in cases:
        if scan_user_text(case["question"]) is None:
            hits += 1
        else:
            misses.append(f"{case['id']}: false positive on {case['question']!r}")
    n = len(cases) or 1
    return CategoryScore(
        id="guardrail_fp",
        metric="in_scope_clean_rate",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_groundedness(threshold: float) -> CategoryScore:
    from app.evals.groundedness import is_grounded

    cases = _load_cases(ROOT / "evals" / "groundedness_cases.json")
    hits = 0
    misses: list[str] = []
    for case in cases:
        got = is_grounded(
            case.get("candidate_answer") or "",
            case.get("context") or "",
            context_kind=case.get("context_kind") or "knowledge",
        )
        expect = bool(case.get("expect_grounded"))
        if got == expect:
            hits += 1
        else:
            misses.append(f"{case['id']}: got={got} expected={expect}")
    n = len(cases) or 1
    return CategoryScore(
        id="groundedness",
        metric="heuristic_accuracy",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_retrieval_keyword(threshold: float) -> CategoryScore:
    from app.knowledge.retrieve import _select_keyword

    payload = json.loads((ROOT / "evals" / "retrieval_cases.json").read_text(encoding="utf-8"))
    k = int(payload.get("k") or 5)
    cases = [c for c in list(payload.get("cases") or []) if not c.get("expect_no_answer")]
    recalls: list[float] = []
    misses: list[str] = []
    for case in cases:
        expected = set(case.get("expected_doc_ids") or [])
        sel = _select_keyword(
            [{"role": "user", "content": case["query"]}],
            query=case["query"],
        )
        got = [p for p in sel.pack_ids if p != "core"][:k]
        if not expected:
            rec = 1.0 if not got else 0.0
        else:
            rec = sum(1 for e in expected if e in got) / len(expected)
        recalls.append(rec)
        if rec < 1.0:
            misses.append(f"{case['id']}: expected={sorted(expected)} got={got}")
    n = len(recalls) or 1
    mean = sum(recalls) / n
    hits = sum(1 for r in recalls if r >= 1.0)
    return CategoryScore(
        id="retrieval",
        metric="mean_recall_at_k",
        score=mean,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses[:20],
        extra={"k": k, "perfect_hits": hits},
    )


def score_retrieval_dense(threshold: float) -> CategoryScore:
    from app.knowledge.dense import select_dense

    payload = json.loads((ROOT / "evals" / "retrieval_cases.json").read_text(encoding="utf-8"))
    k = int(payload.get("k") or 5)
    cases = [c for c in list(payload.get("cases") or []) if not c.get("expect_no_answer")]
    recalls: list[float] = []
    misses: list[str] = []
    for case in cases:
        expected = set(case.get("expected_doc_ids") or [])
        sel = select_dense(case["query"])
        if sel is None:
            return CategoryScore(
                id="retrieval_dense",
                metric="mean_recall_at_k",
                score=0.0,
                hits=0,
                n=len(cases),
                threshold=threshold,
                misses=["dense index not ready"],
            )
        got = [p for p in sel.pack_ids if p != "core"][:k]
        rec = (
            1.0
            if not expected and not got
            else (sum(1 for e in expected if e in got) / len(expected) if expected else 0.0)
        )
        recalls.append(rec)
        if rec < 1.0:
            misses.append(f"{case['id']}: expected={sorted(expected)} got={got}")
    n = len(recalls) or 1
    mean = sum(recalls) / n
    hits = sum(1 for r in recalls if r >= 1.0)
    return CategoryScore(
        id="retrieval_dense",
        metric="mean_recall_at_k",
        score=mean,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses[:20],
        extra={"k": k},
    )


def score_intent(threshold: float) -> CategoryScore:
    from app.orchestration.intent_catalog import finalize_understanding
    from app.orchestration.understanding import classify_request

    payload = json.loads((ROOT / "evals" / "efficiency_cases.json").read_text(encoding="utf-8"))
    cases = [c for c in list(payload.get("cases") or []) if c.get("expected_execution_class")]
    hits = 0
    misses: list[str] = []
    for case in cases:
        query = str(case["query"])
        result = finalize_understanding(classify_request(query), query)
        ok = result.execution_class == case["expected_execution_class"]
        expected_intent = case.get("expected_canonical_intent")
        if expected_intent:
            ok = ok and result.canonical_intent == expected_intent
        if ok:
            hits += 1
        else:
            misses.append(
                f"{case['id']}: got {result.execution_class}/{result.canonical_intent} "
                f"expected {case['expected_execution_class']}/{expected_intent}"
            )
    n = len(cases) or 1
    return CategoryScore(
        id="intent",
        metric="canonical_intent_accuracy",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


def score_efficiency(threshold: float) -> CategoryScore:
    from app.orchestration.pipeline import decide_turn
    from app.schemas.chat import ChatRequest, QueUiContext

    payload = json.loads((ROOT / "evals" / "efficiency_cases.json").read_text(encoding="utf-8"))
    cases = [c for c in list(payload.get("cases") or []) if not c.get("expect_llm")]
    hits = 0
    misses: list[str] = []
    for case in cases:
        ui = case.get("ui")
        request = ChatRequest(
            messages=[{"role": "user", "content": case["query"]}],
            context=QueUiContext.model_validate(ui) if ui else None,
        )
        decision = decide_turn(request)
        if decision.early_reply is not None:
            hits += 1
        else:
            misses.append(f"{case['id']}: expected 0-LLM early reply")
    n = len(cases) or 1
    return CategoryScore(
        id="efficiency",
        metric="zero_llm_simple_rate",
        score=hits / n,
        hits=hits,
        n=n,
        threshold=threshold,
        misses=misses,
    )


_RUNNERS = {
    "scope": score_scope,
    "tools": score_tools,
    "permissions": score_permissions,
    "agent": score_agent,
    "injection": score_injection,
    "guardrail_fp": score_guardrail_fp,
    "groundedness": score_groundedness,
    "retrieval": score_retrieval_keyword,
    "retrieval_dense": score_retrieval_dense,
    "intent": score_intent,
    "efficiency": score_efficiency,
}


def run_offline_suite(*, with_retrieval_dense: bool = False) -> list[CategoryScore]:
    catalog = load_catalog()
    results: list[CategoryScore] = []
    for entry in catalog.get("categories") or []:
        cid = entry["id"]
        if cid == "retrieval_dense" and not with_retrieval_dense:
            continue
        if not entry.get("offline", True) and cid != "retrieval_dense":
            continue
        runner = _RUNNERS.get(cid)
        if runner is None:
            continue
        results.append(runner(float(entry.get("threshold") or 0.0)))
    return results


def compare_to_baseline(
    scores: list[CategoryScore],
    baseline: dict[str, Any] | None,
) -> list[str]:
    """Return regression messages. Empty → no regression vs committed baseline."""
    if not baseline:
        return ["missing baseline file"]
    cats = (baseline.get("categories") or {}) if isinstance(baseline, dict) else {}
    problems: list[str] = []
    for score in scores:
        prior = cats.get(score.id) or {}
        prior_score = float(prior.get("score") or 0.0)
        if round(score.score, 4) < round(prior_score, 4):
            problems.append(
                f"{score.id}: {score.score:.4f} < baseline {prior_score:.4f}"
            )
    return problems


def load_baseline(path: Path | None = None) -> dict[str, Any]:
    target = path or BASELINE_PATH
    if not target.is_file():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def baseline_payload(scores: list[CategoryScore], *, thresholds: dict[str, float]) -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "thresholds": thresholds,
        "categories": {
            s.id: {
                "score": round(s.score, 4),
                "hits": s.hits,
                "n": s.n,
                "metric": s.metric,
                "threshold": s.threshold,
            }
            for s in scores
        },
    }
