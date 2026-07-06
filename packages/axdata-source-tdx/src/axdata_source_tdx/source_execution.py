"""TDX source request execution option enrichers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def tdx_execution_enricher(data_root: str | Path | None):
    """Return an enricher that injects TDX internal execution options."""

    def enrich(options: dict[str, Any]) -> None:
        from .server_cache import tdx_server_cache_root, tdx_stats_cache_root

        server_cache_root = tdx_server_cache_root(data_root)
        if server_cache_root is not None:
            options.setdefault("server_cache_root", server_cache_root)
        stats_cache_root = tdx_stats_cache_root(data_root)
        if stats_cache_root is not None:
            options.setdefault("stats_cache_root", stats_cache_root)

    return enrich
