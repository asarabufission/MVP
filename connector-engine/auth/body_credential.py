"""body_credential — LastPass: credentials in JSON body, no Authorization header."""

from __future__ import annotations

from typing import Any

from errors import ManifestError
from http_client import HttpClient
from resolver import resolve

from .registry import AuthResult, register


@register("body_credential")
class BodyCredential:
    def prepare(
        self,
        auth_cfg: dict[str, Any],
        context: dict[str, Any],
        http: HttpClient,  # noqa: ARG002
    ) -> AuthResult:
        grant_body = auth_cfg.get("grant_body")
        if not grant_body:
            raise ManifestError("body_credential requires auth.grant_body")

        if auth_cfg.get("token_endpoint"):
            raise ManifestError(
                "body_credential must not use token_endpoint (creds go in body only)"
            )

        return AuthResult(body_extra=resolve(grant_body, context))
