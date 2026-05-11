import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _unique_name(prefix: str = "PYT") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def _find_client(client: AsyncClient, headers: dict, search: str) -> dict | None:
    resp = await client.get(
        f"/api/v1/clients?search={search}", headers=headers
    )
    resp.raise_for_status()
    items = resp.json()["items"]
    return items[0] if items else None


async def test_list_clients_returns_seeded_set(
    client: AsyncClient, admin_headers: dict
) -> None:
    resp = await client.get("/api/v1/clients?limit=200", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalCount"] >= 4
    names = {item["name"] for item in body["items"]}
    assert {"ERES Companies", "Scoop Ride", "Pinnacle Legal", "Harbor View Medical"} <= names

    eres = next(i for i in body["items"] if i["name"] == "ERES Companies")
    assert eres["assignedCount"] == 7
    assert eres["billingSourceName"] == "Autotask Billing"
    assert eres["identityAnchorName"] == "M365 Production"


async def test_list_clients_search(
    client: AsyncClient, admin_headers: dict
) -> None:
    resp = await client.get("/api/v1/clients?search=eres", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert all("eres" in i["name"].lower() for i in body["items"])
    assert any(i["name"] == "ERES Companies" for i in body["items"])


async def test_list_clients_pagination(
    client: AsyncClient, admin_headers: dict
) -> None:
    page1 = (await client.get("/api/v1/clients?limit=2", headers=admin_headers)).json()
    assert len(page1["items"]) == 2
    assert page1["nextCursor"] is not None
    cursor = page1["nextCursor"]

    page2 = (
        await client.get(
            f"/api/v1/clients?limit=2&cursor={cursor}", headers=admin_headers
        )
    ).json()
    assert len(page2["items"]) >= 1
    page1_ids = {i["id"] for i in page1["items"]}
    page2_ids = {i["id"] for i in page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


async def test_list_clients_invalid_cursor(
    client: AsyncClient, admin_headers: dict
) -> None:
    resp = await client.get(
        "/api/v1/clients?cursor=not-a-cursor", headers=admin_headers
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_CURSOR"


async def test_create_client_happy(
    client: AsyncClient, admin_headers: dict
) -> None:
    name = _unique_name()
    resp = await client.post(
        "/api/v1/clients",
        headers=admin_headers,
        json={
            "name": name,
            "description": "created by pytest",
            "defaultIdentifierType": "EMAIL_DOMAIN_CONTAINS",
            "defaultIdentifierValue": f"{name.lower()}.test",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == name
    assert body["defaultIdentifierType"] == "EMAIL_DOMAIN_CONTAINS"
    assert body["defaultIdentifierValue"] == f"{name.lower()}.test"
    assert body["assignedCount"] == 0

    # cleanup
    await client.delete(f"/api/v1/clients/{body['id']}", headers=admin_headers)


async def test_create_client_duplicate_409(
    client: AsyncClient, admin_headers: dict
) -> None:
    resp = await client.post(
        "/api/v1/clients",
        headers=admin_headers,
        json={
            "name": "ERES Companies",
            "defaultIdentifierType": "EMAIL_DOMAIN_CONTAINS",
            "defaultIdentifierValue": "x.test",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "CLIENT_NAME_TAKEN"


async def test_create_client_admin_only(
    client: AsyncClient, analyst_headers: dict
) -> None:
    resp = await client.post(
        "/api/v1/clients",
        headers=analyst_headers,
        json={
            "name": _unique_name(),
            "defaultIdentifierType": "X",
            "defaultIdentifierValue": "y",
        },
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "ROLE_FORBIDDEN"


async def test_get_client_detail_with_assignments(
    client: AsyncClient, admin_headers: dict
) -> None:
    eres = await _find_client(client, admin_headers, "eres")
    assert eres is not None
    resp = await client.get(
        f"/api/v1/clients/{eres['id']}", headers=admin_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["assignments"]) == 7

    by_name = {a["datasourceName"]: a for a in body["assignments"]}

    datto = by_name["Datto RMM"]
    assert datto["effectiveIdentifierType"] == "COMPANY_NAME_EQUALS"
    assert datto["effectiveIdentifierValue"] == "ERES Companies Inc."

    proofpoint = by_name["Proofpoint Core"]
    assert proofpoint["effectiveIdentifierType"] == "EMAIL_DOMAIN_CONTAINS"
    assert proofpoint["effectiveIdentifierValue"] == "erescompanies.com"


async def test_patch_client(
    client: AsyncClient, admin_headers: dict
) -> None:
    name = _unique_name()
    created = (
        await client.post(
            "/api/v1/clients",
            headers=admin_headers,
            json={
                "name": name,
                "defaultIdentifierType": "X",
                "defaultIdentifierValue": "y",
            },
        )
    ).json()

    resp = await client.patch(
        f"/api/v1/clients/{created['id']}",
        headers=admin_headers,
        json={"description": "updated by pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "updated by pytest"

    # cleanup
    await client.delete(f"/api/v1/clients/{created['id']}", headers=admin_headers)


async def test_patch_client_name_conflict(
    client: AsyncClient, admin_headers: dict
) -> None:
    name = _unique_name()
    created = (
        await client.post(
            "/api/v1/clients",
            headers=admin_headers,
            json={
                "name": name,
                "defaultIdentifierType": "X",
                "defaultIdentifierValue": "y",
            },
        )
    ).json()

    resp = await client.patch(
        f"/api/v1/clients/{created['id']}",
        headers=admin_headers,
        json={"name": "ERES Companies"},
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "CLIENT_NAME_TAKEN"

    # cleanup
    await client.delete(f"/api/v1/clients/{created['id']}", headers=admin_headers)


async def test_delete_client_soft(
    client: AsyncClient, admin_headers: dict
) -> None:
    name = _unique_name()
    created = (
        await client.post(
            "/api/v1/clients",
            headers=admin_headers,
            json={
                "name": name,
                "defaultIdentifierType": "X",
                "defaultIdentifierValue": "y",
            },
        )
    ).json()

    delete_resp = await client.delete(
        f"/api/v1/clients/{created['id']}", headers=admin_headers
    )
    assert delete_resp.status_code == 204

    list_resp = await client.get(
        "/api/v1/clients?limit=200", headers=admin_headers
    )
    names = {i["name"] for i in list_resp.json()["items"]}
    assert name not in names

    detail_resp = await client.get(
        f"/api/v1/clients/{created['id']}", headers=admin_headers
    )
    assert detail_resp.status_code == 404


async def test_delete_admin_only(
    client: AsyncClient, analyst_headers: dict, admin_headers: dict
) -> None:
    eres = await _find_client(client, admin_headers, "eres")
    assert eres is not None
    resp = await client.delete(
        f"/api/v1/clients/{eres['id']}", headers=analyst_headers
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "ROLE_FORBIDDEN"


async def test_set_assignment_identifier_override_then_clear(
    client: AsyncClient, admin_headers: dict
) -> None:
    eres = await _find_client(client, admin_headers, "eres")
    assert eres is not None
    detail = (
        await client.get(f"/api/v1/clients/{eres['id']}", headers=admin_headers)
    ).json()
    pp_assignment = next(
        a for a in detail["assignments"] if a["datasourceName"] == "Proofpoint Core"
    )
    pp_ds_id = pp_assignment["datasourceId"]

    # Override
    resp = await client.patch(
        f"/api/v1/clients/{eres['id']}/assignments/{pp_ds_id}/identifier",
        headers=admin_headers,
        json={
            "identifierType": "EMAIL_EQUALS",
            "identifierValue": "ops@erescompanies.com",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["identifierType"] == "EMAIL_EQUALS"
    assert body["effectiveIdentifierType"] == "EMAIL_EQUALS"
    assert body["effectiveIdentifierValue"] == "ops@erescompanies.com"

    # Clear → falls back to client default
    cleared = await client.patch(
        f"/api/v1/clients/{eres['id']}/assignments/{pp_ds_id}/identifier",
        headers=admin_headers,
        json={"identifierType": "", "identifierValue": ""},
    )
    assert cleared.status_code == 200
    cb = cleared.json()
    assert cb["identifierType"] is None
    assert cb["effectiveIdentifierType"] == "EMAIL_DOMAIN_CONTAINS"
    assert cb["effectiveIdentifierValue"] == "erescompanies.com"


async def test_set_assignment_identifier_partial_invalid(
    client: AsyncClient, admin_headers: dict
) -> None:
    eres = await _find_client(client, admin_headers, "eres")
    assert eres is not None
    detail = (
        await client.get(f"/api/v1/clients/{eres['id']}", headers=admin_headers)
    ).json()
    pp_ds_id = next(
        a["datasourceId"]
        for a in detail["assignments"]
        if a["datasourceName"] == "Proofpoint Core"
    )

    resp = await client.patch(
        f"/api/v1/clients/{eres['id']}/assignments/{pp_ds_id}/identifier",
        headers=admin_headers,
        json={"identifierType": "X", "identifierValue": ""},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_IDENTIFIER"
