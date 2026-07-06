"""Execution helpers for TDX extended market source requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def chunked(values: Sequence[T], size: int) -> list[list[T]]:
    """Split a sequence into stable, non-empty chunks."""

    chunk_size = max(1, int(size))
    return [list(values[index : index + chunk_size]) for index in range(0, len(values), chunk_size)]


def request_quotes(
    code_list: Sequence[tuple[int, str]],
    *,
    options: Mapping[str, Any],
    root: str | None,
    server_cache_root: str | None,
    timeout: float,
    client_factory: Any,
    pool_tools: tuple[Any, Any, Any],
    client_pool: Any | None = None,
    client_pool_config: Any | None = None,
) -> tuple[tuple[Any, ...], Any | None, int | None]:
    """Fetch quote rows with the configured pool when useful."""

    TdxExtClientPool, flatten_results, resolve_tdx_ext_pool_config = pool_tools
    if client_pool is not None:
        connection_count = max(1, int(getattr(client_pool, "connection_count", 1)))
        quote_batches = chunked(
            code_list,
            max(1, (len(code_list) + connection_count - 1) // connection_count),
        )
        quotes = tuple(
            flatten_results(
                client_pool.map(
                    quote_batches,
                    lambda client, batch: client.get_quote_multi(batch),
                )
            )
        )
        return quotes, client_pool_config, len(quote_batches)

    pool_config = resolve_tdx_ext_pool_config(dict(options), minimum_tasks=len(code_list))
    if pool_config:
        quote_batches = chunked(
            code_list,
            max(1, (len(code_list) + pool_config.connection_count - 1) // pool_config.connection_count),
        )
        with TdxExtClientPool(
            servers=pool_config.servers,
            connections_per_server=pool_config.connections_per_server,
            connection_count=pool_config.connection_count,
            timeout=timeout,
            client_factory=client_factory,
        ) as pool:
            quotes = tuple(
                flatten_results(
                    pool.map(
                        quote_batches,
                        lambda client, batch: client.get_quote_multi(batch),
                    )
                )
            )
        return quotes, pool_config, len(quote_batches)

    with client_factory.from_config(
        tdx_root=root,
        server_cache_root=server_cache_root,
        timeout=timeout,
    ) as client:
        return tuple(client.get_quote_multi(code_list)), None, None


def request_items(
    items: Sequence[T],
    *,
    options: Mapping[str, Any],
    root: str | None,
    server_cache_root: str | None,
    timeout: float,
    client_factory: Any,
    pool_tools: tuple[Any, Any, Any],
    request_item: Callable[[Any, T], Sequence[R]],
    client_pool: Any | None = None,
    client_pool_config: Any | None = None,
) -> tuple[list[R], Any | None, int | None]:
    """Run independent item requests with pool/single-client fallback."""

    TdxExtClientPool, flatten_results, resolve_tdx_ext_pool_config = pool_tools
    if client_pool is not None:
        rows = flatten_results(client_pool.map(items, request_item))
        return rows, client_pool_config, len(items)

    pool_config = resolve_tdx_ext_pool_config(dict(options), minimum_tasks=len(items))
    if pool_config:
        with TdxExtClientPool(
            servers=pool_config.servers,
            connections_per_server=pool_config.connections_per_server,
            connection_count=pool_config.connection_count,
            timeout=timeout,
            client_factory=client_factory,
        ) as pool:
            rows = flatten_results(pool.map(items, request_item))
        return rows, pool_config, len(items)

    with client_factory.from_config(
        tdx_root=root,
        server_cache_root=server_cache_root,
        timeout=timeout,
    ) as client:
        return flatten_results([request_item(client, item) for item in items]), None, None
