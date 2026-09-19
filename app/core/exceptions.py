"""Application exception hierarchy for LLM Brand Visibility Audit Tool.

Defines domain-specific and operational exceptions to ensure structured,
consistent error propagation and clean translation into HTTP API error responses.
"""

from typing import Any


class AuditAppError(Exception):
    """Base exception for all domain errors within the audit application."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(AuditAppError):
    """Raised when application configuration or credentials are missing or invalid."""


class AuditNotFoundError(AuditAppError):
    """Raised when an audit ID does not exist in the storage system."""


class InvalidAuditStateError(AuditAppError):
    """Raised when attempting an operation invalid for the current audit lifecycle state."""


class ProviderError(AuditAppError):
    """Base exception for errors occurring during external LLM provider interactions."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        is_retryable: bool = False,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.provider = provider
        self.model = model
        self.is_retryable = is_retryable
        self.status_code = status_code


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rejects a request due to rate or quota limits."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        retry_after_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            model=model,
            is_retryable=True,
            status_code=429,
            details=details,
        )
        self.retry_after_seconds = retry_after_seconds


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            model=model,
            is_retryable=True,
            status_code=504,
            details=details,
        )


class ProviderAuthenticationError(ProviderError):
    """Raised when authentication with a provider fails (e.g. invalid API key). Non-retryable."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            model=model,
            is_retryable=False,
            status_code=401,
            details=details,
        )


class UnsupportedProviderError(AuditAppError):
    """Raised when an unrecognized provider identifier is specified."""


class StorageError(AuditAppError):
    """Raised when a storage I/O, serialization, or deserialization failure occurs."""


class ReportUnavailableError(AuditAppError):
    """Raised when requesting a report for an audit that has not executed or has no valid observations."""


class ValidationError(AuditAppError):
    """Raised when request payload or audit input data fails domain validation rules."""
