"""TDX quote client factory owned by the provider package."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError


def create_tdx_client(
    *,
    hosts: Sequence[str] | None = None,
    pool_size: int | None = None,
    heartbeat_interval: float | None | object = Ellipsis,
) -> Any:
    """Create the built-in private TDX wire client."""

    from .wire import tdx_client_class

    resolved_hosts = list(hosts) if hosts is not None else configured_tdx_hosts()
    timeout = float(os.getenv("AXDATA_TDX_TIMEOUT", "8.0"))
    resolved_pool_size = int(pool_size if pool_size is not None else os.getenv("AXDATA_TDX_POOL_SIZE", "1"))
    probe_hosts = os.getenv("AXDATA_TDX_PROBE_HOSTS", "").strip().lower() in {"1", "true", "yes"}
    heartbeat_raw = os.getenv("AXDATA_TDX_HEARTBEAT_INTERVAL", "0")
    resolved_heartbeat_interval = (
        None if heartbeat_raw.strip().lower() in {"", "none", "0"} else float(heartbeat_raw)
    )
    if heartbeat_interval is not Ellipsis:
        resolved_heartbeat_interval = heartbeat_interval  # type: ignore[assignment]
    return tdx_client_class().from_hosts(
        hosts=resolved_hosts,
        timeout=timeout,
        pool_size=resolved_pool_size,
        probe_hosts=probe_hosts,
        heartbeat_interval=resolved_heartbeat_interval,
    )


def configured_tdx_hosts() -> list[str]:
    return configured_tdx_hosts_from_options({})


def configured_tdx_hosts_from_options(options: Mapping[str, Any]) -> list[str]:
    from .host_config import configured_tdx_hosts_from_options as configured

    return configured(options)


def tdx_env_int(name: str, default: int, *, minimum: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SourceRequestValidationError(f"{name} must be an integer") from exc
    if value < minimum:
        raise SourceRequestValidationError(f"{name} must be >= {minimum}")
    return value
