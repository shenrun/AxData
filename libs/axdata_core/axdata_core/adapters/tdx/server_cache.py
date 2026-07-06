"""Compatibility wrapper for TDX data-root scoped cache helpers."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import ModuleType


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def tdx_server_cache_root(data_root: str | Path | None) -> str | None:
    """Return the data-root scoped TDX server cache directory."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_server_cache_root(data_root)
    return _fallback_tdx_server_cache_root(data_root)


def _fallback_tdx_server_cache_root(data_root: str | Path | None) -> str | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def tdx_stats_cache_root(data_root: str | Path | None) -> str | None:
    """Return the data-root scoped TDX statistics resource cache directory."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_stats_cache_root(data_root)
    return _fallback_tdx_stats_cache_root(data_root)


def _fallback_tdx_stats_cache_root(data_root: str | Path | None) -> str | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_server_cache() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.server_cache")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.server_cache"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_server_cache()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]
