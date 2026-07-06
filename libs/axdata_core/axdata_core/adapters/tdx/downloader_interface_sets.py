"""Compatibility wrapper for TDX downloader interface groups."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any

_EXPORTS = (
    "DOWNLOADER_PARALLEL_SUSPENSION_INTERFACES",
    "DOWNLOADER_STATS_RESOURCE_INTERFACES",
    "DOWNLOADER_F10_TOPIC_PREFILL_INTERFACES",
    "DOWNLOADER_RUNTIME_SOURCE_SERVER_MAX_INTERFACES",
)
__all__ = list(_EXPORTS)

def _provider_package_downloader_interface_sets() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.downloader_interface_sets")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.downloader_interface_sets"}:
            return None
        raise


def _fallback_value(name: str) -> frozenset[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


_IMPLEMENTATION: ModuleType | None = None
_IMPLEMENTATION_LOADED = False


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION, _IMPLEMENTATION_LOADED
    if not _IMPLEMENTATION_LOADED:
        _IMPLEMENTATION = _provider_package_downloader_interface_sets()
        _IMPLEMENTATION_LOADED = True
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    implementation = _implementation()
    value = getattr(implementation, name) if implementation is not None else _fallback_value(name)
    globals()[name] = value
    return value
