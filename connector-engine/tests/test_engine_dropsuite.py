"""Offline tests for Dropsuite + the engine updates it required.

Covers: header_key auth with X- headers, a top-level JSON ARRAY response,
http_client array support, certificate_msal registration, and that the
Microsoft 365 .yml manifest is now discoverable by source_id.

Run directly:  python tests/test_engine_dropsuite.py   (from connector-engine/)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))

from auth.registry import _REGISTRY, get_auth_strategy  # noqa: E402
from errors import AuthError, ManifestError  # noqa: E402
from http_client import HttpClient  # noqa: E402
from manifest import load_manifest  # noqa: E402
from orchestrator import run_connector  # noqa: E402

DROPSUITE_USERS = [
    {"id": "251939-6", "email": "a@leaftechit.com", "organization_id": 25054,
     "plan_id": "16921-6-3378-14", "is_business": True, "admin": True,
     "seats_used": 2, "seats_available": 2, "storage_used": 0.0,
     "organization_name": "Fritsche Law, LLC", "active_seats": 2},
    {"id": "251939-7", "email": "b@leaftechit.com", "organization_id": 25054,
     "plan_id": "16921-6-3378-14", "is_business": False, "admin": False,
     "seats_used": 1, "seats_available": 2, "storage_used": 1.5,
     "organization_name": "Fritsche Law, LLC", "active_seats": 1},
]


class FakeHttp:
    def __init__(self):
        self.calls = []

    def request(self, method, url, *, headers=None, params=None,
                json_body=None, form_body=None, basic_auth=None):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {})})
        if url.endswith("/api/users") and method == "GET":
            return list(DROPSUITE_USERS)  # top-level array
        raise AssertionError(f"unexpected call: {method} {url}")

    def close(self):
        pass


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, Bucket, Key, Body, ContentType=None):
        self.objects[Key] = json.loads(Body.decode("utf-8"))


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload

    def request(self, **kwargs):
        return _FakeResp(self._payload)

    def close(self):
        pass


def test_dropsuite_end_to_end():
    creds = {
        "DROPSUITE_API_URL": "https://dropsuite.us",
        "DROPSUITE_RESELLER_TOKEN": "900b95bc-reseller",
        "DROPSUITE_ACCESS_TOKEN": "6f9dcad0-access",
    }
    http, s3 = FakeHttp(), FakeS3()
    out = run_connector("dropsuite_v1", creds, client_id="fritsche_law",
                        http=http, s3_client=s3)

    assert set(out) == {"fetch_users"}, out.keys()
    assert len(out["fetch_users"]) == 2, "bare array response -> 2 user rows"

    call = http.calls[0]
    assert call["headers"]["X-Reseller-Token"] == "900b95bc-reseller"
    assert call["headers"]["X-Access-Token"] == "6f9dcad0-access"

    keys = list(s3.objects)
    assert any(k.endswith("fetch_users.json") for k in keys), keys
    assert any(k.endswith("_manifest.json") for k in keys), keys
    assert all(k.startswith("raw/dropsuite_v1/fritsche_law/") for k in keys), keys
    users_file = next(v for k, v in s3.objects.items() if k.endswith("fetch_users.json"))
    assert len(users_file) == 2
    return out


def test_http_client_allows_array():
    client = HttpClient(session=_FakeSession([{"id": 1}, {"id": 2}]))
    payload = client.request("GET", "https://dropsuite.us/api/users")
    assert isinstance(payload, list) and len(payload) == 2


def test_certificate_msal_registered():
    assert "certificate_msal" in _REGISTRY
    strat = get_auth_strategy("certificate_msal")
    cfg = {
        "tenant_id": "{credentials.tenant_id}",
        "client_id": "{credentials.client_id}",
        "certificate": {"from": "credentials.certificate_pem"},
        "scopes": ["https://graph.microsoft.com/.default"],
    }
    ctx = {"credentials": {"tenant_id": "t", "client_id": "c",
                           "certificate_pem": "-----BEGIN CERTIFICATE-----\nX\n-----END CERTIFICATE-----"},
           "steps": {}}
    has_msal = importlib.util.find_spec("msal") is not None
    try:
        strat.prepare(cfg, ctx, None)
        assert has_msal, "prepare should only succeed when msal is installed"
    except (AuthError, ManifestError):
        pass  # expected: missing dep or invalid cert/live failure -> clean engine error


def test_ms365_yml_now_loads():
    m = load_manifest("microsoft_365")  # .yml extension — proves the loader glob fix
    assert m.auth["strategy"] == "certificate_msal"
    assert len(m.steps) >= 3


if __name__ == "__main__":
    out = test_dropsuite_end_to_end()
    print("PASS dropsuite end-to-end:", {k: len(v) for k, v in out.items()})
    test_http_client_allows_array()
    print("PASS http_client allows top-level array")
    test_certificate_msal_registered()
    print("PASS certificate_msal registered + graceful without msal")
    test_ms365_yml_now_loads()
    print("PASS microsoft_365 .yml discoverable by source_id")
    print("ALL PASS")
