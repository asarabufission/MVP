"""Slice 5 — Pagination handlers (none, page, next_link, cursor_url).

A paginator's job is to make however many HTTP calls a step needs and return
(all_rows, first_response). The first response is handed back so the step runner
can run `extract`/`transform` captures and `object_map` shaping against it.

All vendor calls go through HttpClient (Slice 2). URL/headers/params/body are
already resolved by the step runner before they reach a paginator.
"""

from __future__ import annotations

from typing import Any, Callable

from errors import ManifestError
from http_client import HttpClient

Rows = list[Any]
Paginator = Callable[..., tuple[Rows, dict[str, Any]]]


def _rows_from(resp: Any, data_key: str | None) -> Rows:
    """Pull the row list out of a response using response.data_key.

    A top-level array response (e.g. Dropsuite /api/users) is itself the rows,
    regardless of data_key.
    """
    if isinstance(resp, list):
        return resp
    if not data_key:
        return [resp]
    rows = resp.get(data_key, [])
    if rows is None:
        return []
    return rows if isinstance(rows, list) else [rows]


def _dig(data: Any, dotted: str) -> Any:
    """Read a value by key. Tries the literal key first (e.g. '@odata.nextLink'),
    then falls back to dotted traversal (e.g. 'pageDetails.nextPageUrl')."""
    if isinstance(data, dict) and dotted in data:
        return data[dotted]
    node = data
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def _request(
    http: HttpClient,
    method: str,
    url: str,
    headers: dict[str, str] | None,
    params: dict[str, Any] | None,
    body: dict[str, Any] | None,
) -> dict[str, Any]:
    return http.request(
        method,
        url,
        headers=headers or None,
        params=params or None,
        json_body=body or None,
    )


def _paginate_none(
    cfg: dict[str, Any],
    http: HttpClient,
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None,
    params: dict[str, Any] | None,
    body: dict[str, Any] | None,
    data_key: str | None,
) -> tuple[Rows, dict[str, Any]]:
    resp = _request(http, method, url, headers, params, body)
    return _rows_from(resp, data_key), resp


def _paginate_page(
    cfg: dict[str, Any],
    http: HttpClient,
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None,
    params: dict[str, Any] | None,
    body: dict[str, Any] | None,
    data_key: str | None,
) -> tuple[Rows, dict[str, Any]]:
    """Numbered pages; stop on an empty page (stop_when: empty_array)."""
    page_param = cfg.get("page_param", "page")
    size_param = cfg.get("size_param")
    size = cfg.get("size", 100)
    page = 1
    all_rows: Rows = []
    first: dict[str, Any] | None = None
    base_params = dict(params or {})
    while True:
        page_params = dict(base_params)
        page_params[page_param] = page
        if size_param:
            page_params[size_param] = size
        resp = _request(http, method, url, headers, page_params, body)
        if first is None:
            first = resp
        rows = _rows_from(resp, data_key)
        if not rows:
            break
        all_rows.extend(rows)
        page += 1
    return all_rows, first or {}


def _paginate_cursor(
    cfg: dict[str, Any],
    http: HttpClient,
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None,
    params: dict[str, Any] | None,
    body: dict[str, Any] | None,
    data_key: str | None,
) -> tuple[Rows, dict[str, Any]]:
    """Follow a next-page URL carried in the response until it is absent.

    Covers both `next_link` (Graph '@odata.nextLink') and `cursor_url`
    (Autotask 'pageDetails.nextPageUrl'). The next URL is a fully-formed GET
    link, so follow-up pages are GET with no params/body.
    """
    next_key = cfg.get("next_key")
    if not next_key:
        raise ManifestError(
            f"pagination.type {cfg.get('type')!r} requires pagination.next_key"
        )

    resp = _request(http, method, url, headers, params, body)
    first = resp
    all_rows: Rows = list(_rows_from(resp, data_key))

    next_url = _dig(resp, next_key)
    while next_url:
        resp = _request(http, "GET", str(next_url), headers, None, None)
        all_rows.extend(_rows_from(resp, data_key))
        next_url = _dig(resp, next_key)

    return all_rows, first


_PAGINATORS: dict[str, Paginator] = {
    "none": _paginate_none,
    "page": _paginate_page,
    "next_link": _paginate_cursor,
    "cursor_url": _paginate_cursor,
}


def run_pagination(
    pagination_cfg: dict[str, Any] | None,
    http: HttpClient,
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None,
    params: dict[str, Any] | None,
    body: dict[str, Any] | None,
    data_key: str | None,
) -> tuple[Rows, dict[str, Any]]:
    """Dispatch to the paginator named by pagination.type (default 'none')."""
    cfg = pagination_cfg or {"type": "none"}
    ptype = cfg.get("type", "none")
    handler = _PAGINATORS.get(ptype)
    if handler is None:
        raise ManifestError(
            f"Unsupported pagination.type: {ptype!r}. "
            f"Supported: {', '.join(sorted(_PAGINATORS))}"
        )
    return handler(
        cfg,
        http,
        method=method,
        url=url,
        headers=headers,
        params=params,
        body=body,
        data_key=data_key,
    )
