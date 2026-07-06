"""Compatibility wrapper for TDX K-line and trade pagination helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "KlineParallelOptions",
    "KlineRequestResult",
    "KlineHostResult",
    "KlineParallelResult",
    "kline_parallel_options",
    "request_trade_series_history",
    "request_kline_series_history",
    "request_kline_code_history",
    "request_recent_daily_bars",
    "request_kline_codes_on_host",
    "request_kline_codes_parallel",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_series_history() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.series_history")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.series_history"}:
            return None
        raise


def _fallback_series_history() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_series_history()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_series_history()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
