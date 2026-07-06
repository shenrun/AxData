"""Compatibility wrapper for TDX request-module private helper seams."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any


_IMPLEMENTATION: ModuleType | None = None


def _provider_package_request_seams() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_seams")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_seams"}:
            return None
        raise


def _fallback_request_seams() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_seams()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_seams()
    return _IMPLEMENTATION


def __getattr__(name: str) -> Any:
    implementation = _implementation()
    try:
        return getattr(implementation, name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
