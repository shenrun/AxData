from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException, Query, Request, status

from .auth_tokens import api_auth_enabled, api_token_store_path, is_loopback_host, verify_api_token


DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = "8666"
DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = "8667"
DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:8667",
    "http://localhost:8667",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = REPO_ROOT / "data"
RUNTIME_CONFIG_VERSION = 1
RUNTIME_CONFIG_FILE_NAME = "runtime_config.json"
RUNTIME_RESTART_FILE_NAME = "runtime_restart.json"
RUNTIME_LAUNCHER_FILE_NAME = "runtime_launcher.json"
TRADE_CALENDAR_MAINTENANCE_FILE_NAME = "trade_calendar_maintenance.json"
DEFAULT_TRADE_CALENDAR_MAINTENANCE = {
    "enabled": False,
    "time": "22:30",
    "past_days": 30,
    "future_days": 180,
    "recheck_past_days": 7,
}


def configured_cors_origins() -> list[str]:
    raw = os.getenv("AXDATA_CORS_ORIGINS", "")
    configured = [origin.strip() for origin in raw.split(",") if origin.strip()]
    web_port = os.getenv("AXDATA_WEB_PORT", DEFAULT_WEB_PORT)
    env_origins = {f"http://127.0.0.1:{web_port}", f"http://localhost:{web_port}"}
    return sorted({*DEFAULT_CORS_ORIGINS, *env_origins, *configured})


def data_root() -> Path:
    return Path(os.getenv("AXDATA_DATA_DIR", str(DEFAULT_DATA_ROOT))).expanduser().resolve()


def runtime_config_path() -> Path:
    return Path(
        os.getenv(
            "AXDATA_RUNTIME_CONFIG_FILE",
            str(REPO_ROOT / "metadata" / RUNTIME_CONFIG_FILE_NAME),
        )
    ).expanduser().resolve()


def runtime_restart_request_path() -> Path:
    return Path(
        os.getenv(
            "AXDATA_RESTART_REQUEST_FILE",
            str(REPO_ROOT / "metadata" / RUNTIME_RESTART_FILE_NAME),
        )
    ).expanduser().resolve()


def runtime_launcher_path() -> Path:
    return Path(
        os.getenv(
            "AXDATA_LAUNCHER_FILE",
            str(REPO_ROOT / "metadata" / RUNTIME_LAUNCHER_FILE_NAME),
        )
    ).expanduser().resolve()


def trade_calendar_maintenance_config_path() -> Path:
    return Path(
        os.getenv(
            "AXDATA_TRADE_CALENDAR_MAINTENANCE_FILE",
            str(REPO_ROOT / "metadata" / TRADE_CALENDAR_MAINTENANCE_FILE_NAME),
        )
    ).expanduser().resolve()


def load_runtime_config() -> dict[str, Any]:
    path = runtime_config_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid runtime config JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Runtime config at {path} must be a JSON object.")
    return payload


def save_runtime_config(config: dict[str, Any]) -> Path:
    path = runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": RUNTIME_CONFIG_VERSION, **config}
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)
    return path


def load_trade_calendar_maintenance_config() -> dict[str, Any]:
    path = trade_calendar_maintenance_config_path()
    if not path.exists():
        return {**DEFAULT_TRADE_CALENDAR_MAINTENANCE, "path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid trade calendar maintenance JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Trade calendar maintenance config at {path} must be a JSON object.")
    return _normalize_trade_calendar_maintenance_config(payload, path=path)


def save_trade_calendar_maintenance_config(config: dict[str, Any]) -> Path:
    path = trade_calendar_maintenance_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _normalize_trade_calendar_maintenance_config(config, path=path)
    payload.pop("path", None)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)
    return path


def _normalize_trade_calendar_maintenance_config(config: dict[str, Any], *, path: Path) -> dict[str, Any]:
    return {
        "version": RUNTIME_CONFIG_VERSION,
        "enabled": bool(config.get("enabled", DEFAULT_TRADE_CALENDAR_MAINTENANCE["enabled"])),
        "time": str(config.get("time") or DEFAULT_TRADE_CALENDAR_MAINTENANCE["time"]),
        "past_days": int(config.get("past_days", DEFAULT_TRADE_CALENDAR_MAINTENANCE["past_days"])),
        "future_days": int(config.get("future_days", DEFAULT_TRADE_CALENDAR_MAINTENANCE["future_days"])),
        "recheck_past_days": int(config.get("recheck_past_days", DEFAULT_TRADE_CALENDAR_MAINTENANCE["recheck_past_days"])),
        "path": str(path),
    }


def current_runtime_config() -> dict[str, Any]:
    api_host = os.getenv("AXDATA_API_HOST", DEFAULT_API_HOST)
    api_port = int(os.getenv("AXDATA_API_PORT", DEFAULT_API_PORT))
    web_port = int(os.getenv("AXDATA_WEB_PORT", DEFAULT_WEB_PORT))
    local_api_host = "127.0.0.1" if api_host == "0.0.0.0" else api_host
    local_api_base = f"http://{local_api_host}:{api_port}"
    return {
        "api_host": api_host,
        "api_port": api_port,
        "api_base": local_api_base,
        "local_api_base": local_api_base,
        "listen_api_base": f"http://{api_host}:{api_port}",
        "web_host": DEFAULT_WEB_HOST,
        "web_port": web_port,
        "data_root": str(data_root()),
        "auth_enabled": api_auth_enabled(data_root=data_root(), api_host=api_host),
        "cors_origins": configured_cors_origins(),
    }


def require_token(
    request: Request,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    root = data_root()
    if not api_auth_enabled(data_root=root, api_host=os.getenv("AXDATA_API_HOST", DEFAULT_API_HOST)):
        return
    if _local_request_can_skip_named_token_auth(request, data_root=root):
        return

    bearer = None
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value:
            bearer = value.strip()

    if verify_api_token(bearer, data_root=root) or verify_api_token(token, data_root=root):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _local_request_can_skip_named_token_auth(request: Request, *, data_root: Path) -> bool:
    if os.getenv("AXDATA_API_TOKEN"):
        return False
    if os.getenv("AXDATA_API_AUTH_REQUIRED", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False
    if not api_token_store_path(data_root=data_root).exists():
        return False
    client_host = request.client.host if request.client else ""
    return is_loopback_host(client_host)
