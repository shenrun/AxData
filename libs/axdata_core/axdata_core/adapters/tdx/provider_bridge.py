"""Compatibility wrapper for ordinary TDX Provider/legacy adapter bridge helpers."""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .request import TdxRequestAdapter


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def create_tdx_request_adapter(options: Mapping[str, object] | None = None) -> TdxRequestAdapter:
    """Create a TDX request adapter from Provider/legacy execution options."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.create_tdx_request_adapter(options)
    return _fallback_create_tdx_request_adapter(options)


def _fallback_create_tdx_request_adapter(
    options: Mapping[str, object] | None = None,
) -> TdxRequestAdapter:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def split_tdx_provider_options(
    options: Mapping[str, object] | None = None,
) -> tuple[Any | None, dict[str, object]]:
    """Return injected client and remaining TDX execution options."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.split_tdx_provider_options(options)
    return _fallback_split_tdx_provider_options(options)


def _fallback_split_tdx_provider_options(
    options: Mapping[str, object] | None = None,
) -> tuple[Any | None, dict[str, object]]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_bridge() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.provider_bridge")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.provider_bridge"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_bridge()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]
