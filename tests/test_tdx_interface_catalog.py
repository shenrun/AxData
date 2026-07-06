import pytest

from axdata_core.sources import list_request_interfaces as list_builtin_request_interfaces
from tests.tdx_plugin_helpers import (
    ensure_local_tdx_plugin_paths,
    local_request_interface_catalog,
    local_request_interface_dicts,
    local_request_interface_names,
    local_request_interfaces,
)

ensure_local_tdx_plugin_paths()

from axdata_source_tdx.tdx_f10_specs import F10_INTERFACE_SPECS

TDX_SOURCE_INTERFACE_COUNT = 90
TDX_EXT_SOURCE_INTERFACE_COUNT = 31


def list_request_interface_names():
    return local_request_interface_names()


def list_request_interface_dicts():
    return local_request_interface_dicts()


def list_request_interfaces():
    return local_request_interfaces()


def get_request_interface(name: str):
    try:
        return local_request_interface_catalog()[name]
    except KeyError as exc:
        known = ", ".join(local_request_interface_names()) or "<empty>"
        raise KeyError(f"Unknown AxData request interface {name!r}. Known interfaces: {known}.") from exc


KLINE_INTERFACE_PARAMS = {
    "stock_kline_second_tdx": ("code", "seconds", "adjust", "anchor_date"),
    "stock_kline_minute_tdx": ("code", "period", "adjust", "anchor_date"),
    "stock_kline_nminute_tdx": ("code", "minutes", "adjust", "anchor_date"),
    "stock_kline_daily_tdx": ("code", "adjust", "anchor_date"),
    "stock_kline_nday_tdx": ("code", "days", "adjust", "anchor_date"),
    "stock_kline_weekly_tdx": ("code", "adjust", "anchor_date"),
    "stock_kline_monthly_tdx": ("code", "adjust", "anchor_date"),
    "stock_kline_quarterly_tdx": ("code", "adjust", "anchor_date"),
    "stock_kline_yearly_tdx": ("code", "adjust", "anchor_date"),
}


def test_source_request_catalog_registers_stock_codes_tdx():
    names = list_request_interface_names()
    assert names[0] == "stock_codes_tdx"
    for interface_name in (
        "stock_st_list_tdx",
        "stock_realtime_snapshot_tdx",
        "stock_kline_daily_tdx",
        "index_codes_tdx",
        "index_realtime_snapshot_tdx",
        "index_kline_tdx",
    ):
        assert interface_name in names

    interface = get_request_interface("stock_codes_tdx")
    assert interface.display_name_zh == "最新股票列表"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.request_mode == "source_request"
    assert "scope" in interface.parameter_names
    assert "code" in interface.parameter_names
    assert "name" in interface.parameter_names
    assert "instrument_id" in interface.field_names
    assert "market" in interface.field_names
    assert "market_code" not in interface.field_names
    assert "asset_type" not in interface.field_names
    assert "tdx_category" not in interface.field_names
    assert "listing_status" not in interface.field_names

    entries = list_request_interface_dicts()
    expected_count = (
        TDX_SOURCE_INTERFACE_COUNT
        + TDX_EXT_SOURCE_INTERFACE_COUNT
        + len(list_builtin_request_interfaces())
    )
    assert len(list_request_interfaces()) == expected_count
    source_codes = {entry["source_code"] for entry in entries}
    assert entries[0]["name"] == "stock_codes_tdx"
    assert entries[0]["source_code"] == "tdx"
    assert entries[0]["source_name_zh"] == "通达信"
    assert entries[0]["category"] == "基础数据"
    assert entries[0]["source_ability"].startswith("TDX 7709")
    assert source_codes <= {"tdx", "tdx_ext", "exchange", "cninfo", "tencent", "eastmoney", "sina", "cls", "kph"}


def test_source_request_catalog_registers_stock_st_list_tdx():
    interface = get_request_interface("stock_st_list_tdx")

    assert interface.display_name_zh == "最新ST股票列表"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("name", "code", "scope")
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "name",
        "market",
        "st_type",
    )
    assert "limit" not in interface.parameter_names
    assert "tdx_category" not in interface.field_names
    assert interface.example.response[0]["name"] == "*ST国华"
    assert interface.example.response[0]["st_type"] == "*ST"


def test_source_request_catalog_registers_index_tdx_interfaces():
    names = list_request_interface_names()
    for interface_name in (
        "index_codes_tdx",
        "index_realtime_snapshot_tdx",
        "index_realtime_rank_tdx",
        "index_quote_refresh_tdx",
        "index_kline_tdx",
        "index_intraday_today_tdx",
        "index_intraday_history_tdx",
    ):
        assert interface_name in names

    index_codes = get_request_interface("index_codes_tdx")
    assert index_codes.display_name_zh == "指数列表"
    assert index_codes.category == "基础数据"
    assert index_codes.parameter_names == ("name", "code", "exchange", "include_tdx_block_index")
    assert index_codes.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "name",
        "index_type",
        "previous_close",
    )
    assert index_codes.example.response[0]["instrument_id"] == "000001.SH"

    snapshot = get_request_interface("index_realtime_snapshot_tdx")
    assert snapshot.display_name_zh == "指数实时快照"
    assert "bid1_price" not in snapshot.field_names
    assert "locked_amount" not in snapshot.field_names
    assert "inside_volume" not in snapshot.field_names

    kline = get_request_interface("index_kline_tdx")
    assert kline.display_name_zh == "指数K线"
    assert kline.parameter_names == ("code", "period", "count")
    count_param = next(parameter for parameter in kline.parameters if parameter.name == "count")
    assert count_param.default == 120
    assert "预览" in count_param.description_zh
    assert "up_count" in kline.field_names
    assert "down_count" in kline.field_names

    etf_kline = get_request_interface("etf_kline_tdx")
    etf_count_param = next(parameter for parameter in etf_kline.parameters if parameter.name == "count")
    assert etf_count_param.default == 120
    assert "预览" in etf_count_param.description_zh


