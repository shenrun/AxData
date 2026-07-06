"""Compatibility wrapper for TDX plugin source adapter declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module
from types import ModuleType
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

TDX_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tdx",
)
_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def tdx_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_provider_adapter_factories()
    return {}


def tdx_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_legacy_source_adapter_factories()
    return {}


def tdx_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_source_adapter_factory_declarations()
    return tdx_provider_adapter_factories(), tdx_legacy_source_adapter_factories()


def _provider_package_source_adapter_registry() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.source_adapter_registry")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.source_adapter_registry"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_source_adapter_registry()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]


def _fallback_tdx_adapter(options: Mapping[str, object] | None) -> Any:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()
