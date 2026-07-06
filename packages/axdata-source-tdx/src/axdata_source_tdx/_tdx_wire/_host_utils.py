"""Provider-owned host normalization helpers."""

from __future__ import annotations

from typing import Any


def normalize_host(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    host = value.strip()
    if not host or ":" not in host:
        return None
    address, port = host.rsplit(":", 1)
    address = address.strip()
    port = port.strip()
    if not address or not port.isdigit():
        return None
    return f"{address}:{int(port)}"


def unique_hosts(values: list[Any] | tuple[Any, ...]) -> list[str]:
    hosts: list[str] = []
    for value in values:
        host = normalize_host(value)
        if host is not None and host not in hosts:
            hosts.append(host)
    return hosts


__all__ = ["normalize_host", "unique_hosts"]
