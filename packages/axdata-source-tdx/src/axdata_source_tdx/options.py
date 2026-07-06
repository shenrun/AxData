"""TDX source request execution option parsing."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError

TDX_REQUEST_OPTION_KEYS = frozenset(
    {
        "connections_per_server",
        "f10_topic_refill_rounds",
        "f10_topic_refill_workers",
        "f10_topic_workers",
        "f10_workers",
        "hosts",
        "pool_size",
        "server_cache_root",
        "source_server_count",
        "stats_cache_root",
    }
)


def normalize_tdx_request_options(options: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize TDX execution options and reject unsupported keys."""

    normalized: dict[str, Any] = {}
    for key, value in dict(options or {}).items():
        if value is None:
            continue
        normalized[str(key)] = value
    unknown = sorted(set(normalized) - TDX_REQUEST_OPTION_KEYS)
    if unknown:
        raise SourceRequestValidationError(
            f"Unknown request option(s): {', '.join(unknown)}. "
            f"Known options: {', '.join(sorted(TDX_REQUEST_OPTION_KEYS))}."
        )
    return normalized


def stats_resource_params(
    params: Mapping[str, Any],
    options: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge internal stats resource options into public params."""

    resolved = dict(params)
    if "stats_cache_root" in options and "stats_cache_root" not in resolved:
        resolved["stats_cache_root"] = options["stats_cache_root"]
    return resolved


def tdx_request_option_f10_workers(options: Mapping[str, Any], item_count: int) -> int:
    """Return the worker count for direct F10 batch queries."""

    if "f10_workers" not in options:
        return 1
    return max(
        1,
        min(
            positive_option_int(options.get("f10_workers"), "f10_workers", maximum=32),
            int(item_count or 1),
        ),
    )


def tdx_request_option_f10_topic_workers(options: Mapping[str, Any]) -> int:
    """Return the first-pass worker count for F10 topic lookup."""

    if "f10_topic_workers" in options:
        return positive_option_int(options.get("f10_topic_workers"), "f10_topic_workers", maximum=32)
    return 6


def tdx_request_option_f10_topic_refill_workers(options: Mapping[str, Any]) -> int:
    """Return the worker count for F10 topic refill lookup."""

    if "f10_topic_refill_workers" in options:
        return positive_option_int(
            options.get("f10_topic_refill_workers"),
            "f10_topic_refill_workers",
            maximum=32,
        )
    return tdx_request_option_f10_topic_workers(options)


def tdx_request_option_f10_topic_refill_rounds(options: Mapping[str, Any]) -> int:
    """Return how many refill rounds to run for missing F10 topics."""

    if "f10_topic_refill_rounds" in options:
        return nonnegative_option_int(
            options.get("f10_topic_refill_rounds"),
            "f10_topic_refill_rounds",
            maximum=5,
        )
    return 1


def tdx_request_topic_worker_count(options: Mapping[str, Any], item_count: int) -> int:
    """Return a topic worker count capped by the number of requested items."""

    return max(1, min(tdx_request_option_f10_topic_workers(options), int(item_count or 1)))


def tdx_request_option_pool_size(options: Mapping[str, Any]) -> int | None:
    """Return the total TDX request pool size from execution options."""

    if "pool_size" in options:
        return positive_option_int(options["pool_size"], "pool_size", maximum=128)
    source_server_count = positive_option_int(options.get("source_server_count", 1), "source_server_count", maximum=64)
    connections_per_server = positive_option_int(
        options.get("connections_per_server", 1),
        "connections_per_server",
        maximum=64,
    )
    return max(1, min(source_server_count * connections_per_server, 128))


def tdx_request_option_connections_per_server(options: Mapping[str, Any]) -> int:
    """Return the per-server request connection count from execution options."""

    if "connections_per_server" not in options:
        if "pool_size" in options:
            return positive_option_int(options["pool_size"], "pool_size", maximum=128)
        return 1
    return positive_option_int(
        options.get("connections_per_server"),
        "connections_per_server",
        maximum=64,
    )


def tdx_request_option_hosts(
    options: Mapping[str, Any],
    *,
    configured_hosts: Callable[[Mapping[str, Any]], list[str]],
) -> list[str] | None:
    """Return explicit or configured TDX request hosts from execution options."""

    if "hosts" in options:
        hosts = string_values(options.get("hosts"))
        normalized = [str(host).strip() for host in hosts if str(host).strip()]
        return normalized or None
    if "source_server_count" not in options:
        return None
    source_server_count = positive_option_int(options.get("source_server_count"), "source_server_count", maximum=64)
    return configured_hosts(options)[:source_server_count]


def has_tdx_connection_options(options: Mapping[str, Any]) -> bool:
    """Return whether execution options explicitly configure TDX connections."""

    return any(key in options for key in ("hosts", "pool_size", "source_server_count", "connections_per_server"))


def string_values(value: Any) -> list[str]:
    """Return comma/list normalized string values."""

    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def positive_option_int(value: Any, name: str, *, maximum: int) -> int:
    """Parse a positive integer execution option."""

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError(f"{name} must be an integer.") from exc
    if number < 1:
        raise SourceRequestValidationError(f"{name} must be >= 1.")
    if number > maximum:
        raise SourceRequestValidationError(f"{name} must be <= {maximum}.")
    return number


def nonnegative_option_int(value: Any, name: str, *, maximum: int) -> int:
    """Parse a non-negative integer execution option."""

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError(f"{name} must be an integer.") from exc
    if number < 0:
        raise SourceRequestValidationError(f"{name} must be >= 0.")
    if number > maximum:
        raise SourceRequestValidationError(f"{name} must be <= {maximum}.")
    return number
