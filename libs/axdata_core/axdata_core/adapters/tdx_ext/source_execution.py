"""TDX extended source request execution option enrichers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def tdx_ext_execution_enricher(data_root: str | Path | None):
    """Return an enricher that injects TDX Ext internal execution options."""

    def enrich(options: dict[str, Any]) -> None:
        from .server_cache import tdx_ext_server_cache_root

        server_cache_root = tdx_ext_server_cache_root(data_root)
        if server_cache_root is not None:
            options.setdefault("server_cache_root", server_cache_root)

    return enrich
