import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_token
from app.db.session import AsyncSessionLocal
from app.models.login_history import LoginHistory
from tests.conftest import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    ANALYST_PASSWORD,
    ANALYST_USERNAME,
)


pytestmark = pytest.mark.asyncio


async def test_login_happy_path(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "accessToken" in body and body["accessToken"]
    assert "refreshToken" in body and body["refreshToken"]
    assert body["expiresIn"] == 900
    assert body["user"]["role"] == "MSP_ADMIN"
    assert body["user"]["email"] == ADMIN_USERNAME
    uuid.UUID(body["mspId"])


async def test_login_analyst_returns_analyst_role(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": ANALYST_USERNAME, "password": ANALYST_PASSWORD},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "MSP_ANALYST"


async def test_login_wrong_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": "not-the-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


async def test_login_unknown_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "nobody@nowhere.com", "password": "whatever"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


async def test_refresh_rotates_and_invalidates_old(client: AsyncClient) -> None:
    login = (
        await client.post(
            "/api/v1/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
    ).json()
    original_refresh = login["refreshToken"]

    rotated = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": original_refresh}
    )
    assert rotated.status_code == 200
    rotated_body = rotated.json()
    assert rotated_body["accessToken"] != login["accessToken"]
    assert rotated_body["refreshToken"] != original_refresh

    replayed = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": original_refresh}
    )
    assert replayed.status_code == 401
    assert replayed.json()["code"] == "INVALID_REFRESH_TOKEN"

    fresh = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": rotated_body["refreshToken"]}
    )
    assert fresh.status_code == 200


async def test_refresh_garbage_token(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": "not-a-jwt"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_REFRESH_TOKEN"


async def test_logout_marks_history(client: AsyncClient) -> None:
    login = (
        await client.post(
            "/api/v1/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
    ).json()
    access = login["accessToken"]

    resp = await client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {access}"}
    )
    assert resp.status_code == 204

    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(
                select(LoginHistory).where(
                    LoginHistory.access_token_hash == hash_token(access)
                )
            )
        ).scalar_one()
        assert row.status == "LOGGED_OUT"
        assert row.logout_time is not None


async def test_me_returns_profile(client: AsyncClient, admin_headers: dict) -> None:
    resp = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == ADMIN_USERNAME
    assert body["role"] == "MSP_ADMIN"
    uuid.UUID(body["id"])
    uuid.UUID(body["mspId"])


async def test_me_without_token(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_EXPIRED"


async def test_me_with_garbage_token(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_EXPIRED"
