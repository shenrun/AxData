"""Compatibility wrapper for TDX execution helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "client_pool_size",
    "chunked",
    "tdx_client_meta",
    "finish_request_result",
    "apply_asset_type_meta",
    "emit_price_limit_progress",
    "emit_batch_progress",
    "emit_source_progress",
    "elapsed_monotonic_ms",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_execution_utils() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.execution_utils")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.execution_utils"}:
            return None
        raise


def _fallback_execution_utils() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_execution_utils()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_execution_utils()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
