"""TDX extended-market exception hierarchy.

These exceptions are owned by the TDX Ext adapter.  They intentionally inherit
from the ordinary TDX wire exceptions for old catch-site compatibility, but do
not import through the legacy core wire shim.
"""

from __future__ import annotations

try:
    from axdata_source_tdx._tdx_wire.exceptions import (
        ConnectionClosedError as _WireConnectionClosedError,
        ProtocolError as _WireProtocolError,
        ResponseTimeoutError as _WireResponseTimeoutError,
    )
except ModuleNotFoundError as exc:
    if exc.name == "axdata_source_tdx" or str(exc.name).startswith("axdata_source_tdx."):
        class _WireProtocolError(RuntimeError):
            pass

        class _WireConnectionClosedError(_WireProtocolError):
            pass

        class _WireResponseTimeoutError(_WireProtocolError):
            pass
    else:
        raise


class TdxExtError(Exception):
    """Base class for TDX extended-market adapter errors."""


class ProtocolError(_WireProtocolError, TdxExtError):
    """Raised when extended-market protocol encoding or decoding fails."""


class ConnectionClosedError(_WireConnectionClosedError, TdxExtError):
    """Raised when an extended-market server closes or refuses a connection."""


class ResponseTimeoutError(_WireResponseTimeoutError, TdxExtError):
    """Raised when an extended-market request does not receive a response in time."""


__all__ = [
    "TdxExtError",
    "ProtocolError",
    "ConnectionClosedError",
    "ResponseTimeoutError",
]
