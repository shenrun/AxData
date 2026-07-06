"""Compatibility wrapper for TDX ST and suspension status row helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "StockStatusResult",
    "stock_status_stock_params",
    "current_checked_at",
    "stock_st_list_request_result",
    "stock_st_list_result",
    "st_rows_from_stock_rows",
    "stock_suspension_request_result",
    "stock_suspension_result",
    "suspension_rows_from_stock_rows",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_status_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.status_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.status_fetch"}:
            return None
        raise


def _fallback_status_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_status_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_status_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
