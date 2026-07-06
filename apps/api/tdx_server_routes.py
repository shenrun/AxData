from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import data_root
from .serialization import error_payload, response_payload, to_jsonable


router = APIRouter()
ServerKind = Literal["quote", "extended"]
ScheduleFrequency = Literal["daily", "weekly"]
_scheduler_started = Event()


class TdxServerRow(BaseModel):
    name: str = Field(default="")
    host: str
    port: int
    enabled: bool = Field(default=True)
    priority: int | None = None


class TdxServerSaveRequest(BaseModel):
    servers: list[TdxServerRow]

    def enabled_rows(self) -> list[TdxServerRow]:
        return [
            row
            for row in self.servers
            if row.enabled and row.host.strip() and 0 < int(row.port) <= 65535
        ]


class TdxServerProbeRequest(BaseModel):
    timeout: float = Field(default=1.2, ge=0.2, le=10.0)
    max_workers: int = Field(default=32, ge=1, le=128)
    save: bool = Field(default=True)


class TdxServerProbeScheduleRequest(BaseModel):
    enabled: bool = Field(default=True)
    frequency: ScheduleFrequency = Field(default="daily")
    time: str = Field(default="08:30")
    weekday: str = Field(default="1")
    timeout: float = Field(default=1.2, ge=0.2, le=10.0)
    max_workers: int = Field(default=32, ge=1, le=128)
    kinds: list[ServerKind] = Field(default_factory=lambda: ["quote", "extended"])


@router.get("/v1/tdx/servers")
def get_all_tdx_servers() -> JSONResponse:
    try:
        return JSONResponse(
            content=to_jsonable(
                response_payload(
                    {
                        "quote": _server_status("quote"),
                        "extended": _server_status("extended"),
                        "probe_schedule": _read_probe_schedule(),
                    }
                )
            )
        )
    except Exception as exc:
        return _server_error(exc)


@router.get("/v1/tdx/servers/probe-schedule")
def get_tdx_server_probe_schedule() -> JSONResponse:
    try:
        return JSONResponse(content=to_jsonable(response_payload(_read_probe_schedule())))
    except Exception as exc:
        return _server_error(exc)


@router.post("/v1/tdx/servers/probe-schedule")
def save_tdx_server_probe_schedule(request: TdxServerProbeScheduleRequest) -> JSONResponse:
    try:
        schedule = _build_probe_schedule(request)
        previous = _read_probe_schedule()
        schedule["last_run_key"] = previous.get("last_run_key")
        schedule["last_checked_at"] = previous.get("last_checked_at")
        schedule["last_result"] = previous.get("last_result")
        _write_probe_schedule(schedule)
        start_tdx_server_probe_scheduler_loop()
        return JSONResponse(content=to_jsonable(response_payload(schedule)))
    except Exception as exc:
        return _server_error(exc)


@router.delete("/v1/tdx/servers/probe-schedule")
def disable_tdx_server_probe_schedule() -> JSONResponse:
    try:
        schedule = {**_read_probe_schedule(), "enabled": False, "updated_at": _now_text()}
        _write_probe_schedule(schedule)
        return JSONResponse(content=to_jsonable(response_payload(schedule)))
    except Exception as exc:
        return _server_error(exc)


@router.get("/v1/tdx/servers/{kind}")
def get_tdx_servers(kind: ServerKind) -> JSONResponse:
    try:
        return JSONResponse(content=to_jsonable(response_payload(_server_status(kind))))
    except Exception as exc:
        return _server_error(exc)


@router.put("/v1/tdx/servers/{kind}")
def save_tdx_servers(kind: ServerKind, request: TdxServerSaveRequest) -> JSONResponse:
    try:
        from axdata_core.tdx_server_config import write_user_servers

        if not request.enabled_rows():
            raise ValueError("至少保留一个启用的服务器")
        write_user_servers(
            kind,
            [row.model_dump(exclude_none=True) for row in request.servers],
            cache_root=_cache_root(),
            source="user",
        )
        return JSONResponse(content=to_jsonable(response_payload(_server_status(kind))))
    except Exception as exc:
        return _server_error(exc)


@router.post("/v1/tdx/servers/{kind}/probe")
def probe_tdx_servers(kind: ServerKind, request: TdxServerProbeRequest) -> JSONResponse:
    try:
        from axdata_core.tdx_server_config import probe_servers

        probe_servers(
            kind,
            cache_root=_cache_root(),
            timeout=request.timeout,
            max_workers=request.max_workers,
            save=request.save,
        )
        return JSONResponse(content=to_jsonable(response_payload(_server_status(kind))))
    except Exception as exc:
        return _server_error(exc)


