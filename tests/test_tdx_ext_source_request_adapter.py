from __future__ import annotations

import struct
import threading
import time
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from axdata_core import get_request_interface, list_registry_interface_dicts, request_interface
from axdata_core.adapters.tdx_ext.request import TdxExtRequestAdapter
from axdata_core.adapters.tdx_ext.local_cache import INSTRUMENT_RECORD_HEADER_SIZE, INSTRUMENT_RECORD_SIZE
from axdata_core.source_errors import SourceRequestValidationError
from axdata_core.source_request import registry_adapter_for_interface
from tests.tdx_plugin_helpers import build_registry_with_local_tdx_plugins, ensure_local_tdx_plugin_paths

ensure_local_tdx_plugin_paths()


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


@dataclass(frozen=True)
class _Level:
    price: float | None
    volume: int | None


@dataclass(frozen=True)
class _Quote:
    market: int
    code: str
    trade_date: str | None
    last_price: float | None
    pre_close: float | None = None
    pre_settlement: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    settlement: float | None = None
    average_price: float | None = None
    volume: int | None = None
    amount: float | None = None
    open_interest: int | None = None
    open_interest_change: int | None = None
    inside_volume: int | None = None
    outside_volume: int | None = None
    bid_levels: tuple[_Level, ...] = (_Level(None, None),)
    ask_levels: tuple[_Level, ...] = (_Level(None, None),)


@dataclass(frozen=True)
class _Trade:
    trade_date: str | None
    time_label: str
    price: float
    volume: int
    position_change: int
    direction_marker: int = 0


@dataclass(frozen=True)
class _Bar:
    trade_time: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: int | None = None
    settlement: float | None = None


def _write_text(path, text: str) -> None:
    path.write_bytes(text.encode("gbk"))


def _market_record(category: int, market: int, name: str, short_name: str) -> bytes:
    return struct.pack(
        "<B32sB2s26s2s",
        category,
        name.encode("gbk").ljust(32, b"\x00"),
        market,
        short_name.encode("ascii").ljust(2, b"\x00"),
        b"\x00" * 26,
        b"\x00" * 2,
    )


def _instrument_record(category: int, market: int, subtype: int, symbol: str, sort_key: int = 1) -> bytes:
    record = bytearray(INSTRUMENT_RECORD_SIZE)
    record[0] = category
    record[1] = market
    record[2] = subtype
    encoded = symbol.encode("ascii")
    record[5 : 5 + len(encoded)] = encoded
    record[88:90] = int(sort_key).to_bytes(2, "little")
    return bytes(record)


def _build_cache_root(tmp_path):
    root = tmp_path / "tdx"
    hq_cache = root / "T0002" / "hq_cache"
    hq_cache.mkdir(parents=True)
    _write_text(
        root / "dsmarket.dat",
        "\n".join(
            [
                "[GUISet]",
                "GUIMarket01=期货现货",
                "GUIMarketSet01=47",
                "GUIMarketName01=中金所期货",
                "GUIMarket02=期权",
                "GUIMarketSet02=4",
                "GUIMarketName02=郑州商品期权",
                "GUIMarket03=基金理财",
                "GUIMarketSet03=33",
                "GUIMarketName03=开放式基金",
                "GUIMarket04=其它",
                "GUIMarketSet04=38,91",
                "GUIMarketName04=宏观指标,资金市场",
                "GUIMarket05=环球行情",
                "GUIMarketSet05=10",
                "GUIMarketName05=基本汇率",
            ]
        ),
    )
    (hq_cache / "ds_mrk.dat").write_bytes(
        b"".join(
            [
                _market_record(3, 47, "中金所", "JZ"),
                _market_record(12, 4, "郑州商品期权", "OZ"),
                _market_record(8, 33, "开放式基金", "JF"),
                _market_record(7, 91, "资金市场", "ZJ"),
                _market_record(4, 10, "基本汇率", "FE"),
                _market_record(10, 38, "宏观指标", "HI"),
            ]
        )
    )
    (hq_cache / "ds_stk.dat").write_bytes(
        b"\x00" * INSTRUMENT_RECORD_HEADER_SIZE
        + _instrument_record(3, 47, 1, "IC2606")
        + _instrument_record(12, 4, 1, "AP2610-C-10000")
        + _instrument_record(12, 4, 1, "AP2610-P-10000")
        + _instrument_record(8, 33, 4, "159007")
        + _instrument_record(7, 91, 4, "10YGB")
        + _instrument_record(4, 10, 5, "USDCNY")
        + _instrument_record(10, 38, 2, "1_GDP")
    )
    _write_text(
        hq_cache / "code2name.ini",
        "IC,中证,CZ,1,2606,20260622,200,0.2000,10.00,12.00,0.2300,万分之,元\n",
    )
    _write_text(
        hq_cache / "code2name_qq.ini",
        "AP,苹果,OZ,1,2610,20261020,10,1.0000,5,,1.0000,元/手,吨\n",
    )
    _write_text(hq_cache / "specjjdata.txt", "159007,0,,20260617,20560.32,0.7922\n")
    return root


