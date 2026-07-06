"""Compatibility wrapper for TDX adjustment-factor fetch helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "AdjustmentFactorRowsResult",
    "AdjustmentFactorRequestResult",
    "adjustment_factor_request_result",
    "adjustment_factor_meta",
    "adjustment_factor_rows",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_adjustment_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.adjustment_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.adjustment_fetch"}:
            return None
        raise


def _fallback_adjustment_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_adjustment_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_adjustment_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
