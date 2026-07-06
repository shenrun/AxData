"""Compatibility wrapper for TDX realtime rank parameter rules."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "TDX_RANK_CATEGORY_ALIASES",
    "TDX_RANK_SORT_ALIASES",
    "TDX_RANK_FILTER_ALIASES",
    "rank_category_param",
    "rank_sort_param",
    "rank_filter_param",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_rank_params() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.rank_params")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.rank_params"}:
            return None
        raise


def _fallback_rank_params() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_rank_params()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_rank_params()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
