"""Compatibility wrapper for TDX limit-ladder topic helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "attach_limit_ladder_themes",
    "limit_ladder_stock_summary_text",
    "limit_ladder_theme_is_noise",
    "limit_ladder_theme_rank_rows",
    "limit_ladder_theme_stats",
    "limit_ladder_theme_strength_score",
    "topic_missing_stock_count",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_limit_ladder_topics() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.limit_ladder_topics")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.limit_ladder_topics"}:
            return None
        raise


def _fallback_limit_ladder_topics() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_limit_ladder_topics()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_limit_ladder_topics()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
