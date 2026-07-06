"""Compatibility wrapper for TDX intraday, trade, and auction fetch helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "PointRowsResult",
    "TradeRowsResult",
    "IntradayRequestResult",
    "auction_process_request_result",
    "intraday_subchart_request_result",
    "intraday_history_request_result",
    "intraday_recent_history_request_result",
    "intraday_today_request_result",
    "trade_today_request_result",
    "trade_history_request_result",
    "auction_result_today_request_result",
    "auction_result_history_request_result",
    "point_rows_meta",
    "trade_rows_meta",
    "auction_result_rows_meta",
    "request_auction_process_rows",
    "request_intraday_subchart_rows",
    "request_intraday_history_rows",
    "request_intraday_recent_history_rows",
    "request_intraday_today_rows",
    "request_trade_rows",
    "request_auction_result_rows",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_intraday_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.intraday_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.intraday_fetch"}:
            return None
        raise


def _fallback_intraday_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_intraday_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_intraday_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
