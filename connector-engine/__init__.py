"""
Manifest-driven connector engine (Slices 0–3).

See ENGINE_BUILD_PLAN.md for the full specification.
"""

from auth import AuthResult, prepare_auth
from errors import (
    AuthError,
    ConnectorEngineError,
    ManifestError,
    StrategyNotImplementedError,
)
from manifest import Manifest, load_manifest, load_manifest_file
from orchestrator import authenticate_source
from resolver import resolve

__all__ = [
    "AuthResult",
    "Manifest",
    "authenticate_source",
    "load_manifest",
    "load_manifest_file",
    "prepare_auth",
    "resolve",
    "AuthError",
    "ManifestError",
    "StrategyNotImplementedError",
    "ConnectorEngineError",
]