def test_source_request_catalog_registers_tdx_ext_asset_interfaces():
    names = list_request_interface_names()
    for interface_name in (
        "tdx_ext_markets_tdx",
        "tdx_ext_instruments_tdx",
        "futures_contracts_tdx",
        "futures_realtime_snapshot_tdx",
        "futures_kline_tdx",
        "futures_trades_today_tdx",
        "futures_trades_history_tdx",
        "option_contracts_tdx",
        "option_chain_tdx",
        "option_realtime_snapshot_tdx",
        "fund_codes_tdx",
        "fund_nav_tdx",
        "fund_nav_series_tdx",
        "bond_codes_tdx",
        "bond_realtime_snapshot_tdx",
        "fx_codes_tdx",
        "fx_realtime_snapshot_tdx",
        "fx_trades_today_tdx",
        "fx_trades_history_tdx",
        "macro_indicators_tdx",
        "macro_indicator_snapshot_tdx",
        "macro_indicator_series_tdx",
    ):
        assert interface_name in names

    futures = get_request_interface("futures_contracts_tdx")
    assert futures.display_name_zh == "期货合约列表"
    assert futures.source_code == "tdx_ext"
    assert futures.source_name_zh == "通达信扩展行情"
    assert futures.category == "期货数据"
    assert futures.parameter_names == ("code", "exchange", "name", "limit", "tdx_root")
    assert futures.example.response[0]["instrument_id"] == "IC2606.CFFEX"
    assert futures.example.response[0]["product_name"] == "中证"
    assert "last_price" not in futures.field_names

    fund = get_request_interface("fund_codes_tdx")
    assert fund.category == "基金数据"
    assert fund.example.response[0]["update_date"] == "20260617"

    macro = get_request_interface("macro_indicators_tdx")
    assert macro.category == "宏观数据"
    assert "value" not in macro.field_names
    assert "unit" in macro.field_names
    assert "frequency" in macro.field_names

    macro_snapshot = get_request_interface("macro_indicator_snapshot_tdx")
    assert macro_snapshot.display_name_zh == "宏观指标快照"
    assert "value" in macro_snapshot.field_names
    assert "frequency" in macro_snapshot.field_names

    futures_trades = get_request_interface("futures_trades_history_tdx")
    assert futures_trades.display_name_zh == "期货历史逐笔"
    assert futures_trades.parameter_names == ("code", "trade_date", "limit", "all", "page_size", "tdx_root")
    assert "position_change" in futures_trades.field_names

    futures_trades_today = get_request_interface("futures_trades_today_tdx")
    assert futures_trades_today.display_name_zh == "期货当日逐笔"
    assert futures_trades_today.parameter_names == ("code", "limit", "all", "page_size", "tdx_root")

    option_chain = get_request_interface("option_chain_tdx")
    assert option_chain.display_name_zh == "期权T型报价"
    assert "call_last_price" in option_chain.field_names
    assert "put_last_price" in option_chain.field_names


def test_source_request_catalog_registers_stock_trade_calendar_exchange():
    names = list_request_interface_names()
    assert "stock_trade_calendar_exchange" in names

    interface = get_request_interface("stock_trade_calendar_exchange")
    assert interface.display_name_zh == "交易日历"
    assert interface.source_code == "exchange"
    assert interface.source_name_zh == "交易所"
    assert interface.category == "基础数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("year", "start_date", "end_date")
    assert interface.field_names == (
        "cal_date",
        "is_open",
        "pretrade_date",
        "next_trade_date",
    )
    assert interface.example.response[2]["cal_date"] == "20260619"
    assert interface.example.response[2]["is_open"] is False
    assert "SZSE official" in interface.description
    assert "start_date/end_date > year" not in interface.description
    assert "start_date/end_date returns the exact date range" in interface.description


def test_source_request_catalog_registers_stock_historical_list_exchange():
    names = list_request_interface_names()
    assert "stock_historical_list_exchange" in names

    interface = get_request_interface("stock_historical_list_exchange")
    assert interface.display_name_zh == "历史股票列表"
    assert interface.source_code == "exchange"
    assert interface.source_name_zh == "交易所"
    assert interface.category == "基础数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("trade_date", "start_date", "end_date", "exchange")
    assert interface.field_names == (
        "trade_date",
        "instrument_id",
        "symbol",
        "exchange",
        "name",
        "market",
        "list_date",
        "delist_date",
        "listing_status",
    )
    assert interface.example.request["params"]["trade_date"] == "20240102"
    assert interface.example.response[0]["trade_date"] == "20240102"
    assert interface.example.response[1]["instrument_id"] == "000005.SZ"
    assert interface.example.response[1]["delist_date"] == "20240426"


def test_source_request_catalog_registers_stock_basic_info_exchange():
    names = list_request_interface_names()
    assert "stock_basic_info_exchange" in names

    interface = get_request_interface("stock_basic_info_exchange")
    assert interface.display_name_zh == "股票基础信息"
    assert interface.source_code == "exchange"
    assert interface.source_name_zh == "交易所"
    assert interface.category == "基础数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("exchange", "code", "name")
    assert interface.field_names[:5] == (
        "instrument_id",
        "symbol",
        "exchange",
        "asset_type",
        "name",
    )
    assert "industry" in interface.field_names
    assert "total_share" in interface.field_names
    assert interface.example.request["params"]["code"] == "000001.SZ"
    assert interface.example.response[0]["instrument_id"] == "000001.SZ"
    assert interface.example.response[0]["total_share"] == 194.05918198


