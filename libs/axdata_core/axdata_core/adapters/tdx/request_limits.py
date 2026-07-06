"""Compatibility wrapper for TDX request pagination and limit constants."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "DEFAULT_QUOTE_BATCH_SIZE",
    "TDX_CODE_PAGE_SIZE",
    "TDX_SUSPENSION_HOST_COUNT",
    "TDX_SUSPENSION_POOL_SIZE",
    "TDX_SUSPENSION_STATUS_BIT",
    "TDX_KLINE_HOST_COUNT",
    "TDX_KLINE_POOL_SIZE",
    "TDX_TRADE_PAGE_SIZE",
    "TDX_TRADE_MAX_START",
    "TDX_RANK_DEFAULT_COUNT",
    "TDX_RANK_MAX_COUNT",
    "TDX_RANK_MAX_START",
    "TDX_LIMIT_LADDER_SCAN_PAGE_SIZE",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_request_limits() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_limits")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_limits"}:
            return None
        raise


def _fallback_request_limits() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_limits()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_limits()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
