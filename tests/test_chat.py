"""Auth tests for service key + Que access JWT (no live LLM)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt


def test_chat_requires_credentials(client):
    response = client.post(
        "/v1/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 401


def test_chat_rejects_bad_service_key(client):
    response = client.post(
        "/v1/chat",
        headers={"X-Que-Service-Key": "wrong-key"},
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 401


def test_chat_validates_empty_messages(client, service_key):
    response = client.post(
        "/v1/chat",
        headers={"X-Que-Service-Key": service_key},
        json={"messages": []},
    )
    assert response.status_code == 422


def test_stream_canned_works_without_llm_key(client, service_key):
    response = client.post(
        "/v1/chat/stream",
        headers={"X-Que-Service-Key": service_key},
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 200
    body = response.text
    assert "meta" in body
    assert "token" in body
    assert "done" in body


def test_stream_knowledge_needs_llm_key(client, service_key):
    response = client.post(
        "/v1/chat/stream",
        headers={"X-Que-Service-Key": service_key},
        json={"messages": [{"role": "user", "content": "What's the difference between exam duration and link window?"}]},
    )
    assert response.status_code == 200
    assert "llm_not_configured" in response.text


def test_chat_refuse_out_of_scope_without_llm(client, service_key):
    response = client.post(
        "/v1/chat",
        headers={"X-Que-Service-Key": service_key},
        json={"messages": [{"role": "user", "content": "Who is the president of France?"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "scope:refuse"
    assert "Quizzer" in data["message"]["content"]


def test_chat_accepts_valid_que_access_jwt(client, que_jwt_secret):
    token = jwt.encode(
        {
            "sub": "user-123",
            "typ": "que_access",
            "aud": "que-agent",
            "iss": "quizzer",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        que_jwt_secret,
        algorithm="HS256",
    )
    response = client.post(
        "/v1/chat/stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 200
    assert "done" in response.text


def test_chat_rejects_wrong_token_type(client, que_jwt_secret):
    token = jwt.encode(
        {
            "sub": "user-123",
            "typ": "access",
            "aud": "que-agent",
            "iss": "quizzer",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        que_jwt_secret,
        algorithm="HS256",
    )
    response = client.post(
        "/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 401


def test_decode_que_access_token_roundtrip(que_jwt_secret):
    from app.core.config import get_settings
    from app.core.tokens import decode_que_access_token

    get_settings.cache_clear()
    token = jwt.encode(
        {
            "sub": "abc",
            "sid": "sess-1",
            "typ": "que_access",
            "aud": "que-agent",
            "iss": "quizzer",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        que_jwt_secret,
        algorithm="HS256",
    )
    principal = decode_que_access_token(token)
    assert principal.mode == "user"
    assert principal.user_id == "abc"
    assert principal.session_id == "sess-1"
