from __future__ import annotations

import json
import sys
import types

import axdata as ax
import axdata.client as sdk_client
import axdata_core
import pandas as pd
import pytest

from axdata_core import SourceRequestResult
from axdata_core import write_core_table


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, json, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        if url.endswith("/v1/download/stock_codes_tdx"):
            return FakeResponse(
                {
                    "success": True,
                    "data": {
                        "job_id": "run_test",
                        "status": "success",
                        "row_count": 2,
                        "output_path": "data/raw/stock_codes_tdx/run_test.parquet",
                    },
                }
            )
        table = json.get("table") if isinstance(json, dict) else None
        if table == "stock_basic_exchange":
            records = [
                {
                    "instrument_id": "000001.SZ",
                    "name": "平安银行",
                    "exchange": "SZSE",
                    "industry": "J 金融业",
                }
            ]
        elif table == "adj_factor":
            records = [{"ts_code": "000001.SZ", "trade_date": "20240102", "adj_factor": 1.0}]
        else:
            records = [{"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}]
        return FakeResponse(
            {
                "success": True,
                "data": {
                    "records": records
                },
            }
        )

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return FakeResponse(
            {
                "success": True,
                "data": [
                    {
                "instrument_id": "000001.SZ",
                "name": "平安银行",
                "exchange": "SZSE",
                "industry": "J 金融业",
            }
        ],
    }
        )


def test_sdk_daily_posts_v1_query_and_returns_dataframe():
    session = FakeSession()
    client = ax.AxDataClient(token="secret", api_base="http://example.test", session=session)

    df = client.daily(
        ts_code="000001.SZ",
        start_date="20240101",
        end_date="20240131",
        fields=["ts_code", "trade_date", "close"],
    )

    assert df.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]
    assert session.calls[0]["url"] == "http://example.test/v1/query"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer secret"
    assert session.calls[0]["json"]["table"] == "daily"
    assert session.calls[0]["json"]["fields"] == ["ts_code", "trade_date", "close"]


def test_sdk_adj_factor_posts_v1_query_and_returns_dataframe():
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    df = client.adj_factor(
        ts_code="000001.SZ",
        start_date="20240101",
        end_date="20240131",
        fields=["ts_code", "trade_date", "adj_factor"],
    )

    assert df.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "adj_factor": 1.0}
    ]
    assert session.calls[0]["url"] == "http://example.test/v1/query"
    assert session.calls[0]["json"]["table"] == "adj_factor"
    assert session.calls[0]["json"]["fields"] == ["ts_code", "trade_date", "adj_factor"]


def test_sdk_call_posts_v1_request_interface_and_returns_dataframe():
    session = FakeSession()
    client = ax.AxDataClient(token="secret", api_base="http://example.test", session=session)

    df = client.call(
        "daily",
        ts_code="000001.SZ",
        start_date="2024-01-01",
        end_date="20240131",
        fields="ts_code,trade_date,close",
    )

    assert df.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]
    assert session.calls[0]["url"] == "http://example.test/v1/request/daily"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer secret"
    assert session.calls[0]["json"] == {
        "params": {
            "ts_code": "000001.SZ",
            "start_date": "20240101",
            "end_date": "20240131",
        },
        "fields": ["ts_code", "trade_date", "close"],
    }


def test_sdk_call_posts_execution_options_outside_params():
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    client.call(
        "stock_codes_tdx",
        scope="all",
        options={"source_server_count": 2, "connections_per_server": 3},
    )

    assert session.calls[0]["json"] == {
        "params": {"scope": "all"},
        "options": {"source_server_count": 2, "connections_per_server": 3},
    }


