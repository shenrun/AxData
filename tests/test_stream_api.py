from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import apps.api.main as api_main
import apps.api.stream_routes as stream_routes
from apps.api.main import app
from apps.api.auth_tokens import create_api_token


def test_stock_quote_refresh_stream_sends_snapshot_and_update(monkeypatch):
    snapshot_calls = []
    refresh_calls = []

    async def fake_stream_snapshot(*, code, fields):
        snapshot_calls.append({"code": code, "fields": fields})
        return [
            {
                "instrument_id": code[0],
                "last_price": 10.15,
                "change_pct": -1.23,
            }
        ]

    async def fake_stream_refresh(*, code, fields):
        refresh_calls.append({"code": code, "fields": fields})
        return [
            {
                "instrument_id": code[0],
                "last_price": 10.16,
                "change_pct": -1.22,
            }
        ]

    monkeypatch.setattr(api_main, "core_stream_snapshot", fake_stream_snapshot, raising=False)
    monkeypatch.setattr(api_main, "core_stream_refresh", fake_stream_refresh, raising=False)
    client = TestClient(app)

    with client.websocket_connect("/v1/stream/stock_quote_refresh_tdx") as websocket:
        websocket.send_json(
            {
                "op": "subscribe",
                "id": "req_001",
                "params": {
                    "code": "000001.SZ",
                    "fields": ["instrument_id", "last_price", "change_pct"],
                    "interval_ms": 500,
                    "initial_snapshot": True,
                },
            }
        )

        subscribed = websocket.receive_json()
        snapshot = websocket.receive_json()
        update = websocket.receive_json()

    assert subscribed["type"] == "subscribed"
    assert subscribed["request_id"] == "req_001"
    assert subscribed["stream"] == "stock_quote_refresh_tdx"
    assert subscribed["data"]["code"] == ["000001.SZ"]
    assert subscribed["data"]["interval_ms"] == 500

    assert snapshot["type"] == "snapshot"
    assert snapshot["data"] == [
        {
            "instrument_id": "000001.SZ",
            "last_price": 10.15,
            "change_pct": -1.23,
        }
    ]

    assert update["type"] == "update"
    assert update["data"] == [
        {
            "instrument_id": "000001.SZ",
            "last_price": 10.16,
            "change_pct": -1.22,
        }
    ]
    assert snapshot_calls == [
        {
            "code": ["000001.SZ"],
            "fields": ["instrument_id", "last_price", "change_pct"],
        }
    ]
    assert refresh_calls == [
        {
            "code": ["000001.SZ"],
            "fields": ["instrument_id", "last_price", "change_pct"],
        },
    ]


def test_stock_quote_refresh_stream_rejects_missing_code():
    client = TestClient(app)

    with client.websocket_connect("/v1/stream/stock_quote_refresh_tdx") as websocket:
        websocket.send_json({"op": "subscribe", "id": "req_bad", "params": {}})
        payload = websocket.receive_json()

    assert payload["type"] == "error"
    assert payload["request_id"] == "req_bad"
    assert payload["error"]["code"] == "invalid_request"
    assert payload["error"]["details"]["field"] == "code"


def test_stock_quote_refresh_stream_reports_source_errors(monkeypatch):
    async def fake_stream_refresh(*, code, fields):
        raise RuntimeError("source offline")

    monkeypatch.setattr(stream_routes, "MIN_INTERVAL_MS", 1)
    monkeypatch.setattr(api_main, "core_stream_refresh", fake_stream_refresh, raising=False)
    client = TestClient(app)

    with client.websocket_connect("/v1/stream/stock_quote_refresh_tdx") as websocket:
        websocket.send_json(
            {
                "op": "subscribe",
                "id": "req_error",
                "params": {
                    "code": "000001.SZ",
                    "interval_ms": 1,
                    "initial_snapshot": "false",
                },
            }
        )
        subscribed = websocket.receive_json()
        payload = websocket.receive_json()

    assert subscribed["type"] == "subscribed"
    assert subscribed["data"]["initial_snapshot"] is False
    assert payload["type"] == "error"
    assert payload["request_id"] == "req_error"
    assert payload["error"]["code"] == "stream_error"
    assert payload["error"]["message"] == "source offline"


def test_stock_quote_refresh_stream_requires_token_when_configured(monkeypatch):
    monkeypatch.setenv("AXDATA_API_TOKEN", "secret")
    client = TestClient(app)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/v1/stream/stock_quote_refresh_tdx"):
            pass

    with client.websocket_connect("/v1/stream/stock_quote_refresh_tdx?token=secret") as websocket:
        websocket.send_json({"op": "ping", "id": "req_ping"})
        payload = websocket.receive_json()

    assert payload["type"] == "heartbeat"
    assert payload["request_id"] == "req_ping"


def test_stock_quote_refresh_stream_accepts_named_api_token(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    token = create_api_token("stream-client", data_root=tmp_path / "data")["token"]
    client = TestClient(app)

    with client.websocket_connect(f"/v1/stream/stock_quote_refresh_tdx?token={token}") as websocket:
        websocket.send_json({"op": "ping", "id": "req_named"})
        payload = websocket.receive_json()

    assert payload["type"] == "heartbeat"
    assert payload["request_id"] == "req_named"
