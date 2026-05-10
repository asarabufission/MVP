from typing import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

ADMIN_USERNAME = "testmsp@mvp.com"
ADMIN_PASSWORD = "testmsp@123"
ANALYST_USERNAME = "analyst@mvp.com"
ANALYST_PASSWORD = "analyst@123"


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient, username: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    resp.raise_for_status()
    return resp.json()


@pytest_asyncio.fixture
async def admin_login(client: AsyncClient) -> dict:
    return await _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)


@pytest_asyncio.fixture
async def analyst_login(client: AsyncClient) -> dict:
    return await _login(client, ANALYST_USERNAME, ANALYST_PASSWORD)


@pytest_asyncio.fixture
async def admin_headers(admin_login: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_login['accessToken']}"}


@pytest_asyncio.fixture
async def analyst_headers(analyst_login: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {analyst_login['accessToken']}"}
