"""Compatibility wrapper for TDX normalization utilities."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "as_list",
    "get_value",
    "optional_int",
    "round_optional_float",
    "tenk_yuan",
    "tenk_to_unit",
    "tenk_shares_to_lots",
    "market_value",
    "auction_open_volume_hand",
    "open_volume_ratio",
    "limit_board_text",
    "bar_trade_date",
    "percent_change",
    "locked_amount",
    "average_price",
    "safe_ratio",
    "safe_ratio_pct",
    "drawdown_pct",
    "attack_pct",
    "optional_int_diff",
    "balance_pct",
    "volume_ratio_vs_previous_day",
    "volume_change",
    "volume_change_pct",
    "intraday_subchart_minute_time",
    "bytes_hex",
    "format_datetime",
    "format_time",
    "format_time_seconds",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_normalize_utils() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.normalize_utils")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.normalize_utils"}:
            return None
        raise


def _fallback_normalize_utils() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_normalize_utils()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_normalize_utils()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
