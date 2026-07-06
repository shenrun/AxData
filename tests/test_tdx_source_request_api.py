from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import apps.api.main as api_main
from apps.api.main import app
from axdata_core import SourceRequestResult
from axdata_core.sources import list_request_interfaces as list_builtin_request_interfaces
from tests.tdx_plugin_helpers import build_registry_with_local_tdx_plugins, ensure_local_tdx_plugin_paths

ensure_local_tdx_plugin_paths()

TDX_SOURCE_INTERFACE_COUNT = 90
TDX_EXT_SOURCE_INTERFACE_COUNT = 31


@pytest.fixture(autouse=True)
def _enable_local_tdx_plugins(monkeypatch):
    import axdata_core
    import axdata_core.provider_catalog as provider_catalog

    base_builder = provider_catalog.build_builtin_provider_registry

    def build_registry(**kwargs):
        return build_registry_with_local_tdx_plugins(
            base_builder=base_builder,
            **kwargs,
        )

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", build_registry)
    if "build_builtin_provider_registry" in axdata_core.__dict__:
        monkeypatch.setattr(axdata_core, "build_builtin_provider_registry", build_registry)


def test_request_interfaces_catalog_lists_stock_codes_tdx():
    client = TestClient(app)

    response = client.get("/v1/request/interfaces")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    names = [item["name"] for item in payload["data"]]
    display_names = {item["name"]: item["display_name_zh"] for item in payload["data"]}
    source_codes = {item["source_code"] for item in payload["data"]}
    assert "stock_codes_tdx" in names
    assert "stock_st_list_tdx" in names
    assert "stock_suspensions_tdx" in names
    assert "stock_daily_share_tdx" in names
    assert "stock_daily_price_limit_tdx" in names
    assert "stock_trade_calendar_exchange" in names
    assert "stock_historical_list_exchange" in names
    assert "stock_basic_info_exchange" in names
    assert "stock_capital_changes_tdx" in names
    assert "stock_adj_factor_tdx" in names
    assert "stock_limit_ladder_tdx" in names
    assert "stock_theme_strength_rank_tdx" in names
    assert "stock_realtime_rank_tdx" in names
    assert "stock_realtime_snapshot_tdx" in names
    assert "stock_order_book_tdx" in names
    assert "stock_intraday_buy_sell_strength_tdx" in names
    assert "stock_intraday_volume_comparison_tdx" in names
    assert "stock_auction_process_tdx" in names
    assert "stock_auction_result_tdx" in names
    assert "stock_auction_result_history_tdx" in names
    assert "stock_shortline_indicators_tdx" in names
    assert "stock_intraday_today_tdx" in names
    assert "stock_intraday_history_tdx" in names
    assert "stock_intraday_recent_history_tdx" in names
    assert "stock_trades_today_tdx" in names
    assert "stock_trades_history_tdx" in names
    assert "stock_finance_summary_tdx" in names
    assert "stock_share_capital_tdx" in names
    assert "stock_balance_summary_tdx" in names
    assert "stock_profit_cashflow_summary_tdx" in names
    assert "stock_finance_profile_tdx" in names
    assert "stock_kline_second_tdx" in names
    assert "stock_kline_yearly_tdx" in names
    assert "stock_company_profile_tdx" in names
    assert "stock_disclosure_feed_tdx" in names
    assert "stock_valuation_metrics_tdx" in names
    assert "futures_realtime_snapshot_tdx" in names
    assert "futures_kline_tdx" in names
    assert "futures_trades_today_tdx" in names
    assert "futures_trades_history_tdx" in names
    assert "option_chain_tdx" in names
    assert "option_realtime_snapshot_tdx" in names
    assert "option_trades_today_tdx" not in names
    assert "option_trades_history_tdx" not in names
    assert "fund_nav_tdx" in names
    assert "bond_realtime_snapshot_tdx" in names
    assert "fx_realtime_snapshot_tdx" in names
    assert "fx_trades_today_tdx" in names
    assert "fx_trades_history_tdx" in names
    assert "macro_indicator_snapshot_tdx" in names
    assert "cninfo_announcements" in names
    assert "cninfo_announcement_detail" in names
    assert "tencent_realtime_snapshot" in names
    assert "eastmoney_dragon_tiger_daily" in names
    assert "eastmoney_margin_trading" in names
    assert "eastmoney_research_reports" in names
    assert source_codes <= {"tdx", "tdx_ext", "exchange", "cninfo", "tencent", "eastmoney", "sina", "cls", "kph"}
    assert display_names["stock_codes_tdx"] == "最新股票列表"
    assert display_names["stock_st_list_tdx"] == "最新ST股票列表"
    assert display_names["stock_suspensions_tdx"] == "最新停牌列表"
    assert display_names["stock_daily_share_tdx"] == "每日股本（盘前）"
    assert display_names["stock_daily_price_limit_tdx"] == "涨跌停价格"
    assert display_names["stock_trade_calendar_exchange"] == "交易日历"
    assert display_names["stock_historical_list_exchange"] == "历史股票列表"
    assert display_names["stock_basic_info_exchange"] == "股票基础信息"
    assert display_names["stock_capital_changes_tdx"] == "股本变迁"
    assert display_names["stock_adj_factor_tdx"] == "复权因子"
    assert display_names["stock_limit_ladder_tdx"] == "连板天梯"
    assert display_names["stock_theme_strength_rank_tdx"] == "题材强度排行"
    assert display_names["stock_realtime_rank_tdx"] == "实时榜单"
    assert display_names["stock_realtime_snapshot_tdx"] == "实时快照"
    assert display_names["stock_order_book_tdx"] == "五档盘口"
    assert display_names["stock_intraday_buy_sell_strength_tdx"] == "买卖力道"
    assert display_names["stock_intraday_volume_comparison_tdx"] == "成交对比"
    assert display_names["stock_auction_process_tdx"] == "竞价明细"
    assert display_names["stock_auction_result_tdx"] == "竞价结果"
    assert display_names["stock_auction_result_history_tdx"] == "历史竞价结果"
    assert display_names["stock_shortline_indicators_tdx"] == "短线指标"
    assert display_names["stock_intraday_today_tdx"] == "当日分时"
    assert display_names["stock_intraday_history_tdx"] == "历史分时"
    assert display_names["stock_intraday_recent_history_tdx"] == "近期历史分时"
    assert display_names["stock_trades_today_tdx"] == "当日成交明细"
    assert display_names["stock_trades_history_tdx"] == "历史成交明细"
    assert display_names["stock_finance_summary_tdx"] == "财务基础摘要"
    assert display_names["stock_share_capital_tdx"] == "股本结构"
    assert display_names["stock_balance_summary_tdx"] == "资产负债摘要"
    assert display_names["stock_profit_cashflow_summary_tdx"] == "利润现金流摘要"
    assert display_names["stock_finance_profile_tdx"] == "财务资料标签"
    assert display_names["stock_kline_second_tdx"] == "秒K线"
    assert display_names["stock_company_profile_tdx"] == "公司概况"
    assert display_names["stock_disclosure_feed_tdx"] == "新闻公告路演"
    assert display_names["stock_event_drivers_tdx"] == "历史事件关联"
    assert display_names["stock_valuation_metrics_tdx"] == "估值表"
    assert display_names["futures_realtime_snapshot_tdx"] == "期货实时快照"
    assert display_names["futures_trades_today_tdx"] == "期货当日逐笔"
    assert display_names["futures_trades_history_tdx"] == "期货历史逐笔"
    assert display_names["option_chain_tdx"] == "期权T型报价"
    assert display_names["fund_nav_tdx"] == "基金净值"
    assert display_names["fx_trades_today_tdx"] == "外汇当日逐笔"
    assert display_names["fx_trades_history_tdx"] == "外汇历史逐笔"
    assert display_names["macro_indicator_snapshot_tdx"] == "宏观指标快照"
    assert display_names["cninfo_announcements"] == "公告列表"
    assert display_names["cninfo_announcement_detail"] == "公告PDF元信息"
    assert display_names["tencent_realtime_snapshot"] == "实时快照"
    assert display_names["eastmoney_dragon_tiger_daily"] == "龙虎榜每日汇总"
    assert display_names["eastmoney_margin_trading"] == "融资融券明细"
    assert display_names["eastmoney_research_reports"] == "个股研报列表"
    expected_count = (
        TDX_SOURCE_INTERFACE_COUNT
        + TDX_EXT_SOURCE_INTERFACE_COUNT
        + len(list_builtin_request_interfaces())
    )
    assert payload["meta"]["count"] == expected_count
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False


