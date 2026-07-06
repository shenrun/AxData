"""Compatibility shim for axdata_core._tdx_wire.transport.socket.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from .._shim import install_lazy_provider_first


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.transport.socket"


install_lazy_provider_first(
    globals(),
    provider_module=_PROVIDER_MODULE,
        exports=[
        "Any",
        "ConnectionClosedError",
        "DEFAULT_HEARTBEAT_INTERVAL",
        "Empty",
        "ProtocolError",
        "Queue",
        "ResponseTimeoutError",
        "Sequence",
        "SocketTransport",
        "TYPE_CHECKING",
        "TYPE_HANDSHAKE",
        "TYPE_HEARTBEAT",
        "TransportError",
        "annotations",
        "import_module",
        "socket",
        "threading",
        "unique_hosts",
    ],
)
