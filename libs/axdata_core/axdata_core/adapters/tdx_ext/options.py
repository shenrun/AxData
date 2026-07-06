"""Execution option helpers for TDX extended market requests."""

from __future__ import annotations

from typing import Any


def normalize_tdx_ext_request_options(options: dict[str, Any] | None) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in dict(options or {}).items():
        if value is None:
            continue
        normalized[str(key)] = value
    allowed = {"source_server_count", "connections_per_server", "server_cache_root"}
    unknown = sorted(set(normalized) - allowed)
    if unknown:
        from axdata_core.source_errors import SourceRequestValidationError

        raise SourceRequestValidationError(
            f"Unknown request option(s): {', '.join(unknown)}. Known options: {', '.join(sorted(allowed))}."
        )
    return normalized


def positive_tdx_ext_option_int(value: Any, name: str, *, maximum: int) -> int:
    from axdata_core.source_errors import SourceRequestValidationError

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError(f"{name} must be an integer.") from exc
    if number < 1:
        raise SourceRequestValidationError(f"{name} must be >= 1.")
    if number > maximum:
        raise SourceRequestValidationError(f"{name} must be <= {maximum}.")
    return number
