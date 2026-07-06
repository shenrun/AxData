"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.registry.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from ..._shim import load_provider_first


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire._command_registry"

__all__ = ["COMMANDS", "CommandSpec", "command_code", "required_commands"]

_impl = None


def _load_impl():
    global _impl
    if _impl is None:
        _impl = load_provider_first(_PROVIDER_MODULE)
    return _impl


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(_load_impl(), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