def test_source_request_catalog_registers_stock_suspensions_tdx():
    interface = get_request_interface("stock_suspensions_tdx")

    assert interface.display_name_zh == "最新停牌列表"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.request_mode == "source_request"
    assert "scope" in interface.parameter_names
    assert "code" in interface.parameter_names
    assert "name" in interface.parameter_names
    assert "limit" not in interface.parameter_names
    assert "instrument_id" in interface.field_names
    assert "market" in interface.field_names
    assert "is_suspended" not in interface.field_names
    assert "trading_status_raw" not in interface.field_names
    assert "trading_status_hex" not in interface.field_names
    assert "suspend_bit_0x20" not in interface.field_names
    assert "status_source" not in interface.field_names


def test_source_request_catalog_registers_stock_daily_share_tdx():
    interface = get_request_interface("stock_daily_share_tdx")

    assert interface.display_name_zh == "每日股本（盘前）"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "基础数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "scope", "stats_cache_root", "refresh_stats")
    assert interface.field_names == (
        "trade_date",
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "total_share",
        "float_share",
        "free_float_share_z",
        "finance_updated_date",
        "share_source",
    )
    assert "trade_date" in interface.description
    assert "download time" in interface.description
    share_source = next(field for field in interface.fields if field.name == "share_source")
    assert "普通使用可忽略" in share_source.description_zh
    assert "有没有取到" in share_source.description_zh
    assert interface.parameters[0].required is False
    assert interface.parameters[1].default == "all"
    assert interface.example.request["params"] == {"code": "000001.SZ"}
    assert interface.example.response[0]["trade_date"] == "20260615"
    assert interface.example.response[0]["finance_updated_date"] == "20260425"


def test_source_request_catalog_registers_stock_daily_price_limit_tdx():
    interface = get_request_interface("stock_daily_price_limit_tdx")

    assert interface.display_name_zh == "涨跌停价格"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "基础数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "scope", "trade_date")
    assert interface.field_names == (
        "trade_date",
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "name",
        "name_flag",
        "pre_close_trade_date",
        "pre_close",
        "pre_close_source",
        "limit_up_price",
        "limit_down_price",
        "limit_ratio_pct",
        "limit_rule",
        "limit_status",
    )
    assert "trade_date" in interface.description
    assert "realtime snapshot" in interface.description
    assert "daily K-line close" in interface.description
    assert "special_limit_record_hex" not in interface.field_names
    assert interface.parameters[0].required is False
    assert interface.parameters[1].default == "all"
    assert interface.example.response[0]["pre_close_trade_date"] == "20260616"
    assert interface.example.response[0]["pre_close"] == 10.94
    assert interface.example.response[0]["limit_up_price"] == 12.03
    assert interface.example.response[0]["limit_down_price"] == 9.85
    assert interface.example.response[0]["limit_rule"] == "main_10pct"


def test_source_request_catalog_registers_stock_capital_changes_tdx():
    interface = get_request_interface("stock_capital_changes_tdx")

    assert interface.display_name_zh == "股本变迁"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "基础数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("scope", "code", "category")
    assert interface.field_names == (
        "instrument_id",
        "ts_code",
        "symbol",
        "tdx_code",
        "exchange",
        "event_date",
        "category_raw",
        "category_name",
        "c1",
        "c2",
        "c3",
        "c4",
        "c1_raw_hex",
        "c2_raw_hex",
        "c3_raw_hex",
        "c4_raw_hex",
        "record_hex",
    )
    scope = next(parameter for parameter in interface.parameters if parameter.name == "scope")
    code = next(parameter for parameter in interface.parameters if parameter.name == "code")
    category = next(parameter for parameter in interface.parameters if parameter.name == "category")
    assert scope.default == "all"
    assert code.required is False
    assert "除权除息" in category.description_zh
    assert "任意 TDX 原始类别码" in category.description_zh
    assert "0x000f" in interface.description
    assert "复权因子计算的追溯依据" in interface.description
    assert "不写入本地数据层" in interface.description


def test_source_request_catalog_registers_stock_adj_factor_tdx():
    interface = get_request_interface("stock_adj_factor_tdx")

    assert interface.display_name_zh == "复权因子"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "adjust", "anchor_date")
    assert interface.field_names == (
        "instrument_id",
        "ts_code",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_date",
        "adj_factor",
    )
    adjust = next(parameter for parameter in interface.parameters if parameter.name == "adjust")
    anchor_date = next(parameter for parameter in interface.parameters if parameter.name == "anchor_date")
    assert adjust.default == "qfq"
    assert "qfq 前复权因子" in adjust.description_zh
    assert "仅 adjust=qfq" in anchor_date.description_zh
    assert "stock_capital_changes_tdx" in interface.description
    assert "category=1 XDXR" in interface.description
    assert "not guaranteed to match" in interface.description
    assert "realtime" not in interface.parameter_names


def test_source_request_catalog_registers_stock_order_book_tdx():
    interface = get_request_interface("stock_order_book_tdx")

    assert interface.display_name_zh == "五档盘口"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "实时数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code",)
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "level",
        "bid_price",
        "bid_volume",
        "ask_price",
        "ask_volume",
    )
    assert "one row per level" in interface.description
    assert "trading_status_raw" not in interface.field_names


def test_source_request_catalog_registers_stock_realtime_rank_tdx():
    interface = get_request_interface("stock_realtime_rank_tdx")

    assert interface.display_name_zh == "实时榜单"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "实时数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == (
        "category",
        "sort",
        "start",
        "count",
        "ascending",
        "filters",
    )
    assert interface.field_names[:5] == (
        "rank",
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
    )
    assert "last_price" in interface.field_names
    assert "change_pct" in interface.field_names
    assert "locked_amount" in interface.field_names
    assert "level" not in interface.field_names
    assert "0x054b" in interface.source_ability.lower()
    assert "server decides" in interface.description