@pytest.mark.parametrize(
    ("interface_name", "params", "fields"),
    [
        ("stock_realtime_snapshot_tdx", {"code": "000001.SZ"}, ["instrument_id", "last_price"]),
        ("stock_realtime_rank_tdx", {"category": "a_share", "count": 3}, ["rank", "instrument_id"]),
        ("stock_order_book_tdx", {"code": "000001.SZ"}, ["instrument_id", "level", "bid_price"]),
        ("index_realtime_snapshot_tdx", {"code": "000001.SH"}, ["instrument_id", "last_price"]),
        ("index_kline_tdx", {"code": "000001.SH", "count": 3}, ["instrument_id", "trade_time", "close"]),
        ("etf_realtime_snapshot_tdx", {"code": "510050.SH"}, ["instrument_id", "last_price"]),
        ("etf_kline_tdx", {"code": "510050.SH", "count": 3}, ["instrument_id", "trade_time", "close"]),
        ("concept_constituents_tdx", {"concept_code": "881386", "count": 2}, ["instrument_id", "name"]),
        ("stock_intraday_today_tdx", {"code": "000001.SZ"}, ["instrument_id", "time_label", "price"]),
        (
            "stock_intraday_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260519"},
            ["instrument_id", "trade_time", "price"],
        ),
        (
            "stock_intraday_recent_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260519"},
            ["instrument_id", "trade_time", "avg_price"],
        ),
        (
            "stock_intraday_buy_sell_strength_tdx",
            {"code": "000001.SZ"},
            ["instrument_id", "minute_time", "bid_order"],
        ),
        (
            "stock_intraday_volume_comparison_tdx",
            {"code": "000001.SZ"},
            ["instrument_id", "minute_time", "today_volume"],
        ),
        ("stock_trades_today_tdx", {"code": "000001.SZ"}, ["instrument_id", "trade_time", "price"]),
        (
            "stock_trades_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260511"},
            ["instrument_id", "trade_datetime", "price"],
        ),
        ("stock_auction_process_tdx", {"code": "000988.SZ"}, ["instrument_id", "auction_time", "price"]),
        ("stock_auction_result_tdx", {"code": "000001.SZ"}, ["instrument_id", "auction_time", "price"]),
        (
            "stock_auction_result_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260511"},
            ["instrument_id", "auction_datetime", "price"],
        ),
        ("stock_finance_summary_tdx", {"code": "000001.SZ"}, ["instrument_id", "updated_date", "eps"]),
        ("stock_finance_profile_tdx", {"code": "000001.SZ"}, ["instrument_id", "updated_date", "ipo_date"]),
        ("index_realtime_rank_tdx", {"sort": "change_pct", "count": 5}, ["rank", "instrument_id"]),
        ("etf_realtime_rank_tdx", {"sort": "change_pct", "count": 5}, ["rank", "instrument_id"]),
        ("index_intraday_today_tdx", {"code": "000001.SH"}, ["instrument_id", "time_label", "price"]),
        (
            "index_intraday_history_tdx",
            {"code": "000001.SH", "trade_date": "20260617"},
            ["instrument_id", "trade_time", "price"],
        ),
        ("etf_intraday_today_tdx", {"code": "510050.SH"}, ["instrument_id", "time_label", "price"]),
        ("etf_trades_today_tdx", {"code": "510050.SH"}, ["instrument_id", "trade_time", "price"]),
    ],
)
def test_sdk_call_source_only_interface_samples_use_request_channel(interface_name, params, fields):
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    client.call(interface_name, fields=fields, **params)

    assert session.calls[0]["url"] == f"http://example.test/v1/request/{interface_name}"
    assert session.calls[0]["json"] == {
        "params": params,
        "fields": fields,
    }


def test_sdk_download_posts_v1_download_and_returns_job_metadata():
    session = FakeSession()
    client = ax.AxDataClient(token="secret", api_base="http://example.test", session=session)

    job = client.download("stock_codes_tdx", scope="all", fields=["instrument_id", "name"])

    assert job.job_id == "run_test"
    assert job.status == "success"
    assert job.row_count == 2
    assert session.calls[0]["url"] == "http://example.test/v1/download/stock_codes_tdx"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer secret"
    assert session.calls[0]["json"] == {
        "params": {"scope": "all"},
        "fields": ["instrument_id", "name"],
    }


