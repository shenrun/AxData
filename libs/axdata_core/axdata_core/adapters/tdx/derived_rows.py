"""Compatibility wrapper for derived TDX request row builders."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "normalize_auction_indicator_row",
    "normalize_daily_share_row",
    "normalize_daily_price_limit_row",
    "normalize_daily_price_limit_snapshot_row",
    "normalize_daily_price_limit_from_pre_close",
    "normalize_limit_ladder_row",
    "daily_share_source",
    "limit_ladder_rank_page_below_threshold",
    "limit_ladder_candidate",
    "limit_ladder_needs_name_lookup",
    "numeric_at_or_above",
    "limit_ladder_public_row",
    "limit_ladder_trade_date",
    "stats_date_is_today",
    "limit_ladder_level",
    "today_limit_board_window",
    "limit_ladder_year_limit_up_days",
    "limit_ladder_topic_type",
    "limit_ladder_count_param",
    "normalize_order_book_rows",
    "normalize_adj_factor_row",
    "default_daily_price_limit_trade_date",
    "before_daily_close_buffer",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_derived_rows() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.derived_rows")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.derived_rows"}:
            return None
        raise


def _fallback_derived_rows() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_derived_rows()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_derived_rows()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
