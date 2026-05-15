import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _unique_name(prefix: str = "PYT-ASN") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def _create_client(client: AsyncClient, headers: dict) -> dict:
    name = _unique_name()
    resp = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={
            "name": name,
            "defaultIdentifierType": "EMAIL_DOMAIN_CONTAINS",
            "defaultIdentifierValue": f"{name.lower()}.test",
        },
    )
    resp.raise_for_status()
    return resp.json()


async def _datasource_by_name(
    client: AsyncClient, headers: dict, name: str
) -> dict:
    resp = await client.get("/api/v1/datasources?limit=200", headers=headers)
    resp.raise_for_status()
    items = resp.json()["items"]
    return next(d for d in items if d["name"] == name)


async def test_list_assignments_empty_for_new_client(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    resp = await client.get(
        f"/api/v1/clients/{new_client['id']}/assignments", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []
    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_create_assignment_happy(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")

    resp = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": m365["id"]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["datasourceName"] == "M365 Production"
    assert body["status"] == "ACTIVE"
    assert body["isBillingSource"] is False
    assert body["isIdentityAnchor"] is False
    assert body["effectiveIdentifierType"] == "EMAIL_DOMAIN_CONTAINS"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_create_assignment_duplicate_409(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")

    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": m365["id"]},
    )
    dup = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": m365["id"]},
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "ALREADY_ASSIGNED"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_create_assignment_admin_only(
    client: AsyncClient, admin_headers: dict, analyst_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")

    resp = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=analyst_headers,
        json={"datasourceId": m365["id"]},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "ROLE_FORBIDDEN"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_inactivate_then_reactivate(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")

    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": m365["id"]},
    )

    inactivated = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{m365['id']}/inactivate",
        headers=admin_headers,
    )
    assert inactivated.status_code == 200
    assert inactivated.json()["status"] == "INACTIVE"

    reactivated = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{m365['id']}/reactivate",
        headers=admin_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_set_billing_source_swap(
    client: AsyncClient, admin_headers: dict
) -> None:
    # Only RECONCILIATION datasources are eligible billing sources.
    # The seed has just one (Autotask Billing), so this test verifies
    # set-billing-source on the eligible source and rejects others.
    new_client = await _create_client(client, admin_headers)
    autotask = await _datasource_by_name(client, admin_headers, "Autotask Billing")
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")

    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": autotask["id"]},
    )
    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": m365["id"]},
    )

    ok = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{autotask['id']}/set-billing-source",
        headers=admin_headers,
    )
    assert ok.status_code == 200
    assert ok.json()["isBillingSource"] is True

    rejected = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{m365['id']}/set-billing-source",
        headers=admin_headers,
    )
    assert rejected.status_code == 400
    assert rejected.json()["code"] == "INVALID_BILLING_SOURCE"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_set_identity_anchor_swap(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")
    datto = await _datasource_by_name(client, admin_headers, "Datto RMM")
    autotask = await _datasource_by_name(client, admin_headers, "Autotask Billing")

    for ds in (m365, datto, autotask):
        await client.post(
            f"/api/v1/clients/{new_client['id']}/assignments",
            headers=admin_headers,
            json={"datasourceId": ds["id"]},
        )

    first = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{m365['id']}/set-identity-anchor",
        headers=admin_headers,
    )
    assert first.status_code == 200
    assert first.json()["isIdentityAnchor"] is True

    second = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{datto['id']}/set-identity-anchor",
        headers=admin_headers,
    )
    assert second.status_code == 200
    assert second.json()["isIdentityAnchor"] is True

    detail = (
        await client.get(
            f"/api/v1/clients/{new_client['id']}", headers=admin_headers
        )
    ).json()
    by_name = {a["datasourceName"]: a for a in detail["assignments"]}
    assert by_name["M365 Production"]["isIdentityAnchor"] is False
    assert by_name["Datto RMM"]["isIdentityAnchor"] is True

    # RECONCILIATION is not an eligible identity anchor
    rejected = await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{autotask['id']}/set-identity-anchor",
        headers=admin_headers,
    )
    assert rejected.status_code == 400
    assert rejected.json()["code"] == "INVALID_IDENTITY_ANCHOR"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_readiness_flips_to_ready_and_back(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    assert new_client["readiness"] == "NEEDS_SETUP"

    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")
    datto = await _datasource_by_name(client, admin_headers, "Datto RMM")
    autotask = await _datasource_by_name(client, admin_headers, "Autotask Billing")

    for ds in (m365, datto, autotask):
        await client.post(
            f"/api/v1/clients/{new_client['id']}/assignments",
            headers=admin_headers,
            json={"datasourceId": ds["id"]},
        )

    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{m365['id']}/set-identity-anchor",
        headers=admin_headers,
    )
    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{autotask['id']}/set-billing-source",
        headers=admin_headers,
    )

    ready = (
        await client.get(
            f"/api/v1/clients/{new_client['id']}", headers=admin_headers
        )
    ).json()
    assert ready["readiness"] == "READY"

    # Inactivate the endpoint → should drop back to NEEDS_SETUP
    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{datto['id']}/inactivate",
        headers=admin_headers,
    )
    after = (
        await client.get(
            f"/api/v1/clients/{new_client['id']}", headers=admin_headers
        )
    ).json()
    assert after["readiness"] == "NEEDS_SETUP"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )


async def test_assignments_includes_inactive(
    client: AsyncClient, admin_headers: dict
) -> None:
    new_client = await _create_client(client, admin_headers)
    m365 = await _datasource_by_name(client, admin_headers, "M365 Production")

    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments",
        headers=admin_headers,
        json={"datasourceId": m365["id"]},
    )
    await client.post(
        f"/api/v1/clients/{new_client['id']}/assignments/{m365['id']}/inactivate",
        headers=admin_headers,
    )

    listed = await client.get(
        f"/api/v1/clients/{new_client['id']}/assignments", headers=admin_headers
    )
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["status"] == "INACTIVE"

    await client.delete(
        f"/api/v1/clients/{new_client['id']}", headers=admin_headers
    )
