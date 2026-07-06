"""Request-module host compatibility helpers for the TDX provider."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


def _loaded_request_attr(name: str) -> Any | None:
    import sys

    request_module = sys.modules.get("axdata_core.adapters.tdx.request")
    if request_module is None:
        return None
    return request_module.__dict__.get(name)


def _loaded_request_callable(name: str, default: Callable[..., Any]) -> Callable[..., Any]:
    loaded = _loaded_request_attr(name)
    if loaded is None:
        return default
    if (
        getattr(loaded, "__module__", None) == getattr(default, "__module__", None)
        and getattr(loaded, "__name__", None) == getattr(default, "__name__", None)
    ):
        return default
    return loaded


def suspension_scan_hosts(
    *,
    configured_hosts: Callable[[], Sequence[str]],
    host_count: int,
    suspension_scan_hosts_func: Callable[..., list[str]] | None = None,
) -> list[str]:
    if suspension_scan_hosts_func is None:
        from .host_config import suspension_scan_hosts as suspension_scan_hosts_func

    return suspension_scan_hosts_func(configured_hosts(), host_count=host_count)


def env_hosts(env_name: str = "AXDATA_TDX_HOSTS") -> list[str] | None:
    from .host_config import env_hosts as current_env_hosts

    return current_env_hosts(env_name)


def configured_tdx_hosts(
    *,
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    return configured_hosts_from_options({})


def configured_tdx_hosts_from_options(
    options: Mapping[str, Any],
    *,
    effective_host_strings_func: Callable[..., Sequence[str]],
    configured_hosts_from_options_func: Callable[..., list[str]] | None = None,
) -> list[str]:
    if configured_hosts_from_options_func is None:
        from .host_config import configured_tdx_hosts_from_options as configured_hosts_from_options_func

    return configured_hosts_from_options_func(
        options,
        effective_host_strings_func=effective_host_strings_func,
    )


def effective_host_strings(kind: str, *, cache_root: str | None = None) -> Sequence[str]:
    from .host_config import effective_host_strings as current_effective_host_strings

    return current_effective_host_strings(kind, cache_root=cache_root)


def _suspension_scan_hosts() -> list[str]:
    from .request_limits import TDX_SUSPENSION_HOST_COUNT

    loaded_host_count = _loaded_request_attr("TDX_SUSPENSION_HOST_COUNT")
    return suspension_scan_hosts(
        configured_hosts=_loaded_request_callable("_configured_tdx_hosts", _configured_tdx_hosts),
        host_count=TDX_SUSPENSION_HOST_COUNT if loaded_host_count is None else loaded_host_count,
    )


def _env_hosts() -> list[str] | None:
    return env_hosts()


def _configured_tdx_hosts() -> list[str]:
    return configured_tdx_hosts(
        configured_hosts_from_options=_loaded_request_callable(
            "_configured_tdx_hosts_from_options",
            _configured_tdx_hosts_from_options,
        ),
    )


def _configured_tdx_hosts_from_options(options: Mapping[str, Any]) -> list[str]:
    return configured_tdx_hosts_from_options(
        options,
        effective_host_strings_func=_loaded_request_callable("effective_host_strings", effective_host_strings),
    )
