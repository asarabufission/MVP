"""Slice 1 — Templating resolver ({credentials.*}, {steps.*}, {run.*}, defaults)."""

from __future__ import annotations

import re
from typing import Any

PLACEHOLDER = re.compile(r"\{([^}]+)\}")


def _lookup(dotted: str, context: dict[str, Any]) -> Any:
    """Resolve dotted path with optional |default suffix."""
    if "|" in dotted:
        path, default = dotted.split("|", 1)
        default = default.strip()
    else:
        path, default = dotted, None

    node: Any = context
    for part in path.strip().split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


def resolve(value: Any, context: dict[str, Any]) -> Any:
    """Replace every {placeholder} in strings; recurse into dicts and lists."""
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            found = _lookup(match.group(1), context)
            return str(found) if found is not None else ""

        if "{" not in value:
            return value
        return PLACEHOLDER.sub(repl, value)

    if isinstance(value, dict):
        return {k: resolve(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, context) for v in value]
    return value