def test_tdx_ext_catalog_registers_interfaces():
    entries = {
        entry["name"]: entry
        for entry in list_registry_interface_dicts()
    }
    names = tuple(entries)
    for interface_name in (
        "tdx_ext_markets_tdx",
        "tdx_ext_instruments_tdx",
        "futures_contracts_tdx",
        "futures_realtime_snapshot_tdx",
        "futures_kline_tdx",
        "futures_intraday_today_tdx",
        "futures_intraday_history_tdx",
        "futures_trades_today_tdx",
        "futures_trades_history_tdx",
        "option_contracts_tdx",
        "option_chain_tdx",
        "option_realtime_snapshot_tdx",
        "option_kline_tdx",
        "option_intraday_today_tdx",
        "option_intraday_history_tdx",
        "fund_codes_tdx",
        "fund_nav_tdx",
        "fund_nav_series_tdx",
        "bond_codes_tdx",
        "bond_realtime_snapshot_tdx",
        "bond_kline_tdx",
        "fx_codes_tdx",
        "fx_realtime_snapshot_tdx",
        "fx_kline_tdx",
        "fx_intraday_today_tdx",
        "fx_intraday_history_tdx",
        "fx_trades_today_tdx",
        "fx_trades_history_tdx",
        "macro_indicators_tdx",
        "macro_indicator_snapshot_tdx",
        "macro_indicator_series_tdx",
    ):
        assert interface_name in names

    futures = entries["futures_contracts_tdx"]
    assert futures["display_name_zh"] == "期货合约列表"
    assert futures["source_code"] == "tdx_ext"
    assert futures["category"] == "期货数据"
    assert "product_name" in {field["name"] for field in futures["fields"]}
    assert "last_price" not in {field["name"] for field in futures["fields"]}
    assert "protocol" not in futures["description"].lower()

    snapshot = entries["futures_realtime_snapshot_tdx"]
    assert tuple(parameter["name"] for parameter in snapshot["parameters"]) == ("code", "tdx_root")
    assert "open_interest" in {field["name"] for field in snapshot["fields"]}
    assert "bid1_price" in {field["name"] for field in snapshot["fields"]}

    macro_series = entries["macro_indicator_series_tdx"]
    assert macro_series["category"] == "宏观数据"
    assert "value" in {field["name"] for field in macro_series["fields"]}
    assert "unit" in {field["name"] for field in macro_series["fields"]}
    assert "frequency" in {field["name"] for field in macro_series["fields"]}


def test_adapter_for_interface_routes_tdx_ext_before_plain_tdx():
    adapter = registry_adapter_for_interface(
        "futures_contracts_tdx",
        options={"source_server_count": 2, "connections_per_server": 2},
    )

    assert adapter.source == "tdx_ext"
    assert adapter.provider_adapter.options == {"source_server_count": 2, "connections_per_server": 2}
    legacy_adapter = adapter.provider_adapter._adapter_for_call(None)
    assert isinstance(legacy_adapter, TdxExtRequestAdapter)
    assert legacy_adapter._options == {"source_server_count": 2, "connections_per_server": 2}


def test_tdx_ext_adapter_supports_declared_interface_set():
    from axdata_core.adapters.tdx_ext.interface_sets import SUPPORTED_INTERFACES

    adapter = TdxExtRequestAdapter()

    assert {name for name in SUPPORTED_INTERFACES if adapter.supports(name)} == SUPPORTED_INTERFACES
    assert adapter.supports("community_shadow_tdx") is False


