"""oauth2_password_grant — Datto RMM: Basic client + password grant form."""

from __future__ import annotations

from typing import Any

from errors import ManifestError
from http_client import HttpClient
from jsonpath_util import extract_jsonpath
from resolver import resolve

from .registry import AuthResult, register


@register("oauth2_password_grant")
class OAuth2PasswordGrant:
    def prepare(
        self,
        auth_cfg: dict[str, Any],
        context: dict[str, Any],
        http: HttpClient,
    ) -> AuthResult:
        token_endpoint = auth_cfg.get("token_endpoint")
        grant_cfg = auth_cfg.get("grant")
        client_cfg = auth_cfg.get("client") or {}
        extract_cfg = auth_cfg.get("extract") or {}
        if not token_endpoint or not grant_cfg:
            raise ManifestError(
                "oauth2_password_grant requires token_endpoint and grant"
            )

        if client_cfg.get("type") != "basic":
            raise ManifestError(
                f"Unsupported oauth2 client.type: {client_cfg.get('type')!r}"
            )

        resolved_client = resolve(client_cfg, context)
        client_username = resolved_client.get("username")
        client_password = resolved_client.get("password")
        if not client_username or not client_password:
            raise ManifestError(
                "oauth2_password_grant auth.client requires username and password "
                "(e.g. Datto public-client / public)"
            )
        basic_auth = (str(client_username), str(client_password))

        url = resolve(token_endpoint, context)
        # Password grant form body — API user creds from manifest auth.grant
        form = {str(k): str(v) for k, v in resolve(grant_cfg, context).items()}
        resp = http.request("POST", url, form_body=form, basic_auth=basic_auth)

        path = extract_cfg.get("access_token")
        if not path:
            raise ManifestError(
                "oauth2_password_grant requires auth.extract.access_token"
            )
        token = extract_jsonpath(resp, path)
        if not isinstance(token, str):
            raise ManifestError("Extracted access token must be a string")

        placement = auth_cfg.get("token_placement") or {}
        header_value = placement.get("template", "Bearer {access_token}").format(
            access_token=token
        )
        name = placement.get("name", "Authorization")
        return AuthResult(headers={name: header_value}, access_token=token)