@router.post("/v1/tdx/servers/{kind}/reset")
def reset_tdx_servers(kind: ServerKind) -> JSONResponse:
    try:
        from axdata_core.tdx_server_config import reset_user_servers

        reset_user_servers(kind, cache_root=_cache_root())
        return JSONResponse(content=to_jsonable(response_payload(_server_status(kind))))
    except Exception as exc:
        return _server_error(exc)


def start_tdx_server_probe_scheduler_loop() -> None:
    if _scheduler_started.is_set():
        return
    _scheduler_started.set()
    Thread(target=_run_probe_scheduler_loop, name="axdata-tdx-server-probe-scheduler", daemon=True).start()


def _server_status(kind: ServerKind) -> dict[str, Any]:
    from axdata_core.tdx_server_config import server_status

    return server_status(kind, cache_root=_cache_root())


def _cache_root() -> str:
    return str(data_root() / "cache" / "tdx_servers")


def _schedule_path() -> Path:
    return data_root() / "cache" / "tdx_servers" / "probe_schedule.json"


def _default_probe_schedule() -> dict[str, Any]:
    return {
        "enabled": False,
        "frequency": "daily",
        "time": "08:30",
        "weekday": "1",
        "timeout": 1.2,
        "max_workers": 32,
        "kinds": ["quote", "extended"],
        "last_run_key": None,
        "last_checked_at": None,
        "last_result": None,
        "updated_at": None,
    }


def _read_probe_schedule() -> dict[str, Any]:
    path = _schedule_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    return {**_default_probe_schedule(), **raw}


def _build_probe_schedule(request: TdxServerProbeScheduleRequest) -> dict[str, Any]:
    kinds = [kind for kind in request.kinds if kind in ("quote", "extended")]
    if not kinds:
        raise ValueError("至少选择一个测速对象")
    return {
        "enabled": bool(request.enabled),
        "frequency": request.frequency,
        "time": _normalize_time(request.time),
        "weekday": _normalize_weekday(request.weekday),
        "timeout": float(request.timeout),
        "max_workers": int(request.max_workers),
        "kinds": list(dict.fromkeys(kinds)),
        "updated_at": _now_text(),
    }


def _write_probe_schedule(schedule: dict[str, Any]) -> None:
    _write_json_atomic(_schedule_path(), schedule)


def _run_probe_scheduler_loop() -> None:
    while True:
        try:
            _tick_probe_schedule()
        except Exception:
            pass
        sleep(30.0)


def _tick_probe_schedule(*, now: datetime | None = None) -> dict[str, Any] | None:
    schedule = _read_probe_schedule()
    current = now or datetime.now().astimezone()
    if not _probe_schedule_due(schedule, current):
        return None
    result = _run_scheduled_probe(schedule)
    schedule = {
        **schedule,
        "last_run_key": _schedule_run_key(current),
        "last_checked_at": current.isoformat(timespec="seconds"),
        "last_result": result,
        "updated_at": _now_text(),
    }
    _write_probe_schedule(schedule)
    return schedule


def _run_scheduled_probe(schedule: dict[str, Any]) -> dict[str, Any]:
    from axdata_core.tdx_server_config import probe_servers

    result: dict[str, Any] = {}
    timeout = float(schedule.get("timeout") or 1.2)
    max_workers = int(schedule.get("max_workers") or 32)
    for kind in schedule.get("kinds") or []:
        if kind not in ("quote", "extended"):
            continue
        servers = probe_servers(kind, cache_root=_cache_root(), timeout=timeout, max_workers=max_workers, save=True)
        result[kind] = {
            "server_count": len(servers),
            "enabled_count": sum(1 for server in servers if server.enabled),
            "fastest_latency_ms": next((server.latency_ms for server in servers if server.latency_ms is not None), None),
        }
    return result


def _probe_schedule_due(schedule: dict[str, Any], now: datetime) -> bool:
    if not schedule.get("enabled", False):
        return False
    trigger_time = str(schedule.get("time") or "")
    if not trigger_time or now.strftime("%H:%M") != trigger_time:
        return False
    if schedule.get("frequency") == "weekly" and str(schedule.get("weekday") or "1") != str(now.isoweekday()):
        return False
    return schedule.get("last_run_key") != _schedule_run_key(now)


def _schedule_run_key(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.astimezone()
    return value.strftime("%Y%m%d_%H%M")


def _normalize_time(value: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.strptime(text, "%H:%M")
    except ValueError as exc:
        raise ValueError("时间格式应为 HH:MM") from exc
    return parsed.strftime("%H:%M")


def _normalize_weekday(value: str) -> str:
    text = str(value or "1").strip()
    if text not in {"1", "2", "3", "4", "5", "6", "7"}:
        raise ValueError("weekday must be 1-7")
    return text


def _now_text() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        tmp_path.replace(path)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def _server_error(exc: Exception) -> JSONResponse:
    payload = error_payload(
        "TDX_SERVER_CONFIG_ERROR",
        str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(status_code=400, content=to_jsonable(payload))