def test_source_request_catalog_registers_stock_limit_ladder_tdx():
    interface = get_request_interface("stock_limit_ladder_tdx")

    assert interface.display_name_zh == "连板天梯"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "短线数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("count", "scope", "include_touched", "topic_type")
    assert interface.field_names == (
        "trade_date",
        "ladder_level",
        "limit_board_text",
        "instrument_id",
        "name",
        "last_price",
        "change_pct",
        "limit_status",
        "amount",
        "seal_amount",
        "seal_to_amount_ratio",
        "free_float_market_value",
        "primary_theme",
        "secondary_themes",
        "year_limit_up_days",
        "symbol",
        "exchange",
        "pre_close",
        "limit_up_price",
    )
    assert "0x054b" in interface.source_ability.lower()
    assert "does not write raw/staging/core/factor" in interface.description
    assert "stats_cache_root" not in interface.parameter_names
    assert "stats_root" not in interface.parameter_names


def test_source_request_catalog_registers_stock_theme_strength_rank_tdx():
    interface = get_request_interface("stock_theme_strength_rank_tdx")

    assert interface.display_name_zh == "题材强度排行"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "短线数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("count", "scope", "topic_type")
    assert interface.field_names == (
        "rank",
        "trade_date",
        "topic_type",
        "topic_name",
        "topic_id",
        "theme_strength_score",
        "limit_up_count",
        "highest_ladder_level",
        "lianban_stock_count",
        "first_board_count",
        "leader_instrument_id",
        "leader_name",
        "leader_ladder_level",
        "leader_limit_board_text",
        "leader_seal_amount",
        "seal_amount_sum",
        "amount_sum",
        "top_stock_summary",
    )
    assert "stock_limit_ladder_tdx" in interface.description
    assert "does not write raw/staging/core/factor" in interface.description
    assert "include_touched" not in interface.parameter_names


def test_source_request_catalog_registers_stock_realtime_snapshot_tdx():
    interface = get_request_interface("stock_realtime_snapshot_tdx")

    assert interface.display_name_zh == "实时快照"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "实时数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code",)
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "last_price",
        "pre_close",
        "open",
        "high",
        "low",
        "change",
        "change_pct",
        "open_change_pct",
        "high_change_pct",
        "low_change_pct",
        "amplitude_pct",
        "average_price",
        "average_change_pct",
        "drawdown_pct",
        "attack_pct",
        "volume",
        "current_volume",
        "amount",
        "inside_volume",
        "outside_volume",
        "inside_outside_ratio",
        "open_amount",
        "open_amount_ratio_pct",
        "bid1_price",
        "bid1_volume",
        "ask1_price",
        "ask1_volume",
        "locked_amount",
        "bid1_ask1_volume_diff",
        "bid1_ask1_balance_pct",
        "rise_speed",
        "short_turnover",
        "min2_amount",
        "opening_rush",
        "vol_rise_speed",
        "entrust_ratio",
        "activity",
    )
    assert "one row" in interface.description
    assert "level" not in interface.field_names
    assert "trading_status_raw" not in interface.field_names


def test_source_request_catalog_registers_stock_intraday_subchart_interfaces():
    buy_sell = get_request_interface("stock_intraday_buy_sell_strength_tdx")
    volume = get_request_interface("stock_intraday_volume_comparison_tdx")

    assert buy_sell.display_name_zh == "买卖力道"
    assert buy_sell.category == "实时数据"
    assert buy_sell.parameter_names == ("code",)
    assert buy_sell.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "minute_time",
        "minute_index",
        "bid_order",
        "ask_order",
    )
    assert "date or time parameter" in buy_sell.description
    assert "trade_date" not in buy_sell.parameter_names

    assert volume.display_name_zh == "成交对比"
    assert volume.category == "实时数据"
    assert volume.parameter_names == ("code",)
    assert volume.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "minute_time",
        "minute_index",
        "today_volume",
        "yesterday_volume",
        "volume_change",
        "volume_change_pct",
    )
    assert "percentage change" in volume.description
    assert "trade_date" not in volume.parameter_names
    assert "volume_ratio" not in volume.field_names


def test_source_request_catalog_registers_stock_auction_process_tdx():
    interface = get_request_interface("stock_auction_process_tdx")

    assert interface.display_name_zh == "竞价明细"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "竞价数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code",)
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "auction_time",
        "auction_index",
        "price",
        "matched_volume",
        "matched_amount_estimated",
        "unmatched_volume",
        "unmatched_amount_estimated",
        "unmatched_direction",
    )
    assert "09:25" in interface.description
    assert "trade_date" not in interface.parameter_names
    assert "raw_hex" not in interface.field_names
    assert "time_seconds" not in interface.field_names
    assert "price_milli" not in interface.field_names
    assert "unmatched_signed_raw" not in interface.field_names
    assert "unmatched_direction_raw" not in interface.field_names


def test_source_request_catalog_registers_stock_auction_result_tdx():
    interface = get_request_interface("stock_auction_result_tdx")

    assert interface.display_name_zh == "竞价结果"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "竞价数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code",)
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "auction_time",
        "trade_index",
        "price",
        "volume",
        "amount",
        "order_count",
    )
    assert "0x0fc5" in interface.source_ability
    assert "09:25" in interface.description
    assert "stock_auction_process_tdx" in interface.description
    assert "trade_date" not in interface.parameter_names
    assert "start" not in interface.parameter_names
    assert "count" not in interface.parameter_names


