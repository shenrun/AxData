"""Compatibility registry wrapper for provider-owned command metadata."""

from __future__ import annotations

from importlib import import_module

_IMPL_MODULE = "axdata_source_tdx._tdx_wire._command_registry"

__all__ = ["COMMANDS", "CommandSpec", "command_code", "required_commands"]

_impl = None


def _load_impl():
    global _impl
    if _impl is None:
        _impl = import_module(_IMPL_MODULE)
    return _impl


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(_load_impl(), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
