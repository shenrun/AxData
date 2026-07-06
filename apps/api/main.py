from __future__ import annotations

import os
import sys
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware


CORE_PATH = Path(__file__).resolve().parents[2] / "libs" / "axdata_core"
if CORE_PATH.exists() and str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

from .config import (  # noqa: E402
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_WEB_HOST,
    DEFAULT_WEB_PORT,
    configured_cors_origins,
    current_runtime_config,
    data_root,
    load_trade_calendar_maintenance_config,
    load_runtime_config,
    require_token,
    runtime_config_path,
    runtime_launcher_path,
    runtime_restart_request_path,
    save_runtime_config,
)
from .auth_tokens import api_auth_enabled  # noqa: E402
from .models import RuntimeConfigUpdateRequest  # noqa: E402
from .query_routes import query_core_table, router as query_router  # noqa: E402
from .data_routes import router as data_router  # noqa: E402
from .serialization import response_payload  # noqa: E402
from .source_routes import core_request_interface, router as source_router  # noqa: E402
from .plugin_routes import router as plugin_router  # noqa: E402
from .stream_routes import router as stream_router  # noqa: E402
from .downloader_routes import router as downloader_router, start_download_scheduler_loop  # noqa: E402
from .calendar_routes import router as calendar_router  # noqa: E402
from .collector_routes import router as collector_router, start_collector_scheduler_loop  # noqa: E402
from .tdx_server_routes import router as tdx_server_router, start_tdx_server_probe_scheduler_loop  # noqa: E402
from .auth_routes import router as auth_router  # noqa: E402

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    initialize_api_local_environment()
    Thread(target=_run_trade_calendar_maintenance_loop, name="axdata-trade-calendar-maintenance", daemon=True).start()
    start_download_scheduler_loop()
    start_collector_scheduler_loop()
    start_tdx_server_probe_scheduler_loop()
    yield


