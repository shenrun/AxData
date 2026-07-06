"""Shared source request exception types.

This module stays lightweight so source adapters can raise canonical AxData
errors without importing the full source request gateway.
"""

from __future__ import annotations


class SourceRequestError(RuntimeError):
    """Base class for source request failures."""

    code = "SOURCE_REQUEST_ERROR"


class SourceInterfaceNotFound(SourceRequestError):
    """Raised when an interface is not present in the AxData catalog."""

    code = "SOURCE_INTERFACE_NOT_FOUND"


class SourceAdapterNotFound(SourceRequestError):
    """Raised when an interface exists but no adapter supports it yet."""

    code = "SOURCE_ADAPTER_NOT_FOUND"


class SourceRequestValidationError(SourceRequestError, ValueError):
    """Raised when params or fields do not match the interface contract."""

    code = "SOURCE_REQUEST_VALIDATION_ERROR"


class SourceUnavailableError(SourceRequestError):
    """Raised when the upstream source cannot be reached."""

    code = "SOURCE_UNAVAILABLE"


class SourceAdapterError(SourceRequestError):
    """Raised when an adapter fails after reaching its source boundary."""

    code = "SOURCE_ADAPTER_ERROR"
