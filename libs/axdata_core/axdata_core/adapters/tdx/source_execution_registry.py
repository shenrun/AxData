"""Compatibility wrapper for TDX plugin source execution declarations."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

SourceExecutionEnricherFactory = Callable[[str | Path | None], Callable[[dict[str, Any]], None]]

TDX_SOURCE_EXECUTION_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tdx",
    "axdata.source.tdx_external",
)
_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def tdx_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return Provider ID keyed execution enrichers owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_source_execution_enrichers()
    return {}


def tdx_legacy_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return legacy source-code execution enrichers owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_legacy_source_execution_enrichers()
    return {}


def tdx_source_execution_enricher_declarations() -> dict[str, SourceExecutionEnricherFactory]:
    """Return all execution enricher declarations owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_source_execution_enricher_declarations()
    enrichers = tdx_source_execution_enrichers()
    enrichers.update(tdx_legacy_source_execution_enrichers())
    return enrichers


def _provider_package_source_execution_registry() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.source_execution_registry")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.source_execution_registry"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_source_execution_registry()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]


def _fallback_tdx_execution_enricher(data_root: str | Path | None) -> Callable[[dict[str, Any]], None]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()
