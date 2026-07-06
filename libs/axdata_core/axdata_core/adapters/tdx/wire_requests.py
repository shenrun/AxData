"""Compatibility wrapper for TDX wire request helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "tdx_legacy_quotes",
    "tdx_explicit_quotes",
    "tdx_refresh_quotes",
    "tdx_category_quotes",
    "tdx_auction_process",
    "tdx_kline",
    "tdx_capital_changes",
    "tdx_historical_intraday",
    "tdx_recent_historical_intraday",
    "tdx_today_intraday",
    "tdx_intraday_subchart",
    "tdx_today_trades",
    "tdx_historical_trades",
    "tdx_finance_info",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_wire_requests() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.wire_requests")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.wire_requests"}:
            return None
        raise


def _fallback_wire_requests() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_wire_requests()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_wire_requests()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
