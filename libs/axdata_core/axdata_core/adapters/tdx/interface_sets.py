"""Compatibility wrapper for TDX request interface declarations."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "FINANCE_INTERFACE_FIELDS",
    "DAILY_SHARE_FINANCE_BATCH_SIZE",
    "INTRADAY_SUBCHART_INTERFACE_SPECS",
    "SUPPORTED_INTERFACES",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_interface_sets() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.interface_sets")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.interface_sets"}:
            return None
        raise


def _fallback_interface_sets() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_interface_sets()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_interface_sets()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
