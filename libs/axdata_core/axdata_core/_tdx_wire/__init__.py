"""Compatibility shim for ``axdata_core._tdx_wire``.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working when the TDX plugin is installed and
enabled. Core no longer contains a runnable TDX wire fallback.
"""

from __future__ import annotations

from ._shim import load_provider_first


_CLIENT_EXPORTS = {"Client", "TdxClient"}
_PROVIDER_CLIENT_MODULE = "axdata_source_tdx._tdx_wire.client"

__all__ = [
    "Client",
    "TdxClient",
    "__version__",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    if name in _CLIENT_EXPORTS:
        implementation = load_provider_first(_PROVIDER_CLIENT_MODULE)
        value = getattr(implementation, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
