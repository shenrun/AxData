"""Compatibility wrapper for TDX quote snapshot normalization helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any

_EXPORTS = (
    "DEFAULT_PRICE_DECIMAL",
    "INDEX_SNAPSHOT_FIELDS",
    "tdx_codes",
    "tdx_codes_all",
    "price_decimal",
    "quote_tdx_code",
    "quote_level_at",
    "normalize_realtime_snapshot_row",
    "normalize_index_snapshot_row",
    "rescale_price",
    "as_list",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_snapshot_normalize() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.snapshot_normalize")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.snapshot_normalize"}:
            return None
        raise


def _fallback_snapshot_normalize() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_snapshot_normalize()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_snapshot_normalize()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
