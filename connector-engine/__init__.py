"""
Manifest-driven connector engine (Slices 0–3).

See ENGINE_BUILD_PLAN.md for the full specification.
"""

from auth import AuthResult, prepare_auth
from errors import (
    AuthError,
    ConnectorEngineError,
    LandingError,
    ManifestError,
    StepError,
    StrategyNotImplementedError,
)
from landing import land
from manifest import Manifest, load_manifest, load_manifest_file
from orchestrator import authenticate_source, run_connector
from resolver import resolve

__all__ = [
    "AuthResult",
    "Manifest",
    "authenticate_source",
    "run_connector",
    "land",
    "load_manifest",
    "load_manifest_file",
    "prepare_auth",
    "resolve",
    "AuthError",
    "ManifestError",
    "StepError",
    "LandingError",
    "StrategyNotImplementedError",
    "ConnectorEngineError",
]
