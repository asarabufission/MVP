"""Auth strategy registry (Slice 3 phone book)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from http_client import HttpClient

_REGISTRY: dict[str, type] = {}


@dataclass
class AuthResult:
    headers: dict[str, str] = field(default_factory=dict)
    body_extra: dict[str, Any] = field(default_factory=dict)
    access_token: str | None = None


class AuthStrategy(Protocol):
    def prepare(
        self,
        auth_cfg: dict[str, Any],
        context: dict[str, Any],
        http: HttpClient,
    ) -> AuthResult: ...


def register(name: str):
    def wrap(cls: type) -> type:
        _REGISTRY[name] = cls
        return cls

    return wrap


def get_auth_strategy(name: str) -> AuthStrategy:
    from errors import StrategyNotImplementedError

    if name not in _REGISTRY:
        raise StrategyNotImplementedError(
            f"Unknown auth strategy: {name!r}. "
            f"Registered: {', '.join(sorted(_REGISTRY)) or '(none)'}"
        )
    return _REGISTRY[name]()
