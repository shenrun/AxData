"""Small worker pool for TDX extended market requests."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from typing import Any, TypeVar

from .options import normalize_tdx_ext_request_options, positive_tdx_ext_option_int
from .servers import TdxExtServer

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class TdxExtPoolConfig:
    """Resolved extended-market pool configuration."""

    source_server_count: int
    connections_per_server: int
    connection_count: int
    requested_connections_per_server: int
    servers: tuple[TdxExtServer, ...]


class TdxExtClientPool:
    """Run independent extended-market requests on independent clients."""

    def __init__(
        self,
        *,
        servers: Sequence[TdxExtServer],
        connections_per_server: int,
        connection_count: int | None = None,
        timeout: float = 6.0,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.servers = tuple(servers)
        self.connections_per_server = max(1, int(connections_per_server))
        self.timeout = timeout
        self.client_factory = client_factory or _tdx_ext_client_class()
        self._clients: list[Any] = []
        self._client_locks: list[Lock] = []
        target_connection_count = max(1, int(connection_count or (len(self.servers) * self.connections_per_server)))
        created = 0
        while created < target_connection_count:
            server = self.servers[created % len(self.servers)]
            self._clients.append(
                self.client_factory(
                    servers=(server,),
                    timeout=self.timeout,
                )
            )
            self._client_locks.append(Lock())
            created += 1

    @property
    def connection_count(self) -> int:
        return len(self._clients)

    def close(self) -> None:
        for client in self._clients:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> "TdxExtClientPool":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def map(self, items: Sequence[T], func: Callable[[Any, T], R]) -> list[R]:
        if not items:
            return []
        if self.connection_count <= 1 or len(items) <= 1:
            client = self._clients[0]
            return [func(client, item) for item in items]

        worker_count = min(self.connection_count, len(items))

        def run_one(index: int, item: T) -> tuple[int, R]:
            client_index = index % self.connection_count
            client = self._clients[client_index]
            with self._client_locks[client_index]:
                return index, func(client, item)

        results_by_index: dict[int, R] = {}
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-ext") as executor:
            futures = [executor.submit(run_one, index, item) for index, item in enumerate(items)]
            for future in as_completed(futures):
                index, result = future.result()
                results_by_index[index] = result
        return [results_by_index[index] for index in range(len(items))]


def _tdx_ext_client_class() -> Any:
    from .client import TdxExtClient

    return TdxExtClient


def _configured_extended_servers(*, cache_root: str | None = None) -> tuple[TdxExtServer, ...]:
    from .exceptions import ConnectionClosedError
    from .host_config import configured_extended_servers as configured

    return configured(cache_root=cache_root, unavailable_error=ConnectionClosedError)


def resolve_tdx_ext_pool_config(
    options: dict[str, Any],
    *,
    minimum_tasks: int,
) -> TdxExtPoolConfig | None:
    """Return a pool config only when options request useful parallelism."""

    if minimum_tasks <= 1:
        return None
    if not options:
        return None
    server_cache_root = options.get("server_cache_root")
    servers = _configured_extended_servers(cache_root=server_cache_root)
    source_server_count = positive_tdx_ext_option_int(
        options.get("source_server_count", 1),
        "source_server_count",
        maximum=64,
    )
    connections_per_server = positive_tdx_ext_option_int(
        options.get("connections_per_server", 1),
        "connections_per_server",
        maximum=64,
    )
    selected_servers = tuple(servers[: min(source_server_count, len(servers))])
    connection_count = min(len(selected_servers) * connections_per_server, 128)
    if connection_count <= 1:
        return None
    return TdxExtPoolConfig(
        source_server_count=len(selected_servers),
        connections_per_server=max(1, (connection_count + len(selected_servers) - 1) // len(selected_servers)),
        connection_count=connection_count,
        requested_connections_per_server=connections_per_server,
        servers=selected_servers,
    )


def flatten_results(results: Iterable[Sequence[R]]) -> list[R]:
    rows: list[R] = []
    for result in results:
        rows.extend(result)
    return rows
