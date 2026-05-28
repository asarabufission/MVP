import pytest


@pytest.mark.asyncio
async def test_list_connectors(client, admin_headers):
    resp = await client.get("/api/v1/connectors", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 8
    source_ids = {item["sourceId"] for item in body}
    assert "datto_rmm" in source_ids
    assert "microsoft_365" in source_ids


@pytest.mark.asyncio
async def test_get_connector_detail(client, admin_headers):
    resp = await client.get("/api/v1/connectors/datto_rmm", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["sourceId"] == "datto_rmm"
    assert len(body["credentialSchema"]) >= 2
    assert "device_hostname" in body["defaultFieldMappings"]
