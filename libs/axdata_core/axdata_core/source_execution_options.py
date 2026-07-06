"""Source request execution option enrichment."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

SourceExecutionEnricher = Callable[[dict[str, Any]], None]
SourceExecutionEnricherFactory = Callable[[str | Path | None], SourceExecutionEnricher]


def execution_options_for_source(
    options: Mapping[str, Any],
    *,
    data_root: str | Path | None = None,
    provider_id: str | None = None,
    source_code: str | None = None,
    enrichers: Mapping[str, SourceExecutionEnricherFactory] | None = None,
) -> dict[str, Any]:
    """Return internal execution options for one source request."""

    execution_options = dict(options)
    normalized_provider_id = str(provider_id or "").strip()
    normalized_source_code = str(source_code or "").strip()
    if not normalized_provider_id and not normalized_source_code:
        return execution_options
    resolved_enrichers = enrichers
    if resolved_enrichers is None:
        from .source_execution_registry import load_builtin_source_execution_enrichers

        resolved_enrichers = load_builtin_source_execution_enrichers()
    lookup_key = normalized_provider_id or normalized_source_code
    enricher_factory = resolved_enrichers.get(lookup_key)
    if enricher_factory is not None:
        enricher_factory(data_root)(execution_options)
    return execution_options
