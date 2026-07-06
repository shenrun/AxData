"""axdata_source_tdx._tdx_wire exception hierarchy."""


class TdxWireError(Exception):
    """Base class for package errors."""


class ProtocolError(TdxWireError):
    """Raised when protocol encoding or decoding fails."""


class TransportError(TdxWireError):
    """Raised when the transport cannot complete a request."""


class ConnectionClosedError(TransportError):
    """Raised when the remote server closes the connection."""


class ResponseTimeoutError(TransportError):
    """Raised when a request does not receive a response in time."""


class UnsupportedCommandError(TdxWireError):
    """Raised when an API method has no migrated 7709 command yet."""
