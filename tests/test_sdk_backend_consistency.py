from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

import axdata as ax
from apps.api.main import app
from axdata_core import query_table, write_core_table


DAILY_ROWS = [
    {
        "ts_code": "000001.SZ",
        "trade_date": "20240102",
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": 10.2,
        "pre_close": 10.0,
        "change": 0.2,
        "pct_chg": 2.0,
        "vol": 1000.0,
        "amount": 10200.0,
    },
    {
        "ts_code": "000001.SZ",
        "trade_date": "20240103",
        "open": 10.2,
        "high": 10.8,
        "low": 10.1,
        "close": 10.6,
        "pre_close": 10.2,
        "change": 0.4,
        "pct_chg": 3.92,
        "vol": 1200.0,
        "amount": 12600.0,
    },
    {
        "ts_code": "600000.SH",
        "trade_date": "20240102",
        "open": 8.0,
        "high": 8.3,
        "low": 7.9,
        "close": 8.1,
        "pre_close": 8.0,
        "change": 0.1,
        "pct_chg": 1.25,
        "vol": 900.0,
        "amount": 7290.0,
    },
]


TRADE_CAL_ROWS = [
    {"exchange": "SSE", "cal_date": "20240101", "is_open": 0, "pretrade_date": "20231229"},
    {"exchange": "SSE", "cal_date": "20240102", "is_open": 1, "pretrade_date": "20231229"},
    {"exchange": "SZSE", "cal_date": "20240102", "is_open": 1, "pretrade_date": "20231229"},
]


STOCK_BASIC_ROWS = [
    {
        "instrument_id": "000001.SZ",
        "symbol": "000001",
        "exchange": "SZSE",
        "asset_type": "stock",
        "name": "Ping An Bank",
        "market": "Main Board",
        "industry": "Banking",
        "region": "Shenzhen",
        "listing_status": "listed",
        "list_date": "19910403",
    },
    {
        "instrument_id": "600000.SH",
        "symbol": "600000",
        "exchange": "SSE",
        "asset_type": "stock",
        "name": "SPD Bank",
        "market": "Main Board",
        "industry": "Banking",
        "region": "Shanghai",
        "listing_status": "listed",
        "list_date": "19991110",
    },
]


def _write_sample_core(root):
    write_core_table("daily", pd.DataFrame(DAILY_ROWS), root=root)
    write_core_table("trade_cal", pd.DataFrame(TRADE_CAL_ROWS), root=root)
    write_core_table("stock_basic_exchange", pd.DataFrame(STOCK_BASIC_ROWS), root=root)


def _records(df):
    return df.to_dict(orient="records")


def _sorted_records(records, *keys):
    return sorted(records, key=lambda row: tuple(row[key] for key in keys))


def _api_client(root, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    monkeypatch.delenv("AXDATA_API_TOKEN", raising=False)
    return TestClient(app)


def test_v1_query_matches_local_duckdb_for_sdk_style_params(tmp_path, monkeypatch):
    root = tmp_path / "data"
    _write_sample_core(root)
    client = _api_client(root, monkeypatch)
    fields = ["ts_code", "trade_date", "close"]

    local = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=fields,
        start_date="20240102",
        end_date="20240103",
    )
    response = client.post(
        "/v1/query",
        json={
            "table": "daily",
            "fields": fields,
            "params": {
                "ts_code": "000001.SZ",
                "start_date": "2024-01-02",
                "end_date": "2024-01-03",
            },
        },
    )

    assert response.status_code == 200
    assert _sorted_records(response.json()["data"], "trade_date") == _sorted_records(
        _records(local),
        "trade_date",
    )
    assert response.json()["meta"] == {"table": "daily", "count": 2}


def test_query_api_matches_local_queries_for_common_tables(tmp_path, monkeypatch):
    root = tmp_path / "data"
    _write_sample_core(root)
    client = _api_client(root, monkeypatch)

    daily_response = client.post(
        "/v1/query",
        json={
            "table": "daily",
            "params": {
                "ts_code": "000001.SZ",
                "start": "2024-01-02",
                "end": "2024-01-02",
            },
            "fields": "ts_code,trade_date,close",
        },
    )
    daily_local = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=["ts_code", "trade_date", "close"],
        start_date="20240102",
        end_date="20240102",
    )

    assert daily_response.status_code == 200
    assert daily_response.json()["data"] == _records(daily_local)

    trade_cal_response = client.post(
        "/v1/query",
        json={
            "table": "trade_cal",
            "params": {
                "exchange": "SSE",
                "start_date": "2024-01-01",
                "end_date": "2024-01-02",
            },
            "fields": ["exchange", "cal_date", "is_open"],
        },
    )
    trade_cal_local = query_table(
        "trade_cal",
        root=root,
        filters={"exchange": "SSE"},
        fields=["exchange", "cal_date", "is_open"],
        start_date="20240101",
        end_date="20240102",
    )

    assert trade_cal_response.status_code == 200
    assert _sorted_records(trade_cal_response.json()["data"], "cal_date") == _sorted_records(
        _records(trade_cal_local),
        "cal_date",
    )

    stock_basic_response = client.post(
        "/v1/query",
        json={
            "table": "stock_basic_exchange",
            "params": {
                "exchange": "SSE",
                "listing_status": "listed",
            },
            "fields": "instrument_id,symbol,exchange,name",
        },
    )
    stock_basic_local = query_table(
        "stock_basic_exchange",
        root=root,
        filters={"exchange": "SSE", "listing_status": "listed"},
        fields=["instrument_id", "symbol", "exchange", "name"],
    )

    assert stock_basic_response.status_code == 200
    assert stock_basic_response.json()["data"] == _records(stock_basic_local)


