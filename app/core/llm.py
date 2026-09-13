"""LLM gateway — OpenAI-compatible chat with key/model round-robin + failover."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langsmith import traceable
from langsmith.run_helpers import trace

from app.core.config import Settings, get_settings
from app.obs.context import current_trace
from app.obs.cost import TokenUsage, extract_usage

logger = logging.getLogger(__name__)

_NON_RETRYABLE_CODES = {400, 401, 403, 404, 422}
_RETRYABLE_CODES = {408, 429, 500, 502, 503, 504}

_circuit_lock = threading.Lock()
_llm_failures = 0
_llm_circuit_until = 0.0
_last_usage = TokenUsage()


class LLMError(RuntimeError):
    """Raised when the upstream LLM call fails or is misconfigured."""


@dataclass(frozen=True)
class ChatLane:
    """One (model, key_index) pair. Never log ``api_key``."""

    model: str
    key_index: int
    api_key: str


_lock = threading.Lock()
_key_ticket = 0
_model_ticket = 0


def reset_gateway_counters() -> None:
    """Test helper — restart round-robin at index 0."""
    global _key_ticket, _model_ticket
    with _lock:
        _key_ticket = 0
        _model_ticket = 0
    reset_llm_circuit()


def reset_llm_circuit() -> None:
    global _llm_failures, _llm_circuit_until
    with _circuit_lock:
        _llm_failures = 0
        _llm_circuit_until = 0.0


def force_llm_circuit_open(ttl_seconds: float = 30.0) -> None:
    global _llm_circuit_until, _llm_failures
    with _circuit_lock:
        _llm_failures = 0
        _llm_circuit_until = time.time() + max(0.1, ttl_seconds)


def llm_circuit_open(settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    if int(cfg.que_llm_circuit_failures) <= 0:
        return False
    with _circuit_lock:
        return time.time() < _llm_circuit_until


def last_llm_usage() -> TokenUsage:
    return _last_usage


def _record_llm_success() -> None:
    global _llm_failures
    with _circuit_lock:
        _llm_failures = 0


def _record_llm_failure(settings: Settings) -> None:
    global _llm_failures, _llm_circuit_until
    with _circuit_lock:
        _llm_failures += 1
        if _llm_failures >= max(1, int(settings.que_llm_circuit_failures)):
            _llm_circuit_until = time.time() + float(settings.que_llm_circuit_ttl_seconds)
            _llm_failures = 0
            logger.warning(
                "que_llm_circuit_open ttl=%s",
                settings.que_llm_circuit_ttl_seconds,
            )


def _take_tickets(*, rotate_model: bool) -> tuple[int, int]:
    global _key_ticket, _model_ticket
    with _lock:
        key_ticket = _key_ticket
        _key_ticket += 1
        if rotate_model:
            model_ticket = _model_ticket
            _model_ticket += 1
        else:
            model_ticket = _model_ticket
        return key_ticket, model_ticket


def prefer_strong_model(*, complexity: str | None, runtime_mode: str | None) -> bool:
    return (complexity or "").strip() == "multi_step" or (runtime_mode or "").strip() == "agent"


def reasoning_enabled_for_turn(
    *,
    execution_class: str | None = None,
    complexity: str | None = None,
    runtime_mode: str | None = None,
) -> bool:
    """Reasoning models stay off for simple how-tos; on for diagnosis/agent."""
    if (runtime_mode or "").strip() == "agent" or (complexity or "").strip() == "multi_step":
        return True
    return (execution_class or "").strip() == "tool_required"


def _model_extra_body(*, reasoning: bool) -> dict[str, Any]:
    if reasoning:
        return {"reasoning": {"enabled": True}}
    return {"reasoning": {"enabled": False, "effort": "none"}}


def _is_retryable(exc: BaseException) -> bool:
    """Retry timeouts and 5xx/429. Never retry auth, forbidden, or malformed requests."""
    code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if code is None and response is not None:
        code = getattr(response, "status_code", None)
    if code in _NON_RETRYABLE_CODES:
        return False
    if code in _RETRYABLE_CODES:
        return True
    text = str(exc).lower()
    if any(
        n in text
        for n in (
            "unauthorized",
            "invalid api key",
            "forbidden",
            "permission denied",
            "400 bad request",
        )
    ):
        return False
    needles = (
        "429",
        "rate limit",
        "timeout",
        "timed out",
        "503",
        "502",
        "500",
        "overloaded",
        "temporarily",
        "connection",
    )
    return any(n in text for n in needles)


def is_retryable(exc: BaseException) -> bool:
    return _is_retryable(exc)


def _ordered_models(models: Sequence[str], *, prefer_paid_first: bool) -> list[str]:
    """Put non-`:free` OpenRouter models ahead of free-tier ones when enabled."""
    ordered = list(models)
    if not prefer_paid_first or len(ordered) < 2:
        return ordered
    paid = [m for m in ordered if ":free" not in m.casefold()]
    free = [m for m in ordered if ":free" in m.casefold()]
    return paid + free if paid else ordered


def iter_failover_lanes(
    settings: Settings,
    *,
    complexity: str | None = None,
    runtime_mode: str | None = None,
) -> list[ChatLane]:
    """Starting RR offset, then walk keys for a model before the next model."""
    keys = settings.llm_api_keys
    models = _ordered_models(
        settings.llm_models,
        prefer_paid_first=bool(settings.llm_prefer_paid_first),
    )
    if not keys:
        raise LLMError("LLM_API_KEY is not configured")
    if not models:
        raise LLMError("LLM_MODEL / LLM_MODELS is not configured")

    strong = prefer_strong_model(complexity=complexity, runtime_mode=runtime_mode)
    rotate_model = settings.llm_gateway_rr_active and not strong
    key_ticket, model_ticket = _take_tickets(rotate_model=rotate_model)

    preferred = (settings.llm_model or "").strip()
    if settings.llm_gateway_rr_active:
        k0 = key_ticket % len(keys)
        if strong and preferred in models:
            m0 = models.index(preferred)
        else:
            m0 = model_ticket % len(models)
    else:
        k0, m0 = 0, 0

    lanes: list[ChatLane] = []
    for dm in range(len(models)):
        model = models[(m0 + dm) % len(models)]
        for dk in range(len(keys)):
            key_index = (k0 + dk) % len(keys)
            lanes.append(ChatLane(model=model, key_index=key_index, api_key=keys[key_index]))
    return lanes


def _retry_sleep_s(settings: Settings, attempt: int) -> float:
    delay_ms = min(
        settings.llm_retry_cap_ms,
        settings.llm_retry_base_ms * (2**attempt),
    )
    return max(0.0, delay_ms / 1000.0)


def get_chat_model(
    *,
    settings: Settings | None = None,
    lane: ChatLane | None = None,
    complexity: str | None = None,
    runtime_mode: str | None = None,
    intent: str | None = None,
    execution_class: str | None = None,
    max_tokens: int | None = None,
) -> ChatOpenAI:
    """Build a LangChain chat model for one gateway lane."""
    cfg = settings or get_settings()
    chosen = lane or iter_failover_lanes(
        cfg,
        complexity=complexity,
        runtime_mode=runtime_mode,
    )[0]
    tokens = max_tokens if max_tokens is not None else max_tokens_for_turn(
        cfg,
        complexity=complexity,
        runtime_mode=runtime_mode,
        intent=intent,
        execution_class=execution_class,
    )
    extra = _model_extra_body(
        reasoning=reasoning_enabled_for_turn(
            execution_class=execution_class,
            complexity=complexity,
            runtime_mode=runtime_mode,
        )
    )
    model = ChatOpenAI(
        api_key=chosen.api_key,
        base_url=cfg.llm_base_url,
        model=chosen.model,
        temperature=cfg.llm_temperature,
        max_tokens=tokens,
        timeout=cfg.llm_timeout_seconds,
        streaming=True,
        extra_body=extra,
    )
    model.model_name = chosen.model
    model._que_lane = chosen
    return model


def _cap_lanes(
    settings: Settings,
    lanes: Sequence[ChatLane],
    *,
    runtime_mode: str | None = None,
) -> list[ChatLane]:
    if (runtime_mode or "").strip() == "agent":
        cap = max(1, int(settings.llm_max_attempts))
    else:
        cap = max(1, min(int(settings.llm_max_attempts), int(settings.llm_max_attempts_non_agent)))
    return list(lanes)[:cap]


def max_tokens_for_turn(
    settings: Settings,
    *,
    complexity: str | None = None,
    runtime_mode: str | None = None,
    intent: str | None = None,
    execution_class: str | None = None,
) -> int:
    """Task-based completion budget — meta/simple small, agent full."""
    intent_l = (intent or "").strip()
    mode = (runtime_mode or "").strip()
    exec_l = (execution_class or "").strip()
    if intent_l in {"chitchat", "meta", "getting_started"} or exec_l == "conversational":
        return max(64, int(settings.llm_max_tokens_meta))
    if mode == "agent" or (complexity or "").strip() == "multi_step":
        return max(64, int(settings.llm_max_tokens_complex))
    if exec_l == "complex_knowledge":
        return max(64, int(settings.llm_max_tokens_moderate))
    if exec_l == "simple_knowledge":
        return max(64, int(settings.llm_max_tokens_simple))
    if mode in {"workflow", "knowledge"} or intent_l in {
        "knowledge",
        "how_to",
        "explanation",
        "navigation",
        "analytics",
        "live_data",
    }:
        return max(64, int(settings.llm_max_tokens_howto))
    return max(64, int(settings.llm_max_tokens))


def _log_request_id() -> str:
    trace = current_trace()
    if trace is None:
        return ""
    return trace.request_id


def _redact_lane_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Strip API keys; keep model / key_index for LangSmith debugging."""
    out = dict(inputs)
    out.pop("api_key", None)
    lane = out.get("lane")
    if isinstance(lane, ChatLane):
        out["lane"] = {"model": lane.model, "key_index": lane.key_index}
    cfg = out.get("settings")
    if cfg is not None:
        out["settings"] = {"llm_base_url": getattr(cfg, "llm_base_url", None)}
    return out


