"""Compatibility wrapper for TDX 7615 F10 request orchestration."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "f10_interface_specs",
    "_f10_interface_specs",
    "_parse_tqlex_tables",
    "request_f10_interface",
    "request_analyst_rating_rows",
    "request_f10_tables",
    "normalize_institution_holding_rows",
    "normalize_control_ranking_rows",
    "request_f10_interface_once",
    "attach_event_driver_details",
    "request_event_driver_detail",
    "request_f10_all_pages",
    "prepare_f10_params",
    "latest_f10_guarantee_period",
    "f10_private_placement_dates",
    "f10_business_composition_periods",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_f10_request() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.f10_request")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.f10_request"}:
            return None
        raise


def _fallback_f10_request() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_f10_request()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_f10_request()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
