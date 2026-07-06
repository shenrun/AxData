"""Compatibility wrapper for TDX finance normalization helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "lookup_finance_profile_maps",
    "normalize_capital_change_row",
    "normalize_finance_info_row",
    "finance_profile_maps_for_record",
    "finance_market_id",
    "finance_path_value",
    "capital_change_value",
    "capital_change_record_key",
    "requested_capital_change_categories",
    "capital_change_category_matches",
    "finance_records",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_finance_normalize() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.finance_normalize")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.finance_normalize"}:
            return None
        raise


def _fallback_finance_normalize() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_finance_normalize()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_finance_normalize()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
