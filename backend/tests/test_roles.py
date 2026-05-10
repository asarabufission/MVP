import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_admin_passes_admin_guard(
    client: AsyncClient, admin_headers: dict
) -> None:
    resp = await client.get("/api/v1/auth/_probe-admin", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


async def test_analyst_blocked_by_admin_guard(
    client: AsyncClient, analyst_headers: dict
) -> None:
    resp = await client.get("/api/v1/auth/_probe-admin", headers=analyst_headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "ROLE_FORBIDDEN"


async def test_analyst_can_call_authenticated_route(
    client: AsyncClient, analyst_headers: dict
) -> None:
    resp = await client.get("/api/v1/auth/_probe-any", headers=analyst_headers)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


async def test_unauthenticated_blocked(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/_probe-admin")
    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_EXPIRED"
