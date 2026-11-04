"""Health and readiness endpoints.

``/health`` is pure liveness (process is up) — always cheap, always 200 once
the process is running. ``/ready`` actually checks the dependencies a real
request needs, so a load balancer can stop routing to a broken instance
(missing LLM key, empty knowledge index, unreachable Quizzer tools) instead
of serving degraded chat.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Response, status

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


def _chroma_ready(chroma_path: str) -> bool:
    path = Path(chroma_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    if not path.is_dir():
        return False
    # A real Chroma persist dir has at least one sqlite/parquet artifact.
    return any(path.iterdir()) if path.exists() else False


@router.get("/ready")
async def ready(response: Response) -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, bool] = {}

    checks["llm_configured"] = bool(settings.llm_api_keys)

    if settings.que_rag_enabled:
        from app.knowledge.store import chroma_path

        checks["knowledge_index"] = _chroma_ready(str(chroma_path(settings)))
    else:
        checks["knowledge_index"] = True  # not required when RAG is off

    from app.knowledge import validate_knowledge_manifest

    checks["knowledge_manifest"] = not validate_knowledge_manifest()

    if settings.que_tools_enabled:
        from app.tools.quizzer_client import check_tools_health

        checks["quizzer_tools"] = await check_tools_health(settings=settings)
    else:
        checks["quizzer_tools"] = True  # not required when tools are off

    ok = all(checks.values())
    response.status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "degraded", "checks": checks}
