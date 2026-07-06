"""Compatibility wrapper for TDX source request option helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "TDX_REQUEST_OPTION_KEYS",
    "normalize_tdx_request_options",
    "stats_resource_params",
    "tdx_request_option_f10_workers",
    "tdx_request_option_f10_topic_workers",
    "tdx_request_option_f10_topic_refill_workers",
    "tdx_request_option_f10_topic_refill_rounds",
    "tdx_request_topic_worker_count",
    "tdx_request_option_pool_size",
    "tdx_request_option_connections_per_server",
    "tdx_request_option_hosts",
    "has_tdx_connection_options",
    "string_values",
    "positive_option_int",
    "nonnegative_option_int",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_options() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.options")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.options"}:
            return None
        raise


def _fallback_options() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_options()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_options()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