def test_tdx_ext_request_interface_returns_futures_contracts(tmp_path):
    root = _build_cache_root(tmp_path)

    result = request_interface("futures_contracts_tdx", params={"tdx_root": str(root), "limit": 5})

    assert result.meta["source"] == "tdx_ext"
    assert result.records == [
        {
            "instrument_id": "IC2606.CFFEX",
            "symbol": "IC2606",
            "asset_type": "futures",
            "exchange": "CFFEX",
            "market_name": "中金所期货",
            "market_group": "期货现货",
            "product_code": "IC",
            "product_name": "中证",
            "contract_month": "202606",
            "contract_type": "contract",
        }
    ]


def test_tdx_ext_request_interface_returns_all_asset_lists(tmp_path):
    root = _build_cache_root(tmp_path)

    assert request_interface("option_contracts_tdx", params={"tdx_root": str(root)}).records[0]["option_type"] == "call"
    assert request_interface("fund_codes_tdx", params={"tdx_root": str(root)}).records[0]["nav"] == 0.7922
    assert request_interface("bond_codes_tdx", params={"tdx_root": str(root)}).records[0]["bond_type"] == "资金市场"
    assert request_interface("fx_codes_tdx", params={"tdx_root": str(root)}).records[0]["quote_currency"] == "CNY"
    assert request_interface("macro_indicators_tdx", params={"tdx_root": str(root)}).records[0]["indicator_category"] == "1"


def test_tdx_ext_fund_nav_uses_local_verified_value_cache(tmp_path):
    root = _build_cache_root(tmp_path)

    result = request_interface("fund_nav_tdx", params={"tdx_root": str(root), "code": "159007"})

    assert result.meta["source"] == "tdx_ext"
    assert result.meta["data_origin"] == "local_tdx_extended_cache"
    assert result.records == [
        {
            "fund_id": "159007.FUND",
            "symbol": "159007",
            "fund_type": "开放式基金",
            "name": None,
            "update_date": "20260617",
            "nav": 0.7922,
            "accumulated_nav": 20560.32,
        }
    ]


def test_tdx_ext_market_list_filters_asset_type(tmp_path):
    root = _build_cache_root(tmp_path)

    result = request_interface(
        "tdx_ext_markets_tdx",
        params={"tdx_root": str(root), "asset_type": "fx"},
    )

    assert result.records == [
        {
            "market_name": "基本汇率",
            "short_name": "FE",
            "market_group": "环球行情",
            "asset_type": "fx",
            "asset_type_zh": "外汇",
        }
    ]
    assert result.meta["tdx_ext_parallel"] is False


def test_tdx_ext_rejects_unknown_asset_type(tmp_path):
    root = _build_cache_root(tmp_path)

    with pytest.raises(SourceRequestValidationError):
        request_interface("tdx_ext_markets_tdx", params={"tdx_root": str(root), "asset_type": "bad"})


def test_tdx_ext_rejects_unknown_execution_options():
    with pytest.raises(SourceRequestValidationError, match="Unknown request option"):
        adapter = registry_adapter_for_interface("futures_kline_tdx", options={"f10_workers": 6})
        adapter.provider_adapter._adapter_for_call(None)


def test_tdx_ext_parallel_meta_resets_to_false_between_requests(monkeypatch):
    adapter = TdxExtRequestAdapter()

    def fake_snapshot(interface_name, params, *, root):
        adapter._set_parallel_meta(
            SimpleNamespace(
                source_server_count=2,
                requested_connections_per_server=3,
                connection_count=6,
            ),
            task_count=4,
        )
        return []

    def fake_markets(params, *, root):
        return []

    monkeypatch.setattr(adapter, "_request_realtime_snapshot", fake_snapshot)
    monkeypatch.setattr(adapter, "_request_markets", fake_markets)

    adapter.request("futures_realtime_snapshot_tdx", {})
    assert adapter.last_meta["tdx_ext_parallel"] is True

    adapter.request("tdx_ext_markets_tdx", {})
    assert adapter.last_meta["tdx_ext_parallel"] is False


