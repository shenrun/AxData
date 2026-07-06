"""Compatibility wrapper for TDX adjustment-factor helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "AdjustmentFactor",
    "build_adjustment_factors",
    "apply_xdxr_to_last_close",
    "selected_factor_value",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_adjustment() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.adjustment")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.adjustment"}:
            return None
        raise


def _fallback_adjustment() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_adjustment()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_adjustment()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
