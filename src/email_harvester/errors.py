"""Custom exceptions for the harvester domain."""


class HarvesterError(Exception):
    """Base exception for this project."""


class ConfigError(HarvesterError):
    """Raised when runtime configuration is invalid."""


class FetchError(HarvesterError):
    """Raised when fetching a URL fails unexpectedly."""


class ProviderError(HarvesterError):
    """Raised when a third-party provider call fails."""


class VerificationError(HarvesterError):
    """Raised when email verification fails unexpectedly."""
