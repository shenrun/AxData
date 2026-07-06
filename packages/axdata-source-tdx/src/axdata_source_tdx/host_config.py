"""TDX host configuration helpers owned by the provider package."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from typing import Any


def effective_host_strings(kind: str, *, cache_root: str | None = None) -> Sequence[str]:
    from . import tdx_server_config

    return tdx_server_config.effective_host_strings(kind, cache_root=cache_root)


def env_hosts(env_name: str = "AXDATA_TDX_HOSTS") -> list[str] | None:
    raw = os.getenv(env_name, "")
    hosts = [host.strip() for host in raw.split(",") if host.strip()]
    return hosts or None


def default_tdx_hosts() -> list[str]:
    """Return the built-in fallback quote hosts lazily."""

    from .wire import default_tdx_hosts as current_default_tdx_hosts

    return current_default_tdx_hosts()


def configured_tdx_hosts_from_options(
    options: Mapping[str, Any],
    *,
    effective_host_strings_func: Callable[..., Sequence[str]] | None = None,
    default_hosts: Sequence[str] | None = None,
) -> list[str]:
    configured_env_hosts = env_hosts()
    if configured_env_hosts:
        return configured_env_hosts
    host_resolver = effective_host_strings if effective_host_strings_func is None else effective_host_strings_func
    try:
        hosts = host_resolver("quote", cache_root=options.get("server_cache_root"))
    except Exception:
        hosts = []
    if hosts:
        return list(hosts)
    fallback_hosts = default_tdx_hosts() if default_hosts is None else default_hosts
    return list(fallback_hosts)


def suspension_scan_hosts(hosts: Sequence[str], *, host_count: int) -> list[str]:
    return list(hosts[:host_count])