def test_tdx_ext_macro_list_adds_verified_unit_and_frequency(tmp_path):
    root = _build_cache_root(tmp_path)

    result = request_interface("macro_indicators_tdx", params={"tdx_root": str(root), "code": "1_GDP.MACRO"})

    assert result.records == [
        {
            "instrument_id": "1_GDP.MACRO",
            "symbol": "1_GDP",
            "asset_type": "macro",
            "exchange": "MACRO",
            "market_name": "宏观指标",
            "market_group": "其它",
            "indicator_category": "1",
            "unit": "亿元",
            "frequency": "年",
        }
    ]


def test_tdx_ext_snapshot_returns_five_quote_levels(tmp_path, monkeypatch):
    root = _build_cache_root(tmp_path)

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        @classmethod
        def from_config(cls, **kwargs):
            return cls(**kwargs)

        def get_quote_multi(self, code_list):
            assert code_list == [(47, "IC2606")]
            return (
                _Quote(
                    market=47,
                    code="IC2606",
                    trade_date="20260618",
                    last_price=8682.0,
                    bid_levels=tuple(_Level(8682.0 - index, index) for index in range(1, 6)),
                    ask_levels=tuple(_Level(8682.0 + index, index + 10) for index in range(1, 6)),
                ),
            )

    monkeypatch.setattr("axdata_core.adapters.tdx_ext.request.TdxExtClient", FakeClient)

    result = request_interface(
        "futures_realtime_snapshot_tdx",
        params={"tdx_root": str(root), "code": "IC2606.CFFEX"},
    )

    row = result.records[0]
    assert row["bid1_price"] == 8681.0
    assert row["bid5_price"] == 8677.0
    assert row["bid5_volume"] == 5
    assert row["ask1_price"] == 8683.0
    assert row["ask5_price"] == 8687.0
    assert row["ask5_volume"] == 15


def test_tdx_ext_option_chain_groups_call_and_put_quotes(tmp_path, monkeypatch):
    root = _build_cache_root(tmp_path)

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        @classmethod
        def from_config(cls, **kwargs):
            return cls(**kwargs)

        def get_quote_multi(self, code_list):
            assert code_list == [(4, "AP2610-C-10000"), (4, "AP2610-P-10000")]
            return (
                _Quote(
                    market=4,
                    code="AP2610-C-10000",
                    trade_date="20260618",
                    last_price=12.0,
                    volume=993,
                    open_interest=8013,
                    bid_levels=tuple(_Level(12.0 - index, index) for index in range(1, 6)),
                    ask_levels=tuple(_Level(12.0 + index, index + 10) for index in range(1, 6)),
                ),
                _Quote(
                    market=4,
                    code="AP2610-P-10000",
                    trade_date="20260618",
                    last_price=1099.0,
                    volume=621,
                    open_interest=4520,
                    bid_levels=tuple(_Level(1099.0 - index, index + 20) for index in range(1, 6)),
                    ask_levels=tuple(_Level(1099.0 + index, index + 30) for index in range(1, 6)),
                ),
            )

    monkeypatch.setattr("axdata_core.adapters.tdx_ext.request.TdxExtClient", FakeClient)

    result = request_interface(
        "option_chain_tdx",
        params={"tdx_root": str(root), "product_code": "AP", "contract_month": "202610", "limit": 1},
    )

    assert result.records == [
        {
            "product_code": "AP",
            "product_name": "苹果",
            "exchange": "CZCE",
            "contract_month": "202610",
            "strike_price": 10000.0,
            "call_instrument_id": "AP2610-C-10000.CZCE",
            "call_symbol": "AP2610-C-10000",
            "call_last_price": 12.0,
            "call_bid1_price": 11.0,
            "call_bid1_volume": 1,
            "call_ask1_price": 13.0,
            "call_ask1_volume": 11,
            "call_volume": 993,
            "call_open_interest": 8013,
            "put_instrument_id": "AP2610-P-10000.CZCE",
            "put_symbol": "AP2610-P-10000",
            "put_last_price": 1099.0,
            "put_bid1_price": 1098.0,
            "put_bid1_volume": 21,
            "put_ask1_price": 1100.0,
            "put_ask1_volume": 31,
            "put_volume": 621,
            "put_open_interest": 4520,
            "call_bid2_price": 10.0,
            "call_bid2_volume": 2,
            "call_ask2_price": 14.0,
            "call_ask2_volume": 12,
            "call_bid3_price": 9.0,
            "call_bid3_volume": 3,
            "call_ask3_price": 15.0,
            "call_ask3_volume": 13,
            "call_bid4_price": 8.0,
            "call_bid4_volume": 4,
            "call_ask4_price": 16.0,
            "call_ask4_volume": 14,
            "call_bid5_price": 7.0,
            "call_bid5_volume": 5,
            "call_ask5_price": 17.0,
            "call_ask5_volume": 15,
            "put_bid2_price": 1097.0,
            "put_bid2_volume": 22,
            "put_ask2_price": 1101.0,
            "put_ask2_volume": 32,
            "put_bid3_price": 1096.0,
            "put_bid3_volume": 23,
            "put_ask3_price": 1102.0,
            "put_ask3_volume": 33,
            "put_bid4_price": 1095.0,
            "put_bid4_volume": 24,
            "put_ask4_price": 1103.0,
            "put_ask4_volume": 34,
            "put_bid5_price": 1094.0,
            "put_bid5_volume": 25,
            "put_ask5_price": 1104.0,
            "put_ask5_volume": 35,
        }
    ]


