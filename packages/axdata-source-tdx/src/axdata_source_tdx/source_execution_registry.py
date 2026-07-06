"""TDX source execution enricher declarations owned by the provider package."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

SourceExecutionEnricherFactory = Callable[[str | Path | None], Callable[[dict[str, Any]], None]]

TDX_SOURCE_EXECUTION_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tdx",
    "axdata.source.tdx_external",
)


def tdx_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return Provider ID keyed execution enrichers owned by TDX."""

    return {
        provider_id: _tdx_execution_enricher
        for provider_id in TDX_SOURCE_EXECUTION_PROVIDER_IDS
    }


def tdx_legacy_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return legacy source-code execution enrichers owned by TDX."""

    return {"tdx": _tdx_execution_enricher}


def tdx_source_execution_enricher_declarations() -> dict[str, SourceExecutionEnricherFactory]:
    """Return all execution enricher declarations owned by TDX."""

    enrichers = tdx_source_execution_enrichers()
    enrichers.update(tdx_legacy_source_execution_enrichers())
    return enrichers


def _tdx_execution_enricher(data_root: str | Path | None) -> Callable[[dict[str, Any]], None]:
    from .source_execution import tdx_execution_enricher

    return tdx_execution_enricher(data_root)
