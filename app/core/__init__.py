# app/core/__init__.py
"""Core foundation utilities: configuration, structured logging, and exceptions."""

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AuditAppError,
    AuditNotFoundError,
    ConfigurationError,
    InvalidAuditStateError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ReportUnavailableError,
    StorageError,
    UnsupportedProviderError,
    ValidationError,
)
from app.core.logging import setup_logging

__all__ = [
    "AuditAppError",
    "AuditNotFoundError",
    "ConfigurationError",
    "InvalidAuditStateError",
    "ProviderAuthenticationError",
    "ProviderError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ReportUnavailableError",
    "Settings",
    "StorageError",
    "UnsupportedProviderError",
    "ValidationError",
    "get_settings",
    "setup_logging",
]
