"""Compatibility wrapper for legacy TDX request-module private exports."""

from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Any


__all__ = ["resolve_request_compat_export"]
_IMPLEMENTATION: ModuleType | None = None
_MISSING = object()
_SHARED_WRAPPER_EXPORTS: dict[str, tuple[str, str]] = {
    "DAILY_SHARE_FINANCE_BATCH_SIZE": (
        "axdata_core.adapters.tdx.interface_sets",
        "DAILY_SHARE_FINANCE_BATCH_SIZE",
    ),
    "FINANCE_INTERFACE_FIELDS": (
        "axdata_core.adapters.tdx.interface_sets",
        "FINANCE_INTERFACE_FIELDS",
    ),
    "INTRADAY_SUBCHART_INTERFACE_SPECS": (
        "axdata_core.adapters.tdx.interface_sets",
        "INTRADAY_SUBCHART_INTERFACE_SPECS",
    ),
    "SUPPORTED_INTERFACES": (
        "axdata_core.adapters.tdx.interface_sets",
        "SUPPORTED_INTERFACES",
    ),
    "TDX_EXACT_REQUEST_METHODS": (
        "axdata_core.adapters.tdx.request_dispatch",
        "TDX_EXACT_REQUEST_METHODS",
    ),
}


def _provider_package_request_compat() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_compat")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_compat"}:
            return None
        raise


def _fallback_request_compat() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_compat()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_compat()
    return _IMPLEMENTATION


def _loaded_wrapper_export(name: str) -> Any:
    target = _SHARED_WRAPPER_EXPORTS.get(name)
    if target is None:
        return _MISSING
    module = sys.modules.get(target[0])
    if module is None:
        return _MISSING
    return vars(module).get(target[1], _MISSING)


def _cache_loaded_wrapper_export(name: str, value: Any) -> None:
    target = _SHARED_WRAPPER_EXPORTS.get(name)
    if target is None:
        return
    module = sys.modules.get(target[0])
    if module is None:
        return
    vars(module).setdefault(target[1], value)


def resolve_request_compat_export(name: str, module_globals: dict[str, Any], module_name: str) -> Any:
    wrapper_value = _loaded_wrapper_export(name)
    if wrapper_value is not _MISSING:
        module_globals[name] = wrapper_value
        return wrapper_value

    value = _implementation().resolve_request_compat_export(name, module_globals, module_name)
    _cache_loaded_wrapper_export(name, value)
    return value
