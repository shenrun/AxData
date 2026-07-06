"""Transport abstractions for axdata_source_tdx._tdx_wire."""

from __future__ import annotations

from importlib import import_module

__all__ = ["InMemoryTransport", "PooledSocketTransport", "SocketTransport", "Transport"]

_EXPORT_MODULES = {
    "InMemoryTransport": ".memory",
    "PooledSocketTransport": ".pool",
    "SocketTransport": ".socket",
    "Transport": ".base",
}


def __getattr__(name: str):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
