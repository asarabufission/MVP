"""Slice 8 — Land raw step outputs to S3.

One JSON object per data-producing step (file_per: step) or one combined object
(file_per: run), written to the path built from landing.key_pattern. No
transformation — the raw rows are persisted as-is. When include_run_metadata is
set, an extra _manifest file with run info + a file index is also written.

boto3 is imported lazily so the engine (and its tests) load without AWS deps;
tests inject a fake client via the s3_client argument.
"""

from __future__ import annotations

import json
from typing import Any

from errors import LandingError
from manifest import Manifest
from resolver import resolve

_s3_client: Any = None


def _get_s3_client() -> Any:
    global _s3_client
    if _s3_client is None:
        import boto3  # lazy: only needed for real runs

        _s3_client = boto3.client("s3")
    return _s3_client


def _key_for(manifest: Manifest, context: dict[str, Any], step_id: str) -> str:
    return resolve(manifest.landing.key_pattern, {**context, "step_id": step_id})


def _put(client: Any, bucket: str, key: str, payload: Any) -> None:
    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(payload, indent=2, default=str).encode("utf-8"),
            ContentType="application/json",
        )
    except Exception as exc:  # noqa: BLE001 — wrap any boto/client error
        raise LandingError(f"Failed to write s3://{bucket}/{key}: {exc}") from exc


def land(
    manifest: Manifest,
    step_outputs: dict[str, list[Any]],
    context: dict[str, Any],
    *,
    s3_client: Any | None = None,
) -> list[str]:
    """Write step outputs to S3. Returns the list of keys written."""
    cfg = manifest.landing
    client = s3_client or _get_s3_client()
    written: list[str] = []

    if cfg.file_per == "run":
        key = _key_for(manifest, context, "all")
        _put(client, cfg.bucket, key, step_outputs)
        written.append(key)
    else:
        for step_id, rows in step_outputs.items():
            key = _key_for(manifest, context, step_id)
            _put(client, cfg.bucket, key, rows)
            written.append(key)

    if cfg.include_run_metadata:
        meta = {
            "source_id": context.get("source_id"),
            "client_id": context.get("client_id"),
            "run_id": context.get("run_id"),
            "run_date": context.get("run_date"),
            "row_counts": {sid: len(rows) for sid, rows in step_outputs.items()},
            "files": written,
        }
        meta_key = _key_for(manifest, context, "_manifest")
        _put(client, cfg.bucket, meta_key, meta)
        written.append(meta_key)

    return written
