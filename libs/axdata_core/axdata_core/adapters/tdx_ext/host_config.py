"""TDX extended-market host configuration helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from axdata_core.source_errors import SourceUnavailableError

from .servers import TdxExtServer


def effective_servers(kind: str, *, cache_root: str | None = None) -> Sequence[Any]:
    from axdata_core import tdx_server_config

    return tdx_server_config.effective_servers(kind, cache_root=cache_root)


def configured_extended_servers(
    *,
    cache_root: str | None = None,
    effective_servers_func: Callable[..., Sequence[Any]] | None = None,
    unavailable_error: type[Exception] | Callable[[str], Exception] = SourceUnavailableError,
) -> tuple[TdxExtServer, ...]:
    """Return configured TDX extended-market servers as adapter server models."""

    server_resolver = effective_servers if effective_servers_func is None else effective_servers_func
    servers = server_resolver("extended", cache_root=cache_root)
    if not servers:
        raise unavailable_error("no TDX extended market servers are configured")
    return tuple(
        TdxExtServer(
            index=index,
            name=server.name,
            host=server.host,
            port=server.port,
            is_primary=index == 1,
        )
        for index, server in enumerate(servers, start=1)
    )
