"""TDX server list configuration and latency helpers."""

from __future__ import annotations

import json
import os
import socket
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Literal


LOCAL_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
SERVER_KIND_VALUES = {"quote", "extended"}
DEFAULT_CACHE_DIR = Path("data") / "cache" / "tdx_servers"
QUOTE_RESOURCE = "tdx_quote_servers.json"
EXT_RESOURCE = "tdx_extended_servers.json"

ServerKind = Literal["quote", "extended"]


@dataclass(frozen=True, slots=True)
class TdxServerEntry:
    """Clean server row used by both built-in defaults and user overrides."""

    name: str
    host: str
    port: int
    enabled: bool = True
    priority: int = 0
    latency_ms: float | None = None
    last_checked_at: str | None = None
    last_error: str | None = None

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "enabled": self.enabled,
            "priority": self.priority,
            "latency_ms": self.latency_ms,
            "last_checked_at": self.last_checked_at,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, priority: int = 0) -> "TdxServerEntry":
        host = str(data.get("host") or "").strip()
        port_raw = data.get("port")
        if not host or port_raw in (None, ""):
            address = str(data.get("address") or "").strip()
            if ":" not in address:
                raise ValueError("server host and port are required")
            host, port_text = address.rsplit(":", 1)
            port_raw = port_text
        port = int(port_raw)
        if not host or not 0 < port <= 65535:
            raise ValueError("server host and port are invalid")
        return cls(
            name=str(data.get("name") or host).strip(),
            host=host,
            port=port,
            enabled=bool(data.get("enabled", True)),
            priority=int(data.get("priority", priority)),
            latency_ms=_optional_float(data.get("latency_ms")),
            last_checked_at=_optional_text(data.get("last_checked_at")),
            last_error=_optional_text(data.get("last_error")),
        )


@dataclass(frozen=True, slots=True)
class TdxServerProbeResult:
    host: str
    port: int
    ok: bool
    latency_ms: float | None = None
    error: str | None = None

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "address": self.address,
            "ok": self.ok,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


def default_server_cache_root() -> Path:
    raw = os.getenv("AXDATA_TDX_SERVER_CACHE_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    data_root = os.getenv("AXDATA_DATA_DIR", "").strip()
    if data_root:
        return (Path(data_root).expanduser().resolve() / "cache" / "tdx_servers")
    return (Path.cwd() / DEFAULT_CACHE_DIR).resolve()


def data_root_server_cache_root(data_root: str | Path | None) -> Path | None:
    """Return the TDX server cache root under an explicit AxData data root."""

    if data_root in (None, ""):
        return None
    return Path(data_root).expanduser().resolve() / "cache" / "tdx_servers"


def built_in_servers(kind: ServerKind) -> tuple[TdxServerEntry, ...]:
    resource_name = _resource_name(kind)
    try:
        payload = resources.files("axdata_source_tdx.resources").joinpath(resource_name).read_text(encoding="utf-8")
        data = json.loads(payload)
    except (FileNotFoundError, ModuleNotFoundError, json.JSONDecodeError, OSError):
        data = {}
    rows = data.get("servers") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        rows = []
    servers = _normalize_server_entries(rows)
    if servers:
        return servers
    if kind == "quote":
        from .wire import fallback_tdx_hosts

        return tuple(
            TdxServerEntry(
                name=f"普通行情{index}",
                host=address.rsplit(":", 1)[0],
                port=int(address.rsplit(":", 1)[1]),
                priority=index,
            )
            for index, address in enumerate(fallback_tdx_hosts(), start=1)
        )
    return ()


def effective_servers(
    kind: ServerKind,
    *,
    cache_root: str | Path | None = None,
    include_disabled: bool = False,
) -> tuple[TdxServerEntry, ...]:
    env_hosts = _env_server_entries(kind)
    if env_hosts:
        servers = env_hosts
    else:
        try:
            servers = read_user_servers(kind, cache_root=cache_root)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            servers = built_in_servers(kind)
    if not include_disabled:
        servers = tuple(server for server in servers if server.enabled)
    return _sort_servers(servers)


def effective_host_strings(kind: ServerKind, *, cache_root: str | Path | None = None) -> list[str]:
    return [server.address for server in effective_servers(kind, cache_root=cache_root)]


def read_user_servers(kind: ServerKind, *, cache_root: str | Path | None = None) -> tuple[TdxServerEntry, ...]:
    payload = _read_json(_user_servers_path(kind, cache_root=cache_root))
    rows = payload.get("servers") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"Invalid TDX {kind} server config")
    servers = _normalize_server_entries(rows)
    if not servers:
        raise ValueError(f"TDX {kind} server config is empty")
    return servers


def write_user_servers(
    kind: ServerKind,
    servers: Iterable[TdxServerEntry | dict[str, Any]],
    *,
    cache_root: str | Path | None = None,
    source: str = "user",
) -> Path:
    entries = _normalize_server_entries(servers)
    if not entries:
        raise ValueError("at least one server is required")
    payload = {
        "schema_version": 1,
        "kind": kind,
        "source": source,
        "updated_at": _now_text(),
        "servers": [server.to_dict() for server in entries],
    }
    path = _user_servers_path(kind, cache_root=cache_root)
    _write_json_atomic(path, payload)
    return path


