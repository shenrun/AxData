"""Compatibility wrapper for TDX F10 parameter and context helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "analyst_target_stats",
    "control_ranking_item",
    "f10_unfiltered_page_params",
    "f10_business_period_candidates",
    "f10_business_period_value",
    "f10_context",
    "f10_function",
    "f10_dividend_metrics_function",
    "int_param",
    "bool_param",
    "normalize_optional_date_text",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_f10_params() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.f10_params")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.f10_params"}:
            return None
        raise


def _fallback_f10_params() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_f10_params()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_f10_params()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
