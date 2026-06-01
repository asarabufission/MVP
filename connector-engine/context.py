"""Build resolver context from manifest + credentials (+ optional run metadata)."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

from manifest import Manifest


def build_context(
    credentials: dict[str, Any],
    manifest: Manifest,
    *,
    run: dict[str, Any] | None = None,
    steps: dict[str, Any] | None = None,
    item: dict[str, Any] | None = None,
    platform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Context namespaces for Slice 1 resolver (Manifest Spec §9).

    Bare keys like {source_id} resolve from run + top-level aliases.
    """
    run_data: dict[str, Any] = {
        "source_id": manifest.source_id,
        "run_date": date.today().isoformat(),
        "run_id": str(uuid4()),
        "step_id": "",
        "client_id": credentials.get("client_id", ""),
    }
    if run:
        run_data.update(run)

    ctx: dict[str, Any] = {
        "credentials": credentials,
        "steps": steps or {},
        "item": item or {},
        "platform": platform or {},
        "run": run_data,
        "source_id": run_data["source_id"],
        "client_id": run_data["client_id"],
        "run_date": run_data["run_date"],
        "run_id": run_data["run_id"],
        "step_id": run_data["step_id"],
    }
    return ctx
