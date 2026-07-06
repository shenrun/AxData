"""TDX data-root scoped cache helpers owned by the provider package."""

from __future__ import annotations

from pathlib import Path


def tdx_server_cache_root(data_root: str | Path | None) -> str | None:
    """Return the data-root scoped TDX server cache directory."""

    if data_root in (None, ""):
        return None
    return str(Path(data_root).expanduser().resolve() / "cache" / "tdx_servers")


def tdx_stats_cache_root(data_root: str | Path | None) -> str | None:
    """Return the data-root scoped TDX statistics resource cache directory."""

    if data_root in (None, ""):
        return None
    return str(Path(data_root).expanduser().resolve() / "cache" / "tdx" / "stats")
