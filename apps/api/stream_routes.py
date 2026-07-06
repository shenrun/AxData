from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .auth_tokens import verify_api_token
from .config import api_auth_enabled, data_root, is_loopback_host
from .serialization import parse_fields, to_jsonable
from .source_routes import core_request_interface


router = APIRouter()

STREAM_NAME = "stock_quote_refresh_tdx"
DEFAULT_INTERVAL_MS = 3000
MIN_INTERVAL_MS = 500
MAX_CODES_PER_SUBSCRIPTION = 100


def _server_time() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _normalize_codes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list | tuple | set | frozenset):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _normalize_interval_ms(value: Any) -> int:
    if value is None:
        return DEFAULT_INTERVAL_MS
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_INTERVAL_MS
    return max(MIN_INTERVAL_MS, parsed)


def _normalize_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _request_snapshot(code: list[str], fields: list[str] | None) -> list[dict[str, Any]]:
    result = core_request_interface(
        "stock_realtime_snapshot_tdx",
        params={"code": code},
        fields=fields,
        persist=False,
    )
    return list(to_jsonable(result.records))


def _request_refresh(code: list[str], fields: list[str] | None) -> list[dict[str, Any]]:
    from axdata_core.adapters.tdx.realtime_refresh import request_realtime_refresh_rows

    return request_realtime_refresh_rows(code=code, fields=fields)


def _request_refresh_with_cursors(
    code: list[str],
    fields: list[str] | None,
    cursors: dict[str, int],
) -> list[dict[str, Any]]:
    from axdata_core.adapters.tdx.realtime_refresh import request_realtime_refresh_rows

    return request_realtime_refresh_rows(
        code=code,
        fields=fields,
        cursors=cursors,
        include_internal=True,
    )


def _stream_snapshot_override() -> Any:
    main_module = sys.modules.get("apps.api.main")
    return getattr(main_module, "core_stream_snapshot", None) if main_module else None


def _stream_refresh_override() -> Any:
    main_module = sys.modules.get("apps.api.main")
    return getattr(main_module, "core_stream_refresh", None) if main_module else None


async def request_quote_snapshot(code: list[str], fields: list[str] | None) -> list[dict[str, Any]]:
    override = _stream_snapshot_override()
    if override is not None:
        result = override(code=code, fields=fields)
        if asyncio.iscoroutine(result):
            result = await result
        return list(to_jsonable(result))
    return await asyncio.to_thread(_request_snapshot, code, fields)


async def request_quote_refresh(code: list[str], fields: list[str] | None) -> list[dict[str, Any]]:
    override = _stream_refresh_override()
    if override is not None:
        result = override(code=code, fields=fields)
        if asyncio.iscoroutine(result):
            result = await result
        return list(to_jsonable(result))
    return await asyncio.to_thread(_request_refresh, code, fields)


async def request_quote_refresh_with_cursors(
    code: list[str],
    fields: list[str] | None,
    cursors: dict[str, int],
) -> list[dict[str, Any]]:
    override = _stream_refresh_override()
    if override is not None:
        result = override(code=code, fields=fields)
        if asyncio.iscoroutine(result):
            result = await result
        return list(to_jsonable(result))
    return await asyncio.to_thread(_request_refresh_with_cursors, code, fields, cursors)


