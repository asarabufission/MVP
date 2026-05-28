import uuid

import pytest


async def _first_client_id(client, headers) -> str:
    resp = await client.get("/api/v1/clients", headers=headers)
    resp.raise_for_status()
    return resp.json()["items"][0]["id"]


@pytest.mark.asyncio
async def test_datasource_detail(client, admin_headers):
    listed = await client.get("/api/v1/datasources", headers=admin_headers)
    listed.raise_for_status()
    ds_id = listed.json()["items"][0]["id"]
    detail = await client.get(f"/api/v1/datasources/{ds_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == ds_id


@pytest.mark.asyncio
async def test_create_draft_test_connection_activate(client, admin_headers):
    client_id = await _first_client_id(client, admin_headers)

    draft_resp = await client.post(
        "/api/v1/datasource-drafts",
        headers=admin_headers,
        json={
            "clientId": client_id,
            "blueprintId": "datto_rmm",
            "displayName": "Datto POC",
            "config": {"api_version": "v1", "timeout_seconds": 30},
        },
    )
    assert draft_resp.status_code == 201
    draft = draft_resp.json()
    draft_id = draft["draftId"]
    assert draft["blueprintDetails"]["category"] == "ENDPOINT"

    attempt_id = str(uuid.uuid4())
    test_resp = await client.post(
        f"/api/v1/datasource-drafts/{draft_id}/test-connection",
        headers=admin_headers,
        json={
            "credentials": {
                "api_url": "https://zinfandel-api.centrastage.net",
                "api_key": "demo-key",
                "api_secret_key": "demo-secret",
            },
            "attemptId": attempt_id,
        },
    )
    assert test_resp.status_code == 200
    schema_hash = test_resp.json()["schemaHash"]

    preview_resp = await client.get(
        f"/api/v1/datasource-drafts/{draft_id}/schema-preview",
        headers=admin_headers,
    )
    assert preview_resp.status_code == 200

    details = draft["blueprintDetails"]
    mappings = details.get("defaultFieldMappings") or details.get("default_field_mappings", {})
    field_mappings = [
        {"standardField": std, "sourceField": src, "transform": "none"}
        for std, src in mappings.items()
    ]

    activate_resp = await client.post(
        "/api/v1/datasources/activate",
        headers=admin_headers,
        json={
            "draftId": draft_id,
            "mapping": {
                "schemaHash": schema_hash,
                "fieldMappings": field_mappings,
                "additionalParams": [],
            },
            "schedule": {
                "frequency": "MANUAL",
                "timezone": "America/New_York",
                "isEnabled": True,
            },
        },
    )
    assert activate_resp.status_code == 202
    ds_id = activate_resp.json()["datasourceId"]

    detail = await client.get(f"/api/v1/datasources/{ds_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] in ("ACTIVATING", "ACTIVE", "DEGRADED")