@traceable(
    name="que_llm.ainvoke_lane",
    run_type="llm",
    process_inputs=_redact_lane_inputs,
)
async def _ainvoke_lane(
    messages: Sequence[BaseMessage],
    *,
    lane: ChatLane,
    settings: Settings,
    attempt: int,
    complexity: str | None = None,
    runtime_mode: str | None = None,
    intent: str | None = None,
    execution_class: str | None = None,
) -> object:
    model = get_chat_model(
        settings=settings,
        lane=lane,
        complexity=complexity,
        runtime_mode=runtime_mode,
        intent=intent,
        execution_class=execution_class,
    )
    return await model.ainvoke(list(messages))


@traceable(name="que_llm.ainvoke_chat", tags=["que-agent"])
async def ainvoke_chat(
    messages: Sequence[BaseMessage],
    *,
    settings: Settings | None = None,
    complexity: str | None = None,
    runtime_mode: str | None = None,
    intent: str | None = None,
    execution_class: str | None = None,
) -> tuple[object, ChatLane]:
    """ainvoke with capped failover. Returns (response, lane)."""
    global _last_usage
    cfg = settings or get_settings()
    if llm_circuit_open(cfg):
        raise LLMError("LLM circuit open")
    lanes = _cap_lanes(
        cfg,
        iter_failover_lanes(cfg, complexity=complexity, runtime_mode=runtime_mode),
        runtime_mode=runtime_mode,
    )
    last_error: BaseException | None = None
    for attempt, lane in enumerate(lanes):
        try:
            response = await _ainvoke_lane(
                messages,
                lane=lane,
                settings=cfg,
                attempt=attempt,
                complexity=complexity,
                runtime_mode=runtime_mode,
                intent=intent,
                execution_class=execution_class,
            )
            _record_llm_success()
            _last_usage = extract_usage(response, model=lane.model)
            logger.info(
                "que_llm_ok model=%s key_index=%s attempt=%s fallback=%s prompt_tokens=%s completion_tokens=%s reasoning_tokens=%s request_id=%s",
                lane.model,
                lane.key_index,
                attempt,
                attempt > 0,
                _last_usage.prompt_tokens,
                _last_usage.completion_tokens,
                _last_usage.reasoning_tokens,
                _log_request_id(),
            )
            return response, lane
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            retry = _is_retryable(exc) and attempt + 1 < len(lanes)
            if _is_retryable(exc):
                _record_llm_failure(cfg)
            logger.warning(
                "que_llm_fail model=%s key_index=%s attempt=%s retry=%s error=%s request_id=%s",
                lane.model,
                lane.key_index,
                attempt,
                retry,
                type(exc).__name__,
                _log_request_id(),
            )
            if not retry:
                break
            await asyncio.sleep(_retry_sleep_s(cfg, attempt))
    raise LLMError(str(last_error) if last_error else "LLM call failed") from last_error


