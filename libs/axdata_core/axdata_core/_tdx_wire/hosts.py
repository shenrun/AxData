"""Compatibility hosts helpers for ``axdata_core._tdx_wire.hosts``.

The provider-owned TDX wire stack is the primary implementation. This legacy
module keeps old host imports working while reading lightweight provider facts.
Core no longer contains a runnable TDX wire fallback.
"""

from __future__ import annotations

from importlib import import_module as _import_module
from types import ModuleType as _ModuleType

from axdata_core.tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE
from axdata_core.source_errors import SourceUnavailableError


_PROVIDER_STATIC_FACT_MODULES = (
    "axdata_source_tdx._tdx_wire._host_defaults",
    "axdata_source_tdx._tdx_wire._host_utils",
    "axdata_source_tdx._tdx_wire._connection_defaults",
)
_PROVIDER_RESOURCE_MODULE = "axdata_source_tdx._tdx_wire._host_resource"
_PROVIDER_PROBE_MODULE = "axdata_source_tdx._tdx_wire._host_probe"
_RUNTIME_EXPORTS = {"HostProbeResult", "probe_host", "probe_hosts", "sort_hosts_by_latency"}
_RESOURCE_EXPORTS = {"SERVER_FILE", "SERVER_RESOURCE_PACKAGE", "load_server_config", "load_server_hosts"}


def _load_fact_modules(module_names: tuple[str, str, str]) -> tuple[_ModuleType, _ModuleType, _ModuleType]:
    return tuple(_import_module(name) for name in module_names)  # type: ignore[return-value]


def _load_provider_facts() -> tuple[_ModuleType, _ModuleType, _ModuleType]:
    try:
        return _load_fact_modules(_PROVIDER_STATIC_FACT_MODULES)
    except ModuleNotFoundError as exc:
        missing_name = str(exc.name)
        if exc.name == "axdata_source_tdx" or missing_name.startswith("axdata_source_tdx."):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise


def _load_resource_module() -> _ModuleType:
    try:
        return _import_module(_PROVIDER_RESOURCE_MODULE)
    except ModuleNotFoundError as exc:
        missing_name = str(exc.name)
        if exc.name == "axdata_source_tdx" or missing_name.startswith("axdata_source_tdx."):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise


def _load_probe_module() -> _ModuleType:
    try:
        return _import_module(_PROVIDER_PROBE_MODULE)
    except ModuleNotFoundError as exc:
        missing_name = str(exc.name)
        if exc.name == "axdata_source_tdx" or missing_name.startswith("axdata_source_tdx."):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise


_HOST_DEFAULTS, _HOST_UTILS, _CONNECTION_DEFAULTS = _load_provider_facts()

DEFAULT_HOSTS = _HOST_DEFAULTS.DEFAULT_QUOTE_HOSTS
DEFAULT_PROBE_TIMEOUT = _CONNECTION_DEFAULTS.DEFAULT_PROBE_TIMEOUT
DEFAULT_PROBE_WORKERS = _CONNECTION_DEFAULTS.DEFAULT_PROBE_WORKERS
FALLBACK_HOSTS = _HOST_DEFAULTS.DEFAULT_QUOTE_HOSTS
normalize_host = _HOST_UTILS.normalize_host
unique_hosts = _HOST_UTILS.unique_hosts


def __getattr__(name: str):
    if name in _RESOURCE_EXPORTS:
        resource = _load_resource_module()
        value = getattr(resource, name)
        globals()[name] = value
        return value
    runtime = _load_probe_module()
    try:
        value = getattr(runtime, name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__) | _RESOURCE_EXPORTS | _RUNTIME_EXPORTS)


__all__ = [
    "DEFAULT_HOSTS",
    "DEFAULT_PROBE_TIMEOUT",
    "DEFAULT_PROBE_WORKERS",
    "FALLBACK_HOSTS",
    "HostProbeResult",
    "SERVER_FILE",
    "SERVER_RESOURCE_PACKAGE",
    "load_server_config",
    "load_server_hosts",
    "normalize_host",
    "probe_host",
    "probe_hosts",
    "sort_hosts_by_latency",
    "unique_hosts",
]
