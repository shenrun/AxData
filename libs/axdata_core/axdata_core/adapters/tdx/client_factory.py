"""Compatibility wrapper for TDX quote client factory helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from importlib import import_module
from types import ModuleType
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def create_tdx_client(
    *,
    hosts: Sequence[str] | None = None,
    pool_size: int | None = None,
    heartbeat_interval: float | None | object = Ellipsis,
) -> Any:
    """Create the built-in private TDX wire client."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.create_tdx_client(
            hosts=hosts,
            pool_size=pool_size,
            heartbeat_interval=heartbeat_interval,
        )
    return _fallback_create_tdx_client(
        hosts=hosts,
        pool_size=pool_size,
        heartbeat_interval=heartbeat_interval,
    )


def _fallback_create_tdx_client(
    *,
    hosts: Sequence[str] | None = None,
    pool_size: int | None = None,
    heartbeat_interval: float | None | object = Ellipsis,
) -> Any:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_tdx_client_class() -> Any:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def configured_tdx_hosts() -> list[str]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.configured_tdx_hosts()
    return _fallback_configured_tdx_hosts()


def _fallback_configured_tdx_hosts() -> list[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def configured_tdx_hosts_from_options(options: Mapping[str, Any]) -> list[str]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.configured_tdx_hosts_from_options(options)
    return _fallback_configured_tdx_hosts_from_options(options)


def _fallback_configured_tdx_hosts_from_options(options: Mapping[str, Any]) -> list[str]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def tdx_env_int(name: str, default: int, *, minimum: int) -> int:
    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_env_int(name, default, minimum=minimum)
    return _fallback_tdx_env_int(name, default, minimum=minimum)


def _fallback_tdx_env_int(name: str, default: int, *, minimum: int) -> int:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_client_factory() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.client_factory")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.client_factory"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_client_factory()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]