def _chunk_text(chunk: object) -> list[str]:
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str) and content:
        return [content]
    if isinstance(content, list):
        out: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                out.append(str(block["text"]))
            elif isinstance(block, str) and block:
                out.append(block)
        return out
    return []


@traceable(name="que_llm.astream_chat", tags=["que-agent"])
async def astream_chat(
    messages: Sequence[BaseMessage],
    *,
    settings: Settings | None = None,
    complexity: str | None = None,
    runtime_mode: str | None = None,
    intent: str | None = None,
    execution_class: str | None = None,
) -> AsyncIterator[tuple[str, ChatLane]]:
    """Stream tokens from one lane. Fail over only before the first token."""
    global _last_usage
    cfg = settings or get_settings()
    if llm_circuit_open(cfg):
        raise LLMError("LLM circuit open")
    lanes = _cap_lanes(
        cfg,
        iter_failover_lanes(cfg, complexity=complexity, runtime_mode=runtime_mode),
        runtime_mode=runtime_mode,
    )
    last_error: BaseException | None = None
    for attempt, lane in enumerate(lanes):
        model = get_chat_model(
            settings=cfg,
            lane=lane,
            complexity=complexity,
            runtime_mode=runtime_mode,
            intent=intent,
            execution_class=execution_class,
        )
        emitted = False
        usage = TokenUsage(model=lane.model)
        with trace(
            name="que_llm.astream_lane",
            run_type="llm",
            inputs={
                "model": lane.model,
                "key_index": lane.key_index,
                "attempt": attempt,
            },
        ) as run_tree:
            try:
                async for chunk in model.astream(list(messages)):
                    piece_usage = extract_usage(chunk, model=lane.model)
                    if piece_usage.total:
                        usage = piece_usage
                    for piece in _chunk_text(chunk):
                        emitted = True
                        yield piece, lane
                if emitted:
                    _record_llm_success()
                    _last_usage = usage
                    logger.info(
                        "que_llm_ok model=%s key_index=%s attempt=%s fallback=%s stream=1 prompt_tokens=%s completion_tokens=%s reasoning_tokens=%s request_id=%s",
                        lane.model,
                        lane.key_index,
                        attempt,
                        attempt > 0,
                        usage.prompt_tokens,
                        usage.completion_tokens,
                        usage.reasoning_tokens,
                        _log_request_id(),
                    )
                    if run_tree is not None:
                        run_tree.end(
                            outputs={
                                "ok": True,
                                "prompt_tokens": usage.prompt_tokens,
                                "completion_tokens": usage.completion_tokens,
                                "reasoning_tokens": usage.reasoning_tokens,
                            }
                        )
                    return
                last_error = LLMError("LLM returned an empty stream")
                if run_tree is not None:
                    run_tree.end(error="empty stream")
            except LLMError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if run_tree is not None:
                    run_tree.end(error=f"{type(exc).__name__}: {str(exc)[:200]}")
                if emitted:
                    if _is_retryable(exc):
                        _record_llm_failure(cfg)
                    logger.warning(
                        "que_llm_fail model=%s key_index=%s attempt=%s retry=False mid_stream error=%s request_id=%s",
                        lane.model,
                        lane.key_index,
                        attempt,
                        type(exc).__name__,
                        _log_request_id(),
                    )
                    raise LLMError(str(exc)) from exc
                retry = _is_retryable(exc) and attempt + 1 < len(lanes)
                if _is_retryable(exc):
                    _record_llm_failure(cfg)
                logger.warning(
                    "que_llm_fail model=%s key_index=%s attempt=%s retry=%s error=%s request_id=%s",
                    lane.model,
                    lane.key_index,
                    attempt,
                    retry,
                    type(exc).__name__,
                    _log_request_id(),
                )
                if not retry:
                    break
                await asyncio.sleep(_retry_sleep_s(cfg, attempt))
                continue
        retry_empty = attempt + 1 < len(lanes)
        if not retry_empty:
            break
        await asyncio.sleep(_retry_sleep_s(cfg, attempt))
    raise LLMError(str(last_error) if last_error else "LLM stream failed") from last_error
