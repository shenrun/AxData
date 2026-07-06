"""TDX Ext source execution enricher declarations."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

SourceExecutionEnricherFactory = Callable[[str | Path | None], Callable[[dict[str, Any]], None]]

TDX_EXT_SOURCE_EXECUTION_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tdx_ext",
    "axdata.source.tdx_ext_external",
)


def tdx_ext_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return Provider ID keyed execution enrichers owned by TDX Ext."""

    return {
        provider_id: _tdx_ext_execution_enricher
        for provider_id in TDX_EXT_SOURCE_EXECUTION_PROVIDER_IDS
    }


def tdx_ext_legacy_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return legacy source-code execution enrichers owned by TDX Ext."""

    return {"tdx_ext": _tdx_ext_execution_enricher}


def tdx_ext_source_execution_enricher_declarations() -> dict[str, SourceExecutionEnricherFactory]:
    """Return all execution enricher declarations owned by TDX Ext."""

    enrichers = tdx_ext_source_execution_enrichers()
    enrichers.update(tdx_ext_legacy_source_execution_enrichers())
    return enrichers


def _tdx_ext_execution_enricher(data_root: str | Path | None) -> Callable[[dict[str, Any]], None]:
    from .source_execution import tdx_ext_execution_enricher

    return tdx_ext_execution_enricher(data_root)
