"""JSONPath extraction for auth.extract and step captures."""

from __future__ import annotations

from typing import Any

from jsonpath_ng import parse as jp_parse

from errors import AuthError


def extract_jsonpath(data: Any, path: str) -> Any:
    matches = jp_parse(path).find(data)
    if not matches:
        raise AuthError(f"JSONPath {path!r} not found in response")
    return matches[0].value
