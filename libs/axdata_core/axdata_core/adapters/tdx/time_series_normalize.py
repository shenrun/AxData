"""Compatibility wrapper for TDX K-line, intraday, trade, and auction helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "kline_row_sort_key",
    "trade_row_sort_key",
    "auction_result_row_sort_key",
    "normalize_index_kline_row",
    "normalize_stock_kline_row",
    "normalize_kline_row",
    "normalize_intraday_history_row",
    "normalize_intraday_recent_history_row",
    "normalize_intraday_today_row",
    "normalize_intraday_subchart_row",
    "normalize_auction_process_row",
    "price_from_raw",
    "avg_price_from_raw",
    "normalize_trade_row",
    "is_opening_auction_result_trade",
    "normalize_auction_result_row",
    "auction_result_amount",
    "kline_bars",
    "intraday_points",
    "subchart_points",
    "trade_records",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_time_series_normalize() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.time_series_normalize")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.time_series_normalize"}:
            return None
        raise


def _fallback_time_series_normalize() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_time_series_normalize()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_time_series_normalize()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
