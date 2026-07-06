"""Compatibility wrapper for TDX request client helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "configured_hosts",
    "request_hosts",
    "create_request_client",
    "should_parallelize_stock_code_request",
    "stock_code_request_pool_size",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_request_client() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_client")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_client"}:
            return None
        raise


def _fallback_request_client() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_client()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_client()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