def reset_user_servers(kind: ServerKind, *, cache_root: str | Path | None = None) -> Path:
    path = _user_servers_path(kind, cache_root=cache_root)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return path


def probe_server(server: TdxServerEntry, *, timeout: float = 1.2) -> TdxServerProbeResult:
    started = time.perf_counter()
    try:
        with socket.create_connection((server.host, server.port), timeout=timeout):
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            return TdxServerProbeResult(server.host, server.port, True, latency_ms=latency_ms)
    except OSError as exc:
        return TdxServerProbeResult(server.host, server.port, False, error=type(exc).__name__)


def probe_servers(
    kind: ServerKind,
    *,
    servers: Iterable[TdxServerEntry] | None = None,
    cache_root: str | Path | None = None,
    timeout: float = 1.2,
    max_workers: int = 32,
    save: bool = False,
) -> tuple[TdxServerEntry, ...]:
    candidates = tuple(servers or effective_servers(kind, cache_root=cache_root, include_disabled=True))
    if not candidates:
        return ()
    worker_count = min(max(1, int(max_workers)), len(candidates))
    checked_at = _now_text()
    results: dict[str, TdxServerProbeResult] = {}
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-server-probe") as executor:
        futures = [executor.submit(probe_server, server, timeout=timeout) for server in candidates if server.enabled]
        for future in as_completed(futures):
            result = future.result()
            results[result.address] = result
    updated = []
    for server in candidates:
        result = results.get(server.address)
        if result is None:
            updated.append(server)
            continue
        updated.append(
            replace(
                server,
                latency_ms=result.latency_ms,
                last_checked_at=checked_at,
                last_error=None if result.ok else result.error,
            )
        )
    sorted_entries = _sort_servers(tuple(updated))
    if save:
        write_user_servers(kind, sorted_entries, cache_root=cache_root, source="latency_probe")
    return sorted_entries


def server_status(kind: ServerKind, *, cache_root: str | Path | None = None) -> dict[str, Any]:
    source = "built_in"
    env_hosts = _env_server_entries(kind)
    if env_hosts:
        servers = env_hosts
        source = "environment"
    else:
        try:
            payload = _read_json(_user_servers_path(kind, cache_root=cache_root))
            rows = payload.get("servers") if isinstance(payload, dict) else None
            if not isinstance(rows, list):
                raise ValueError(f"Invalid TDX {kind} server config")
            servers = _normalize_server_entries(rows)
            if not servers:
                raise ValueError(f"TDX {kind} server config is empty")
            source = str(payload.get("source") or "user")
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            servers = built_in_servers(kind)
    sorted_servers = _sort_servers(servers)
    return {
        "kind": kind,
        "source": source,
        "config_path": str(_user_servers_path(kind, cache_root=cache_root)),
        "server_count": len(sorted_servers),
        "enabled_count": sum(1 for server in sorted_servers if server.enabled),
        "servers": [server.to_dict() | {"address": server.address} for server in sorted_servers],
    }


def _resource_name(kind: ServerKind) -> str:
    _validate_kind(kind)
    return QUOTE_RESOURCE if kind == "quote" else EXT_RESOURCE


def _validate_kind(kind: str) -> None:
    if kind not in SERVER_KIND_VALUES:
        raise ValueError("server kind must be quote or extended")


def _normalize_server_entries(values: Iterable[TdxServerEntry | dict[str, Any]]) -> tuple[TdxServerEntry, ...]:
    entries: list[TdxServerEntry] = []
    seen: set[str] = set()
    for index, value in enumerate(values, start=1):
        entry = value if isinstance(value, TdxServerEntry) else TdxServerEntry.from_dict(value, priority=index)
        key = entry.address.lower()
        if key in seen:
            continue
        seen.add(key)
        priority = entry.priority or index
        entries.append(replace(entry, priority=priority))
    return tuple(entries)


def _sort_servers(servers: Iterable[TdxServerEntry]) -> tuple[TdxServerEntry, ...]:
    return tuple(
        sorted(
            servers,
            key=lambda server: (
                not server.enabled,
                server.latency_ms is None,
                server.latency_ms if server.latency_ms is not None else float("inf"),
                server.priority,
            ),
        )
    )


def _env_server_entries(kind: ServerKind) -> tuple[TdxServerEntry, ...]:
    if kind == "quote":
        raw = os.getenv("AXDATA_TDX_HOSTS", "")
    else:
        raw = os.getenv("AXDATA_TDX_EXT_HOSTS", "")
    hosts = [item.strip() for item in raw.split(",") if item.strip()]
    rows = []
    for index, address in enumerate(hosts, start=1):
        if ":" not in address:
            continue
        host, port = address.rsplit(":", 1)
        rows.append({"name": f"环境变量{index}", "host": host, "port": port, "priority": index})
    return _normalize_server_entries(rows)


def _user_servers_path(kind: ServerKind, *, cache_root: str | Path | None = None) -> Path:
    _validate_kind(kind)
    root = Path(cache_root).expanduser().resolve() if cache_root not in (None, "") else default_server_cache_root()
    return root / f"{kind}_servers.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def _now_text() -> str:
    return datetime.now(LOCAL_TIMEZONE).isoformat(timespec="seconds")


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
