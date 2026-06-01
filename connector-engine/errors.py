"""Connector engine exceptions."""


class ConnectorEngineError(Exception):
    """Base error for the connector engine."""


class ManifestError(ConnectorEngineError):
    """Invalid or missing manifest configuration."""


class AuthError(ConnectorEngineError):
    """Authentication failed (vendor rejected credentials or misconfiguration)."""


class StrategyNotImplementedError(ConnectorEngineError):
    """Manifest references an auth strategy that is not implemented yet."""


class StepError(ConnectorEngineError):
    """A data step failed (request, pagination, foreach, or transform)."""


class LandingError(ConnectorEngineError):
    """Writing raw step output to the landing target (S3) failed."""
