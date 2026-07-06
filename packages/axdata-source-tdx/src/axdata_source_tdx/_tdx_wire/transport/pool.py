"""Connection pool transport for the 7709 quote protocol."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import TYPE_CHECKING, Any

from axdata_source_tdx._tdx_wire._connection_defaults import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_PROBE_TIMEOUT,
    DEFAULT_PROBE_WORKERS,
)
from axdata_source_tdx._tdx_wire._host_utils import unique_hosts

if TYPE_CHECKING:
    from .socket import SocketTransport

_STDLIB_EXPORTS = {"itertools", "threading"}


class PooledSocketTransport:
    """Small round-robin pool of ``SocketTransport`` instances."""

    def __init__(
        self,
        hosts: Sequence[str] | None = None,
        *,
        timeout: float = 8.0,
        pool_size: int = 2,
        probe_hosts: bool = False,
        probe_timeout: float = DEFAULT_PROBE_TIMEOUT,
        probe_workers: int = DEFAULT_PROBE_WORKERS,
        heartbeat_interval: float | None = DEFAULT_HEARTBEAT_INTERVAL,
    ) -> None:
        resolved_hosts = _resolve_hosts(hosts)
        if not resolved_hosts:
            raise ValueError("at least one host is required")
        if probe_hosts and len(resolved_hosts) > 1:
            from axdata_source_tdx._tdx_wire._host_probe import sort_hosts_by_latency

            resolved_hosts = sort_hosts_by_latency(resolved_hosts, timeout=probe_timeout, max_workers=probe_workers)

        self._hosts = resolved_hosts
        self._timeout = timeout
        self._pool_size = max(1, int(pool_size))
        self._heartbeat_interval = heartbeat_interval
        self._transports: list[SocketTransport | None] = [None] * self._pool_size
        self._round_robin = _itertools_module().cycle(range(self._pool_size))
        self._round_robin_lock = _threading_module().Lock()

    @property
    def hosts(self) -> tuple[str, ...]:
        return tuple(self._hosts)

    @property
    def pool_size(self) -> int:
        return self._pool_size

    @property
    def heartbeat_interval(self) -> float | None:
        return self._heartbeat_interval

    @property
    def connected_hosts(self) -> tuple[str | None, ...]:
        return tuple(transport.connected_host if transport is not None else None for transport in self._transports)

    @property
    def connected_host(self) -> str | None:
        for transport in self._transports:
            if transport is not None and transport.connected_host is not None:
                return transport.connected_host
        return None

    def connect(self) -> None:
        for index in range(self._pool_size):
            self._transport_at(index).connect()

    def close(self) -> None:
        for transport in self._transports:
            if transport is not None:
                transport.close()

    def execute(self, command: int, payload: dict[str, Any] | None = None) -> Any:
        return self._pick_transport().execute(command, payload)

    def request(self, command: str) -> str:
        if command == "ping":
            return "pong"
        return self._pick_transport().request(command)

    def _pick_transport(self) -> SocketTransport:
        with self._round_robin_lock:
            index = next(self._round_robin)
        return self._transport_at(index)

    def _transport_at(self, index: int) -> SocketTransport:
        transport = self._transports[index]
        if transport is None:
            from .socket import SocketTransport

            transport = SocketTransport(
                hosts=_rotate_hosts(self._hosts, index),
                timeout=self._timeout,
                heartbeat_interval=self._heartbeat_interval,
            )
            self._transports[index] = transport
        return transport


def _rotate_hosts(hosts: list[str], offset: int) -> list[str]:
    if not hosts:
        return []
    index = offset % len(hosts)
    return hosts[index:] + hosts[:index]


def _resolve_hosts(hosts: Sequence[str] | None) -> list[str]:
    if hosts:
        return unique_hosts(list(hosts))

    from axdata_source_tdx._tdx_wire._host_resource import DEFAULT_HOSTS

    return unique_hosts(list(DEFAULT_HOSTS))


def _itertools_module():
    module = import_module("itertools")
    globals()["itertools"] = module
    return module


def _threading_module():
    module = import_module("threading")
    globals()["threading"] = module
    return module


def __getattr__(name: str) -> Any:
    if name == "itertools":
        return _itertools_module()
    if name == "threading":
        return _threading_module()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _STDLIB_EXPORTS)
