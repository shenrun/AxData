"""Compatibility wrapper for TDX K-line result and metadata helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "KlineResultLike",
    "KlineParallelResultLike",
    "KlineRequestRowsResult",
    "stock_kline_request_result",
    "stock_kline_parallel_request_result",
    "index_like_kline_request_result",
    "sequential_kline_rows_and_meta",
    "flatten_kline_results",
    "kline_rows_and_meta",
    "kline_parallel_rows_and_meta",
    "kline_meta",
    "tdx_parallel_client_meta",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_kline_helpers() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.kline_helpers")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.kline_helpers"}:
            return None
        raise


def _fallback_kline_helpers() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_kline_helpers()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_kline_helpers()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