def _strip_internal_fields(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for row in rows:
        cleaned.append({key: value for key, value in dict(row).items() if not str(key).startswith("_tdx_")})
    return cleaned


def _update_refresh_cursors(cursors: dict[str, int], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        instrument_id = row.get("_tdx_instrument_id") or row.get("instrument_id")
        update_time_raw = row.get("_tdx_update_time_raw")
        if not instrument_id or update_time_raw in (None, ""):
            continue
        try:
            cursors[str(instrument_id).upper()] = int(update_time_raw)
        except (TypeError, ValueError):
            continue


async def _send_event(websocket: WebSocket, payload: dict[str, Any]) -> None:
    await websocket.send_json(to_jsonable(payload))


async def _send_error(
    websocket: WebSocket,
    *,
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    await _send_event(
        websocket,
        {
            "type": "error",
            "stream": STREAM_NAME,
            "request_id": request_id,
            "server_time": _server_time(),
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        },
    )


def _websocket_authorize(websocket: WebSocket) -> None:
    root = data_root()
    if not api_auth_enabled(data_root=root):
        return
    if not os.getenv("AXDATA_API_TOKEN") and not os.getenv("AXDATA_API_AUTH_REQUIRED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        client_host = websocket.client.host if websocket.client else ""
        if is_loopback_host(client_host):
            return
    token = websocket.query_params.get("token")
    authorization = websocket.headers.get("authorization")
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


async def _run_subscription(
    websocket: WebSocket,
    *,
    request_id: str | None,
    code: list[str],
    fields: list[str] | None,
    interval_ms: int,
    initial_snapshot: bool,
) -> None:
    subscription_id = f"sub_{uuid4().hex[:12]}"
    try:
        await _send_event(
            websocket,
            {
                "type": "subscribed",
                "stream": STREAM_NAME,
                "request_id": request_id,
                "subscription_id": subscription_id,
                "server_time": _server_time(),
                "data": {
                    "code": code,
                    "fields": fields,
                    "interval_ms": interval_ms,
                    "initial_snapshot": initial_snapshot,
                },
            },
        )

        if initial_snapshot:
            rows = await request_quote_snapshot(code, fields)
            await _send_event(
                websocket,
                {
                    "type": "snapshot",
                    "stream": STREAM_NAME,
                    "request_id": request_id,
                    "subscription_id": subscription_id,
                    "server_time": _server_time(),
                    "data": rows,
                },
            )

        refresh_cursors: dict[str, int] = {}
        while True:
            await asyncio.sleep(interval_ms / 1000.0)
            rows = await request_quote_refresh_with_cursors(code, fields, refresh_cursors)
            _update_refresh_cursors(refresh_cursors, rows)
            await _send_event(
                websocket,
                {
                    "type": "update",
                    "stream": STREAM_NAME,
                    "subscription_id": subscription_id,
                    "server_time": _server_time(),
                    "data": _strip_internal_fields(rows),
                },
            )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        await _send_error(
            websocket,
            code="stream_error",
            message=str(exc),
            request_id=request_id,
            details={"subscription_id": subscription_id},
        )


@router.websocket(f"/v1/stream/{STREAM_NAME}")
async def stream_stock_quote_refresh_tdx(websocket: WebSocket) -> None:
    try:
        _websocket_authorize(websocket)
    except HTTPException as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc.detail))
        return
    await websocket.accept()
    subscription_task: asyncio.Task[None] | None = None
    try:
        while True:
            message = await websocket.receive_json()
            op = str(message.get("op") or message.get("action") or "").strip().lower()
            request_id = message.get("id") or message.get("request_id")

            if op in {"ping", "heartbeat"}:
                await _send_event(
                    websocket,
                    {
                        "type": "heartbeat",
                        "stream": STREAM_NAME,
                        "request_id": request_id,
                        "server_time": _server_time(),
                        "data": {"active": True},
                    },
                )
                continue

            if op in {"unsubscribe", "close"}:
                if subscription_task is not None:
                    subscription_task.cancel()
                    subscription_task = None
                await _send_event(
                    websocket,
                    {
                        "type": "status",
                        "stream": STREAM_NAME,
                        "request_id": request_id,
                        "server_time": _server_time(),
                        "status": "unsubscribed",
                        "data": {},
                    },
                )
                if op == "close":
                    await websocket.close()
                    return
                continue

            if op != "subscribe":
                await _send_error(
                    websocket,
                    code="invalid_request",
                    message="op must be subscribe, unsubscribe, ping, or close.",
                    request_id=request_id,
                    details={"op": op},
                )
                continue

            params = dict(message.get("params") or {})
            code = _normalize_codes(params.get("code"))
            if not code:
                await _send_error(
                    websocket,
                    code="invalid_request",
                    message="code 至少需要传入 1 个证券代码。",
                    request_id=request_id,
                    details={"field": "code"},
                )
                continue
            if len(code) > MAX_CODES_PER_SUBSCRIPTION:
                await _send_error(
                    websocket,
                    code="invalid_request",
                    message=f"单次订阅最多支持 {MAX_CODES_PER_SUBSCRIPTION} 个证券代码。",
                    request_id=request_id,
                    details={"field": "code", "count": len(code)},
                )
                continue

            fields = parse_fields(params.get("fields"))
            interval_ms = _normalize_interval_ms(params.get("interval_ms"))
            initial_snapshot = _normalize_bool(params.get("initial_snapshot", params.get("snapshot")), True)

            if subscription_task is not None:
                subscription_task.cancel()
            subscription_task = asyncio.create_task(
                _run_subscription(
                    websocket,
                    request_id=request_id,
                    code=code,
                    fields=fields,
                    interval_ms=interval_ms,
                    initial_snapshot=initial_snapshot,
                )
            )
    except WebSocketDisconnect:
        pass
    finally:
        if subscription_task is not None:
            subscription_task.cancel()
