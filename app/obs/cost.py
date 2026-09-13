"""Token usage extraction and a small static USD table (OpenRouter ids)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# USD per 1M tokens. `:free` models are $0. Unknown → usd=None.
_PAID_PER_MILLION: dict[str, tuple[float, float]] = {
    "openai/gpt-4o-mini": (0.15, 0.60),
}


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    model: str = ""

    @property
    def total(self) -> int:
        return int(self.prompt_tokens) + int(self.completion_tokens)


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _reasoning_from_mapping(payload: dict[str, Any]) -> int:
    """OpenRouter / OpenAI-style reasoning token details."""
    if not payload:
        return 0
    direct = _as_int(payload.get("reasoning_tokens") or payload.get("reasoning"))
    if direct:
        return direct
    details = payload.get("completion_tokens_details") or payload.get("output_token_details") or {}
    if isinstance(details, dict):
        return _as_int(details.get("reasoning_tokens") or details.get("reasoning"))
    return 0


def extract_usage(message: Any, *, model: str = "") -> TokenUsage:
    """Read LangChain usage_metadata or OpenAI-style response_metadata."""
    prompt = completion = reasoning = 0
    meta = getattr(message, "usage_metadata", None)
    if isinstance(meta, dict):
        prompt = _as_int(meta.get("input_tokens") or meta.get("prompt_tokens"))
        completion = _as_int(meta.get("output_tokens") or meta.get("completion_tokens"))
        reasoning = _reasoning_from_mapping(meta)
    if prompt == 0 and completion == 0:
        resp = getattr(message, "response_metadata", None) or {}
        if isinstance(resp, dict):
            usage = resp.get("token_usage") or resp.get("usage") or {}
            if isinstance(usage, dict):
                prompt = _as_int(usage.get("prompt_tokens") or usage.get("input_tokens"))
                completion = _as_int(usage.get("completion_tokens") or usage.get("output_tokens"))
                reasoning = _reasoning_from_mapping(usage)
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        reasoning_tokens=reasoning,
        model=model,
    )


def estimate_prompt_tokens(text_or_messages: Any) -> int:
    """Cheap char/4 estimate when the provider has not returned usage yet."""
    if isinstance(text_or_messages, str):
        n = len(text_or_messages)
    elif isinstance(text_or_messages, list):
        n = 0
        for item in text_or_messages:
            content = getattr(item, "content", item)
            if isinstance(content, str):
                n += len(content)
            elif isinstance(content, dict):
                n += len(str(content.get("content") or ""))
            else:
                n += len(str(content or ""))
    else:
        n = len(str(text_or_messages or ""))
    return max(1, n // 4) if n else 0


def usd_for_usage(usage: TokenUsage) -> float | None:
    model = (usage.model or "").strip()
    if not model:
        return None
    if ":free" in model.casefold():
        return 0.0
    rates = _PAID_PER_MILLION.get(model)
    if rates is None:
        return None
    inn, out = rates
    return round(
        (usage.prompt_tokens / 1_000_000.0) * inn
        + (usage.completion_tokens / 1_000_000.0) * out,
        8,
    )
