"""Built-in source request execution option enrichers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

SourceExecutionEnricherFactory = Callable[[str | Path | None], Callable[[dict[str, Any]], None]]


def load_builtin_source_execution_enrichers() -> dict[str, SourceExecutionEnricherFactory]:
    """Return source-specific execution option enrichers for bundled providers."""

    enrichers: dict[str, SourceExecutionEnricherFactory] = {}
    for declarations in _source_execution_enricher_declarations():
        enrichers.update(declarations)
    return enrichers


def _source_execution_enricher_declarations() -> tuple[
    dict[str, SourceExecutionEnricherFactory],
    ...,
]:
    from .builtin_source_declarations import builtin_source_execution_enricher_declarations

    return builtin_source_execution_enricher_declarations()
