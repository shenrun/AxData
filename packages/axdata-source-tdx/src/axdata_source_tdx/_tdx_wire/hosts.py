"""Default 7709 quote server hosts."""

from __future__ import annotations

from importlib import import_module

from ._connection_defaults import DEFAULT_PROBE_TIMEOUT, DEFAULT_PROBE_WORKERS
from ._host_defaults import DEFAULT_QUOTE_HOSTS
from ._host_probe import HostProbeResult, probe_host, probe_hosts, sort_hosts_by_latency
from ._host_utils import normalize_host, unique_hosts


_RESOURCE_MODULE = "axdata_source_tdx._tdx_wire._host_resource"
_RESOURCE_EXPORTS = {"DEFAULT_HOSTS", "SERVER_FILE", "SERVER_RESOURCE_PACKAGE", "load_server_config", "load_server_hosts"}
FALLBACK_HOSTS: tuple[str, ...] = DEFAULT_QUOTE_HOSTS


def __getattr__(name: str):
    if name in _RESOURCE_EXPORTS:
        value = getattr(import_module(_RESOURCE_MODULE), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _RESOURCE_EXPORTS)
