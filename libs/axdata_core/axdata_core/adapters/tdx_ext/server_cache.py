"""TDX extended data-root scoped server cache helpers."""

from __future__ import annotations

from pathlib import Path


def tdx_ext_server_cache_root(data_root: str | Path | None) -> str | None:
    """Return the data-root scoped TDX extended server cache directory."""

    if data_root in (None, ""):
        return None
    return str(Path(data_root).expanduser().resolve() / "cache" / "tdx_servers")
