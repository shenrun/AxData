"""Compatibility wrapper for TDX host configuration helpers."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from importlib import import_module
from types import ModuleType
from typing import Any


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def effective_host_strings(kind: str, *, cache_root: str | None = None) -> Sequence[str]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.effective_host_strings(kind, cache_root=cache_root)
    return _fallback_effective_host_strings(kind, cache_root=cache_root)


def _fallback_effective_host_strings(kind: str, *, cache_root: str | None = None) -> Sequence[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def env_hosts(env_name: str = "AXDATA_TDX_HOSTS") -> list[str] | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.env_hosts(env_name)
    return _fallback_env_hosts(env_name)


def _fallback_env_hosts(env_name: str = "AXDATA_TDX_HOSTS") -> list[str] | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def default_tdx_hosts() -> list[str]:
    """Return the built-in fallback quote hosts lazily."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.default_tdx_hosts()
    return _fallback_default_tdx_hosts()


def _fallback_default_tdx_hosts() -> list[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def configured_tdx_hosts_from_options(
    options: Mapping[str, Any],
    *,
    effective_host_strings_func: Callable[..., Sequence[str]] | None = None,
    default_hosts: Sequence[str] | None = None,
) -> list[str]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.configured_tdx_hosts_from_options(
            options,
            effective_host_strings_func=effective_host_strings_func,
            default_hosts=default_hosts,
        )
    return _fallback_configured_tdx_hosts_from_options(
        options,
        effective_host_strings_func=effective_host_strings_func,
        default_hosts=default_hosts,
    )


def _fallback_configured_tdx_hosts_from_options(
    options: Mapping[str, Any],
    *,
    effective_host_strings_func: Callable[..., Sequence[str]] | None = None,
    default_hosts: Sequence[str] | None = None,
) -> list[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def suspension_scan_hosts(hosts: Sequence[str], *, host_count: int) -> list[str]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.suspension_scan_hosts(hosts, host_count=host_count)
    return _fallback_suspension_scan_hosts(hosts, host_count=host_count)


def _fallback_suspension_scan_hosts(hosts: Sequence[str], *, host_count: int) -> list[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_host_config() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.host_config")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.host_config"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_host_config()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]
