"""Connector engine exceptions."""


class ConnectorEngineError(Exception):
    """Base error for the connector engine."""


class ManifestError(ConnectorEngineError):
    """Invalid or missing manifest configuration."""


class AuthError(ConnectorEngineError):
    """Authentication failed (vendor rejected credentials or misconfiguration)."""


class StrategyNotImplementedError(ConnectorEngineError):
    """Manifest references an auth strategy that is not implemented yet."""