def test_tdx_ext_kline_uses_parallel_pool_for_multiple_codes(tmp_path, monkeypatch):
    root = _build_cache_root(tmp_path)
    hq_cache = root / "T0002" / "hq_cache"
    ds_stk = hq_cache / "ds_stk.dat"
    ds_stk.write_bytes(ds_stk.read_bytes() + _instrument_record(3, 47, 1, "IF2606", sort_key=2))
    code2name = hq_cache / "code2name.ini"
    code2name.write_bytes(
        code2name.read_bytes()
        + "IF,沪深,CZ,1,2606,20260622,200,0.2000,10.00,12.00,0.2300,万分之,元\n".encode("gbk")
    )
    from axdata_core.adapters.tdx_ext.servers import TdxExtServer

    active = 0
    max_active = 0
    closed_count = 0
    lock = threading.Lock()

    class FakeClient:
        def __init__(self, **kwargs):
            self.servers = kwargs.get("servers")

        def close(self):
            nonlocal closed_count
            with lock:
                closed_count += 1

        def get_kline2(self, market, code, period, *, count):
            nonlocal active, max_active
            assert period == 4
            assert count == 1
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                if code == "IC2606":
                    time.sleep(0.04)
                else:
                    time.sleep(0.01)
                close = 100.0 if code == "IC2606" else 200.0
                return (_Bar("20260618", close - 1, close + 1, close - 2, close, 10),)
            finally:
                with lock:
                    active -= 1

    monkeypatch.setattr("axdata_core.adapters.tdx_ext.request.TdxExtClient", FakeClient)
    monkeypatch.setattr(
        "axdata_core.adapters.tdx_ext.pool._configured_extended_servers",
        lambda *, cache_root=None: (
            TdxExtServer(index=1, name="扩展一", host="10.0.0.1", port=7727, is_primary=True),
            TdxExtServer(index=2, name="扩展二", host="10.0.0.2", port=7727, is_primary=False),
        ),
    )

    result = request_interface(
        "futures_kline_tdx",
        params={"tdx_root": str(root), "code": ["IC2606.CFFEX", "IF2606.CFFEX"], "period": "day", "limit": 1},
        options={"source_server_count": 2, "connections_per_server": 1},
    )

    assert max_active == 2
    assert closed_count == 2
    assert result.meta["options"] == {"source_server_count": 2, "connections_per_server": 1}
    assert result.meta["tdx_ext_parallel"] is True
    assert result.meta["tdx_ext_source_server_count"] == 2
    assert result.meta["tdx_ext_connection_count"] == 2
    assert [row["instrument_id"] for row in result.records] == ["IC2606.CFFEX", "IF2606.CFFEX"]
    assert [row["close"] for row in result.records] == [100.0, 200.0]


