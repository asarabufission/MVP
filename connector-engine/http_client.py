"""Slice 2 — HTTP client wrapper (all vendor calls go through here)."""

from __future__ import annotations

from typing import Any

import requests

from errors import AuthError


class HttpClient:
    def __init__(self, timeout: int = 30, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self._owns_session = session is None

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        form_body: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """One HTTP call; returns parsed JSON dict."""
        req_headers = dict(headers or {})
        if json_body is not None and "Content-Type" not in req_headers:
            req_headers.setdefault("Content-Type", "application/json")

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=req_headers or None,
                params=params,
                json=json_body,
                data=form_body,
                auth=basic_auth,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = str(response.json())
            except Exception:
                detail = response.text[:500] if response is not None else ""
            raise AuthError(
                f"HTTP {response.status_code if response is not None else '?'}: {detail}"
            ) from exc
        except requests.RequestException as exc:
            raise AuthError(f"Request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AuthError("Vendor returned non-JSON response") from exc

        if not isinstance(payload, dict):
            raise AuthError("Vendor response must be a JSON object")
        return payload

    def close(self) -> None:
        if self._owns_session:
            self.session.close()
