"""Compatibility wrapper for TDX code and market normalization helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "EXCHANGE_TO_MARKET",
    "MARKET_TO_EXCHANGE",
    "MARKET_TO_SUFFIX",
    "SUFFIX_TO_MARKET",
    "MARKET_TO_ID",
    "tdx_code_to_instrument_id",
    "instrument_id_to_tdx_code",
    "exchange_to_market",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_codes() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.codes")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.codes"}:
            return None
        raise


def _fallback_codes() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_codes()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_codes()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
