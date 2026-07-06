"""Compatibility wrapper for TDX F10 batch execution helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "F10DispatchResult",
    "TopicRowsLookupResult",
    "request_f10_dispatch_result",
    "stock_f10_request_result",
    "default_stock_f10_request_result",
    "request_f10_many_with_default_interface",
    "request_f10_rows",
    "request_f10_many_by_code",
    "request_topic_rows_with_refill",
    "request_topic_rows_by_instrument_id",
    "request_topic_rows_lookup_result",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_f10_executor() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.f10_executor")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.f10_executor"}:
            return None
        raise


def _fallback_f10_executor() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_f10_executor()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_f10_executor()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
