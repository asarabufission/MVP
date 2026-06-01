"""Slice 7 — Extract captures, named transform ops, and response shaping.

Two "phone books" plus a response-shape helper:
  * TRANSFORMS  — name -> function (e.g. extract_guid_from_url)
  * extract      — JSONPath captures stored under context["steps"][id]
  * apply_response_shape — object_map -> list (LastPass-style dict responses)

Nothing here is source-specific; manifests opt in by naming these pieces.
"""

from __future__ import annotations

import re
from typing import Any

from jsonpath_ng import parse as jp_parse

from errors import ManifestError
from resolver import resolve


def extract_guid_from_url(value: Any) -> str | None:
    """Pull a 36-char GUID out of a URL (Microsoft issuer URL -> tenant id)."""
    if not isinstance(value, str):
        return None
    match = re.search(r"[0-9a-fA-F-]{36}", value)
    return match.group(0) if match else None


TRANSFORMS = {
    "extract_guid_from_url": extract_guid_from_url,
}


def _safe_jsonpath(data: Any, path: str) -> Any:
    """First JSONPath match, or None when absent (captures are best-effort)."""
    try:
        matches = jp_parse(path).find(data)
    except Exception:
        return None
    return matches[0].value if matches else None


def apply_captures(step: dict[str, Any], response: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Run a step's `extract` JSONPaths and `transform` ops against `response`.

    Returns a flat dict merged into the step result so later steps can read
    {steps.<id>.<name>}. Transform `source` may reference this step's own
    captures (resolved against a context that includes them).
    """
    captured: dict[str, Any] = {}

    for name, path in (step.get("extract") or {}).items():
        captured[name] = _safe_jsonpath(response, path)

    transform_cfg = step.get("transform") or {}
    if transform_cfg:
        step_id = step.get("id", "")
        local_steps = {**context.get("steps", {}), step_id: dict(captured)}
        local_ctx = {**context, "steps": local_steps}
        for name, spec in transform_cfg.items():
            op = spec.get("op")
            fn = TRANSFORMS.get(op)
            if fn is None:
                raise ManifestError(
                    f"Unknown transform op: {op!r}. "
                    f"Registered: {', '.join(sorted(TRANSFORMS)) or '(none)'}"
                )
            source = spec.get("source")
            value = resolve("{" + source + "}", local_ctx) if source else None
            captured[name] = fn(value)

    return captured


def apply_response_shape(
    rows: list[Any],
    response_cfg: dict[str, Any],
    first_response: dict[str, Any],
) -> list[Any]:
    """Convert an object_map response (a dict keyed by id) into a list of rows,
    injecting the map key as a field. Non-object_map responses pass through."""
    cfg = response_cfg or {}
    if cfg.get("shape") != "object_map":
        return rows

    data_key = cfg.get("data_key")
    mapping = (first_response or {}).get(data_key) if data_key else first_response
    if not isinstance(mapping, dict):
        return rows

    key_as = (cfg.get("to_array") or {}).get("key_as", "key")
    shaped: list[Any] = []
    for key, value in mapping.items():
        if isinstance(value, dict):
            shaped.append({**value, key_as: key})
        else:
            shaped.append({key_as: key, "value": value})
    return shaped
