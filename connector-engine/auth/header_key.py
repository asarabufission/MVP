"""header_key — Autotask: static auth headers, no token exchange."""

from __future__ import annotations

from typing import Any

from errors import ManifestError
from http_client import HttpClient
from resolver import resolve

from .registry import AuthResult, register


@register("header_key")
class HeaderKey:
    def prepare(
        self,
        auth_cfg: dict[str, Any],
        context: dict[str, Any],
        http: HttpClient,  # noqa: ARG002 — no token call; headers are static
    ) -> AuthResult:
        headers = auth_cfg.get("headers")
        if not headers or not isinstance(headers, dict):
            raise ManifestError("header_key requires a non-empty auth.headers mapping")

        resolved = {str(k): str(v) for k, v in resolve(headers, context).items()}
        return AuthResult(headers=resolved)
