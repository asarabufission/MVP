"""Slices 4 + 6 — request step runner and foreach.

run_request_step  — build one request from the manifest, inject auth, paginate,
                    shape, and capture. Returns {"rows": [...], <captures...>}.
run_foreach_step  — repeat run_request_step once per item from a prior step's
                    rows, with optional dedup and parent-field joins.
"""

from __future__ import annotations

from typing import Any

from auth.registry import AuthResult
from errors import StepError
from http_client import HttpClient
from pagination import run_pagination
from resolver import resolve
from transforms import apply_captures, apply_response_shape


def run_request_step(
    step: dict[str, Any],
    context: dict[str, Any],
    http: HttpClient,
    auth_result: AuthResult,
) -> dict[str, Any]:
    """Execute one ordinary (non-foreach) step."""
    url = resolve(step["url"], context)

    headers = {
        str(k): str(v)
        for k, v in resolve(step.get("headers", {}) or {}, context).items()
    }
    headers.update(auth_result.headers)

    params = resolve(step.get("params", {}) or {}, context) or None

    body = resolve(step.get("body", {}) or {}, context)
    if auth_result.body_extra:
        body = {**auth_result.body_extra, **body}
    body = body or None

    response_cfg = step.get("response", {}) or {}
    data_key = response_cfg.get("data_key")

    rows, first = run_pagination(
        step.get("pagination"),
        http,
        method=step.get("method", "GET"),
        url=url,
        headers=headers,
        params=params,
        body=body,
        data_key=data_key,
    )

    rows = apply_response_shape(rows, response_cfg, first)

    result: dict[str, Any] = {"rows": rows}
    result.update(apply_captures(step, first, context))
    return result


def run_foreach_step(
    step: dict[str, Any],
    context: dict[str, Any],
    http: HttpClient,
    auth_result: AuthResult,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a step once per item from a previous step's rows."""
    source = step.get("foreach_source", "")
    parts = source.split(".")
    if len(parts) < 2 or parts[0] != "steps":
        raise StepError(f"foreach_source must be 'steps.<id>': {source!r}")
    source_id = parts[1]

    parent = context.get("steps", {}).get(source_id)
    if parent is None:
        raise StepError(f"foreach_source step has not run yet: {source_id!r}")
    items: list[Any] = list(parent.get("rows", []))

    dedup_keys = step.get("foreach_dedup_on")
    if dedup_keys:
        seen: set[tuple[Any, ...]] = set()
        unique: list[Any] = []
        for it in items:
            sig = tuple(it.get(k) if isinstance(it, dict) else it for k in dedup_keys)
            if sig not in seen:
                seen.add(sig)
                unique.append(it)
        items = unique

    if dry_run:
        items = items[:3]

    join_fields = step.get("join_fields_from_parent") or []
    out: list[Any] = []
    saved_item = context.get("item")
    try:
        for item in items:
            context["item"] = item
            result = run_request_step(step, context, http, auth_result)
            rows = result["rows"]
            if not rows and step.get("skip_if_response_empty"):
                continue
            for row in rows:
                if isinstance(row, dict) and isinstance(item, dict):
                    for field in join_fields:
                        row[field] = item.get(field)
            out.extend(rows)
    finally:
        if saved_item is None:
            context.pop("item", None)
        else:
            context["item"] = saved_item

    return {"rows": out}