def test_request_stock_codes_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_codes_tdx"
        assert params == {"scope": "all"}
        assert fields == ["instrument_id", "name"]
        assert persist is False
        return SourceRequestResult(
            records=[{"instrument_id": "000001.SZ", "name": "平安银行"}],
            meta={
                "source": "tdx",
                "tdx_connected_host": "127.0.0.1:7709",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_codes_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [{"instrument_id": "000001.SZ", "name": "平安银行"}]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_connected_host"] == "127.0.0.1:7709"
    assert payload["meta"]["count"] == 1


def test_request_stock_suspensions_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_suspensions_tdx"
        assert params == {"scope": "all"}
        assert fields == ["instrument_id", "name"]
        assert persist is False
        return SourceRequestResult(
            records=[{"instrument_id": "000004.SZ", "name": "*ST国华"}],
            meta={
                "source": "tdx",
                "tdx_status_source": "tdx_0x053e",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_suspensions_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [{"instrument_id": "000004.SZ", "name": "*ST国华"}]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_status_source"] == "tdx_0x053e"


def test_request_stock_st_list_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_st_list_tdx"
        assert params == {"scope": "all"}
        assert fields == ["instrument_id", "name", "st_type"]
        assert persist is False
        return SourceRequestResult(
            records=[{"instrument_id": "000004.SZ", "name": "*ST国华", "st_type": "*ST"}],
            meta={
                "source": "tdx",
                "tdx_st_count": 1,
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_st_list_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name", "st_type"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [{"instrument_id": "000004.SZ", "name": "*ST国华", "st_type": "*ST"}]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_st_count"] == 1


def test_request_stock_historical_list_exchange_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_historical_list_exchange"
        assert params == {"trade_date": "20240102", "exchange": "SZSE"}
        assert fields == ["trade_date", "instrument_id", "name", "delist_date"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {"trade_date": "20240102", "instrument_id": "000001.SZ", "name": "平安银行", "delist_date": None},
                {"trade_date": "20240102", "instrument_id": "000005.SZ", "name": "ST星源", "delist_date": "20240426"},
            ],
            meta={
                "source": "exchange",
                "trade_date": "20240102",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_historical_list_exchange",
        json={
            "params": {"trade_date": "20240102", "exchange": "SZSE"},
            "fields": ["trade_date", "instrument_id", "name", "delist_date"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {"trade_date": "20240102", "instrument_id": "000001.SZ", "name": "平安银行", "delist_date": None},
        {"trade_date": "20240102", "instrument_id": "000005.SZ", "name": "ST星源", "delist_date": "20240426"},
    ]
    assert payload["meta"]["source"] == "exchange"
    assert payload["meta"]["trade_date"] == "20240102"


def test_request_stock_basic_info_exchange_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_basic_info_exchange"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "name", "industry", "total_share"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "name": "平安银行",
                    "industry": "J 金融业",
                    "total_share": 194.05,
                }
            ],
            meta={
                "source": "exchange",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_basic_info_exchange",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "name", "industry", "total_share"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "name": "平安银行",
            "industry": "J 金融业",
            "total_share": 194.05,
        }
    ]
    assert payload["meta"]["source"] == "exchange"


def test_request_stock_kline_second_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_kline_second_tdx"
        assert params == {"code": "000001.SZ", "seconds": 5}
        assert fields == ["instrument_id", "trade_time", "close"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "trade_time": "2026-05-19T13:39:50+08:00",
                    "close": 10.14,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x052d",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_kline_second_tdx",
        json={
            "params": {"code": "000001.SZ", "seconds": 5},
            "fields": ["instrument_id", "trade_time", "close"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "trade_time": "2026-05-19T13:39:50+08:00",
            "close": 10.14,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x052d"


def test_request_stock_adj_factor_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_adj_factor_tdx"
        assert params == {"code": "000001.SZ", "adjust": "qfq"}
        assert fields == ["ts_code", "trade_date", "adj_factor"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20240531",
                    "adj_factor": 0.825,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x000f+0x052d",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_adj_factor_tdx",
        json={
            "params": {"code": "000001.SZ", "adjust": "qfq"},
            "fields": ["ts_code", "trade_date", "adj_factor"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [{"ts_code": "000001.SZ", "trade_date": "20240531", "adj_factor": 0.825}]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x000f+0x052d"


def test_request_stock_intraday_volume_comparison_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_intraday_volume_comparison_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "minute_index", "today_volume", "volume_change_pct"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "minute_index": 0,
                    "today_volume": 105552.0,
                    "volume_change_pct": 78.438963,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x051b",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_intraday_volume_comparison_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "minute_index", "today_volume", "volume_change_pct"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "minute_index": 0,
            "today_volume": 105552.0,
            "volume_change_pct": 78.438963,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x051b"


def test_request_stock_intraday_history_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_intraday_history_tdx"
        assert params == {"code": "000001.SZ", "trade_date": "20260519"}
        assert fields == ["instrument_id", "trade_time", "price", "volume"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "trade_time": "2026-05-19T09:31:00+08:00",
                    "price": 10.13,
                    "volume": 120,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0fb4",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_intraday_history_tdx",
        json={
            "params": {"code": "000001.SZ", "trade_date": "20260519"},
            "fields": ["instrument_id", "trade_time", "price", "volume"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "trade_time": "2026-05-19T09:31:00+08:00",
            "price": 10.13,
            "volume": 120,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0fb4"


def test_request_stock_intraday_recent_history_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_intraday_recent_history_tdx"
        assert params == {"code": "000001.SZ", "trade_date": "20260519"}
        assert fields == ["instrument_id", "time_label", "price", "avg_price", "open_price"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "time_label": "09:31",
                    "price": 10.13,
                    "avg_price": 10.115,
                    "open_price": 10.12,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0feb",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_intraday_recent_history_tdx",
        json={
            "params": {"code": "000001.SZ", "trade_date": "20260519"},
            "fields": ["instrument_id", "time_label", "price", "avg_price", "open_price"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "time_label": "09:31",
            "price": 10.13,
            "avg_price": 10.115,
            "open_price": 10.12,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0feb"


def test_request_stock_intraday_today_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_intraday_today_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "time_label", "price", "avg_price", "volume"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "time_label": "09:31",
                    "price": 10.86,
                    "avg_price": 10.8417,
                    "volume": 120,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0537",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_intraday_today_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "time_label", "price", "avg_price", "volume"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "time_label": "09:31",
            "price": 10.86,
            "avg_price": 10.8417,
            "volume": 120,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0537"


def test_request_stock_trades_today_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_trades_today_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "trade_time", "price", "volume", "side"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "trade_time": "14:08",
                    "price": 10.86,
                    "volume": 89,
                    "side": "buy",
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0fc5",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_trades_today_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "trade_time", "price", "volume", "side"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "trade_time": "14:08",
            "price": 10.86,
            "volume": 89,
            "side": "buy",
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0fc5"


def test_request_stock_realtime_snapshot_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_realtime_snapshot_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "last_price", "change_pct", "bid1_price", "ask1_price"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "last_price": 10.14,
                    "change_pct": -1.361868,
                    "bid1_price": 10.13,
                    "ask1_price": 10.14,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x054c",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_realtime_snapshot_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "last_price", "change_pct", "bid1_price", "ask1_price"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "last_price": 10.14,
            "change_pct": -1.361868,
            "bid1_price": 10.13,
            "ask1_price": 10.14,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x054c"


def test_request_stock_realtime_rank_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_realtime_rank_tdx"
        assert params == {
            "category": "a_share",
            "sort": "change_pct",
            "count": "all",
        }
        assert fields == ["rank", "instrument_id", "last_price", "change_pct"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "rank": 1,
                    "instrument_id": "000001.SZ",
                    "last_price": 10.14,
                    "change_pct": -1.361868,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x054b",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_realtime_rank_tdx",
        json={
            "params": {"category": "a_share", "sort": "change_pct", "count": "all"},
            "fields": ["rank", "instrument_id", "last_price", "change_pct"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "rank": 1,
            "instrument_id": "000001.SZ",
            "last_price": 10.14,
            "change_pct": -1.361868,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x054b"


def test_request_stock_limit_ladder_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_limit_ladder_tdx"
        assert params == {
            "count": 2,
            "include_touched": True,
        }
        assert fields == ["instrument_id", "ladder_level", "limit_status"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "ladder_level": 4,
                    "limit_status": "sealed",
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x054b+tdxstat",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_limit_ladder_tdx",
        json={
            "params": {"count": 2, "include_touched": True},
            "fields": ["instrument_id", "ladder_level", "limit_status"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "ladder_level": 4,
            "limit_status": "sealed",
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x054b+tdxstat"


def test_request_stock_theme_strength_rank_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_theme_strength_rank_tdx"
        assert params == {
            "count": 2,
            "scope": "all",
        }
        assert fields == ["rank", "topic_name", "limit_up_count"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "rank": 1,
                    "topic_name": "机器人",
                    "limit_up_count": 3,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x054b+tdxstat+7615",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_theme_strength_rank_tdx",
        json={
            "params": {"count": 2, "scope": "all"},
            "fields": ["rank", "topic_name", "limit_up_count"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "rank": 1,
            "topic_name": "机器人",
            "limit_up_count": 3,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x054b+tdxstat+7615"


def test_request_stock_auction_process_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_auction_process_tdx"
        assert params == {"code": "000988.SZ"}
        assert fields == ["instrument_id", "auction_time", "price", "matched_volume"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000988.SZ",
                    "auction_time": "09:15:00",
                    "price": 162.12,
                    "matched_volume": 2568,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x056a",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_auction_process_tdx",
        json={
            "params": {"code": "000988.SZ"},
            "fields": ["instrument_id", "auction_time", "price", "matched_volume"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000988.SZ",
            "auction_time": "09:15:00",
            "price": 162.12,
            "matched_volume": 2568,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x056a"


def test_request_stock_auction_result_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_auction_result_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "auction_time", "price", "volume", "amount"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "auction_time": "09:25",
                    "price": 10.86,
                    "volume": 1200,
                    "amount": 1303200.0,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0fc5",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_auction_result_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "auction_time", "price", "volume", "amount"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "auction_time": "09:25",
            "price": 10.86,
            "volume": 1200,
            "amount": 1303200.0,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0fc5"


def test_request_stock_auction_result_history_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_auction_result_history_tdx"
        assert params == {"code": "000001.SZ", "trade_date": "20260511"}
        assert fields == ["instrument_id", "auction_datetime", "price", "volume", "amount"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "auction_datetime": "2026-05-11T09:25:00+08:00",
                    "price": 10.86,
                    "volume": 1200,
                    "amount": 1303200.0,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0fc6",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_auction_result_history_tdx",
        json={
            "params": {"code": "000001.SZ", "trade_date": "20260511"},
            "fields": ["instrument_id", "auction_datetime", "price", "volume", "amount"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "auction_datetime": "2026-05-11T09:25:00+08:00",
            "price": 10.86,
            "volume": 1200,
            "amount": 1303200.0,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0fc6"


def test_request_stock_shortline_indicators_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_shortline_indicators_tdx"
        assert params == {"code": "000001.SZ", "refresh_stats": True}
        assert fields == ["instrument_id", "open_amount", "open_volume_ratio"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "open_amount": 10000.0,
                    "open_volume_ratio": 0.987167,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x054c+0x052d+0x0010+tdxstat",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_shortline_indicators_tdx",
        json={
            "params": {"code": "000001.SZ", "refresh_stats": True},
            "fields": ["instrument_id", "open_amount", "open_volume_ratio"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "open_amount": 10000.0,
            "open_volume_ratio": 0.987167,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x054c+0x052d+0x0010+tdxstat"


def test_request_stock_daily_share_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_daily_share_tdx"
        assert params == {"code": "000001.SZ", "refresh_stats": True}
        assert fields == ["trade_date", "instrument_id", "total_share", "free_float_share_z"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "trade_date": "20260612",
                    "instrument_id": "000001.SZ",
                    "total_share": 19405918750.0,
                    "free_float_share_z": 8160481200.0,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0010+tdxstat",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_daily_share_tdx",
        json={
            "params": {"code": "000001.SZ", "refresh_stats": True},
            "fields": ["trade_date", "instrument_id", "total_share", "free_float_share_z"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "trade_date": "20260612",
            "instrument_id": "000001.SZ",
            "total_share": 19405918750.0,
            "free_float_share_z": 8160481200.0,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0010+tdxstat"


def test_request_stock_daily_price_limit_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_daily_price_limit_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["trade_date", "instrument_id", "pre_close_trade_date", "limit_up_price", "limit_down_price", "limit_rule"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "trade_date": "20260617",
                    "instrument_id": "000001.SZ",
                    "pre_close_trade_date": "20260616",
                    "limit_up_price": 12.03,
                    "limit_down_price": 9.85,
                    "limit_rule": "main_10pct",
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x052d+tdxstat",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_daily_price_limit_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["trade_date", "instrument_id", "pre_close_trade_date", "limit_up_price", "limit_down_price", "limit_rule"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "trade_date": "20260617",
            "instrument_id": "000001.SZ",
            "pre_close_trade_date": "20260616",
            "limit_up_price": 12.03,
            "limit_down_price": 9.85,
            "limit_rule": "main_10pct",
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x052d+tdxstat"


def test_request_stock_trades_history_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_trades_history_tdx"
        assert params == {"code": "000001.SZ", "trade_date": "20260511"}
        assert fields == ["instrument_id", "trade_datetime", "price", "volume", "side"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "trade_datetime": "2026-05-11T14:12:00+08:00",
                    "price": 10.86,
                    "volume": 89,
                    "side": "buy",
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0fc6",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_trades_history_tdx",
        json={
            "params": {"code": "000001.SZ", "trade_date": "20260511"},
            "fields": ["instrument_id", "trade_datetime", "price", "volume", "side"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "trade_datetime": "2026-05-11T14:12:00+08:00",
            "price": 10.86,
            "volume": 89,
            "side": "buy",
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0fc6"


def test_request_stock_capital_changes_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_capital_changes_tdx"
        assert params == {"code": "000001.SZ", "category": "xdxr"}
        assert fields == ["ts_code", "event_date", "category_name", "c1"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "ts_code": "000001.SZ",
                    "event_date": "20240614",
                    "category_name": "除权除息",
                    "c1": 7.19,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x000f",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_capital_changes_tdx",
        json={
            "params": {"code": "000001.SZ", "category": "xdxr"},
            "fields": ["ts_code", "event_date", "category_name", "c1"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "ts_code": "000001.SZ",
            "event_date": "20240614",
            "category_name": "除权除息",
            "c1": 7.19,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x000f"


def test_request_stock_finance_summary_tdx_uses_gateway(monkeypatch):
    def fake_request_interface(interface_name, *, params, fields, persist, data_root=None):
        assert interface_name == "stock_finance_summary_tdx"
        assert params == {"code": "000001.SZ"}
        assert fields == ["instrument_id", "updated_date", "net_profit"]
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "updated_date": "20260425",
                    "net_profit": 14523000000.0,
                }
            ],
            meta={
                "source": "tdx",
                "tdx_protocol": "0x0010",
                "persisted": False,
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_finance_summary_tdx",
        json={
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "updated_date", "net_profit"],
            "persist": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == [
        {
            "instrument_id": "000001.SZ",
            "updated_date": "20260425",
            "net_profit": 14523000000.0,
        }
    ]
    assert payload["meta"]["source"] == "tdx"
    assert payload["meta"]["tdx_protocol"] == "0x0010"


def test_request_unknown_interface_returns_404_before_gateway(monkeypatch):
    def fake_request_interface(*args, **kwargs):
        raise AssertionError("gateway should not be called for unknown catalog entries")

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post("/v1/request/custom_interface", json={"params": {}})

    assert response.status_code == 404
    assert "custom_interface" in response.json()["detail"]


def test_request_unknown_interface_does_not_write_data_layers(tmp_path, monkeypatch):
    data_root = tmp_path / "data"

    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    client = TestClient(app)

    response = client.post(
        "/v1/request/custom_interface",
        json={"params": {"code": "demo"}, "persist": False},
    )

    assert response.status_code == 404
    assert not any((data_root / layer).exists() for layer in ("raw", "staging", "core", "factor"))
