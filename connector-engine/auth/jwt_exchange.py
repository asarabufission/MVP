"""jwt_exchange — Ironscales: POST key, extract $.jwt, Bearer header."""

from __future__ import annotations

from typing import Any

from errors import ManifestError
from http_client import HttpClient
from jsonpath_util import extract_jsonpath
from resolver import resolve

from .registry import AuthResult, register


@register("jwt_exchange")
class JwtExchange:
    def prepare(
        self,
        auth_cfg: dict[str, Any],
        context: dict[str, Any],
        http: HttpClient,
    ) -> AuthResult:
        grant_body = auth_cfg.get("grant_body")
        token_endpoint = auth_cfg.get("token_endpoint")
        extract_cfg = auth_cfg.get("extract") or {}
        if not grant_body or not token_endpoint:
            raise ManifestError("jwt_exchange requires grant_body and token_endpoint")

        body = resolve(grant_body, context)
        url = resolve(token_endpoint, context)
        resp = http.request("POST", url, json_body=body)

        path = extract_cfg.get("access_token")
        if not path:
            raise ManifestError("jwt_exchange requires auth.extract.access_token")
        token = extract_jsonpath(resp, path)
        if not isinstance(token, str):
            raise ManifestError("Extracted access token must be a string")

        placement = auth_cfg.get("token_placement") or {}
        header_value = placement.get("template", "Bearer {access_token}").format(
            access_token=token
        )
        name = placement.get("name", "Authorization")
        return AuthResult(headers={name: header_value}, access_token=token)
