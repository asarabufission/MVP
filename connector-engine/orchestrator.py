"""Orchestrator — Slice 3 wiring (full pipeline in Slices 4–8)."""

from __future__ import annotations

from typing import Any

from auth import AuthResult, prepare_auth
from context import build_context
from http_client import HttpClient
from manifest import Manifest, load_manifest


def authenticate_source(
    source_id: str,
    credentials: dict[str, Any],
    *,
    http: HttpClient | None = None,
) -> AuthResult:
    """Load manifest by source_id and run auth.strategy."""
    manifest = load_manifest(source_id)
    client = http or HttpClient()
    owns_http = http is None
    try:
        context = build_context(credentials, manifest)
        return prepare_auth(manifest, credentials, client, context=context)
    finally:
        if owns_http:
            client.close()
