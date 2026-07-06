"""Compatibility wrapper for TDX price-limit and limit-up status helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "price_limit_ratio_from_rule",
    "price_limit_rule",
    "price_limit_name_flag",
    "st_type_from_name",
    "price_limit_ratio",
    "rule_price_limits",
    "special_limit_ratio",
    "round_price",
    "positive_number",
    "price_close",
    "price_at_or_above",
    "limit_ladder_status",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_price_limits() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.price_limits")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.price_limits"}:
            return None
        raise


def _fallback_price_limits() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_price_limits()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_price_limits()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
