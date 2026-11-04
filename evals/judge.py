"""DeepEval judge.

Preferred: Gemini through its OpenAI-compatible endpoint, using ``Deepeval_API_KEY``
from `.env` (model ``EVAL_JUDGE_MODEL``, default gemma-4-31b-it: Gemini flash models are capped
at 20 requests/day on the free tier). That keeps the
judge a different model family from the one QUE answers with.
Fallback: LLM_API_KEY / LLM_BASE_URL / LLM_MODEL (OpenRouter). Nemotron writes a
chain of thought unless reasoning tokens are turned off.
"""

from __future__ import annotations

import json
import os
import re
import time

from deepeval.models import DeepEvalBaseLLM
from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from pydantic import ValidationError

from app.core.config import get_settings

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# A rejected Confident AI key crashes the CLI after the metric finishes.
os.environ.pop("CONFIDENT_API_KEY", None)

# Fast models first. Each Gemini model has its own free daily quota; the judge moves
# to the next one when a quota is spent. The model used is recorded with every baseline.
_DEFAULT_GEMINI_MODELS = "gemini-3.5-flash-lite,gemini-flash-lite-latest,gemini-3.1-flash-lite"

_THOUGHT_RE = re.compile(r"<thought>.*?(?:</thought>|$)", re.DOTALL | re.IGNORECASE)

_SCORE_RE = re.compile(
    r'(?:"score"\s*:\s*|score\s*[:=]\s*)(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:/\s*10|out of\s*10)',
    re.IGNORECASE,
)


