"""Provider-owned TDX connection defaults kept outside transport runtimes."""

from __future__ import annotations

DEFAULT_PROBE_TIMEOUT = 1.2
DEFAULT_PROBE_WORKERS = 32
DEFAULT_HEARTBEAT_INTERVAL: float | None = None

__all__ = [
    "DEFAULT_HEARTBEAT_INTERVAL",
    "DEFAULT_PROBE_TIMEOUT",
    "DEFAULT_PROBE_WORKERS",
]