def test_source_request_catalog_registers_stock_auction_result_history_tdx():
    interface = get_request_interface("stock_auction_result_history_tdx")

    assert interface.display_name_zh == "历史竞价结果"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "竞价数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "trade_date")
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_date",
        "auction_time",
        "auction_datetime",
        "trade_index",
        "price",
        "volume",
        "amount",
        "order_count",
    )
    trade_date = next(parameter for parameter in interface.parameters if parameter.name == "trade_date")
    assert trade_date.required is True
    assert "YYYYMMDD" in trade_date.description_zh
    assert "0x0fc6" in interface.source_ability
    assert "09:25" in interface.description
    assert "start" not in interface.parameter_names
    assert "count" not in interface.parameter_names


def test_source_request_catalog_registers_stock_shortline_indicators_tdx():
    interface = get_request_interface("stock_shortline_indicators_tdx")

    assert interface.display_name_zh == "短线指标"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "短线数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "stats_root", "stats_cache_root", "refresh_stats")
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "stats_date",
        "open_price",
        "pre_close",
        "open_change_pct",
        "open_amount",
        "open_volume_hand",
        "open_volume_ratio",
        "open_turnover_z",
        "open_prev_amount_ratio",
        "auction_prev_volume_ratio",
        "opening_rush",
        "open_prev_seal_ratio",
        "prev_amount",
        "prev_seal_amount",
        "prev2_seal_amount",
        "prev_open_volume_hand",
        "prev_open_amount",
        "float_shares",
        "float_market_value",
        "free_float_shares",
        "free_float_market_value",
        "seal_amount",
        "seal_to_amount_ratio",
        "seal_to_float_ratio",
        "seal_prev_ratio",
        "limit_stat_days",
        "limit_up_count_in_stat_days",
        "limit_board_text",
        "limit_up_streak_days",
        "year_limit_up_days",
    )
    assert "tdxstat" in interface.source_ability
    assert "raw/staging/core/factor" in interface.description


def test_source_request_catalog_registers_stock_intraday_history_tdx():
    interface = get_request_interface("stock_intraday_history_tdx")

    assert interface.display_name_zh == "历史分时"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "trade_date")
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_date",
        "trade_time",
        "minute_index",
        "price",
        "volume",
        "prev_close",
    )
    trade_date = next(parameter for parameter in interface.parameters if parameter.name == "trade_date")
    assert trade_date.required is True
    assert "YYYYMMDD" in trade_date.description_zh
    assert "not a K-line" in interface.description
    assert "open" not in interface.field_names
    assert "high" not in interface.field_names
    assert "low" not in interface.field_names
    assert "close" not in interface.field_names
    assert "adjust" not in interface.parameter_names


def test_source_request_catalog_registers_stock_intraday_recent_history_tdx():
    interface = get_request_interface("stock_intraday_recent_history_tdx")

    assert interface.display_name_zh == "近期历史分时"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "trade_date")
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_date",
        "trade_time",
        "time_label",
        "minute_index",
        "price",
        "avg_price",
        "volume",
        "prev_close",
        "open_price",
    )
    trade_date = next(parameter for parameter in interface.parameters if parameter.name == "trade_date")
    assert trade_date.required is True
    assert "YYYYMMDD" in trade_date.description_zh
    assert "0x0feb" in interface.source_ability
    assert "K-line" not in interface.description
    assert "adjust" not in interface.parameter_names


def test_source_request_catalog_registers_stock_intraday_today_tdx():
    interface = get_request_interface("stock_intraday_today_tdx")

    assert interface.display_name_zh == "当日分时"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code",)
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "time_label",
        "minute_index",
        "price",
        "avg_price",
        "volume",
    )
    assert "0x0537" in interface.source_ability
    assert "not a K-line" in interface.description
    assert "does not carry a date" in interface.description
    assert interface.example.request["params"] == {"code": "000001.SZ"}
    assert tuple(interface.example.response[0]) == (
        "instrument_id",
        "time_label",
        "price",
        "avg_price",
        "volume",
    )
    assert "trade_date" not in interface.parameter_names
    assert "open" not in interface.field_names
    assert "high" not in interface.field_names
    assert "low" not in interface.field_names
    assert "close" not in interface.field_names
    assert "adjust" not in interface.parameter_names


def test_source_request_catalog_registers_stock_trades_today_tdx():
    interface = get_request_interface("stock_trades_today_tdx")

    assert interface.display_name_zh == "当日成交明细"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code",)
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_time",
        "trade_index",
        "price",
        "volume",
        "order_count",
        "side",
    )
    assert "start" not in interface.parameter_names
    assert "count" not in interface.parameter_names
    assert "trade_date" not in interface.field_names
    assert "price_delta_raw" not in interface.field_names
    assert "record_hex" not in interface.field_names


def test_source_request_catalog_registers_stock_trades_history_tdx():
    interface = get_request_interface("stock_trades_history_tdx")

    assert interface.display_name_zh == "历史成交明细"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == ("code", "trade_date")
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_date",
        "trade_time",
        "trade_datetime",
        "trade_index",
        "price",
        "volume",
        "order_count",
        "side",
    )
    trade_date = next(parameter for parameter in interface.parameters if parameter.name == "trade_date")
    assert trade_date.required is True
    assert "YYYYMMDD" in trade_date.description_zh
    assert "K-line" in interface.description
    assert "start" not in interface.parameter_names
    assert "count" not in interface.parameter_names
    assert "price_delta_raw" not in interface.field_names
    assert "record_hex" not in interface.field_names