def test_sdk_download_posts_downloader_configuration():
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    client.download(
        "stock_codes_tdx",
        scope="all",
        output_root="D:/axdata/export",
        output_dir="D:/axdata/export/raw/stock_codes_tdx",
        formats=["parquet", "csv"],
        collect_mode="incremental",
        connection_mode="long_connection",
        connection_count=1,
        source_server_count=2,
        connections_per_server=3,
        max_concurrent_tasks=6,
        batch_size=80,
        request_interval_ms=50,
        retry_count=2,
        timeout_ms=15000,
    )

    assert session.calls[0]["json"] == {
        "params": {"scope": "all"},
        "output_root": "D:/axdata/export",
        "output_dir": "D:/axdata/export/raw/stock_codes_tdx",
        "formats": ["parquet", "csv"],
        "collect_mode": "incremental",
        "connection_mode": "long_connection",
        "connection_count": 1,
        "source_server_count": 2,
        "connections_per_server": 3,
        "max_concurrent_tasks": 6,
        "batch_size": 80,
        "request_interval_ms": 50,
        "retry_count": 2,
        "timeout_ms": 15000,
    }


def test_sdk_stream_opens_websocket_and_sends_subscribe(monkeypatch):
    created = {}

    class FakeWebSocket:
        def __init__(self):
            self.sent = []
            self.closed = False
            self.messages = [
                json.dumps({"type": "subscribed", "data": {"code": ["000001.SZ"]}}),
            ]

        def send(self, message):
            self.sent.append(json.loads(message))

        def recv(self):
            return self.messages.pop(0)

        def close(self):
            self.closed = True

    fake_ws = FakeWebSocket()

    def fake_create_connection(url, timeout=None, header=None):
        created["url"] = url
        created["timeout"] = timeout
        created["header"] = header
        return fake_ws

    monkeypatch.setitem(
        sys.modules,
        "websocket",
        types.SimpleNamespace(create_connection=fake_create_connection),
    )

    client = ax.AxDataClient(
        token="secret",
        api_base="http://example.test:8666",
        timeout=12.5,
    )

    with client.stream(
        "stock_quote_refresh_tdx",
        code=["000001.SZ"],
        fields="instrument_id,last_price",
        interval_ms=3000,
    ) as stream:
        event = next(stream)

    assert created == {
        "url": "ws://example.test:8666/v1/stream/stock_quote_refresh_tdx?token=secret",
        "timeout": 12.5,
        "header": ["Authorization: Bearer secret"],
    }
    assert fake_ws.sent == [
        {
            "op": "subscribe",
            "stream": "stock_quote_refresh_tdx",
            "params": {
                "code": ["000001.SZ"],
                "fields": ["instrument_id", "last_price"],
                "interval_ms": 3000,
            },
        }
    ]
    assert event.type == "subscribed"
    assert event.data == {"code": ["000001.SZ"]}
    assert fake_ws.closed is True


