"""
Slice 3 — Auth strategy registry and prepare_auth entry point.
"""

from __future__ import annotations

from typing import Any

from context import build_context
from errors import ManifestError
from http_client import HttpClient
from manifest import Manifest

from .registry import AuthResult, get_auth_strategy, register
from . import body_credential as _body_credential  # noqa: F401 — registers
from . import certificate_msal as _certificate_msal  # noqa: F401
from . import header_key as _header_key  # noqa: F401
from . import jwt_exchange as _jwt_exchange  # noqa: F401
from . import oauth2_password as _oauth2_password  # noqa: F401


def prepare_auth(
    manifest: Manifest,
    credentials: dict[str, Any],
    http: HttpClient,
    *,
    context: dict[str, Any] | None = None,
) -> AuthResult:
    auth_cfg = manifest.auth
    if not auth_cfg:
        raise ManifestError("Manifest is missing auth section")

    strategy_name = auth_cfg.get("strategy")
    if not strategy_name:
        raise ManifestError("Manifest auth.strategy is required")

    ctx = context or build_context(credentials, manifest)
    strategy = get_auth_strategy(strategy_name)
    return strategy.prepare(auth_cfg, ctx, http)


__all__ = ["AuthResult", "register", "get_auth_strategy", "prepare_auth"]