@pytest.mark.parametrize(
    ("interface_name", "display_name", "expected_fields"),
    [
        (
            "stock_finance_summary_tdx",
            "财务基础摘要",
            ("updated_date", "ipo_date", "total_share", "float_share", "eps", "bps", "total_assets", "net_profit"),
        ),
        (
            "stock_share_capital_tdx",
            "股本结构",
            ("total_share", "float_share", "state_share", "legal_person_share", "shareholder_count"),
        ),
        (
            "stock_balance_summary_tdx",
            "资产负债摘要",
            ("total_assets", "current_assets", "fixed_assets", "net_assets", "inventory"),
        ),
        (
            "stock_profit_cashflow_summary_tdx",
            "利润现金流摘要",
            ("revenue", "operating_profit", "net_profit", "operating_cashflow", "eps"),
        ),
        (
            "stock_finance_profile_tdx",
            "财务资料标签",
            ("updated_date", "ipo_date", "province_raw", "industry_raw"),
        ),
    ],
)
def test_source_request_catalog_registers_stock_finance_views(
    interface_name,
    display_name,
    expected_fields,
):
    interface = get_request_interface(interface_name)

    assert interface.display_name_zh == display_name
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "财务数据"
    assert interface.request_mode == "source_request"
    expected_params = ("code", "map_root") if interface_name == "stock_finance_profile_tdx" else ("code",)
    assert interface.parameter_names == expected_params
    if interface_name == "stock_finance_profile_tdx":
        assert "map_root" in interface.parameter_names
        assert "bundled TDX code-table snapshot" in interface.description
    assert "TDX 0x0010" in interface.description
    assert "not a full F10" in interface.description
    assert set(expected_fields).issubset(interface.field_names)
    assert "instrument_id" in interface.field_names
    assert "tdx_code" in interface.field_names
    assert "record_hex" not in interface.field_names
    assert "finance_info_hex" not in interface.field_names
    assert "reserved_2" not in interface.field_names


def test_source_request_catalog_registers_stock_kline_second_tdx():
    interface = get_request_interface("stock_kline_second_tdx")

    assert interface.display_name_zh == "秒K线"
    assert interface.source_code == "tdx"
    assert interface.source_name_zh == "通达信"
    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == (
        "code",
        "seconds",
        "adjust",
        "anchor_date",
    )
    assert "instrument_id" in interface.field_names
    assert "trade_time" in interface.field_names
    assert "period" in interface.field_names
    assert "open" in interface.field_names
    assert "close" in interface.field_names
    assert "adjust" not in interface.field_names
    assert "period_raw" not in interface.field_names
    assert "record_hex" not in interface.field_names
    seconds = next(parameter for parameter in interface.parameters if parameter.name == "seconds")
    assert "1-60 内可自定义" in seconds.description_zh
    assert "推荐 3、4、5、10、15、30、60" in seconds.description_zh
    assert "支持 1、2" not in seconds.description_zh


def test_source_request_catalog_explains_fixed_minute_kline_periods():
    interface = get_request_interface("stock_kline_minute_tdx")
    period = next(parameter for parameter in interface.parameters if parameter.name == "period")

    assert "1m、5m、15m、30m、60m" in period.description_zh
    assert "其他分钟数请使用自定义分钟K线" in period.description_zh


@pytest.mark.parametrize(
    ("interface_name", "expected_range"),
    [
        ("stock_kline_second_tdx", "3s 8 trading days"),
        ("stock_kline_minute_tdx", "1m 94 trading days"),
        ("stock_kline_nminute_tdx", "minutes=10 covered 494 trading days"),
        ("stock_kline_daily_tdx", "Measured range: since listing"),
        ("stock_kline_nday_tdx", "Measured range: since listing for tested day aggregation"),
        ("stock_kline_weekly_tdx", "Measured range: since listing"),
        ("stock_kline_monthly_tdx", "Measured range: since listing"),
        ("stock_kline_quarterly_tdx", "Measured range: since listing"),
        ("stock_kline_yearly_tdx", "Measured range: since listing"),
    ],
)
def test_source_request_catalog_notes_measured_kline_ranges(interface_name, expected_range):
    interface = get_request_interface(interface_name)

    assert "Measured range" in interface.description
    assert expected_range in interface.description
    assert "2026-06-12" not in interface.description
    assert " calendar days" not in interface.description
    assert "depends on the TDX server and symbol" in interface.description


@pytest.mark.parametrize(("interface_name", "parameter_names"), KLINE_INTERFACE_PARAMS.items())
def test_source_request_catalog_keeps_all_kline_interfaces_clean(interface_name, parameter_names):
    interface = get_request_interface(interface_name)

    assert interface.category == "行情数据"
    assert interface.request_mode == "source_request"
    assert interface.parameter_names == parameter_names
    assert interface.field_names == (
        "instrument_id",
        "symbol",
        "tdx_code",
        "exchange",
        "trade_time",
        "period",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
    )
    assert "count" not in interface.parameter_names
    assert "start" not in interface.parameter_names
    assert "period_raw" not in interface.field_names
    assert "period_param_raw" not in interface.field_names
    assert "adjust" not in interface.field_names
    trade_time = next(field for field in interface.fields if field.name == "trade_time")
    assert "K 线结束时间" in trade_time.description_zh
    assert "15:00:00+08:00" in trade_time.description_zh


def test_unknown_request_interface_raises_helpful_error():
    with pytest.raises(KeyError, match="Unknown AxData request interface"):
        get_request_interface("missing_interface")