def test_tdx_ext_trades_history_returns_verified_trade_fields(tmp_path, monkeypatch):
    root = _build_cache_root(tmp_path)

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        @classmethod
        def from_config(cls, **kwargs):
            return cls(**kwargs)

        def get_history_transaction(self, market, code, trade_date, *, start, count, price_scale):
            assert (market, code, trade_date, start, count, price_scale) == (47, "IC2606", "20260618", 0, 2, 1000)
            return (
                _Trade("20260618", "14:58:50", 8681.801, 2, -1),
                _Trade("20260618", "14:58:51", 8681.601, 2, 0, 1),
            )

    monkeypatch.setattr("axdata_core.adapters.tdx_ext.request.TdxExtClient", FakeClient)

    result = request_interface(
        "futures_trades_history_tdx",
        params={"tdx_root": str(root), "code": "IC2606.CFFEX", "trade_date": "20260618", "limit": 2},
    )

    assert result.records == [
        {
            "instrument_id": "IC2606.CFFEX",
            "symbol": "IC2606",
            "exchange": "CFFEX",
            "name": "中证",
            "trade_date": "20260618",
            "time_label": "14:58:50",
            "price": 8681.8,
            "volume": 2,
            "position_change": -1,
            "open_close_type": "空平",
        },
        {
            "instrument_id": "IC2606.CFFEX",
            "symbol": "IC2606",
            "exchange": "CFFEX",
            "name": "中证",
            "trade_date": "20260618",
            "time_label": "14:58:51",
            "price": 8681.6,
            "volume": 2,
            "position_change": 0,
            "open_close_type": "空换",
        },
    ]


def test_tdx_ext_trades_today_returns_verified_trade_fields(tmp_path, monkeypatch):
    root = _build_cache_root(tmp_path)

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        @classmethod
        def from_config(cls, **kwargs):
            return cls(**kwargs)

        def get_today_transaction(self, market, code, *, start, count, price_scale):
            assert (market, code, start, count, price_scale) == (47, "IC2606", 0, 2, 1000)
            return (
                _Trade(None, "14:59:56", 8682.001, 1, -1),
                _Trade(None, "14:59:56", 8681.601, 1, 0, 1),
            )

    monkeypatch.setattr("axdata_core.adapters.tdx_ext.request.TdxExtClient", FakeClient)

    result = request_interface(
        "futures_trades_today_tdx",
        params={"tdx_root": str(root), "code": "IC2606.CFFEX", "limit": 2},
    )

    assert result.records == [
        {
            "instrument_id": "IC2606.CFFEX",
            "symbol": "IC2606",
            "exchange": "CFFEX",
            "name": "中证",
            "trade_date": None,
            "time_label": "14:59:56",
            "price": 8682.0,
            "volume": 1,
            "position_change": -1,
            "open_close_type": "双平",
        },
        {
            "instrument_id": "IC2606.CFFEX",
            "symbol": "IC2606",
            "exchange": "CFFEX",
            "name": "中证",
            "trade_date": None,
            "time_label": "14:59:56",
            "price": 8681.6,
            "volume": 1,
            "position_change": 0,
            "open_close_type": "空换",
        },
    ]


def test_tdx_ext_trades_history_all_pages_and_orders_chronologically(tmp_path, monkeypatch):
    root = _build_cache_root(tmp_path)

    class FakeClient:
        def __init__(self, **kwargs):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        @classmethod
        def from_config(cls, **kwargs):
            return cls(**kwargs)

        def get_history_transaction(self, market, code, trade_date, *, start, count, price_scale):
            self.calls.append((start, count))
            if start == 0:
                return (
                    _Trade("20260618", "14:59:55", 8681.601, 1, 0, 1),
                    _Trade("20260618", "14:59:56", 8682.001, 1, -1),
                )
            if start == 2:
                return (_Trade("20260618", "14:59:54", 8681.401, 1, 1),)
            return ()

    monkeypatch.setattr("axdata_core.adapters.tdx_ext.request.TdxExtClient", FakeClient)

    result = request_interface(
        "futures_trades_history_tdx",
        params={
            "tdx_root": str(root),
            "code": "IC2606.CFFEX",
            "trade_date": "20260618",
            "all": True,
            "limit": 5,
            "page_size": 2,
        },
    )

    assert [row["time_label"] for row in result.records] == ["14:59:54", "14:59:55", "14:59:56"]