def test_deleted_convenience_api_routes_are_not_registered(tmp_path, monkeypatch):
    root = tmp_path / "data"
    _write_sample_core(root)
    client = _api_client(root, monkeypatch)

    for path in (
        "/v1/daily",
        "/v1/trade_cal",
        "/v1/stock_basic_exchange",
        "/v1/stock_basic",
    ):
        assert client.get(path).status_code == 404


def test_sdk_api_backend_daily_matches_api_and_local_query(tmp_path, monkeypatch):
    root = tmp_path / "data"
    _write_sample_core(root)
    api_session = _api_client(root, monkeypatch)
    sdk = ax.AxDataClient(api_base="http://testserver", session=api_session)
    fields = ["ts_code", "trade_date", "open", "close"]

    sdk_df = sdk.daily(
        ts_code="000001.SZ",
        start_date="2024-01-02",
        end_date="2024-01-03",
        fields=fields,
    )
    api_response = api_session.post(
        "/v1/query",
        json={
            "table": "daily",
            "fields": fields,
            "params": {
                "ts_code": "000001.SZ",
                "start_date": "2024-01-02",
                "end_date": "2024-01-03",
            },
        },
    )
    local = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=fields,
        start_date="20240102",
        end_date="20240103",
    )

    assert api_response.status_code == 200
    assert _sorted_records(_records(sdk_df), "trade_date") == _sorted_records(
        api_response.json()["data"],
        "trade_date",
    )
    assert _sorted_records(_records(sdk_df), "trade_date") == _sorted_records(
        _records(local),
        "trade_date",
    )


def test_sdk_first_convenience_methods_match_local_queries(tmp_path, monkeypatch):
    root = tmp_path / "data"
    _write_sample_core(root)
    api_session = _api_client(root, monkeypatch)
    sdk = ax.AxDataClient(api_base="http://testserver", session=api_session)

    stock_basic = sdk.stock_basic_exchange(
        exchange="SZSE",
        listing_status="listed",
        fields=["instrument_id", "symbol", "exchange", "name"],
    )
    stock_basic_local = query_table(
        "stock_basic_exchange",
        root=root,
        filters={"exchange": "SZSE", "listing_status": "listed"},
        fields=["instrument_id", "symbol", "exchange", "name"],
    )

    assert _records(stock_basic) == _records(stock_basic_local)

    trade_cal = sdk.trade_cal(
        exchange="SSE",
        start_date="20240101",
        end_date="20240102",
        fields=["exchange", "cal_date", "is_open"],
    )
    trade_cal_local = query_table(
        "trade_cal",
        root=root,
        filters={"exchange": "SSE"},
        fields=["exchange", "cal_date", "is_open"],
        start_date="20240101",
        end_date="20240102",
    )

    assert _sorted_records(_records(trade_cal), "cal_date") == _sorted_records(
        _records(trade_cal_local),
        "cal_date",
    )


class NoHttpSession:
    def get(self, *args, **kwargs):
        raise AssertionError("local SDK backend must not issue HTTP GET requests")

    def post(self, *args, **kwargs):
        raise AssertionError("local SDK backend must not issue HTTP POST requests")


def test_sdk_local_backend_contract_matches_local_duckdb_without_http(tmp_path):
    root = tmp_path / "data"
    _write_sample_core(root)
    expected = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=["ts_code", "trade_date", "close"],
        start_date="20240102",
        end_date="20240103",
    )

    sdk = ax.AxDataClient(backend="local", data_dir=root, session=NoHttpSession())
    result = sdk.daily(
        ts_code="000001.SZ",
        start_date="20240102",
        end_date="20240103",
        fields=["ts_code", "trade_date", "close"],
    )

    assert _sorted_records(_records(result), "trade_date") == _sorted_records(
        _records(expected),
        "trade_date",
    )