def test_source_request_catalog_registers_tdx_f10_interfaces():
    names = list_request_interface_names()
    for interface_name in F10_INTERFACE_SPECS:
        assert interface_name in names

    listing = get_request_interface("stock_ipo_listing_profile_tdx")
    assert listing.display_name_zh == "发行上市资料"
    assert listing.category == "F10数据"
    assert listing.request_mode == "source_request"
    assert listing.parameter_names == ("code",)
    assert "issue_price" in listing.field_names
    assert "publish_date" not in listing.field_names
    assert "源端直取默认不写入本地数据" in listing.description

    index_changes = get_request_interface("stock_index_constituent_changes_tdx")
    assert index_changes.display_name_zh == "指数调入调出"
    assert index_changes.parameter_names == ("code", "start_date", "end_date")
    assert "publish_date_change_pct" in index_changes.field_names
    assert "effective_date_change_pct" in index_changes.field_names
    assert "issue_price" not in index_changes.field_names

    financial_statement = get_request_interface("stock_financial_statement_tdx")
    assert financial_statement.display_name_zh == "资产负债表"
    assert financial_statement.parameter_names == ("code",)
    assert "total_assets" in financial_statement.field_names
    assert "net_profit" not in financial_statement.field_names

    business = get_request_interface("stock_business_composition_tdx")
    assert business.display_name_zh == "主营构成"
    assert business.parameter_names == ("code", "period")
    period = next(parameter for parameter in business.parameters if parameter.name == "period")
    assert period.default is None
    assert "不传时返回全部可用报告期" in period.description_zh

    company = get_request_interface("stock_company_profile_tdx")
    assert company.display_name_zh == "公司概况"
    assert company.parameter_names == ("code", "type")

    event_drivers = get_request_interface("stock_event_drivers_tdx")
    assert event_drivers.display_name_zh == "历史事件关联"
    assert event_drivers.parameter_names == ("code", "start_date", "end_date", "include_detail")
    assert "涨停原因" in next(field for field in event_drivers.fields if field.name == "event_name").description_zh
    assert "详情正文" in next(field for field in event_drivers.fields if field.name == "detail_text").description_zh
    assert "按事件创建日期过滤" in next(
        parameter for parameter in event_drivers.parameters if parameter.name == "start_date"
    ).description_zh
    assert "补充详情正文" in next(
        parameter for parameter in event_drivers.parameters if parameter.name == "include_detail"
    ).description_zh

    topic_exposure = get_request_interface("stock_topic_exposure_tdx")
    assert topic_exposure.display_name_zh == "个股题材"
    assert topic_exposure.category == "短线数据"
    assert topic_exposure.parameter_names == ("code", "topic_type")
    assert "sector 板块题材、theme 主题题材" in next(
        parameter for parameter in topic_exposure.parameters if parameter.name == "topic_type"
    ).description_zh
    assert "默认 theme" in next(
        parameter for parameter in topic_exposure.parameters if parameter.name == "topic_type"
    ).description_zh
    assert "源端评价分值" in next(field for field in topic_exposure.fields if field.name == "relevance").description_zh
    assert "主题题材可能为空" in next(field for field in topic_exposure.fields if field.name == "group_code").description_zh

    related_boards = get_request_interface("concept_related_boards_tdx")
    assert related_boards.display_name_zh == "相关板块"
    assert related_boards.category == "短线数据"
    assert related_boards.parameter_names == ("code",)
    assert "instrument_id" in related_boards.field_names
    assert "symbol" in related_boards.field_names
    assert "当前关联板块" in related_boards.description

    constituents = get_request_interface("concept_constituents_tdx")
    assert constituents.display_name_zh == "板块成分股"
    assert constituents.category == "短线数据"
    assert constituents.parameter_names == ("concept_code", "count")
    assert "按板块代码" in constituents.description
    assert "board_code" in next(
        parameter for parameter in constituents.parameters if parameter.name == "concept_code"
    ).description_zh
    assert "返回前多少只" in next(
        parameter for parameter in constituents.parameters if parameter.name == "count"
    ).description_zh
    assert "instrument_id" in constituents.field_names
    assert "exchange" in constituents.field_names
    assert constituents.example.request["params"]["concept_code"] == "881386"

    capital_flow = get_request_interface("concept_capital_flow_tdx")
    assert capital_flow.display_name_zh == "题材资金走势"
    assert capital_flow.category == "短线数据"
    assert capital_flow.parameter_names == ("concept_code", "start_date", "end_date", "count")
    assert "题材或行业 ID" in next(
        parameter for parameter in capital_flow.parameters if parameter.name == "concept_code"
    ).description_zh
    assert "按 date 过滤" in next(
        parameter for parameter in capital_flow.parameters if parameter.name == "start_date"
    ).description_zh
    assert "返回条数" in next(
        parameter for parameter in capital_flow.parameters if parameter.name == "count"
    ).description_zh
    assert capital_flow.example.request["params"]["concept_code"] == "2817"
    assert capital_flow.example.request["params"]["count"] == 20

    disclosure = get_request_interface("stock_disclosure_feed_tdx")
    assert disclosure.display_name_zh == "新闻公告路演"
    assert disclosure.category == "F10数据"
    assert disclosure.parameter_names == ("code", "category", "count")
    assert "title" in disclosure.field_names
    assert "url" in disclosure.field_names
    assert "detail_table" in disclosure.field_names
    assert "type_code" in disclosure.field_names
    assert "start_date" in disclosure.field_names
    assert "start_time" in disclosure.field_names
    assert "end_time" in disclosure.field_names
    assert "路演" in next(field for field in disclosure.fields if field.name == "start_date").description_zh
    assert "非公告" in next(field for field in disclosure.fields if field.name == "type_code").description_zh

    dividends = get_request_interface("stock_dividend_history_tdx")
    assert dividends.display_name_zh == "分红历史"
    assert dividends.parameter_names == ("code", "start_year", "end_year")
    start_year = next(parameter for parameter in dividends.parameters if parameter.name == "start_year")
    end_year = next(parameter for parameter in dividends.parameters if parameter.name == "end_year")
    assert "不传返回全部记录" in start_year.description_zh
    assert "不传返回全部记录" in end_year.description_zh

    financing = get_request_interface("stock_equity_financing_events_tdx")
    assert financing.display_name_zh == "融资事件"
    assert financing.parameter_names == ("code", "event_type")
    assert "placement 增发" in next(parameter for parameter in financing.parameters if parameter.name == "event_type").description_zh
    assert "融资金额" in next(field for field in financing.fields if field.name == "amount").description_zh
    assert "转股价格" in next(field for field in financing.fields if field.name == "price").description_zh

    valuation = get_request_interface("stock_valuation_metrics_tdx")
    assert valuation.display_name_zh == "估值表"
    assert valuation.category == "F10数据"
    assert valuation.parameter_names == ("code", "start_date", "end_date", "count")
    assert "按 date 过滤" in next(parameter for parameter in valuation.parameters if parameter.name == "start_date").description_zh
    assert "pe_ttm" in valuation.field_names
    assert "total_market_cap" in valuation.field_names

    control_series = get_request_interface("concept_control_series_tdx")
    assert control_series.display_name_zh == "主力控盘序列"
    assert control_series.parameter_names == ("code", "start_date", "end_date", "count")
    assert "按 date 过滤" in next(
        parameter for parameter in control_series.parameters if parameter.name == "start_date"
    ).description_zh
    assert "返回条数" in next(parameter for parameter in control_series.parameters if parameter.name == "count").description_zh

    control_ranking = get_request_interface("concept_control_ranking_tdx")
    assert control_ranking.display_name_zh == "控盘榜单"
    assert control_ranking.parameter_names == ("concept_code", "count")
    assert "题材或行业 ID" in next(
        parameter for parameter in control_ranking.parameters if parameter.name == "concept_code"
    ).description_zh
    assert "拍平后计数" in next(parameter for parameter in control_ranking.parameters if parameter.name == "count").description_zh
    assert "date" in control_ranking.field_names
    assert "instrument_id" in control_ranking.field_names
    assert "exchange" in control_ranking.field_names
    assert control_ranking.example.request["params"]["concept_code"] == "2817"

    comparison = get_request_interface("concept_constituent_comparison_tdx")
    assert comparison.display_name_zh == "题材内对比"
    assert comparison.parameter_names == ("code", "concept_code", "compare_type", "sort_by")
    assert "report_period" in comparison.field_names
    assert "源端排序字段" in next(parameter for parameter in comparison.parameters if parameter.name == "sort_by").description_zh

    valuation_series = get_request_interface("stock_valuation_series_tdx")
    assert valuation_series.display_name_zh == "单指标估值序列"
    assert valuation_series.parameter_names == ("code", "metric", "start_date", "end_date", "count")
    assert "pe、pb、pcf、ps" in next(parameter for parameter in valuation_series.parameters if parameter.name == "metric").description_zh
    assert "按 date 过滤" in next(
        parameter for parameter in valuation_series.parameters if parameter.name == "start_date"
    ).description_zh
    assert valuation_series.example.request["params"]["start_date"] == "20260601"
    assert valuation_series.example.request["params"]["end_date"] == "20260605"
    assert valuation_series.example.response[0]["date"] == "20260601"
    assert valuation_series.example.response[0]["metric"] == "pe"
    assert valuation_series.example.response[0]["value"] == 4.95

    guarantees = get_request_interface("stock_governance_guarantees_tdx")
    assert guarantees.display_name_zh == "担保明细"
    assert guarantees.parameter_names == ("code", "period", "count")
    assert "amount" in guarantees.field_names

    regulatory = get_request_interface("stock_regulatory_actions_tdx")
    assert regulatory.display_name_zh == "监管措施"
    assert regulatory.parameter_names == ("code", "start_date", "end_date", "count")
    assert "cursor" not in regulatory.parameter_names
    assert "按处罚公布日期过滤" in next(parameter for parameter in regulatory.parameters if parameter.name == "start_date").description_zh
    assert "源端可能为空" in next(field for field in regulatory.fields if field.name == "link").description_zh

    score = get_request_interface("stock_score_summary_tdx")
    assert score.display_name_zh == "综合评分"
    assert score.parameter_names == ("code",)
    assert "trade_date" not in score.parameter_names
    assert "industry_name" in score.field_names
    assert "stock_name" in score.field_names

    rankings = get_request_interface("stock_market_rankings_tdx")
    assert rankings.display_name_zh == "排名明细"
    assert rankings.parameter_names == ("code", "scope", "count")
    assert "instrument_id" in rankings.field_names
    assert "exchange" in rankings.field_names
    assert "所属行业" in next(parameter for parameter in rankings.parameters if parameter.name == "scope").description_zh

    chips = get_request_interface("stock_chip_distribution_tdx")
    assert chips.display_name_zh == "筹码分布"
    assert chips.parameter_names == ("code", "start_date", "end_date")
    assert "cost90_concentration" in chips.field_names
    assert "cost70_range" in chips.field_names
    assert "按统计日期过滤" in next(parameter for parameter in chips.parameters if parameter.name == "start_date").description_zh
    assert "本次给出的全部记录" in next(parameter for parameter in chips.parameters if parameter.name == "start_date").description_zh


def test_source_request_catalog_hides_tdx_f10_protocol_details_from_user_description():
    for interface_name in F10_INTERFACE_SPECS:
        interface = get_request_interface(interface_name)
        user_text = " ".join(
            [
                interface.display_name_zh,
                interface.first_stage_strategy,
                interface.description,
                *[parameter.description_zh for parameter in interface.parameters],
                *[field.description_zh for field in interface.fields],
            ]
        )
        assert "TQLEX" not in user_text
        assert "Entry" not in user_text
        assert "ResultSets" not in user_text