def test_sdk_local_session_uses_core_source_session_without_http(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    session = FakeSession()
    created = []
    calls = []

    class FakeSourceSession:
        def open(self):
            calls.append({"op": "open"})

        def close(self):
            calls.append({"op": "close"})

        def call(self, interface, *, params=None, fields=None, options=None):
            calls.append(
                {
                    "op": "call",
                    "interface": interface,
                    "params": params,
                    "fields": fields,
                    "options": options,
                }
            )
            return SourceRequestResult(
                records=[{"interface": interface, "value": len(calls)}],
                meta={"source": "tdx"},
            )

    def fake_create_source_session(*, source, data_root=None, options=None):
        created.append({"source": source, "data_root": data_root, "options": options})
        return FakeSourceSession()

    monkeypatch.setattr(axdata_core, "create_source_session", fake_create_source_session, raising=False)

    client = ax.AxDataClient(data_root=tmp_path / "data", session=session)
    with client.session(source="tdx", source_server_count=4, connections_per_server=2) as source_session:
        snapshot = source_session.call(
            "stock_realtime_snapshot_tdx",
            code=["000001.SZ", "600000.SH"],
            fields=["interface", "value"],
        )
        rank = source_session.call("stock_realtime_rank_tdx", category="a_share")

    assert session.calls == []
    assert created == [
        {
            "source": "tdx",
            "data_root": tmp_path / "data",
            "options": {"source_server_count": 4, "connections_per_server": 2},
        }
    ]
    assert calls == [
        {"op": "open"},
        {
            "op": "call",
            "interface": "stock_realtime_snapshot_tdx",
            "params": {"code": ["000001.SZ", "600000.SH"]},
            "fields": ["interface", "value"],
            "options": None,
        },
        {
            "op": "call",
            "interface": "stock_realtime_rank_tdx",
            "params": {"category": "a_share"},
            "fields": None,
            "options": None,
        },
        {"op": "close"},
    ]
    assert snapshot.to_dict(orient="records") == [
        {"interface": "stock_realtime_snapshot_tdx", "value": 2}
    ]
    assert rank.to_dict(orient="records") == [
        {"interface": "stock_realtime_rank_tdx", "value": 3}
    ]


def test_sdk_api_client_rejects_local_session():
    client = ax.AxDataClient(api_base="http://example.test")

    with pytest.raises(ax.AxDataError, match="local-only"):
        client.session(source="tdx")


def test_sdk_local_session_rejects_unsupported_source(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    client = ax.AxDataClient(data_root=tmp_path / "data")

    with pytest.raises(ax.AxDataError, match="support only"):
        with client.session(source="eastmoney"):
            pass


def test_sdk_local_stream_emits_subscribed_snapshot_and_update(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    fake_client = object()
    create_calls = []
    snapshot_calls = []
    refresh_calls = []
    sleeps = []

    class FakeSourceSession:
        tdx_client = fake_client

        def open(self):
            create_calls.append({"op": "open"})

        def close(self):
            create_calls.append({"op": "close"})

        def call(self, interface, *, params=None, fields=None, options=None):
            snapshot_calls.append(
                {
                    "interface": interface,
                    "params": params,
                    "fields": fields,
                    "options": options,
                }
            )
            return SourceRequestResult(
                records=[
                    {
                        "instrument_id": "000001.SZ",
                        "last_price": 10.2,
                    }
                ],
                meta={"source": "tdx"},
            )

    def fake_create_source_session(*, source, data_root=None, options=None):
        create_calls.append({"source": source, "data_root": data_root, "options": options})
        return FakeSourceSession()

    def fake_refresh(**kwargs):
        refresh_calls.append(kwargs)
        return [
            {
                "instrument_id": "000001.SZ",
                "last_price": 10.3,
                "_tdx_instrument_id": "000001.SZ",
                "_tdx_update_time_raw": 93001,
            }
        ]

    monkeypatch.setattr(axdata_core, "create_source_session", fake_create_source_session, raising=False)
    import axdata_core.adapters.tdx.realtime_refresh as realtime_refresh

    monkeypatch.setattr(realtime_refresh, "request_realtime_refresh_rows", fake_refresh)
    monkeypatch.setattr(sdk_client.time, "sleep", lambda seconds: sleeps.append(seconds))

    client = ax.AxDataClient(data_root=tmp_path / "data")
    with client.stream(
        "stock_quote_refresh_tdx",
        code=["000001.SZ"],
        fields="instrument_id,last_price",
        interval_ms=100,
    ) as stream:
        subscribed = next(stream)
        snapshot = next(stream)
        update = next(stream)

    assert [event.type for event in [subscribed, snapshot, update]] == [
        "subscribed",
        "snapshot",
        "update",
    ]
    assert subscribed.data == {
        "code": ["000001.SZ"],
        "fields": ["instrument_id", "last_price"],
        "interval_ms": 500,
        "initial_snapshot": True,
    }
    assert snapshot.data == [{"instrument_id": "000001.SZ", "last_price": 10.2}]
    assert update.data == [{"instrument_id": "000001.SZ", "last_price": 10.3}]
    assert sleeps == [0.5]
    assert create_calls == [
        {"source": "tdx", "data_root": tmp_path / "data", "options": {}},
        {"op": "open"},
        {"op": "close"},
    ]
    assert snapshot_calls == [
        {
            "interface": "stock_realtime_snapshot_tdx",
            "params": {"code": ["000001.SZ"]},
            "fields": ["instrument_id", "last_price"],
            "options": None,
        }
    ]
    assert refresh_calls == [
        {
            "code": ["000001.SZ"],
            "fields": ["instrument_id", "last_price"],
            "cursors": {},
            "include_internal": True,
            "client": fake_client,
        }
    ]


def test_sdk_local_stream_respects_initial_snapshot_false(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    snapshot_calls = []
    refresh_calls = []

    class FakeSourceSession:
        tdx_client = None

        def open(self):
            return None

        def close(self):
            return None

        def call(self, interface, *, params=None, fields=None, options=None):
            snapshot_calls.append(interface)
            return SourceRequestResult(records=[], meta={})

    monkeypatch.setattr(
        axdata_core,
        "create_source_session",
        lambda **kwargs: FakeSourceSession(),
        raising=False,
    )

    import axdata_core.adapters.tdx.realtime_refresh as realtime_refresh

    def fake_refresh(**kwargs):
        refresh_calls.append(kwargs)
        return [{"instrument_id": "000001.SZ", "_tdx_update_time_raw": 1}]

    monkeypatch.setattr(realtime_refresh, "request_realtime_refresh_rows", fake_refresh)
    monkeypatch.setattr(sdk_client.time, "sleep", lambda seconds: None)

    client = ax.AxDataClient(data_root=tmp_path / "data")
    with client.stream(
        "stock_quote_refresh_tdx",
        code="000001.SZ",
        initial_snapshot=False,
    ) as stream:
        subscribed = next(stream)
        update = next(stream)

    assert subscribed.type == "subscribed"
    assert subscribed.data["initial_snapshot"] is False
    assert update.type == "update"
    assert snapshot_calls == []
    assert len(refresh_calls) == 1


def test_sdk_local_stream_reports_source_open_errors(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)

    class FailingSourceSession:
        def open(self):
            raise RuntimeError("source unavailable")

    monkeypatch.setattr(
        axdata_core,
        "create_source_session",
        lambda **kwargs: FailingSourceSession(),
        raising=False,
    )

    client = ax.AxDataClient(data_root=tmp_path / "data")

    with pytest.raises(ax.AxDataError, match="source unavailable"):
        with client.stream("stock_quote_refresh_tdx", code=["000001.SZ"]):
            pass


def test_sdk_local_call_uses_core_source_request_gateway_without_http(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    session = FakeSession()
    client = ax.AxDataClient(data_root=tmp_path / "data", session=session)
    calls = []

    def fake_request_interface(interface, *, params=None, fields=None, persist=False, options=None, data_root=None):
        calls.append(
            {
                "interface": interface,
                "params": params,
                "fields": fields,
                "persist": persist,
                "options": options,
                "data_root": data_root,
            }
        )
        return SourceRequestResult(
            records=[{"code": "demo", "value": 10.5}],
            meta={"source": "custom", "persisted": False},
        )

    monkeypatch.setattr(axdata_core, "request_interface", fake_request_interface)

    df = client.call(
        "custom_interface",
        code="demo",
        fields=["code", "value"],
        options={"pool_size": 3},
    )

    assert session.calls == []
    assert calls == [
        {
            "interface": "custom_interface",
            "params": {"code": "demo"},
            "fields": ["code", "value"],
            "persist": False,
            "options": {"pool_size": 3},
            "data_root": tmp_path / "data",
        }
    ]
    assert df.to_dict(orient="records") == [{"code": "demo", "value": 10.5}]


def test_sdk_stock_basic_uses_query_channel_and_axdata_fields():
    session = FakeSession()
    client = ax.AxDataClient(token="secret", api_base="http://example.test", session=session)

    df = client.stock_basic_exchange(
        exchange="SZSE",
        industry="J 金融业",
        listing_status="listed",
        limit=100,
        fields=["instrument_id", "name", "exchange", "industry"],
    )

    assert df.to_dict(orient="records") == [
        {
            "instrument_id": "000001.SZ",
            "name": "平安银行",
            "exchange": "SZSE",
            "industry": "J 金融业",
        }
    ]
    assert session.calls[0]["url"] == "http://example.test/v1/query"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer secret"
    assert session.calls[0]["json"] == {
        "table": "stock_basic_exchange",
        "params": {
            "exchange": "SZSE",
            "industry": "J 金融业",
            "listing_status": "listed",
        },
        "fields": ["instrument_id", "name", "exchange", "industry"],
        "limit": 100,
    }


def test_sdk_stock_basic_alias_uses_exchange_table():
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    client.stock_basic(exchange="SSE", fields=["instrument_id", "name"])

    assert session.calls[0]["url"] == "http://example.test/v1/query"
    assert session.calls[0]["json"] == {
        "table": "stock_basic_exchange",
        "params": {"exchange": "SSE"},
        "fields": ["instrument_id", "name"],
        "limit": 1000,
    }


def test_sdk_api_stock_basic_expands_filters_param():
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    client.stock_basic_exchange(
        filters={"exchange": "SSE", "listing_status": "listed"},
        fields="instrument_id,name,exchange",
    )

    assert session.calls[0]["url"] == "http://example.test/v1/query"
    assert session.calls[0]["json"] == {
        "table": "stock_basic_exchange",
        "params": {},
        "fields": ["instrument_id", "name", "exchange"],
        "filters": {
            "exchange": "SSE",
            "listing_status": "listed",
        },
        "limit": 1000,
    }


def test_sdk_defaults_to_local_query_without_api_service(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    root = tmp_path / "data"
    write_core_table(
        "daily",
        pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2},
                {"ts_code": "000002.SZ", "trade_date": "20240103", "close": 20.5},
            ]
        ),
        root=root,
    )
    session = FakeSession()

    client = ax.AxDataClient(data_root=root, session=session)
    df = client.daily(
        ts_code="000001.SZ",
        start="2024-01-01",
        end_date="20240131",
        fields=["ts_code", "trade_date", "close"],
    )

    assert client.mode == "local"
    assert session.calls == []
    assert df.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]


def test_sdk_local_stock_basic_uses_axdata_core_filters(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)
    root = tmp_path / "data"
    write_core_table(
        "stock_basic_exchange",
        pd.DataFrame(
            [
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "exchange": "SZSE",
                    "asset_type": "stock",
                    "name": "平安银行",
                    "market": "主板",
                    "industry": "J 金融业",
                    "listing_status": "listed",
                },
                {
                    "instrument_id": "600000.SH",
                    "symbol": "600000",
                    "exchange": "SSE",
                    "asset_type": "stock",
                    "name": "浦发银行",
                    "market": "主板",
                    "industry": "金融业",
                    "listing_status": "listed",
                },
            ]
        ),
        root=root,
    )

    client = ax.Client.local(data_root=root)
    df = client.stock_basic(
        exchange="SSE",
        fields=["instrument_id", "symbol", "exchange", "name"],
        limit=1,
    )

    assert df.to_dict(orient="records") == [
        {
            "instrument_id": "600000.SH",
            "symbol": "600000",
            "exchange": "SSE",
            "name": "浦发银行",
        }
    ]


def test_sdk_api_mode_is_selected_by_api_base():
    session = FakeSession()
    client = ax.AxDataClient(api_base="http://example.test", session=session)

    df = client.daily(ts_code="000001.SZ", fields=["ts_code", "close"])

    assert client.mode == "api"
    assert df.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]
    assert session.calls[0]["url"] == "http://example.test/v1/query"


def test_sdk_rejects_conflicting_local_data_paths(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_BASE", raising=False)

    with pytest.raises(ValueError, match="data_root or data_dir"):
        ax.AxDataClient(data_root=tmp_path / "one", data_dir=tmp_path / "two")
