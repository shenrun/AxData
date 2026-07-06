"""Compatibility wrapper for TDX F10 table post-processing helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "normalize_f10_row",
    "normalize_dividend_metrics_row",
    "normalize_dividend_metrics_summary_rows",
    "normalize_equity_financing_rows",
    "normalize_equity_financing_row",
    "normalize_private_placement_allocation_row",
    "normalize_northbound_holding_row",
    "northbound_record_channel_type",
    "equity_financing_event_type",
    "equity_rights_issue_plan",
    "convertible_bond_status",
    "normalize_f10_row_for_summary",
    "postprocess_f10_rows",
    "postprocess_concept_constituent_row",
    "postprocess_market_ranking_row",
    "topic_exposure_type",
    "valuation_metric_name",
    "filter_f10_rows",
    "filter_shareholder_change_direction",
    "filter_date_range",
    "year_in_range",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_f10_postprocess() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.f10_postprocess")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.f10_postprocess"}:
            return None
        raise


def _fallback_f10_postprocess() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_f10_postprocess()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_f10_postprocess()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
