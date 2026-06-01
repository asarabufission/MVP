"""Slice 0 — Load and validate connector manifests (Pydantic)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from errors import ManifestError

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_DIR = _REPO_ROOT / "manifest"


def _iter_manifest_files(directory: Path) -> list[Path]:
    """All manifest files in a directory (.yaml and .yml), sorted by name."""
    return sorted(
        [*directory.glob("*.yaml"), *directory.glob("*.yml")],
        key=lambda p: p.name,
    )


class CredentialField(BaseModel):
    key: str
    label: str
    type: str = "text"
    required: bool = True
    secret: bool = False
    default: Any | None = None
    visible: bool | None = None
    placeholder: str | None = None
    hint: str | None = None


class Landing(BaseModel):
    type: str = "s3"
    bucket: str
    key_pattern: str
    format: str = "json"
    file_per: str = "step"
    write_mode: str = "overwrite"
    include_run_metadata: bool = True


class Manifest(BaseModel):
    """Validated manifest contract (auth/steps kept loose per strategy)."""

    schema_version: float
    source_id: str
    display_name: str
    category: str | None = None
    scope_default: str | None = None
    credential_schema: list[CredentialField] = Field(default_factory=list)
    auth: dict[str, Any]
    steps: list[dict[str, Any]]
    schema_fields: list[dict[str, Any]] = Field(default_factory=list)
    landing: Landing

    model_config = {"extra": "allow"}


def load_manifest_file(path: str | Path) -> Manifest:
    """Read a YAML manifest file and validate its shape."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ManifestError(f"Manifest file not found: {file_path}")
    with file_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ManifestError(f"Manifest must be a YAML mapping: {file_path}")
    try:
        return Manifest(**raw)
    except Exception as exc:
        raise ManifestError(f"Invalid manifest {file_path}: {exc}") from exc


def load_manifest(
    source_id: str,
    *,
    manifest_dir: Path | None = None,
) -> Manifest:
    """Load a manifest YAML by top-level source_id (scans manifest_dir)."""
    directory = manifest_dir or DEFAULT_MANIFEST_DIR
    if not directory.is_dir():
        raise ManifestError(f"Manifest directory not found: {directory}")

    for path in _iter_manifest_files(directory):
        with path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        if isinstance(raw, dict) and raw.get("source_id") == source_id:
            try:
                return Manifest(**raw)
            except Exception as exc:
                raise ManifestError(f"Invalid manifest {path}: {exc}") from exc

    raise ManifestError(
        f"No manifest found for source_id={source_id!r} in {directory}"
    )


def manifest_path_for_source(
    source_id: str,
    *,
    manifest_dir: Path | None = None,
) -> Path:
    """Return filesystem path for a source_id (for Slice 0 smoke tests)."""
    directory = manifest_dir or DEFAULT_MANIFEST_DIR
    manifest = load_manifest(source_id, manifest_dir=directory)
    for path in _iter_manifest_files(directory):
        with path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        if isinstance(raw, dict) and raw.get("source_id") == manifest.source_id:
            return path
    raise ManifestError(f"Could not resolve path for source_id={source_id!r}")
