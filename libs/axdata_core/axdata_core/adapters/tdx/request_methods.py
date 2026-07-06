"""Compatibility wrapper for ordinary TDX request method glue."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any


_IMPLEMENTATION: ModuleType | None = None


def _provider_package_request_methods() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_methods")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_methods"}:
            return None
        raise


def _fallback_request_methods() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_methods()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_methods()
    return _IMPLEMENTATION


def __getattr__(name: str) -> Any:
    implementation = _implementation()
    try:
        return getattr(implementation, name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
