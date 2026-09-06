# syntax=docker/dockerfile:1
# QUE-Agent — production image (gunicorn + uvicorn workers)

FROM python:3.11.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /usr/local/bin/uv

FROM base AS deps
COPY pyproject.toml uv.lock README.md ./
COPY app ./app
RUN uv sync --frozen --no-dev --no-editable

FROM base AS runtime
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin que
ENV PATH="/app/.venv/bin:$PATH" \
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8100

COPY --from=deps /app/.venv /app/.venv
COPY app ./app
COPY knowledge ./knowledge
COPY scripts/start.sh ./scripts/start.sh
RUN chmod +x scripts/start.sh \
    && chown -R que:que /app

USER que
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" || exit 1

CMD ["./scripts/start.sh"]
