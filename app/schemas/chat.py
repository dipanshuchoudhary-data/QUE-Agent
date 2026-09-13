"""Chat request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ChatRole = Literal["system", "user", "assistant"]

# Stable page keys from Quizzer creator-workspace routes (Phase 3).
QuePageKey = Literal[
    "dashboard",
    "exams_list",
    "exam_workspace",
    "exam_results",
    "monitoring",
    "analytics",
    "students",
    "arena",
    "arena_host",
    "integrations",
    "account_settings",
    "create_exam",
    "help",
    "unknown",
]


class QueUiContext(BaseModel):
    """Structured Quizzer UI context — UX hint only, never an auth boundary.

    Client may send a role hint; Quizzer BFF overwrites ``user_role`` from the
    authenticated User before forwarding to QUE.
    """

    current_page: str = Field(default="unknown", max_length=64)
    current_exam_id: str | None = Field(default=None, max_length=64)
    current_exam_title: str | None = Field(default=None, max_length=200)
    current_entity_type: str | None = Field(default=None, max_length=64)
    current_entity_id: str | None = Field(default=None, max_length=128)
    user_role: str | None = Field(
        default=None,
        max_length=32,
        description="Server-stamped Quizzer role; client hint is overwritten by BFF",
    )
    route_path: str | None = Field(default=None, max_length=256)
    captured_at: str | None = Field(default=None, max_length=64)

    @field_validator(
        "current_page",
        "current_exam_id",
        "current_exam_title",
        "current_entity_type",
        "current_entity_id",
        "user_role",
        "route_path",
        "captured_at",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value

    @field_validator("current_page")
    @classmethod
    def require_page(cls, value: str | None) -> str:
        return (value or "unknown")[:64]

    @field_validator("route_path")
    @classmethod
    def cap_route(cls, value: str | None) -> str | None:
        if not value:
            return None
        return value[:256]


class ChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=32_000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("content must not be empty")
        return cleaned


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)
    conversation_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(
        default=None,
        max_length=64,
        description="Opaque Quizzer user id for audit/rate-limit only — never used for DB access",
    )
    context: QueUiContext | None = Field(
        default=None,
        description="Structured Quizzer UI context (page/entity/role) — Phase 3",
    )


class ChatResponse(BaseModel):
    message: ChatMessage
    conversation_id: str | None = None
    model: str
    knowledge_packs: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)


class ErrorBody(BaseModel):
    detail: str
