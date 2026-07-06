"""Compatibility shim for axdata_core._tdx_wire.transport.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from .._shim import load_provider_first


_EXPORT_MODULES = {
    "InMemoryTransport": "axdata_source_tdx._tdx_wire.transport.memory",
    "PooledSocketTransport": "axdata_source_tdx._tdx_wire.transport.pool",
    "SocketTransport": "axdata_source_tdx._tdx_wire.transport.socket",
    "Transport": "axdata_source_tdx._tdx_wire.transport.base",
}

__all__ = ["InMemoryTransport", "PooledSocketTransport", "SocketTransport", "Transport"]


def __getattr__(name: str):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    implementation = load_provider_first(module_name)
    value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
