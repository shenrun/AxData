"""Provider-owned host probe helpers."""

from __future__ import annotations

from dataclasses import dataclass

from ._connection_defaults import DEFAULT_PROBE_TIMEOUT, DEFAULT_PROBE_WORKERS
from ._host_utils import normalize_host, unique_hosts


@dataclass(frozen=True, slots=True)
class HostProbeResult:
    host: str
    ok: bool
    latency_ms: float | None = None
    error: str | None = None


def probe_host(host: str, *, timeout: float = DEFAULT_PROBE_TIMEOUT) -> HostProbeResult:
    """Measure whether a 7709 host accepts TCP connections."""

    normalized = normalize_host(host)
    if normalized is None:
        return HostProbeResult(host=str(host), ok=False, error="invalid host")

    import socket
    import time

    address, port_text = normalized.rsplit(":", 1)
    started = time.perf_counter()
    try:
        with socket.create_connection((address, int(port_text)), timeout=timeout):
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            return HostProbeResult(host=normalized, ok=True, latency_ms=latency_ms)
    except OSError as exc:
        return HostProbeResult(host=normalized, ok=False, error=type(exc).__name__)


def probe_hosts(
    hosts: list[str] | tuple[str, ...],
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT,
    max_workers: int = DEFAULT_PROBE_WORKERS,
) -> list[HostProbeResult]:
    """Probe many hosts concurrently."""

    candidates = unique_hosts(list(hosts))
    if not candidates:
        return []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    worker_count = min(max(1, int(max_workers)), len(candidates))
    results: list[HostProbeResult] = []
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata_source_tdx._tdx_wire-probe") as executor:
        futures = [executor.submit(probe_host, host, timeout=timeout) for host in candidates]
        for future in as_completed(futures):
            results.append(future.result())
    return results


def sort_hosts_by_latency(
    hosts: list[str] | tuple[str, ...],
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT,
    max_workers: int = DEFAULT_PROBE_WORKERS,
) -> list[str]:
    """Return reachable hosts first, ordered by TCP latency."""

    candidates = unique_hosts(list(hosts))
    results = probe_hosts(candidates, timeout=timeout, max_workers=max_workers)
    reachable = sorted(
        (result for result in results if result.ok),
        key=lambda result: (result.latency_ms if result.latency_ms is not None else float("inf"), candidates.index(result.host)),
    )
    reachable_hosts = {result.host for result in reachable}
    unreachable = [host for host in candidates if host not in reachable_hosts]
    return [result.host for result in reachable] + unreachable


__all__ = ["HostProbeResult", "probe_host", "probe_hosts", "sort_hosts_by_latency"]
