"""Compatibility wrapper for TDX F10 value normalization helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "f10_first_text",
    "f10_first_value",
    "f10_identifier_text",
    "f10_market_from_market_code",
    "scale_f10_hundred",
    "f10_field_value",
    "f10_source_value",
    "normalize_f10_value",
    "normalize_f10_plain_text",
    "is_empty_f10_value",
    "f10_date_text",
    "f10_number",
    "f10_page",
    "f10_rating_code",
    "date_dash",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_f10_normalize() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.f10_normalize")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.f10_normalize"}:
            return None
        raise


def _fallback_f10_normalize() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_f10_normalize()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_f10_normalize()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
