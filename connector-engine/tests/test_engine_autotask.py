"""Offline end-to-end test for the Autotask connector via the generic engine.

No network, no AWS: a fake HttpClient returns canned Autotask responses and a
fake S3 client captures writes. Exercises header_key auth, cursor_url
pagination, foreach chaining, foreach_dedup_on, and S3 landing.

Run directly:  python tests/test_engine_autotask.py   (from connector-engine/)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Engine modules use flat imports; put the engine root on the path.
ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))

from orchestrator import run_connector  # noqa: E402


def _filter_value(body, field):
    for entry in (body or {}).get("filter", []):
        if entry.get("field") == field:
            return entry.get("value")
    return None


class FakeHttp:
    """Stand-in for HttpClient that dispatches on URL + filter body."""

    def __init__(self):
        self.calls = []

    def request(self, method, url, *, headers=None, params=None,
                json_body=None, form_body=None, basic_auth=None):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {}),
                           "body": json_body})

        # --- Contracts: paginated via pageDetails.nextPageUrl (2 pages) ---
        if "Contracts/query" in url and method == "POST":
            return {
                "items": [
                    {"id": 1, "companyID": 516, "contractName": "Recurring A"},
                    {"id": 2, "companyID": 516, "contractName": "Recurring B"},
                ],
                "pageDetails": {"nextPageUrl": "https://ws.autotask.net/Contracts/query?page=2"},
            }
        if "Contracts/query?page=2" in url and method == "GET":
            return {
                "items": [{"id": 3, "companyID": 516, "contractName": "Recurring C"}],
                "pageDetails": {"nextPageUrl": None},
            }

        # --- ContractServices: one query per contract (foreach) ---
        if "ContractServices/query" in url and method == "POST":
            cid = int(_filter_value(json_body, "contractID"))
            data = {
                1: [{"id": 10, "contractID": 1}, {"id": 11, "contractID": 1}],
                2: [{"id": 10, "contractID": 2}, {"id": 10, "contractID": 2}],  # duplicate
                3: [],
            }
            return {"items": data.get(cid, []), "pageDetails": {"nextPageUrl": None}}

        # --- ContractServiceUnits: one query per unique (contractID, id) pair ---
        if "ContractServiceUnits/query" in url and method == "POST":
            cid = int(_filter_value(json_body, "contractID"))
            sid = int(_filter_value(json_body, "contractServiceID"))
            return {
                "items": [{"id": int(f"{cid}{sid}"), "contractID": cid,
                           "contractServiceID": sid, "units": 5}],
                "pageDetails": {"nextPageUrl": None},
            }

        raise AssertionError(f"unexpected call: {method} {url}")

    def close(self):
        pass


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, Bucket, Key, Body, ContentType=None):
        self.objects[Key] = json.loads(Body.decode("utf-8"))


def test_autotask_end_to_end():
    creds = {
        "AUTOTASK_API_URL": "https://webservices15.autotask.net",
        "AUTOTASK_USERNAME": "apiuser@example.com",
        "AUTOTASK_API_SECRET": "shh-secret",
        "AUTOTASK_INTEGRATION_CODE": "INTG123",
        "AUTOTASK_COMPANY_ID": "516",
    }
    http = FakeHttp()
    s3 = FakeS3()

    out = run_connector("autotask_v1", creds, client_id="acme_corp",
                        http=http, s3_client=s3)

    # --- step outputs ---
    assert set(out) == {"fetch_contracts", "fetch_contract_services",
                        "fetch_contract_service_units"}, out.keys()
    assert len(out["fetch_contracts"]) == 3, "pagination should merge 2 + 1 contracts"
    assert len(out["fetch_contract_services"]) == 4, "foreach over 3 contracts (2+2+0 rows)"
    assert len(out["fetch_contract_service_units"]) == 3, "dedup -> 3 unique pairs"

    # --- dedup actually reduced the unit calls ---
    unit_calls = [c for c in http.calls if "ContractServiceUnits/query" in c["url"]]
    assert len(unit_calls) == 3, f"expected 3 unique-pair calls, got {len(unit_calls)}"

    # --- auth headers injected on every data call ---
    for call in http.calls:
        assert call["headers"].get("ApiIntegrationCode") == "INTG123"
        assert call["headers"].get("UserName") == "apiuser@example.com"
        assert call["headers"].get("Secret") == "shh-secret"

    # --- placeholders resolved inside the structured body (no brace breakage) ---
    contracts_post = next(c for c in http.calls if "Contracts/query" in c["url"]
                          and c["method"] == "POST")
    assert _filter_value(contracts_post["body"], "companyID") == "516"

    # --- landing wrote one file per step + a run manifest, at the right prefix ---
    keys = list(s3.objects)
    assert any(k.endswith("fetch_contracts.json") for k in keys), keys
    assert any(k.endswith("fetch_contract_services.json") for k in keys), keys
    assert any(k.endswith("fetch_contract_service_units.json") for k in keys), keys
    assert any(k.endswith("_manifest.json") for k in keys), keys
    assert all(k.startswith("raw/autotask_v1/acme_corp/") for k in keys), keys

    # raw rows persisted as-is
    contracts_file = next(v for k, v in s3.objects.items()
                          if k.endswith("fetch_contracts.json"))
    assert len(contracts_file) == 3

    return out, http, s3


if __name__ == "__main__":
    out, http, s3 = test_autotask_end_to_end()
    print("PASS — Autotask connector ran end-to-end through the generic engine")
    for step_id, rows in out.items():
        print(f"  {step_id}: {len(rows)} rows")
    print(f"  total HTTP calls: {len(http.calls)}")
    print(f"  S3 objects written: {len(s3.objects)}")
    for k in s3.objects:
        print(f"    s3://msp-guardian-mvp/{k}")