app = FastAPI(
    title="AxData API",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "HTTP channel for AxData Web, LAN/server access, and cross-language clients. "
        "Normal query endpoints only read already-ingested AxData tables."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AuthDependency = Depends(require_token)


def initialize_api_local_environment() -> None:
    """Create missing local AxData directories without overwriting user data."""

    try:
        from axdata_core import initialize_local_environment

        initialize_local_environment(data_root())
    except Exception as exc:  # startup should still expose diagnostics if init fails
        logger.warning("AxData local environment initialization skipped: %s", exc)


def _run_trade_calendar_maintenance_loop() -> None:
    startup_checked = False
    last_daily_key: str | None = None
    while True:
        now = datetime.now().astimezone()
        maintenance_config = _trade_calendar_maintenance_config()
        is_startup_check = not startup_checked
        if should_maintain_trade_calendar_cache(
            now=now,
            startup_checked=startup_checked,
            last_daily_key=last_daily_key,
            config=maintenance_config,
        ):
            _maintain_trade_calendar_cache(config=maintenance_config, startup=is_startup_check)
            startup_checked = True
            if maintenance_config.get("enabled") and not is_startup_check:
                last_daily_key = now.strftime("%Y%m%d")
        sleep(_seconds_until_next_calendar_maintenance_check())


def should_maintain_trade_calendar_cache(
    *,
    now: datetime,
    startup_checked: bool,
    last_daily_key: str | None,
    config: dict[str, Any] | None = None,
) -> bool:
    if not startup_checked:
        return True
    maintenance_config = config or {}
    if not maintenance_config.get("enabled"):
        return False
    run_time = _parse_maintenance_time(str(maintenance_config.get("time") or "22:30"))
    today_key = now.strftime("%Y%m%d")
    return last_daily_key != today_key and (now.hour, now.minute) >= run_time


def _maintain_trade_calendar_cache(*, config: dict[str, Any] | None = None, startup: bool = False) -> None:
    try:
        from axdata_core import ensure_trade_calendar_cache

        options = config or {}
        status = ensure_trade_calendar_cache(
            data_root(),
            past_days=int(options.get("past_days", 30 if not startup else 180)),
            future_days=int(options.get("future_days", 180)),
            monthly_recheck_past_days=int(options.get("recheck_past_days", 30)),
        )
        logger.info(
            "Trade calendar cache checked: mode=%s fetched_ranges=%s",
            status.get("maintenance_mode"),
            status.get("fetched_ranges"),
        )
    except Exception as exc:  # cache maintenance should not block API startup
        logger.warning("Trade calendar cache startup maintenance failed: %s", exc)


def _trade_calendar_maintenance_config() -> dict[str, Any]:
    try:
        return load_trade_calendar_maintenance_config()
    except Exception as exc:
        logger.warning("Trade calendar maintenance config load failed: %s", exc)
        return {"enabled": False, "time": "22:30", "past_days": 30, "future_days": 180, "recheck_past_days": 7}


def _parse_maintenance_time(value: str) -> tuple[int, int]:
    try:
        hour_text, minute_text = value.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (TypeError, ValueError):
        return (22, 30)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return (22, 30)
    return (hour, minute)


def _seconds_until_next_calendar_maintenance_check() -> float:
    return 60.0


@app.get("/health", dependencies=[AuthDependency])
def health() -> dict[str, Any]:
    core_modules = {}
    for module_name in ("schema", "query"):
        try:
            __import__(f"axdata_core.{module_name}")
            core_modules[module_name] = True
        except ImportError:
            core_modules[module_name] = False

    return {
        "status": "ok",
        "service": "axdata-api",
        "version": "0.1.0",
        "auth_enabled": api_auth_enabled(
            data_root=data_root(),
            api_host=os.getenv("AXDATA_API_HOST", DEFAULT_API_HOST),
        ),
        "data_root": str(data_root()),
        "core": core_modules,
    }


@app.get("/v1/config", dependencies=[AuthDependency])
def config() -> dict[str, Any]:
    runtime = current_runtime_config()
    try:
        pending = load_runtime_config()
    except ValueError as exc:
        pending = {"error": str(exc)}
    return response_payload(
        {
            **runtime,
            "pending_restart": _runtime_config_pending_restart(runtime, pending),
            "runtime_config_path": str(runtime_config_path()),
            "restart_supported": _restart_supported(),
            "restart_unavailable_reason": _restart_unavailable_reason(),
            "next_start": _next_start_config(runtime, pending),
        }
    )


@app.put("/v1/config/runtime", dependencies=[AuthDependency])
def update_runtime_config(request: RuntimeConfigUpdateRequest) -> dict[str, Any]:
    if request.api_host not in {"127.0.0.1", "0.0.0.0"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="api_host must be 127.0.0.1 or 0.0.0.0.",
        )
    config_payload = {
        "api_host": request.api_host,
        "api_port": request.api_port,
        "web_host": DEFAULT_WEB_HOST,
        "web_port": request.web_port,
    }
    path = save_runtime_config(config_payload)
    runtime = current_runtime_config()
    next_start = _next_start_config(runtime, config_payload)
    return response_payload(
        {
            "saved": True,
            "path": str(path),
            "next_start": next_start,
            "pending_restart": _runtime_config_pending_restart(runtime, config_payload),
            "restart_supported": _restart_supported(),
            "restart_unavailable_reason": _restart_unavailable_reason(),
        }
    )


@app.post("/v1/config/restart-api", dependencies=[AuthDependency])
def request_api_restart() -> dict[str, Any]:
    restart_unavailable_reason = _restart_unavailable_reason()
    if restart_unavailable_reason is not None:
        return response_payload(
            {
                "accepted": False,
                "restart_supported": False,
                "restart_unavailable_reason": restart_unavailable_reason,
                "message": "当前后端不是由 AxData 启动器托管，Web 不能自动重启它。请先停止当前后端，再从项目根目录运行 npm run dev:api 启动。",
            }
        )
    request_path = runtime_restart_request_path()
    request_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": uuid.uuid4().hex,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
    }
    temp_path = request_path.with_name(f".{request_path.name}.tmp")
    import json

    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(request_path)
    return response_payload(
        {
            "accepted": True,
            "restart_supported": True,
            "path": str(request_path),
            "message": "已请求重启后端。几秒后页面会自动重新连接。",
        }
    )


