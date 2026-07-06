"""Compatibility wrapper for TDX server list configuration helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "LOCAL_TIMEZONE",
    "SERVER_KIND_VALUES",
    "DEFAULT_CACHE_DIR",
    "QUOTE_RESOURCE",
    "EXT_RESOURCE",
    "ServerKind",
    "TdxServerEntry",
    "TdxServerProbeResult",
    "default_server_cache_root",
    "data_root_server_cache_root",
    "built_in_servers",
    "effective_servers",
    "effective_host_strings",
    "read_user_servers",
    "write_user_servers",
    "reset_user_servers",
    "probe_server",
    "probe_servers",
    "server_status",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_tdx_server_config() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.tdx_server_config")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.tdx_server_config"}:
            return None
        raise


def _fallback_tdx_server_config() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_tdx_server_config()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_tdx_server_config()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