def _gemini_key() -> str | None:
    """Judge key from the environment, else the repo .env (pydantic does not export it)."""
    from pathlib import Path

    from dotenv import dotenv_values

    for name in ("Deepeval_API_KEY", "DEEPEVAL_API_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    values = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    for name in ("Deepeval_API_KEY", "DEEPEVAL_API_KEY"):
        if (values.get(name) or "").strip():
            return values[name].strip()
    return None


class QueJudge(DeepEvalBaseLLM):
    def __init__(self, pin: str | None = None) -> None:
        # pin: use exactly this model; no silent failover (a quota error fails the call).
        self._pinned = pin
        settings = get_settings()
        gemini_key = _gemini_key()
        if gemini_key:
            # Dedicated eval judge, a different model family from the one QUE answers with.
            self._gemini = True
            names = os.environ.get("EVAL_JUDGE_MODELS", _DEFAULT_GEMINI_MODELS)
            self._pool = [n.strip() for n in names.split(",") if n.strip()]
            self._client = OpenAI(api_key=gemini_key, base_url=_GEMINI_BASE_URL, timeout=120)
            return
        self._gemini = False
        self._pool = []
        keys = settings.llm_api_keys
        if not keys:
            raise RuntimeError("Set Deepeval_API_KEY, or LLM_API_KEY / LLM_API_KEY_1, in .env")
        self._fixed_model = settings.llm_model
        self._client = OpenAI(
            api_key=keys[0],
            base_url=settings.llm_base_url,
            timeout=90,
        )

    def load_model(self):
        return self._client

    # Shared across instances so a spent quota is not rediscovered on every metric.
    _shared_index = 0
    _used: set[str] = set()
    # Cumulative usage counters; callers diff snapshots around a unit of work.
    stats: dict = {'calls': 0, 'retries': 0, 'seconds': 0.0, 'prompt_tokens': 0, 'completion_tokens': 0}

    @property
    def _pool_index(self) -> int:
        return QueJudge._shared_index

    @_pool_index.setter
    def _pool_index(self, value: int) -> None:
        QueJudge._shared_index = value

    @property
    def _model(self) -> str:
        name = self._pinned or (self._pool[self._pool_index] if self._pool else self._fixed_model)
        QueJudge._used.add(name)
        return name

    @staticmethod
    def used_models() -> list[str]:
        return sorted(QueJudge._used)

    def get_model_name(self) -> str:
        return self._model

    def _next_model(self) -> bool:
        """Move to the next pooled model after a daily-quota error."""
        if self._pinned or self._pool_index + 1 >= len(self._pool):
            return False
        self._pool_index += 1
        return True

    def _complete(self, messages: list[dict], *, max_tokens: int = 800) -> str:
        extra = {} if self._gemini else {"extra_body": {"reasoning": {"max_tokens": 0}}}
        # Gemini spends output tokens on thinking, so give it more room.
        budget = max_tokens * 4 if self._gemini else max_tokens
        started = time.perf_counter()
        for attempt in range(8):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0,
                    max_tokens=budget,
                    **extra,
                )
                break
            except (InternalServerError, APIConnectionError, APITimeoutError):
                # Gemini 503 "high demand" spikes are transient.
                QueJudge.stats['retries'] += 1
                if attempt == 7:
                    raise
                time.sleep(10)
            except RateLimitError as exc:
                # Per-minute limits clear by waiting. A daily cap does not, so fail fast.
                daily = "PerDay" in str(exc) or "per-day" in str(exc)
                if daily and self._next_model():
                    continue
                QueJudge.stats['retries'] += 1
                if attempt == 7 or daily:
                    raise
                time.sleep(15)
        usage = getattr(response, 'usage', None)
        QueJudge.stats['calls'] += 1
        QueJudge.stats['seconds'] += time.perf_counter() - started
        QueJudge.stats['prompt_tokens'] += getattr(usage, 'prompt_tokens', 0) or 0
        QueJudge.stats['completion_tokens'] += getattr(usage, 'completion_tokens', 0) or 0
        message = response.choices[0].message
        # Gemma prints its reasoning in <thought> tags; braces in there would confuse JSON parsing.
        content = _THOUGHT_RE.sub("", message.content or "").strip()
        if _score_payload(content) is not None:
            return content
        extra = getattr(message, "model_extra", None) or {}
        reasoning = extra.get("reasoning") or ""
        return content or reasoning

    def generate(self, prompt: str, schema=None):
        if schema is not None:
            spec = json.dumps(schema.model_json_schema(), default=str)
            prompt = (
                f"{prompt}\n\nReturn ONLY one JSON object that validates against this "
                f"JSON schema (use these exact key names):\n{spec}"
            )
        messages = [{"role": "user", "content": prompt}]
        text = self._complete(messages, max_tokens=2000 if schema is not None else 800)
        if schema is None:
            payload = _score_payload(text)
            if payload is None:
                snippet = " ".join(text.split())[:180]
                raise RuntimeError(f"Judge did not return a 0-10 score: {snippet!r}")
            return json.dumps(payload), 0
        parsed = _json_object(text)
        if parsed is None:
            text = self._complete(
                [
                    *messages,
                    {"role": "assistant", "content": text or "{}"},
                    {
                        "role": "user",
                        "content": "Reply with only the JSON object requested above.",
                    },
                ],
                max_tokens=2000,
            )
            parsed = _json_object(text)
        if parsed is None:
            snippet = " ".join(text.split())[:180]
            raise RuntimeError(f"Judge did not return JSON for {getattr(schema, '__name__', schema)}: {snippet!r}")
        # Custom (non-native) models return the schema object itself, not (obj, cost).
        for _attempt in range(2):
            try:
                return schema.model_validate(parsed)
            except ValidationError as exc:
                text = self._complete(
                    [
                        *messages,
                        {"role": "assistant", "content": json.dumps(parsed)},
                        {
                            "role": "user",
                            "content": f"That JSON failed validation:\n{exc}\nReturn corrected JSON only.",
                        },
                    ],
                    max_tokens=2000,
                )
                parsed = _json_object(text) or parsed
        return schema.model_validate(parsed)

    async def a_generate(self, prompt: str, schema=None):
        return self.generate(prompt, schema=schema)


def _json_object(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _score_payload(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if "score" in data:
                return {
                    "score": float(data["score"]),
                    "reason": str(data.get("reason", text[:240])),
                }
        except json.JSONDecodeError:
            pass
    matches = list(_SCORE_RE.finditer(text))
    if matches:
        last = matches[-1]
        raw = last.group(1) or last.group(2)
        return {"score": float(raw), "reason": text[:240]}
    return None
