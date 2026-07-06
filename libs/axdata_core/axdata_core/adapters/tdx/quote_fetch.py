"""Compatibility wrapper for TDX quote fetch helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "QuoteRowsResult",
    "QuoteRequestResult",
    "order_book_request_result",
    "explicit_quote_request_result",
    "refresh_quote_request_result",
    "quote_rows_meta",
    "order_book_rows",
    "explicit_quote_rows",
    "refresh_quote_rows",
    "request_realtime_refresh_rows",
    "request_legacy_quotes_parallel",
    "request_legacy_quote_batches_concurrent",
    "request_legacy_quotes_on_host",
    "request_legacy_quote_batches",
    "explicit_snapshot_rows_by_tdx_code",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_quote_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.quote_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.quote_fetch"}:
            return None
        raise


def _fallback_quote_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_quote_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_quote_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
