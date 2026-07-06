"""Compatibility wrapper for TDX stock code table scan helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "StockCodeScanResult",
    "StockCodePoolResult",
    "CodeRowsResult",
    "index_codes_result",
    "index_codes_request_result",
    "etf_codes_result",
    "etf_codes_request_result",
    "stock_rows_to_tdx_code_pool",
    "stock_code_pool_from_params",
    "should_parallelize_stock_code_request",
    "stock_code_request_pool_size",
    "stock_codes_request_result",
    "request_stock_codes",
    "request_stock_codes_exchange",
    "request_index_codes",
    "request_etf_codes",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_code_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.code_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.code_fetch"}:
            return None
        raise


def _fallback_code_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_code_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_code_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
