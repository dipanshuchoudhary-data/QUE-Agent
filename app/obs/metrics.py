"""In-process latency/cost ring, percentiles, and log-only alerts."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

import structlog

from app.core.config import Settings, get_settings
from app.obs.trace import TurnTrace

logger = structlog.get_logger(__name__)

_lock = threading.Lock()
_turns: deque[dict[str, Any]] = deque()
_alert_until: dict[str, float] = {}


def reset_obs() -> None:
    with _lock:
        _turns.clear()
        _alert_until.clear()


def _ring_size(settings: Settings | None = None) -> int:
    cfg = settings or get_settings()
    return max(32, int(cfg.que_obs_ring_size or 512))


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    idx = min(len(ordered) - 1, max(0, int((p / 100.0) * (len(ordered) - 1))))
    return round(ordered[idx], 2)


def record_turn(trace: TurnTrace, *, latency_ms: float, settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    e2e = round(latency_ms, 2)
    row: dict[str, Any] = {
        "request_id": trace.request_id,
        "user_hash": trace.user_hash,
        "route": trace.route,
        "freshness": trace.freshness,
        "model": trace.model,
        "latency_ms": e2e,
        "prompt_tokens": trace.prompt_tokens,
        "completion_tokens": trace.completion_tokens,
        "reasoning_tokens": trace.reasoning_tokens,
        "cost_usd": trace.cost_usd,
        "error": trace.error,
        "spans": [
            {"name": s.name, "ms": s.ms, "ok": s.ok, "extra": s.extra}
            for s in trace.spans
        ],
        "ts": time.time(),
    }
    with _lock:
        _turns.append(row)
        while len(_turns) > _ring_size(cfg):
            _turns.popleft()
    _maybe_alert(cfg)
    _maybe_jsonl(row, cfg)
    logger.info("que_turn_trace", **trace.as_log_dict(), latency_ms=e2e)


def snapshot(settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    with _lock:
        rows = list(_turns)
    lat = [float(r["latency_ms"]) for r in rows]
    by_span: dict[str, list[float]] = {}
    by_tool: dict[str, dict[str, Any]] = {}
    for row in rows:
        for span in row.get("spans") or []:
            by_span.setdefault(str(span.get("name") or "unknown"), []).append(float(span.get("ms") or 0))
            if span.get("name") == "tool":
                extra = span.get("extra") or {}
                tool_name = str(extra.get("name") or "unknown")
                bucket = by_tool.setdefault(tool_name, {"calls": 0, "errors": 0, "ms": []})
                bucket["calls"] += 1
                if not span.get("ok", True):
                    bucket["errors"] += 1
                bucket["ms"].append(float(span.get("ms") or 0))
    tools_snapshot = {
        name: {
            "calls": b["calls"],
            "errors": b["errors"],
            "error_rate": round(b["errors"] / b["calls"], 4) if b["calls"] else 0.0,
            "p50": percentile(b["ms"], 50),
            "p95": percentile(b["ms"], 95),
            "p99": percentile(b["ms"], 99),
        }
        for name, b in sorted(by_tool.items())
    }
    success = [r for r in rows if not r.get("error")]
    priced = [
        float(r["cost_usd"]) if r.get("cost_usd") is not None else 0.0 for r in success
    ]
    tokens = sum(int(r.get("prompt_tokens") or 0) + int(r.get("completion_tokens") or 0) for r in rows)
    errors = sum(1 for r in rows if r.get("error"))
    by_model: dict[str, int] = {}
    by_route: dict[str, int] = {}
    ttft_vals: list[float] = []
    attempt_vals: list[float] = []
    for row in rows:
        model = str(row.get("model") or "unknown")
        route = str(row.get("route") or "unknown")
        by_model[model] = by_model.get(model, 0) + 1
        by_route[route] = by_route.get(route, 0) + 1
        for span in row.get("spans") or []:
            name = str(span.get("name") or "")
            if name == "ttft":
                ttft_vals.append(float(span.get("ms") or 0))
            if name == "llm":
                extra = span.get("extra") or {}
                if "attempt" in extra:
                    attempt_vals.append(float(extra.get("attempt") or 0))
    return {
        "n": len(rows),
        "errors": errors,
        "error_rate": round(errors / len(rows), 4) if rows else 0.0,
        "latency_ms": {
            "p50": percentile(lat, 50),
            "p95": percentile(lat, 95),
            "p99": percentile(lat, 99),
        },
        "ttft_ms": {
            "p50": percentile(ttft_vals, 50),
            "p95": percentile(ttft_vals, 95),
            "p99": percentile(ttft_vals, 99),
            "n": len(ttft_vals),
        },
        "llm_attempts": {
            "p50": percentile(attempt_vals, 50),
            "p95": percentile(attempt_vals, 95),
            "mean": round(sum(attempt_vals) / len(attempt_vals), 3) if attempt_vals else None,
            "n": len(attempt_vals),
        },
        "spans": {
            name: {
                "p50": percentile(vals, 50),
                "p95": percentile(vals, 95),
                "p99": percentile(vals, 99),
            }
            for name, vals in sorted(by_span.items())
        },
        "tools": tools_snapshot,
        "tokens_total": tokens,
        "cost_usd_total": round(sum(priced), 6) if priced else 0.0,
        "cost_per_successful_task": round(sum(priced) / len(priced), 8) if priced else 0.0,
        "budget_breaches": sum(
            1 for r in rows if str(r.get("model") or "").startswith("budget:")
        ),
        "by_model": by_model,
        "by_route": by_route,
        "alerts": list_active_alerts(cfg),
    }


def list_active_alerts(settings: Settings | None = None) -> list[dict[str, Any]]:
    cfg = settings or get_settings()
    now = time.time()
    with _lock:
        return [
            {"kind": kind, "until": until}
            for kind, until in _alert_until.items()
            if until > now
        ] or []


def _maybe_alert(cfg: Settings) -> None:
    with _lock:
        rows = list(_turns)
    if len(rows) < 8:
        return
    window = rows[-32:]
    n = len(window)
    err = sum(1 for r in window if r.get("error"))
    error_rate = err / n
    minute_ago = time.time() - 60.0
    usd_min = sum(
        float(r["cost_usd"] or 0)
        for r in window
        if r.get("ts", 0) >= minute_ago and r.get("cost_usd") is not None
    )
    _fire(cfg, "error_rate", error_rate >= float(cfg.que_alert_error_rate), extra={"error_rate": round(error_rate, 4)})
    _fire(
        cfg,
        "cost_anomaly",
        usd_min >= float(cfg.que_alert_usd_per_minute) > 0,
        extra={"usd_per_minute": round(usd_min, 6)},
    )


def _fire(cfg: Settings, kind: str, tripped: bool, *, extra: dict[str, Any]) -> None:
    if not tripped:
        return
    now = time.time()
    cooldown = float(cfg.que_alert_cooldown_seconds or 60.0)
    with _lock:
        until = _alert_until.get(kind, 0.0)
        if until > now:
            return
        _alert_until[kind] = now + cooldown
    logger.warning("que_alert", kind=kind, **extra)


def _maybe_jsonl(row: dict[str, Any], cfg: Settings) -> None:
    path_raw = (cfg.que_obs_jsonl or "").strip()
    if not path_raw:
        return
    path = Path(path_raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    except OSError:
        return
