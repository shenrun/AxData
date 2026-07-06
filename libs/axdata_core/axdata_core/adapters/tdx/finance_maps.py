"""Compatibility wrapper for local TDX finance code-table mappings."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "TdxFinanceLocalMaps",
    "empty_finance_local_maps",
    "load_finance_local_maps",
    "load_finance_local_maps_from_root",
    "parse_incon_dict",
    "parse_region_map",
    "parse_security_industry_map",
    "lookup_finance_profile_maps",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_finance_maps() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.finance_maps")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.finance_maps"}:
            return None
        raise


def _fallback_finance_maps() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_finance_maps()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_finance_maps()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