def _restart_supported() -> bool:
    return _restart_unavailable_reason() is None


def _restart_unavailable_reason() -> str | None:
    if os.getenv("AXDATA_DEV_LAUNCHER") != "1":
        return "not_managed_by_launcher"
    launcher_path = runtime_launcher_path()
    if not launcher_path.exists():
        return "launcher_file_missing"
    try:
        payload = json.loads(launcher_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "launcher_file_invalid"
    if str(payload.get("restart_request_path") or "") != str(runtime_restart_request_path()):
        return "launcher_path_mismatch"
    launcher_id = os.getenv("AXDATA_DEV_LAUNCHER_ID")
    if launcher_id and str(payload.get("launcher_id") or "") != launcher_id:
        return "launcher_id_mismatch"
    if not _launcher_heartbeat_recent(payload.get("heartbeat_at")):
        return "launcher_heartbeat_stale"
    if not _launcher_process_alive(payload.get("pid")):
        return "launcher_process_not_alive"
    return None


def _launcher_heartbeat_recent(value: Any) -> bool:
    if not value:
        return False
    try:
        heartbeat = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    if heartbeat.tzinfo is None:
        heartbeat = heartbeat.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - heartbeat.astimezone(timezone.utc) < timedelta(seconds=30)


def _launcher_process_alive(pid: Any) -> bool:
    try:
        process_id = int(pid)
    except (TypeError, ValueError):
        return False
    if process_id <= 0 or process_id == os.getpid():
        return False
    if os.name == "nt":
        return _windows_process_alive(process_id)
    try:
        os.kill(process_id, 0)
    except (OSError, SystemError):
        return False
    return True


def _windows_process_alive(process_id: int) -> bool:
    try:
        import ctypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, process_id)
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        try:
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return False


def _next_start_config(runtime: dict[str, Any], pending: dict[str, Any]) -> dict[str, Any]:
    if pending.get("error"):
        return {
            "api_host": runtime.get("api_host", DEFAULT_API_HOST),
            "api_port": runtime.get("api_port", int(DEFAULT_API_PORT)),
            "web_host": DEFAULT_WEB_HOST,
            "web_port": runtime.get("web_port", int(DEFAULT_WEB_PORT)),
            "error": pending["error"],
        }
    return {
        "api_host": pending.get("api_host", runtime.get("api_host", DEFAULT_API_HOST)),
        "api_port": int(pending.get("api_port", runtime.get("api_port", int(DEFAULT_API_PORT)))),
        "web_host": DEFAULT_WEB_HOST,
        "web_port": int(pending.get("web_port", runtime.get("web_port", int(DEFAULT_WEB_PORT)))),
    }


def _runtime_config_pending_restart(runtime: dict[str, Any], pending: dict[str, Any]) -> bool:
    next_start = _next_start_config(runtime, pending)
    if next_start.get("error"):
        return False
    return (
        str(next_start.get("api_host")) != str(runtime.get("api_host"))
        or int(next_start.get("api_port", 0)) != int(runtime.get("api_port", 0))
        or int(next_start.get("web_port", 0)) != int(runtime.get("web_port", 0))
    )


@app.get("/v1/status", dependencies=[AuthDependency])
def local_status() -> dict[str, Any]:
    from axdata_core import build_local_diagnostics

    return response_payload(build_local_diagnostics(data_root()))


@app.get("/v1/doctor", dependencies=[AuthDependency])
def local_doctor() -> dict[str, Any]:
    return local_status()


app.include_router(source_router, dependencies=[AuthDependency])
app.include_router(plugin_router, dependencies=[AuthDependency])
app.include_router(query_router, dependencies=[AuthDependency])
app.include_router(data_router, dependencies=[AuthDependency])
app.include_router(downloader_router, dependencies=[AuthDependency])
app.include_router(collector_router, dependencies=[AuthDependency])
app.include_router(calendar_router, dependencies=[AuthDependency])
app.include_router(tdx_server_router, dependencies=[AuthDependency])
app.include_router(auth_router, dependencies=[AuthDependency])
app.include_router(stream_router)
