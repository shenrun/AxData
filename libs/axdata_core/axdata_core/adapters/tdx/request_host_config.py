"""Compatibility wrapper for TDX request-module host helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from importlib import import_module
from types import ModuleType
from typing import Any


_IMPLEMENTATION: ModuleType | None = None


def suspension_scan_hosts(
    *,
    configured_hosts: Callable[[], Sequence[str]],
    host_count: int,
    suspension_scan_hosts_func: Callable[..., list[str]] | None = None,
) -> list[str]:
    loaded = _loaded_request_override("_suspension_scan_hosts")
    if loaded is not None and suspension_scan_hosts_func is None:
        return list(loaded())
    return _implementation().suspension_scan_hosts(
        configured_hosts=configured_hosts,
        host_count=host_count,
        suspension_scan_hosts_func=suspension_scan_hosts_func,
    )


def env_hosts(env_name: str = "AXDATA_TDX_HOSTS") -> list[str] | None:
    loaded = _loaded_request_override("_env_hosts")
    if loaded is not None and env_name == "AXDATA_TDX_HOSTS":
        return loaded()
    return _implementation().env_hosts(env_name)


def configured_tdx_hosts(
    *,
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    loaded = _loaded_request_override("_configured_tdx_hosts")
    if loaded is not None:
        return list(loaded())
    return _implementation().configured_tdx_hosts(
        configured_hosts_from_options=configured_hosts_from_options,
    )


def configured_tdx_hosts_from_options(
    options: Mapping[str, Any],
    *,
    effective_host_strings_func: Callable[..., Sequence[str]],
    configured_hosts_from_options_func: Callable[..., list[str]] | None = None,
) -> list[str]:
    loaded = _loaded_request_override("_configured_tdx_hosts_from_options")
    if loaded is not None and configured_hosts_from_options_func is None:
        return list(loaded(options))
    return _implementation().configured_tdx_hosts_from_options(
        options,
        effective_host_strings_func=effective_host_strings_func,
        configured_hosts_from_options_func=configured_hosts_from_options_func,
    )


def effective_host_strings(kind: str, *, cache_root: str | None = None) -> Sequence[str]:
    loaded = _loaded_request_override("effective_host_strings")
    if loaded is not None:
        return loaded(kind, cache_root=cache_root)
    return _implementation().effective_host_strings(kind, cache_root=cache_root)


def _loaded_request_attr(name: str) -> Any | None:
    import sys

    request_module = sys.modules.get("axdata_core.adapters.tdx.request")
    if request_module is None:
        return None
    return getattr(request_module, name, None)


def _loaded_request_override(name: str) -> Any | None:
    loaded = _loaded_request_attr(name)
    if loaded is None:
        return None
    if getattr(loaded, "__module__", None) == "axdata_core.adapters.tdx.request" and getattr(loaded, "__name__", None) == name:
        return None
    return loaded


def _provider_package_request_host_config() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.request_host_config")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.request_host_config"}:
            return None
        raise


def _fallback_request_host_config() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_request_host_config()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_request_host_config()
    return _IMPLEMENTATION
