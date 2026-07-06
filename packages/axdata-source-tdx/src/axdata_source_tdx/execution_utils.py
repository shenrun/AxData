"""Execution helpers shared by the TDX request adapter."""

from __future__ import annotations

from collections.abc import Sequence
from time import monotonic
from typing import Any, Callable


def client_pool_size(client: Any) -> int:
    transport = getattr(client, "transport", None)
    value = getattr(transport, "pool_size", getattr(client, "pool_size", 1))
    try:
        return max(1, int(value or 1))
    except (TypeError, ValueError):
        return 1


def chunked(values: Sequence[Any], size: int) -> list[list[Any]]:
    size = max(1, int(size))
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def tdx_client_meta(client: Any) -> dict[str, Any]:
    transport = getattr(client, "transport", None)
    hosts = tuple(getattr(transport, "hosts", None) or getattr(client, "hosts", None) or ())
    connected_hosts = getattr(transport, "connected_hosts", None)
    connected_host = getattr(transport, "connected_host", None)
    pool_size = getattr(transport, "pool_size", getattr(client, "pool_size", None))
    heartbeat_interval = getattr(
        transport,
        "heartbeat_interval",
        getattr(client, "heartbeat_interval", None),
    )
    return {
        "tdx_connected_host": connected_host,
        "tdx_connected_hosts": tuple(connected_hosts) if connected_hosts is not None else None,
        "tdx_configured_host_count": len(hosts),
        "tdx_configured_hosts_sample": hosts[:5],
        "tdx_pool_size": pool_size,
        "tdx_heartbeat_interval": heartbeat_interval,
    }


def finish_request_result(
    *,
    client: Any,
    result: Any,
    client_meta: Callable[[Any], dict[str, Any]] = tdx_client_meta,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return result.rows, {
        **client_meta(client),
        **result.meta,
    }


def apply_asset_type_meta(
    rows: list[dict[str, Any]],
    meta: dict[str, Any],
    *,
    asset_type: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return rows, {
        **meta,
        "tdx_asset_type": asset_type,
    }


def emit_price_limit_progress(
    progress_callback: Callable[..., None] | None,
    *,
    completed: int,
    total: int,
    started_at: float,
) -> None:
    if total <= 0:
        return
    fraction = min(1.0, max(0.0, completed / total))
    percent = 20 + int(fraction * 48)
    elapsed_ms = max(0.0, (monotonic() - started_at) * 1000)
    eta_ms = None
    if completed > 0 and completed < total:
        eta_ms = int((elapsed_ms / completed) * (total - completed))
    emit_source_progress(
        progress_callback,
        percent,
        f"计算涨跌停价格 {completed}/{total} 只",
        progress_current=completed,
        progress_total=total,
        progress_unit="只",
        eta_ms=eta_ms,
    )


def emit_batch_progress(
    progress_callback: Callable[..., None] | None,
    *,
    completed: int,
    total: int,
    unit: str,
    started_at: float,
    percent_start: int,
    percent_span: int,
    label: str,
) -> None:
    if total <= 0:
        return
    safe_completed = min(total, max(0, completed))
    fraction = min(1.0, max(0.0, safe_completed / total))
    percent = percent_start + int(fraction * percent_span)
    elapsed_ms = max(0.0, (monotonic() - started_at) * 1000)
    eta_ms = None
    if safe_completed > 0 and safe_completed < total:
        eta_ms = int((elapsed_ms / safe_completed) * (total - safe_completed))
    emit_source_progress(
        progress_callback,
        percent,
        f"{label} {safe_completed}/{total} {unit}",
        progress_current=safe_completed,
        progress_total=total,
        progress_unit=unit,
        eta_ms=eta_ms,
    )


def emit_source_progress(
    progress_callback: Callable[..., None] | None,
    percent: int,
    message: str,
    **details: Any,
) -> None:
    if progress_callback is None:
        return
    try:
        progress_callback(percent, message, **details)
    except TypeError:
        progress_callback(percent, message)


def elapsed_monotonic_ms(started_at: float) -> int:
    return max(0, int((monotonic() - started_at) * 1000))
