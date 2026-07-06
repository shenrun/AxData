"""Compatibility wrapper for TDX request filter helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "requested_exchanges",
    "requested_boards",
    "requested_codes",
    "is_all_codes_value",
    "scope_meta_value",
    "requested_kline_codes",
    "requested_f10_codes",
    "requested_names",
    "string_values",
    "normalize_code_filter",
    "code_matches",
    "name_matches",
    "exchanges_for_boards",
    "board_matches",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_request_filters() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_filters")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_filters"}:
            return None
        raise


def _fallback_request_filters() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_filters()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_filters()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
