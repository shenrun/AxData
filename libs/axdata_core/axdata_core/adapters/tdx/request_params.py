"""Compatibility wrapper for TDX source request parameter helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "KLINE_INTERFACE_SPECS",
    "INDEX_KLINE_INTERFACE",
    "INDEX_KLINE_PERIODS",
    "TDX_KLINE_MAX_COUNT",
    "bool_param",
    "int_param",
    "adjust_param",
    "adj_factor_adjust_param",
    "anchor_date_param",
    "validate_kline_anchor_date",
    "normalize_adj_factor_anchor_date",
    "trade_date_param",
    "normalize_optional_date_text",
    "kline_page_size",
    "kline_period",
    "index_kline_period",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_request_params() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_params")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_params"}:
            return None
        raise


def _fallback_request_params() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_params()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_params()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
