"""Compatibility wrapper for TDX daily price-limit calendar helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "PriceLimitCalendarDates",
    "latest_daily_price_limit_calendar_dates",
    "latest_calendar_dates_from_source_request",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_price_limit_calendar() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.price_limit_calendar")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.price_limit_calendar"}:
            return None
        raise


def _fallback_price_limit_calendar() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_price_limit_calendar()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_price_limit_calendar()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
