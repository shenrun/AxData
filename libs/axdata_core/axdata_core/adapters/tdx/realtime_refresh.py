"""Compatibility wrapper for TDX realtime quote refresh entry points."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = ("request_realtime_refresh_rows", "create_tdx_client")
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_realtime_refresh() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.realtime_refresh")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.realtime_refresh"}:
            return None
        raise


def _fallback_realtime_refresh() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_realtime_refresh()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_realtime_refresh()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
