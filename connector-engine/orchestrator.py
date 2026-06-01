"""Orchestrator — the conductor.

authenticate_source  — Slice 3: load a manifest and run its auth strategy only.
run_connector        — full pipeline: pre-auth steps -> authenticate -> run steps
                       (request/foreach) in order -> land raw output to S3.

All real work lives in the slices; this file only coordinates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from auth import AuthResult, prepare_auth
from context import build_context
from errors import ConnectorEngineError, StepError
from http_client import HttpClient
from landing import land
from manifest import Manifest, load_manifest
from resolver import resolve
from steps import run_foreach_step, run_request_step


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


def _truthy(expr: str, context: dict[str, Any]) -> bool:
    """Evaluate a step `condition` like 'credentials.x' or '!credentials.x'."""
    expr = expr.strip()
    negate = expr.startswith("!")
    if negate:
        expr = expr[1:].strip()
    value = resolve("{" + expr + "}", context)
    truth = bool(value) and value not in ("", "None", "False", "false")
    return (not truth) if negate else truth


def _run_step(
    step: dict[str, Any],
    context: dict[str, Any],
    http: HttpClient,
    auth_result: AuthResult,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    if step.get("type") == "foreach":
        return run_foreach_step(step, context, http, auth_result, dry_run=dry_run)
    return run_request_step(step, context, http, auth_result)


def run_connector(
    source_id: str,
    credentials: dict[str, Any],
    *,
    client_id: str | None = None,
    platform: dict[str, Any] | None = None,
    dry_run: bool = False,
    http: HttpClient | None = None,
    manifest_dir: Path | None = None,
    land_results: bool | None = None,
    s3_client: Any | None = None,
) -> dict[str, list[Any]]:
    """Run a full connector: authenticate, run every step, land raw output.

    Returns {step_id: rows}. Landing is skipped on dry_run unless land_results
    is explicitly set.
    """
    manifest = load_manifest(source_id, manifest_dir=manifest_dir)
    client = http or HttpClient()
    owns_http = http is None
    if land_results is None:
        land_results = not dry_run

    run_meta = {"client_id": client_id} if client_id is not None else None
    context = build_context(credentials, manifest, run=run_meta, platform=platform)

    pre_auth_steps = [s for s in manifest.steps if s.get("pre_auth")]
    main_steps = [s for s in manifest.steps if not s.get("pre_auth")]

    step_outputs: dict[str, list[Any]] = {}
    try:
        # Pre-auth steps run before a token exists (e.g. tenant discovery).
        empty_auth = AuthResult()
        for step in pre_auth_steps:
            if "condition" in step and not _truthy(step["condition"], context):
                continue
            result = _execute(step, context, client, empty_auth, dry_run=dry_run)
            if result is None:
                continue
            context["steps"][step["id"]] = result

        auth_result = prepare_auth(manifest, credentials, client, context=context)

        for step in main_steps:
            if "condition" in step and not _truthy(step["condition"], context):
                continue
            result = _execute(step, context, client, auth_result, dry_run=dry_run)
            if result is None:
                continue
            context["steps"][step["id"]] = result
            step_outputs[step["id"]] = result["rows"]

        if land_results:
            land(manifest, step_outputs, context, s3_client=s3_client)

        return step_outputs
    finally:
        if owns_http:
            client.close()


def _execute(
    step: dict[str, Any],
    context: dict[str, Any],
    http: HttpClient,
    auth_result: AuthResult,
    *,
    dry_run: bool,
) -> dict[str, Any] | None:
    """Run a step, honouring on_failure (abort | continue)."""
    try:
        return _run_step(step, context, http, auth_result, dry_run=dry_run)
    except ConnectorEngineError as exc:
        if step.get("on_failure") == "continue":
            return None
        raise StepError(f"Step {step.get('id')!r} failed: {exc}") from exc
