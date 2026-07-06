"""Common source adapter execution option helpers."""

from __future__ import annotations

from collections.abc import Mapping


def timeout_seconds(options: Mapping[str, object] | None, *, default: float) -> float:
    """Return a timeout in seconds from common AxData execution options."""

    resolved_options = dict(options or {})
    if "timeout_ms" in resolved_options:
        return float(resolved_options["timeout_ms"]) / 1000.0
    if "timeout_seconds" in resolved_options:
        return float(resolved_options["timeout_seconds"])
    if "timeout" in resolved_options:
        return float(resolved_options["timeout"])
    return default
