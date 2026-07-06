"""TDX source request interface catalog."""

from __future__ import annotations

from typing import Dict

from axdata_core.tdx_f10_catalog import F10_CATALOG_SPECS
from axdata_core.tdx_f10_models import F10FieldSpec
from axdata_core.sources.base import RequestExample, RequestField, RequestParameter, SourceRequestInterface


KLINE_RETENTION_NOTES = {
    "stock_kline_second_tdx": (
        "Measured range on 000001.SZ: 3s 8 trading days, 4s 10 trading days, "
        "5s 12 trading days, 10s 24 trading days, and 15s/30s/60s 28 trading days. Actual availability "
        "depends on the TDX server and symbol."
    ),
    "stock_kline_minute_tdx": (
        "Measured range on 000001.SZ: 1m 94 trading days, and "
        "5m/15m/30m/60m 494 trading days. Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_nminute_tdx": (
        "Measured range on 000001.SZ: minutes=10 covered 494 trading days. "
        "Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_daily_tdx": (
        "Measured range: since listing. "
        "Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_nday_tdx": (
        "Measured range: since listing for tested day aggregation. "
        "Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_weekly_tdx": (
        "Measured range: since listing. "
        "Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_monthly_tdx": (
        "Measured range: since listing. "
        "Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_quarterly_tdx": (
        "Measured range: since listing. "
        "Actual availability depends on the TDX server and symbol."
    ),
    "stock_kline_yearly_tdx": (
        "Measured range: since listing. "
        "Actual availability depends on the TDX server and symbol."
    ),
}


CAPITAL_CHANGE_CATEGORY_REFERENCE_ZH = (
    "TDX 0x000f category values currently mapped by AxData: "
    "1=除权除息, 2=送配股上市, 3=非流通股上市, 4=未知股本变动, "
    "5=股本变化, 6=增发新股, 7=股份回购, 8=增发新股上市, "
    "9=转配股上市, 10=可转债上市, 11=扩缩股, 12=非流通股缩股, "
    "13=送认购权证, 14=送认沽权证, 15=重整调整. "
    "The current adjustment-factor implementation directly uses category=1 only; "
    "other categories are exposed as capital-change and corporate-action evidence."
)


ADJ_FACTOR_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="ts_code",
        dtype="string",
        description="Alias of instrument_id for compatibility with AxData core adj_factor.",
        description_zh="与 instrument_id 相同，用于兼容 AxData core adj_factor 表字段。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="trade_date",
        dtype="date/string",
        description="Trading date, YYYYMMDD.",
        description_zh="交易日期，YYYYMMDD。",
    ),
    RequestField(
        name="adj_factor",
        dtype="number",
        description="Adjustment factor under the requested adjustment method.",
        description_zh="按请求复权口径计算出的复权因子。",
    ),
)


INTRADAY_HISTORY_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="trade_date",
        dtype="date/string",
        description="Trading date, YYYYMMDD.",
        description_zh="交易日期，YYYYMMDD。",
    ),
    RequestField(
        name="trade_time",
        dtype="datetime/string",
        description="Intraday minute timestamp.",
        description_zh="分时点时间。",
    ),
    RequestField(
        name="minute_index",
        dtype="integer",
        description="Zero-based minute point index in the returned day trace.",
        description_zh="分时点序号，从 0 开始。",
    ),
    RequestField(
        name="price",
        dtype="number",
        description="Minute intraday price.",
        description_zh="该分钟分时价格。",
    ),
    RequestField(
        name="volume",
        dtype="number",
        description="Minute volume.",
        description_zh="该分钟成交量。",
    ),
    RequestField(
        name="prev_close",
        dtype="number",
        description="Previous close carried by the TDX intraday response.",
        description_zh="昨收价。",
    ),
)


INTRADAY_TODAY_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="time_label",
        dtype="time/string",
        description="Intraday minute label derived from point order, HH:MM.",
        description_zh="分时点时间，由返回顺序映射得到，格式 HH:MM。",
    ),
    RequestField(
        name="minute_index",
        dtype="integer",
        description="Zero-based minute point index in the current-day intraday trace.",
        description_zh="分时点序号，从 0 开始。",
    ),
    RequestField(
        name="price",
        dtype="number",
        description="Current-day intraday price.",
        description_zh="该分钟分时价格。",
    ),
    RequestField(
        name="avg_price",
        dtype="number",
        description="Current-day intraday average price.",
        description_zh="该分钟分时均价。",
    ),
    RequestField(
        name="volume",
        dtype="number",
        description="Minute volume.",
        description_zh="该分钟成交量。",
    ),
)


INTRADAY_RECENT_HISTORY_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="trade_date",
        dtype="date/string",
        description="Trading date, YYYYMMDD.",
        description_zh="交易日期，YYYYMMDD。",
    ),
    RequestField(
        name="trade_time",
        dtype="datetime/string",
        description="Intraday minute timestamp.",
        description_zh="分时点时间。",
    ),
    RequestField(
        name="time_label",
        dtype="time/string",
        description="Intraday minute label, HH:MM.",
        description_zh="分时点时间标签，格式 HH:MM。",
    ),
    RequestField(
        name="minute_index",
        dtype="integer",
        description="Zero-based minute point index in the returned day trace.",
        description_zh="分时点序号，从 0 开始。",
    ),
    RequestField(
        name="price",
        dtype="number",
        description="Minute intraday price.",
        description_zh="该分钟分时价格。",
    ),
    RequestField(
        name="avg_price",
        dtype="number",
        description="Minute intraday average price.",
        description_zh="该分钟分时均价。",
    ),
    RequestField(
        name="volume",
        dtype="number",
        description="Minute volume.",
        description_zh="该分钟成交量。",
    ),
    RequestField(
        name="prev_close",
        dtype="number",
        description="Previous close carried by the TDX recent intraday response.",
        description_zh="昨收价。",
    ),
    RequestField(
        name="open_price",
        dtype="number",
        description="Open price carried by the TDX recent intraday response.",
        description_zh="开盘价。",
    ),
)


ORDER_BOOK_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="level",
        dtype="integer",
        description="Order-book level from 1 to 5.",
        description_zh="盘口档位，1 到 5。",
    ),
    RequestField(
        name="bid_price",
        dtype="number",
        description="Bid price at this level.",
        description_zh="该档委买价。",
    ),
    RequestField(
        name="bid_volume",
        dtype="integer",
        description="Bid volume at this level, in lots for common A-share symbols.",
        description_zh="该档委买量，A 股常见口径为手。",
    ),
    RequestField(
        name="ask_price",
        dtype="number",
        description="Ask price at this level.",
        description_zh="该档委卖价。",
    ),
    RequestField(
        name="ask_volume",
        dtype="integer",
        description="Ask volume at this level, in lots for common A-share symbols.",
        description_zh="该档委卖量，A 股常见口径为手。",
    ),
)


REALTIME_RANK_FIELD = RequestField(
    name="rank",
    dtype="integer",
    description="One-based rank position in the returned realtime list.",
    description_zh="榜单名次，从 1 开始，按当前返回结果顺序连续编号。",
)


REALTIME_SNAPSHOT_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(name="last_price", dtype="number", description="Latest price.", description_zh="最新价，单位：元。"),
    RequestField(name="pre_close", dtype="number", description="Previous close price.", description_zh="昨收价，单位：元。"),
    RequestField(name="open", dtype="number", description="Open price.", description_zh="开盘价，单位：元。"),
    RequestField(name="high", dtype="number", description="High price.", description_zh="最高价，单位：元。"),
    RequestField(name="low", dtype="number", description="Low price.", description_zh="最低价，单位：元。"),
    RequestField(name="change", dtype="number", description="Price change.", description_zh="涨跌额，单位：元。"),
    RequestField(
        name="change_pct",
        dtype="number",
        description="Percentage price change.",
        description_zh="百分比数值；例如 1.23 表示上涨 1.23%，-0.85 表示下跌 0.85%。",
    ),
    RequestField(
        name="open_change_pct",
        dtype="number",
        description="Opening price change percentage.",
        description_zh="开盘涨幅，派生计算：(开盘价 - 昨收价) / 昨收价 * 100。",
    ),
    RequestField(
        name="high_change_pct",
        dtype="number",
        description="High price change percentage.",
        description_zh="最高涨幅，派生计算：(最高价 - 昨收价) / 昨收价 * 100。",
    ),
    RequestField(
        name="low_change_pct",
        dtype="number",
        description="Low price change percentage.",
        description_zh="最低涨幅，派生计算：(最低价 - 昨收价) / 昨收价 * 100。",
    ),
    RequestField(
        name="amplitude_pct",
        dtype="number",
        description="Intraday amplitude percentage.",
        description_zh="百分比数值；按 (最高价 - 最低价) / 昨收价 * 100 计算。",
    ),
    RequestField(
        name="average_price",
        dtype="number",
        description="Average traded price derived from amount and volume.",
        description_zh="均价，派生计算：成交额 / (成交量 * 100)，单位：元。",
    ),
    RequestField(
        name="average_change_pct",
        dtype="number",
        description="Average price change percentage.",
        description_zh="均涨幅，派生计算：(均价 - 昨收价) / 昨收价 * 100。",
    ),
    RequestField(
        name="drawdown_pct",
        dtype="number",
        description="Intraday drawdown percentage from high to latest price.",
        description_zh="回头波，派生计算：(最高价 - 最新价) / 昨收价 * 100。",
    ),
    RequestField(
        name="attack_pct",
        dtype="number",
        description="Intraday attack percentage from low to latest price.",
        description_zh="攻击波，派生计算：(最新价 - 最低价) / 昨收价 * 100。",
    ),
    RequestField(
        name="volume",
        dtype="integer",
        description="Total traded volume, in lots for common A-share symbols.",
        description_zh="总成交量，单位：手。",
    ),
    RequestField(
        name="current_volume",
        dtype="integer",
        description="Current traded volume, in lots for common A-share symbols.",
        description_zh="最近一笔成交量，单位：手；不是累计成交量。",
    ),
    RequestField(name="amount", dtype="number", description="Decoded turnover amount.", description_zh="成交额，单位：元。"),
    RequestField(
        name="inside_volume",
        dtype="integer",
        description="Inside volume, in lots for common A-share symbols.",
        description_zh="内盘成交量，单位：手。",
    ),
    RequestField(
        name="outside_volume",
        dtype="integer",
        description="Outside volume, in lots for common A-share symbols.",
        description_zh="外盘成交量，单位：手。",
    ),
    RequestField(
        name="inside_outside_ratio",
        dtype="number",
        description="Inside/outside volume ratio.",
        description_zh="内外比，派生计算：内盘 / 外盘。",
    ),
    RequestField(name="open_amount", dtype="number", description="Opening turnover amount.", description_zh="开盘金额，单位：元。"),
    RequestField(
        name="open_amount_ratio_pct",
        dtype="number",
        description="Opening amount as a percentage of current turnover amount.",
        description_zh="开盘占比，派生计算：开盘金额 / 成交额 * 100。",
    ),
    RequestField(name="bid1_price", dtype="number", description="Best bid price.", description_zh="买一价，单位：元。"),
    RequestField(
        name="bid1_volume",
        dtype="integer",
        description="Best bid volume, in lots for common A-share symbols.",
        description_zh="买一量，单位：手。",
    ),
    RequestField(name="ask1_price", dtype="number", description="Best ask price.", description_zh="卖一价，单位：元。"),
    RequestField(
        name="ask1_volume",
        dtype="integer",
        description="Best ask volume, in lots for common A-share symbols.",
        description_zh="卖一量，单位：手。",
    ),
    RequestField(
        name="locked_amount",
        dtype="number",
        description="Limit-order locked amount estimated from best bid price and volume.",
        description_zh="封单额，按买一价 * 买一量 * 100 计算，单位：元。",
    ),
    RequestField(
        name="bid1_ask1_volume_diff",
        dtype="integer",
        description="Best bid volume minus best ask volume.",
        description_zh="买一量减卖一量，单位：手。",
    ),
    RequestField(
        name="bid1_ask1_balance_pct",
        dtype="number",
        description="Best bid/ask volume balance percentage.",
        description_zh="买一卖一量差占比，按 (买一量 - 卖一量) / (买一量 + 卖一量) * 100 计算。",
    ),
    RequestField(name="rise_speed", dtype="number", description="Rise speed percentage.", description_zh="涨速，百分比数值。"),
    RequestField(name="short_turnover", dtype="number", description="Short turnover percentage.", description_zh="短换手，百分比数值。"),
    RequestField(name="min2_amount", dtype="number", description="Two-minute turnover amount.", description_zh="近 2 分钟成交金额，单位：元。"),
    RequestField(name="opening_rush", dtype="number", description="Opening rush percentage.", description_zh="开盘抢筹，百分比数值。"),
    RequestField(
        name="vol_rise_speed",
        dtype="number",
        description="Volume rise-speed percentage.",
        description_zh="量涨速，百分比数值。",
    ),
    RequestField(
        name="entrust_ratio",
        dtype="number",
        description="Entrust ratio percentage.",
        description_zh="委比，百分比数值。",
    ),
    RequestField(
        name="activity",
        dtype="integer",
        description="Activity value carried by the realtime snapshot.",
        description_zh="活跃度，通达信实时快照携带的活跃度数值。",
    ),
)

REALTIME_RANK_FIELDS = (REALTIME_RANK_FIELD, *REALTIME_SNAPSHOT_FIELDS)


INDEX_CODE_FIELDS = (
    RequestField(name="instrument_id", dtype="string", description="AxData index code.", description_zh="AxData 统一指数代码，例如 000001.SH。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit index code.", description_zh="交易所原始六位指数代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed index code.", description_zh="TDX 带市场前缀代码，例如 sh000001。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="name", dtype="string", description="Index short name.", description_zh="指数简称。"),
    RequestField(name="index_type", dtype="string", description="Index type.", description_zh="指数类型：official_index 常规指数，tdx_block_index 通达信板块/行业/题材指数。"),
    RequestField(name="previous_close", dtype="number", description="Previous close from the TDX code table.", description_zh="代码表携带的昨收价。"),
)


INDEX_SNAPSHOT_FIELDS = (
    RequestField(name="instrument_id", dtype="string", description="AxData index code.", description_zh="AxData 统一指数代码，例如 000001.SH。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit index code.", description_zh="交易所原始六位指数代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed index code.", description_zh="TDX 带市场前缀代码，例如 sh000001。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="last_price", dtype="number", description="Latest index value.", description_zh="最新点位。"),
    RequestField(name="pre_close", dtype="number", description="Previous close index value.", description_zh="昨收点位。"),
    RequestField(name="open", dtype="number", description="Open index value.", description_zh="开盘点位。"),
    RequestField(name="high", dtype="number", description="High index value.", description_zh="最高点位。"),
    RequestField(name="low", dtype="number", description="Low index value.", description_zh="最低点位。"),
    RequestField(name="change", dtype="number", description="Index change.", description_zh="涨跌点数。"),
    RequestField(name="change_pct", dtype="number", description="Index percentage change.", description_zh="涨跌幅，百分比数值。"),
    RequestField(name="open_change_pct", dtype="number", description="Open percentage change.", description_zh="开盘涨幅，百分比数值。"),
    RequestField(name="high_change_pct", dtype="number", description="High percentage change.", description_zh="最高涨幅，百分比数值。"),
    RequestField(name="low_change_pct", dtype="number", description="Low percentage change.", description_zh="最低涨幅，百分比数值。"),
    RequestField(name="amplitude_pct", dtype="number", description="Intraday amplitude percentage.", description_zh="振幅，百分比数值。"),
    RequestField(name="volume", dtype="integer", description="Total traded volume carried by the index quote.", description_zh="指数快照携带的成交量。"),
    RequestField(name="current_volume", dtype="integer", description="Current volume carried by the index quote.", description_zh="指数快照携带的最近成交量。"),
    RequestField(name="amount", dtype="number", description="Turnover amount carried by the index quote.", description_zh="指数快照携带的成交额，单位：元。"),
    RequestField(name="open_amount", dtype="number", description="Opening turnover amount.", description_zh="开盘金额，单位：元。"),
    RequestField(name="rise_speed", dtype="number", description="Rise speed percentage.", description_zh="涨速，百分比数值。"),
    RequestField(name="activity", dtype="integer", description="Activity value carried by the realtime snapshot.", description_zh="活跃度。"),
)


INDEX_RANK_FIELDS = (REALTIME_RANK_FIELD, *INDEX_SNAPSHOT_FIELDS)


INDEX_KLINE_FIELDS = (
    RequestField(name="instrument_id", dtype="string", description="AxData index code.", description_zh="AxData 统一指数代码，例如 000001.SH。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit index code.", description_zh="交易所原始六位指数代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed index code.", description_zh="TDX 带市场前缀代码，例如 sh000001。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="trade_time", dtype="datetime/string", description="Bar timestamp.", description_zh="K 线时间。"),
    RequestField(name="period", dtype="string", description="K-line period.", description_zh="K 线周期。"),
    RequestField(name="open", dtype="number", description="Open index value.", description_zh="开盘点位。"),
    RequestField(name="high", dtype="number", description="High index value.", description_zh="最高点位。"),
    RequestField(name="low", dtype="number", description="Low index value.", description_zh="最低点位。"),
    RequestField(name="close", dtype="number", description="Close index value.", description_zh="收盘点位。"),
    RequestField(name="volume", dtype="number", description="Volume carried by the index K-line.", description_zh="指数 K 线成交量。"),
    RequestField(name="amount", dtype="number", description="Turnover amount carried by the index K-line.", description_zh="指数 K 线成交额，单位：元。"),
    RequestField(name="up_count", dtype="integer", description="Number of rising constituents carried by the index K-line.", description_zh="上涨家数。"),
    RequestField(name="down_count", dtype="integer", description="Number of falling constituents carried by the index K-line.", description_zh="下跌家数。"),
)


ETF_CODE_FIELDS = (
    RequestField(name="instrument_id", dtype="string", description="AxData ETF code.", description_zh="AxData 统一 ETF 代码，例如 510050.SH。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit ETF code.", description_zh="交易所原始六位 ETF 代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed ETF code.", description_zh="TDX 带市场前缀代码，例如 sh510050。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE 或 SZSE。"),
    RequestField(name="name", dtype="string", description="ETF short name.", description_zh="ETF 简称。"),
    RequestField(name="previous_close", dtype="number", description="Previous close from the TDX code table.", description_zh="代码表携带的昨收价。"),
)


ETF_SNAPSHOT_FIELDS = INDEX_SNAPSHOT_FIELDS
ETF_RANK_FIELDS = (REALTIME_RANK_FIELD, *ETF_SNAPSHOT_FIELDS)
ETF_KLINE_FIELDS = INDEX_KLINE_FIELDS


LIMIT_LADDER_FIELDS = (
    RequestField(name="trade_date", dtype="date/string", description="Current ladder trade date.", description_zh="天梯日期，也就是这张连板天梯对应的交易日。"),
    RequestField(name="ladder_level", dtype="integer", description="Current consecutive limit-up level.", description_zh="当前连板高度；封住涨停时按历史连板数加今天计算。"),
    RequestField(name="limit_board_text", dtype="string", description="Combined N-days/M-limit-up text.", description_zh="连板状态，也就是几天几板，例如 7天5板。"),
    RequestField(name="instrument_id", dtype="string", description="AxData security code.", description_zh="AxData 统一证券代码，例如 000001.SZ。"),
    RequestField(name="name", dtype="string", description="Security short name.", description_zh="证券简称。"),
    RequestField(name="last_price", dtype="number", description="Latest price.", description_zh="最新价，单位：元。"),
    RequestField(name="change_pct", dtype="number", description="Current price-change percentage.", description_zh="当前涨跌幅，百分比数值。"),
    RequestField(name="limit_status", dtype="string", description="sealed or touched.", description_zh="涨停状态：sealed 当前封住涨停；touched 盘中触及涨停但当前未封住。"),
    RequestField(name="amount", dtype="number", description="Current turnover amount.", description_zh="当前成交额，单位：元。"),
    RequestField(name="seal_amount", dtype="number", description="Current limit-order seal amount.", description_zh="当前封单额，单位：元。"),
    RequestField(name="seal_to_amount_ratio", dtype="number", description="Seal amount divided by current turnover amount.", description_zh="封成比，按封单额 / 当前成交额计算。"),
    RequestField(name="free_float_market_value", dtype="number", description="TDX free-float market value.", description_zh="流通市值Z，按流通股本Z * 当前价计算，单位：元。"),
    RequestField(name="primary_theme", dtype="string", description="Primary theme name.", description_zh="主题材；过滤噪音题材后，优先按题材内涨停数排序，其次看最高板、连板数和个股关联度，取排序第一的一个题材。"),
    RequestField(name="secondary_themes", dtype="string", description="Secondary theme names joined by plus signs.", description_zh="辅助题材；从主题材之后的有效题材中最多取三个，用 + 连接。"),
    RequestField(name="year_limit_up_days", dtype="integer", description="Limit-up days in the current year.", description_zh="年内涨停天数。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit security code.", description_zh="交易所原始六位代码。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="pre_close", dtype="number", description="Previous close price.", description_zh="昨收价，单位：元。"),
    RequestField(name="limit_up_price", dtype="number", description="Calculated limit-up price.", description_zh="按昨收价和涨跌停规则计算的涨停价，单位：元。"),
)


THEME_STRENGTH_RANK_FIELDS = (
    RequestField(name="rank", dtype="integer", description="Theme ranking number.", description_zh="题材排行名次。"),
    RequestField(name="trade_date", dtype="date/string", description="Ranking trade date.", description_zh="排行日期，也就是这张题材强度排行对应的交易日。"),
    RequestField(name="topic_type", dtype="string", description="Topic type used for ranking.", description_zh="题材类型：theme 主题题材，sector 板块题材。"),
    RequestField(name="topic_name", dtype="string", description="Theme name.", description_zh="题材名称。"),
    RequestField(name="topic_id", dtype="string", description="Theme ID when available.", description_zh="题材 ID；源端没有给出时为空。"),
    RequestField(name="theme_strength_score", dtype="number", description="Derived theme strength score.", description_zh="题材强度分，用于排序；按涨停数量、最高板和连板股数量综合计算。"),
    RequestField(name="limit_up_count", dtype="integer", description="Sealed limit-up stock count in this theme.", description_zh="题材内当前封住涨停的股票数量。"),
    RequestField(name="highest_ladder_level", dtype="integer", description="Highest ladder level in this theme.", description_zh="题材内最高连板高度。"),
    RequestField(name="lianban_stock_count", dtype="integer", description="Count of stocks with two or more consecutive limit-ups.", description_zh="题材内连板股数量，指二连板及以上股票数量。"),
    RequestField(name="first_board_count", dtype="integer", description="Count of first-board limit-up stocks.", description_zh="题材内首板股票数量。"),
    RequestField(name="leader_instrument_id", dtype="string", description="Leader stock code in this theme.", description_zh="题材内高度最高的代表股票代码。"),
    RequestField(name="leader_name", dtype="string", description="Leader stock short name.", description_zh="题材内高度最高的代表股票简称。"),
    RequestField(name="leader_ladder_level", dtype="integer", description="Leader stock ladder level.", description_zh="代表股票连板高度。"),
    RequestField(name="leader_limit_board_text", dtype="string", description="Leader stock N-days/M-limit-up text.", description_zh="代表股票连板状态，例如 7天5板。"),
    RequestField(name="leader_seal_amount", dtype="number", description="Leader stock seal amount.", description_zh="代表股票当前封单额，单位：元。"),
    RequestField(name="seal_amount_sum", dtype="number", description="Total seal amount for stocks in this theme.", description_zh="题材内涨停股封单额合计，单位：元。"),
    RequestField(name="amount_sum", dtype="number", description="Total turnover amount for stocks in this theme.", description_zh="题材内涨停股成交额合计，单位：元。"),
    RequestField(name="top_stock_summary", dtype="string", description="Top stock summary text.", description_zh="题材内代表股票摘要，按连板高度和封单额排序。"),
)


TRADE_DETAIL_TODAY_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="trade_time",
        dtype="time/string",
        description="Intraday trade time, HH:MM.",
        description_zh="成交时间，HH:MM。",
    ),
    RequestField(
        name="trade_index",
        dtype="integer",
        description="TDX pagination index of the trade-detail record.",
        description_zh="成交明细序号，用于保持同一标的返回记录的相对顺序。",
    ),
    RequestField(
        name="price",
        dtype="number",
        description="Trade price.",
        description_zh="成交价。",
    ),
    RequestField(
        name="volume",
        dtype="number",
        description="Trade volume in lots for common A-share symbols.",
        description_zh="成交量，A 股常见口径为手。",
    ),
    RequestField(
        name="order_count",
        dtype="integer",
        description="Order count or aggregated trade count carried by the TDX detail record.",
        description_zh="成交笔数 / 聚合笔数。",
    ),
    RequestField(
        name="side",
        dtype="string",
        description="Trade direction label decoded from TDX status: buy, sell, neutral, or status_N.",
        description_zh="成交方向：buy、sell、neutral；少数未识别状态会保留原始状态标记，实测为盘后定价成交。",
    ),
)


TRADE_DETAIL_HISTORY_FIELDS = (
    TRADE_DETAIL_TODAY_FIELDS[0],
    TRADE_DETAIL_TODAY_FIELDS[1],
    TRADE_DETAIL_TODAY_FIELDS[2],
    TRADE_DETAIL_TODAY_FIELDS[3],
    RequestField(
        name="trade_date",
        dtype="date/string",
        description="Trading date, YYYYMMDD.",
        description_zh="交易日期，YYYYMMDD。",
    ),
    TRADE_DETAIL_TODAY_FIELDS[4],
    RequestField(
        name="trade_datetime",
        dtype="datetime/string",
        description="Trade timestamp composed from trade_date and trade_time.",
        description_zh="成交日期时间，由 trade_date 和 trade_time 组合得到。",
    ),
    TRADE_DETAIL_TODAY_FIELDS[5],
    TRADE_DETAIL_TODAY_FIELDS[6],
    TRADE_DETAIL_TODAY_FIELDS[7],
    TRADE_DETAIL_TODAY_FIELDS[8],
    TRADE_DETAIL_TODAY_FIELDS[9],
)


AUCTION_PROCESS_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="auction_time",
        dtype="time/string",
        description="Call-auction process time, HH:MM:SS.",
        description_zh="竞价过程时间，格式 HH:MM:SS。",
    ),
    RequestField(
        name="auction_index",
        dtype="integer",
        description="Zero-based record index in the returned auction process series.",
        description_zh="竞价过程记录序号，从 0 开始。",
    ),
    RequestField(
        name="price",
        dtype="number",
        description="Call-auction price.",
        description_zh="竞价价格，单位：元。",
    ),
    RequestField(
        name="matched_volume",
        dtype="integer",
        description="Matched auction volume.",
        description_zh="撮合量，A 股常见口径为手。",
    ),
    RequestField(
        name="matched_amount_estimated",
        dtype="number",
        description="Estimated matched amount: price * matched_volume * 100.",
        description_zh="估算撮合金额，按 竞价价格 * 撮合量 * 100 计算，单位：元。",
    ),
    RequestField(
        name="unmatched_volume",
        dtype="integer",
        description="Absolute unmatched volume.",
        description_zh="未撮合量绝对值。",
    ),
    RequestField(
        name="unmatched_amount_estimated",
        dtype="number",
        description="Estimated unmatched amount: price * unmatched_volume * 100.",
        description_zh="估算未撮合金额，按 竞价价格 * 未撮合量 * 100 计算，单位：元。",
    ),
    RequestField(
        name="unmatched_direction",
        dtype="integer",
        description="Derived unmatched direction marker: 1 for positive, -1 for negative, and 0 for zero unmatched volume.",
        description_zh="未撮合方向：正数为 1，负数为 -1，未撮合量为 0 时为 0。",
    ),
)


AUCTION_RESULT_TODAY_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="auction_time",
        dtype="time/string",
        description="Opening auction result time, fixed to 09:25 when present in trade detail.",
        description_zh="竞价结果时间，从成交明细中筛选 09:25。",
    ),
    RequestField(
        name="trade_index",
        dtype="integer",
        description="TDX trade-detail index of the 09:25 record.",
        description_zh="09:25 成交明细在源端返回中的序号。",
    ),
    RequestField(
        name="price",
        dtype="number",
        description="Opening auction result price.",
        description_zh="竞价结果价格，单位：元。",
    ),
    RequestField(
        name="volume",
        dtype="number",
        description="Opening auction result volume in lots for common A-share symbols.",
        description_zh="竞价结果成交量，A 股常见口径为手。",
    ),
    RequestField(
        name="amount",
        dtype="number",
        description="Estimated amount: price * volume * 100.",
        description_zh="竞价结果成交额，按 价格 * 成交量 * 100 计算，单位：元。",
    ),
    RequestField(
        name="order_count",
        dtype="integer",
        description="Order count or aggregated trade count carried by the TDX 09:25 record.",
        description_zh="09:25 成交笔数 / 聚合笔数。",
    ),
)


AUCTION_RESULT_HISTORY_FIELDS = (
    AUCTION_RESULT_TODAY_FIELDS[0],
    AUCTION_RESULT_TODAY_FIELDS[1],
    AUCTION_RESULT_TODAY_FIELDS[2],
    AUCTION_RESULT_TODAY_FIELDS[3],
    RequestField(
        name="trade_date",
        dtype="date/string",
        description="Trading date, YYYYMMDD, from the historical request parameter.",
        description_zh="交易日期，YYYYMMDD；由历史接口 trade_date 参数确定。",
    ),
    AUCTION_RESULT_TODAY_FIELDS[4],
    RequestField(
        name="auction_datetime",
        dtype="datetime/string",
        description="Auction result timestamp composed from trade_date and 09:25.",
        description_zh="竞价结果日期时间，由 trade_date 和 09:25 组合得到。",
    ),
    AUCTION_RESULT_TODAY_FIELDS[5],
    AUCTION_RESULT_TODAY_FIELDS[6],
    AUCTION_RESULT_TODAY_FIELDS[7],
    AUCTION_RESULT_TODAY_FIELDS[8],
    AUCTION_RESULT_TODAY_FIELDS[9],
)

AUCTION_INDICATOR_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(name="symbol", dtype="string", description="Raw six-digit security code.", description_zh="交易所原始六位代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed code.", description_zh="TDX 带市场前缀代码，例如 sz000001。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="stats_date", dtype="date/string", description="Statistics date of tdxstat/tdxstat2.", description_zh="历史统计分母日期，来自 tdxstat/tdxstat2。"),
    RequestField(name="open_price", dtype="number", description="Opening price.", description_zh="开盘价，单位：元。"),
    RequestField(name="pre_close", dtype="number", description="Previous close price.", description_zh="昨收价，单位：元。"),
    RequestField(name="open_change_pct", dtype="number", description="Opening price change percentage.", description_zh="开盘涨幅，百分比数值。"),
    RequestField(name="open_amount", dtype="number", description="Opening auction amount.", description_zh="开盘金额，单位：元。"),
    RequestField(name="open_volume_hand", dtype="number", description="Estimated opening auction volume in lots.", description_zh="开盘成交量，按 开盘金额 / 开盘价 / 100 估算，单位：手。"),
    RequestField(name="open_volume_ratio", dtype="number", description="Opening volume ratio versus last five full trading days.", description_zh="开盘量比，按开盘成交量 / 近 5 个完整交易日平均每分钟成交量计算。"),
    RequestField(name="open_turnover_z", dtype="number", description="Opening turnover on free-float shares.", description_zh="开盘换手Z，按开盘成交量 / 流通股本Z 计算，百分比数值。"),
    RequestField(name="open_prev_amount_ratio", dtype="number", description="Opening amount versus previous-day turnover amount.", description_zh="开盘昨比，按开盘金额 / 昨成交额 * 100 计算。"),
    RequestField(name="auction_prev_volume_ratio", dtype="number", description="Opening auction volume versus previous opening auction volume.", description_zh="竞价昨比，按今日开盘成交量 / 昨开盘成交量计算。"),
    RequestField(name="opening_rush", dtype="number", description="TDX opening rush value.", description_zh="开盘抢筹，通达信实时快照携带的百分比数值。"),
    RequestField(name="open_prev_seal_ratio", dtype="number", description="Opening amount versus previous-day limit-order seal amount.", description_zh="开盘昨封比，按开盘金额 / 昨封单额 * 100 计算。"),
    RequestField(name="prev_amount", dtype="number", description="Previous-day turnover amount.", description_zh="昨成交额，单位：元。"),
    RequestField(name="prev_seal_amount", dtype="number", description="Previous-day seal amount.", description_zh="昨封单额，单位：元；负值通常表示昨日收盘跌停封单。"),
    RequestField(name="prev2_seal_amount", dtype="number", description="Previous-previous-day seal amount.", description_zh="前封单额，单位：元。"),
    RequestField(name="prev_open_volume_hand", dtype="number", description="Previous-day opening auction volume.", description_zh="昨开盘成交量，单位：手。"),
    RequestField(name="prev_open_amount", dtype="number", description="Previous-day opening auction amount.", description_zh="昨开盘金额，单位：元。"),
    RequestField(name="float_shares", dtype="number", description="Common float shares.", description_zh="流通股，普通财务口径，单位：股。"),
    RequestField(name="float_market_value", dtype="number", description="Common float market value.", description_zh="流通市值，按流通股 * 当前价计算，单位：元。"),
    RequestField(name="free_float_shares", dtype="number", description="TDX free-float shares.", description_zh="流通股本Z（自由流通股本口径），单位：股。"),
    RequestField(name="free_float_market_value", dtype="number", description="TDX free-float market value.", description_zh="流通市值Z，按流通股本Z * 当前价计算，单位：元。"),
    RequestField(name="seal_amount", dtype="number", description="Current limit-order seal amount.", description_zh="封单额，单位：元。"),
    RequestField(name="seal_to_amount_ratio", dtype="number", description="Seal amount divided by current turnover amount.", description_zh="封成比，按封单额 / 当前成交额计算。"),
    RequestField(name="seal_to_float_ratio", dtype="number", description="Seal amount divided by free-float market value.", description_zh="封流比，按封单额 / 流通市值Z * 100 计算。"),
    RequestField(name="seal_prev_ratio", dtype="number", description="Seal amount divided by previous-day seal amount.", description_zh="封昨比，按当前封单额 / 昨封单额计算。"),
    RequestField(name="limit_stat_days", dtype="integer", description="Window days for N-days/M-limit-up display.", description_zh="几天几板统计天数。"),
    RequestField(name="limit_up_count_in_stat_days", dtype="integer", description="Limit-up count in the N-day window.", description_zh="几天几板中的涨停数。"),
    RequestField(name="limit_board_text", dtype="string", description="Combined N-days/M-limit-up text.", description_zh="几天几板文本，例如 7天5板。"),
    RequestField(name="limit_up_streak_days", dtype="integer", description="Current consecutive limit-up days.", description_zh="连板天数。"),
    RequestField(name="year_limit_up_days", dtype="integer", description="Limit-up days in the current year.", description_zh="年涨停天数。"),
)


INTRADAY_BUY_SELL_STRENGTH_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="minute_time",
        dtype="string",
        description="Intraday time derived from minute_index using the TDX subchart time axis, in HH:MM.",
        description_zh="按 TDX 分时副图横轴由 minute_index 派生的时间，格式 HH:MM。",
    ),
    RequestField(
        name="minute_index",
        dtype="integer",
        description="Zero-based point index in the returned current intraday subchart.",
        description_zh="当前分时副图点序号，从 0 开始。",
    ),
    RequestField(
        name="bid_order",
        dtype="number",
        description="Bid-order value displayed as 委买 in the TDX buy/sell strength subchart.",
        description_zh="TDX 买卖力道副图显示的委买。",
    ),
    RequestField(
        name="ask_order",
        dtype="number",
        description="Ask-order value displayed as 委卖 in the TDX buy/sell strength subchart.",
        description_zh="TDX 买卖力道副图显示的委卖。",
    ),
)


INTRADAY_VOLUME_COMPARISON_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="minute_time",
        dtype="string",
        description="Intraday time derived from minute_index using the TDX subchart time axis, in HH:MM.",
        description_zh="按 TDX 分时副图横轴由 minute_index 派生的时间，格式 HH:MM。",
    ),
    RequestField(
        name="minute_index",
        dtype="integer",
        description="Zero-based point index in the returned current intraday subchart.",
        description_zh="当前分时副图点序号，从 0 开始。",
    ),
    RequestField(
        name="today_volume",
        dtype="number",
        description="Current day's cumulative volume at this intraday point.",
        description_zh="今日成交量，TDX 成交对比副图中的今日累计成交量。",
    ),
    RequestField(
        name="yesterday_volume",
        dtype="number",
        description="Previous trading day's cumulative volume at the same intraday point.",
        description_zh="昨日成交量，TDX 成交对比副图中的昨日同分时点累计成交量。",
    ),
    RequestField(
        name="volume_change",
        dtype="number",
        description="today_volume minus yesterday_volume.",
        description_zh="变动量，今日成交量减昨日成交量。",
    ),
    RequestField(
        name="volume_change_pct",
        dtype="number",
        description="Percentage change from yesterday_volume to today_volume.",
        description_zh="变动比例，百分比数值；例如 34.44 表示 34.44%。",
    ),
)


FINANCE_FIELD_MAP = {
    "instrument_id": RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    "symbol": RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    "tdx_code": RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    "exchange": RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    "updated_date": RequestField(
        name="updated_date",
        dtype="date/string",
        description="Finance snapshot update/report date, YYYYMMDD.",
        description_zh="财务快照更新/报告日期，YYYYMMDD。",
    ),
    "ipo_date": RequestField(
        name="ipo_date",
        dtype="date/string",
        description="Listing date carried by the TDX finance snapshot, YYYYMMDD.",
        description_zh="TDX 财务快照携带的上市日期，YYYYMMDD。",
    ),
    "total_share": RequestField(
        name="total_share",
        dtype="number",
        description="Total share capital, unit: shares.",
        description_zh="总股本，单位：股。",
    ),
    "float_share": RequestField(
        name="float_share",
        dtype="number",
        description="Floating share capital, unit: shares.",
        description_zh="流通股本，单位：股。",
    ),
    "state_share": RequestField(
        name="state_share",
        dtype="number",
        description="State-owned share amount, unit: shares.",
        description_zh="国家股，单位：股。",
    ),
    "founder_legal_person_share": RequestField(
        name="founder_legal_person_share",
        dtype="number",
        description="Founder legal-person share amount, unit: shares.",
        description_zh="发起法人股，单位：股。",
    ),
    "legal_person_share": RequestField(
        name="legal_person_share",
        dtype="number",
        description="Legal-person share amount, unit: shares.",
        description_zh="法人股，单位：股。",
    ),
    "b_share": RequestField(
        name="b_share",
        dtype="number",
        description="B-share amount, unit: shares.",
        description_zh="B 股股本，单位：股。",
    ),
    "h_share": RequestField(
        name="h_share",
        dtype="number",
        description="H-share amount, unit: shares.",
        description_zh="H 股股本，单位：股。",
    ),
    "shareholder_count": RequestField(
        name="shareholder_count",
        dtype="integer",
        description="Shareholder count carried by the TDX finance snapshot.",
        description_zh="股东人数。",
    ),
    "eps": RequestField(
        name="eps",
        dtype="number",
        description="Earnings per share, unit: yuan/share.",
        description_zh="每股收益，单位：元/股。",
    ),
    "bps": RequestField(
        name="bps",
        dtype="number",
        description="Book value per share, unit: yuan/share.",
        description_zh="每股净资产，单位：元/股。",
    ),
    "total_assets": RequestField(
        name="total_assets",
        dtype="number",
        description="Total assets, unit: yuan.",
        description_zh="总资产，单位：元。",
    ),
    "current_assets": RequestField(
        name="current_assets",
        dtype="number",
        description="Current assets, unit: yuan.",
        description_zh="流动资产，单位：元。",
    ),
    "fixed_assets": RequestField(
        name="fixed_assets",
        dtype="number",
        description="Fixed assets, unit: yuan.",
        description_zh="固定资产，单位：元。",
    ),
    "intangible_assets": RequestField(
        name="intangible_assets",
        dtype="number",
        description="Intangible assets, unit: yuan.",
        description_zh="无形资产，单位：元。",
    ),
    "current_liabilities": RequestField(
        name="current_liabilities",
        dtype="number",
        description="Current liabilities, unit: yuan.",
        description_zh="流动负债，单位：元。",
    ),
    "long_term_liabilities": RequestField(
        name="long_term_liabilities",
        dtype="number",
        description="Long-term liabilities, unit: yuan.",
        description_zh="长期负债，单位：元。",
    ),
    "capital_reserve": RequestField(
        name="capital_reserve",
        dtype="number",
        description="Capital reserve, unit: yuan.",
        description_zh="资本公积金，单位：元。",
    ),
    "net_assets": RequestField(
        name="net_assets",
        dtype="number",
        description="Net assets, unit: yuan.",
        description_zh="净资产，单位：元。",
    ),
    "accounts_receivable": RequestField(
        name="accounts_receivable",
        dtype="number",
        description="Accounts receivable, unit: yuan.",
        description_zh="应收账款，单位：元。",
    ),
    "inventory": RequestField(
        name="inventory",
        dtype="number",
        description="Inventory, unit: yuan.",
        description_zh="存货，单位：元。",
    ),
    "revenue": RequestField(
        name="revenue",
        dtype="number",
        description="Revenue, unit: yuan.",
        description_zh="营业收入，单位：元。",
    ),
    "main_business_profit": RequestField(
        name="main_business_profit",
        dtype="number",
        description="Main-business profit, unit: yuan.",
        description_zh="主营业务利润，单位：元。",
    ),
    "operating_profit": RequestField(
        name="operating_profit",
        dtype="number",
        description="Operating profit, unit: yuan.",
        description_zh="营业利润，单位：元。",
    ),
    "investment_income": RequestField(
        name="investment_income",
        dtype="number",
        description="Investment income, unit: yuan.",
        description_zh="投资收益，单位：元。",
    ),
    "operating_cashflow": RequestField(
        name="operating_cashflow",
        dtype="number",
        description="Operating cash flow, unit: yuan.",
        description_zh="经营现金流量，单位：元。",
    ),
    "total_cashflow": RequestField(
        name="total_cashflow",
        dtype="number",
        description="Total cash flow, unit: yuan.",
        description_zh="总现金流量，单位：元。",
    ),
    "total_profit": RequestField(
        name="total_profit",
        dtype="number",
        description="Total profit, unit: yuan.",
        description_zh="利润总额，单位：元。",
    ),
    "after_tax_profit": RequestField(
        name="after_tax_profit",
        dtype="number",
        description="After-tax profit, unit: yuan.",
        description_zh="税后利润，单位：元。",
    ),
    "net_profit": RequestField(
        name="net_profit",
        dtype="number",
        description="Net profit, unit: yuan.",
        description_zh="净利润，单位：元。",
    ),
    "undistributed_profit": RequestField(
        name="undistributed_profit",
        dtype="number",
        description="Undistributed profit, unit: yuan.",
        description_zh="未分配利润，单位：元。",
    ),
    "province_raw": RequestField(
        name="province_raw",
        dtype="integer",
        description="TDX raw region/province code carried by the finance snapshot.",
        description_zh="TDX 财务快照携带的地区/省份原始码。",
    ),
    "province_name": RequestField(
        name="province_name",
        dtype="string",
        description="Region/province name mapped from province_raw by AxData TDX region tables.",
        description_zh="由 province_raw 通过 AxData TDX 地区码表映射得到的地区/省份名称。",
    ),
    "province_board_name": RequestField(
        name="province_board_name",
        dtype="string",
        description="TDX region board name mapped from province_raw by AxData TDX region tables.",
        description_zh="由 province_raw 通过 AxData TDX 地区码表映射得到的地区板块名称。",
    ),
    "province_board_code": RequestField(
        name="province_board_code",
        dtype="string",
        description="TDX region board code mapped from province_raw by AxData TDX region tables.",
        description_zh="由 province_raw 通过 AxData TDX 地区码表映射得到的地区板块代码。",
    ),
    "industry_raw": RequestField(
        name="industry_raw",
        dtype="integer",
        description="TDX raw industry code carried by the finance snapshot.",
        description_zh="TDX 财务快照携带的行业原始码。",
    ),
    "tdx_industry_code": RequestField(
        name="tdx_industry_code",
        dtype="string",
        description="TDX industry board code mapped from the stock code by AxData TDX industry tables.",
        description_zh="由股票代码通过 AxData TDX 行业码表映射得到的行业板块代码。",
    ),
    "tdx_industry_name": RequestField(
        name="tdx_industry_name",
        dtype="string",
        description="TDX industry board name mapped from the stock code by AxData TDX industry tables.",
        description_zh="由股票代码通过 AxData TDX 行业码表映射得到的行业板块名称。",
    ),
    "tdx_industry_path": RequestField(
        name="tdx_industry_path",
        dtype="string",
        description="TDX industry board path mapped from the stock code by AxData TDX industry tables.",
        description_zh="由股票代码通过 AxData TDX 行业码表映射得到的行业板块路径。",
    ),
    "tdx_research_industry_code": RequestField(
        name="tdx_research_industry_code",
        dtype="string",
        description="TDX research industry code mapped from the stock code by AxData TDX industry tables.",
        description_zh="由股票代码通过 AxData TDX 行业码表映射得到的研究行业代码。",
    ),
    "tdx_research_industry_name": RequestField(
        name="tdx_research_industry_name",
        dtype="string",
        description="TDX research industry name mapped from the stock code by AxData TDX industry tables.",
        description_zh="由股票代码通过 AxData TDX 行业码表映射得到的研究行业名称。",
    ),
    "tdx_research_industry_path": RequestField(
        name="tdx_research_industry_path",
        dtype="string",
        description="TDX research industry path mapped from the stock code by AxData TDX industry tables.",
        description_zh="由股票代码通过 AxData TDX 行业码表映射得到的研究行业路径。",
    ),
}


def _finance_fields(*names: str) -> tuple[RequestField, ...]:
    return tuple(FINANCE_FIELD_MAP[name] for name in names)


FINANCE_SUMMARY_FIELDS = _finance_fields(
    "instrument_id",
    "symbol",
    "tdx_code",
    "exchange",
    "updated_date",
    "ipo_date",
    "total_share",
    "float_share",
    "eps",
    "bps",
    "total_assets",
    "net_assets",
    "revenue",
    "net_profit",
    "operating_cashflow",
    "shareholder_count",
)


FINANCE_SHARE_CAPITAL_FIELDS = _finance_fields(
    "instrument_id",
    "symbol",
    "tdx_code",
    "exchange",
    "updated_date",
    "total_share",
    "float_share",
    "state_share",
    "founder_legal_person_share",
    "legal_person_share",
    "b_share",
    "h_share",
    "shareholder_count",
)


FINANCE_BALANCE_FIELDS = _finance_fields(
    "instrument_id",
    "symbol",
    "tdx_code",
    "exchange",
    "updated_date",
    "total_assets",
    "current_assets",
    "fixed_assets",
    "intangible_assets",
    "current_liabilities",
    "long_term_liabilities",
    "capital_reserve",
    "net_assets",
    "accounts_receivable",
    "inventory",
)


FINANCE_PROFIT_CASHFLOW_FIELDS = _finance_fields(
    "instrument_id",
    "symbol",
    "tdx_code",
    "exchange",
    "updated_date",
    "revenue",
    "main_business_profit",
    "operating_profit",
    "investment_income",
    "operating_cashflow",
    "total_cashflow",
    "total_profit",
    "after_tax_profit",
    "net_profit",
    "undistributed_profit",
    "eps",
    "bps",
)


FINANCE_PROFILE_FIELDS = _finance_fields(
    "instrument_id",
    "symbol",
    "tdx_code",
    "exchange",
    "updated_date",
    "ipo_date",
    "province_raw",
    "province_name",
    "province_board_name",
    "province_board_code",
    "industry_raw",
    "tdx_industry_code",
    "tdx_industry_name",
    "tdx_industry_path",
    "tdx_research_industry_code",
    "tdx_research_industry_name",
    "tdx_research_industry_path",
)


FINANCE_CODE_PARAMETER = RequestParameter(
    name="code",
    dtype="string/list",
    required=True,
    description=(
        "Security code, for example 000001, 000001.SZ, or sz000001. "
        "Multiple codes can be a list or comma-separated string."
    ),
    description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
)


FINANCE_MAP_ROOT_PARAMETER = RequestParameter(
    name="map_root",
    dtype="string",
    required=False,
    description=(
        "Optional local TDX directory used to refresh finance profile mappings. "
        "The directory may contain incon.dat and T0002/hq_cache/tdxzs.cfg/tdxhy.cfg."
    ),
    description_zh=(
        "可选本地 TDX 码表目录；不传时使用 AxData 内置映射快照，传入时从该目录读取 "
        "incon.dat、tdxzs.cfg、tdxhy.cfg 更新地区和行业映射。"
    ),
)


FINANCE_EXAMPLE_ROW = {
    "instrument_id": "000001.SZ",
    "symbol": "000001",
    "tdx_code": "sz000001",
    "exchange": "SZSE",
    "updated_date": "20260425",
    "ipo_date": "19910403",
    "total_share": 19405918750.0,
    "float_share": 19405601250.0,
    "state_share": 0.0,
    "founder_legal_person_share": 0.0,
    "legal_person_share": 0.0,
    "b_share": 0.0,
    "h_share": 0.0,
    "shareholder_count": 457610,
    "eps": 0.67,
    "bps": 23.91,
    "total_assets": 35277000000.0,
    "current_assets": 1000000.0,
    "fixed_assets": 2000000.0,
    "intangible_assets": 3000000.0,
    "current_liabilities": 4000000.0,
    "long_term_liabilities": 5000000.0,
    "capital_reserve": 6000000.0,
    "net_assets": 7000000.0,
    "accounts_receivable": 9000000.0,
    "inventory": 14000000.0,
    "revenue": 35277000000.0,
    "main_business_profit": 8000000.0,
    "operating_profit": 10000000.0,
    "investment_income": 11000000.0,
    "operating_cashflow": 12000000.0,
    "total_cashflow": 13000000.0,
    "total_profit": 15000000.0,
    "after_tax_profit": 16000000.0,
    "net_profit": 14523000000.0,
    "undistributed_profit": 17000000.0,
    "province_raw": 18,
    "province_name": "深圳",
    "province_board_name": "深圳板块",
    "province_board_code": "880218",
    "industry_raw": 101,
    "tdx_industry_code": "T1001",
    "tdx_industry_name": "银行",
    "tdx_industry_path": "金融 / 银行",
    "tdx_research_industry_code": "X500102",
    "tdx_research_industry_name": "股份制银行",
    "tdx_research_industry_path": "银行 / 全国性银行 / 股份制银行",
}


def _finance_interface(
    *,
    name: str,
    display_name_zh: str,
    fields: tuple[RequestField, ...],
    view_zh: str,
    example_fields: tuple[str, ...],
    parameters: tuple[RequestParameter, ...] = (FINANCE_CODE_PARAMETER,),
    description_extra: str = "",
) -> SourceRequestInterface:
    return SourceRequestInterface(
        name=name,
        display_name_zh=display_name_zh,
        source_code="tdx",
        source_name_zh="通达信",
        category="财务数据",
        request_mode="source_request",
        first_stage_strategy=f"临时请求通达信 0x0010 财务信息快照，并按{view_zh}视图返回，默认不入库。",
        source_ability="TDX 7709 0x0010 finance-info batch request",
        description=(
            "Request the TDX 0x0010 compact finance-info snapshot and expose a focused "
            f"{name} field view. This is a finance summary/snapshot interface, not a full "
            "F10 financial-statement replacement. Units are normalized by AxData: share "
            "capital fields are shares, amount fields are yuan, and per-share fields are "
            "yuan/share. Empty all-zero upstream records are filtered."
            f"{description_extra}"
        ),
        parameters=parameters,
        fields=fields,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": list(example_fields),
                "persist": False,
            },
            response=(
                {field.name: FINANCE_EXAMPLE_ROW.get(field.name) for field in fields},
            ),
        ),
    )


def _f10_fields(fields: tuple[F10FieldSpec, ...]) -> tuple[RequestField, ...]:
    return tuple(
        RequestField(
            name=field.name,
            dtype=field.dtype,
            description=field.description_zh,
            description_zh=field.description_zh,
        )
        for field in fields
    )


def _f10_interface(name: str) -> SourceRequestInterface:
    spec = F10_CATALOG_SPECS[name]
    example_params = {
        parameter.name: (
            "000001.SZ"
            if parameter.name == "code"
            else "20081"
            if parameter.name == "detail_id"
            else "881386"
            if name == "concept_constituents_tdx" and parameter.name == "concept_code"
            else "2817"
            if name == "concept_capital_flow_tdx" and parameter.name == "concept_code"
            else "2817"
            if name == "concept_control_ranking_tdx" and parameter.name == "concept_code"
            else "2945"
            if parameter.name == "concept_code"
            else parameter.default
        )
        for parameter in spec.params
        if parameter.required or parameter.default is not None or parameter.name in {"code"}
    }
    if name == "stock_valuation_series_tdx":
        example_params["start_date"] = "20260601"
        example_params["end_date"] = "20260605"
    if name == "stock_return_calendar_tdx":
        example_params["year"] = "2026"
    fields = _f10_fields(spec.fields)
    example_row = {
        field.name: field.example
        for field in spec.fields
        if field.example is not None
    }
    if "instrument_id" in {field.name for field in spec.fields}:
        example_row.setdefault("instrument_id", "000001.SZ")
    if "symbol" in {field.name for field in spec.fields}:
        example_row.setdefault("symbol", "000001")
    if not example_row:
        example_row = {field.name: None for field in spec.fields[:3]}

    return SourceRequestInterface(
        name=spec.name,
        display_name_zh=spec.display_name_zh,
        source_code="tdx",
        source_name_zh="通达信",
        category=spec.category,
        request_mode="source_request",
        first_stage_strategy=f"临时请求通达信 F10 资料数据，返回{spec.display_name_zh}视图，默认不入库。",
        source_ability="TDX F10 source request",
        description=(
            f"{spec.summary_zh}"
            + (" 该接口返回源端评价或评分，不代表 AxData 自有判断。" if spec.evaluation else "")
            + " 源端直取默认不写入本地数据。"
        ),
        parameters=tuple(
            RequestParameter(
                name=parameter.name,
                dtype=parameter.dtype,
                required=parameter.required,
                description=parameter.description_zh,
                description_zh=parameter.description_zh,
                default=parameter.default,
            )
            for parameter in spec.params
        ),
        fields=fields,
        example=RequestExample(
            request={
                "params": example_params,
                "fields": [field.name for field in fields],
                "persist": False,
            },
            response=(example_row,),
        ),
    )


CAPITAL_CHANGE_FIELDS = (
    RequestField(
        name="instrument_id",
        dtype="string",
        description="AxData security code, for example 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ。",
    ),
    RequestField(
        name="ts_code",
        dtype="string",
        description="Alias of instrument_id for compatibility with stock event tables.",
        description_zh="与 instrument_id 相同，用于兼容股票事件类字段。",
    ),
    RequestField(
        name="symbol",
        dtype="string",
        description="Raw six-digit security code.",
        description_zh="交易所原始六位代码。",
    ),
    RequestField(
        name="tdx_code",
        dtype="string",
        description="TDX market-prefixed code, for example sz000001.",
        description_zh="TDX 带市场前缀代码，例如 sz000001。",
    ),
    RequestField(
        name="exchange",
        dtype="string",
        description="AxData exchange code: SSE, SZSE, or BSE.",
        description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
    ),
    RequestField(
        name="event_date",
        dtype="date/string",
        description="Event date, YYYYMMDD.",
        description_zh="事件日期，YYYYMMDD。",
    ),
    RequestField(
        name="category_raw",
        dtype="integer",
        description="TDX raw event category code.",
        description_zh="TDX 原始事件类别码。",
    ),
    RequestField(
        name="category_name",
        dtype="string",
        description="TDX client category name mapped from category_raw.",
        description_zh="按 TDX 客户端内置类别表映射的事件名称。",
    ),
    RequestField(
        name="c1",
        dtype="number",
        description="Event parameter slot 1; meaning depends on category_raw.",
        description_zh="事件参数槽 1；具体含义取决于 category_raw。",
    ),
    RequestField(
        name="c2",
        dtype="number",
        description="Event parameter slot 2; meaning depends on category_raw.",
        description_zh="事件参数槽 2；具体含义取决于 category_raw。",
    ),
    RequestField(
        name="c3",
        dtype="number",
        description="Event parameter slot 3; meaning depends on category_raw.",
        description_zh="事件参数槽 3；具体含义取决于 category_raw。",
    ),
    RequestField(
        name="c4",
        dtype="number",
        description="Event parameter slot 4; meaning depends on category_raw.",
        description_zh="事件参数槽 4；具体含义取决于 category_raw。",
    ),
    RequestField(
        name="c1_raw_hex",
        dtype="string",
        description="TDX raw bytes for c1 as hex, mainly for parser diagnostics.",
        description_zh="参数 1 的 TDX 原始字节，主要用于解析排查。",
    ),
    RequestField(
        name="c2_raw_hex",
        dtype="string",
        description="TDX raw bytes for c2 as hex, mainly for parser diagnostics.",
        description_zh="参数 2 的 TDX 原始字节，主要用于解析排查。",
    ),
    RequestField(
        name="c3_raw_hex",
        dtype="string",
        description="TDX raw bytes for c3 as hex, mainly for parser diagnostics.",
        description_zh="参数 3 的 TDX 原始字节，主要用于解析排查。",
    ),
    RequestField(
        name="c4_raw_hex",
        dtype="string",
        description="TDX raw bytes for c4 as hex, mainly for parser diagnostics.",
        description_zh="参数 4 的 TDX 原始字节，主要用于解析排查。",
    ),
    RequestField(
        name="record_hex",
        dtype="string",
        description=(
            "Full TDX raw record as hex when available; otherwise an AxData stable row key "
            "built from the normalized event fields."
        ),
        description_zh="完整 TDX 原始记录；源端未带原始记录时返回 AxData 根据事件字段生成的稳定行键。",
    ),
)


DAILY_SHARE_FIELDS = (
    RequestField(name="trade_date", dtype="date/string", description="Pre-market share-capital date.", description_zh="盘前股本口径日期。"),
    RequestField(name="instrument_id", dtype="string", description="AxData security code.", description_zh="AxData 统一证券代码，例如 000001.SZ。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit security code.", description_zh="交易所原始六位代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed code.", description_zh="TDX 带市场前缀代码，例如 sz000001。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="total_share", dtype="number", description="Total shares from finance snapshot.", description_zh="总股本，来自财务快照，单位：股。"),
    RequestField(name="float_share", dtype="number", description="Float shares from finance snapshot.", description_zh="流通股本，来自财务快照，单位：股。"),
    RequestField(name="free_float_share_z", dtype="number", description="TDX free-float shares from tdxstat.", description_zh="流通股本Z（自由流通股本口径），来自统计资源，单位：股。"),
    RequestField(name="finance_updated_date", dtype="date/string", description="Finance snapshot update date.", description_zh="财务快照更新日期；不是本次请求时间戳。"),
    RequestField(
        name="share_source",
        dtype="string",
        description=(
            "Share field source combination: finance_snapshot means total/float shares "
            "came from the finance snapshot; tdxstat means free_float_share_z came from "
            "the statistics resource."
        ),
        description_zh="普通使用可忽略；用于说明这行里的总股本、流通股本、流通股本Z分别有没有取到。",
    ),
)


DAILY_PRICE_LIMIT_FIELDS = (
    RequestField(name="trade_date", dtype="date/string", description="Daily price-limit date.", description_zh="涨跌停价格口径日期。"),
    RequestField(name="instrument_id", dtype="string", description="AxData security code.", description_zh="AxData 统一证券代码，例如 000001.SZ。"),
    RequestField(name="symbol", dtype="string", description="Raw six-digit security code.", description_zh="交易所原始六位代码。"),
    RequestField(name="tdx_code", dtype="string", description="TDX market-prefixed code.", description_zh="TDX 带市场前缀代码，例如 sz000001。"),
    RequestField(name="exchange", dtype="string", description="AxData exchange code.", description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。"),
    RequestField(name="name", dtype="string", description="Security short name when available.", description_zh="证券简称；用于识别 ST、N、C 等名称标记。"),
    RequestField(name="name_flag", dtype="string", description="Detected name flag such as N, C, ST, or *ST.", description_zh="名称标记，例如 N、C、ST、*ST；没有识别到时为空。"),
    RequestField(name="pre_close_trade_date", dtype="date/string", description="Previous-close trade date used as the base.", description_zh="实际使用的基准收盘日；不传 trade_date 时由交易日历确定，传 trade_date 时为日 K 基准日。"),
    RequestField(name="pre_close", dtype="number", description="Previous close price used as the base.", description_zh="基准收盘价，单位：元；不传 trade_date 时来自实时快照（盘中用昨收，非交易日或收盘后用最近交易日最新价），传 trade_date 时来自日 K 收盘价。"),
    RequestField(name="pre_close_source", dtype="string", description="Previous close source.", description_zh="基准收盘价来源：tdx_realtime_snapshot 或 tdx_daily_kline。"),
    RequestField(name="limit_up_price", dtype="number", description="Limit-up price.", description_zh="涨停价，单位：元。"),
    RequestField(name="limit_down_price", dtype="number", description="Limit-down price.", description_zh="跌停价，单位：元。"),
    RequestField(name="limit_ratio_pct", dtype="number", description="Limit ratio percentage when known.", description_zh="涨跌停比例，百分比数值。"),
    RequestField(name="limit_rule", dtype="string", description="Applied price-limit rule.", description_zh="计算规则：main_10pct、st_5pct、chinext_20pct、star_20pct、bse_30pct、ipo_first_day、ipo_first_5_days。"),
    RequestField(name="limit_status", dtype="string", description="normal, no_price_limit, or missing_pre_close.", description_zh="计算状态：normal 正常计算，no_price_limit 无涨跌幅限制，missing_pre_close 缺少基准收盘价。"),
)


INTERFACES: Dict[str, SourceRequestInterface] = {
    "stock_codes_tdx": SourceRequestInterface(
        name="stock_codes_tdx",
        display_name_zh="最新股票列表",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="先做临时请求预览；确认字段后再接入显式采集任务。",
        source_ability="TDX 7709 stock list preview",
        description=(
            "Query the TDX 7709 security code table and return AxData-normalized A-share "
            "stock rows matched by full_code prefixes: sh600/601/603/605/688, sh689 CDR, "
            "sz000/001/002/003/004/300/301, and bj92."
        ),
        parameters=(
            RequestParameter(
                name="name",
                dtype="string/list",
                required=False,
                description=(
                    "Security short name filter. Supports one or many values as a list "
                    "or comma-separated string."
                ),
                description_zh="股票简称：例如 平安银行、浦发银行。",
            ),
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description=(
                    "Security code filter. Supports one or many codes such as 000001, "
                    "000001.SZ, or sz000001. Multiple codes can be a list or comma-separated string."
                ),
                description_zh="股票代码：可传单个或多个，支持 000001、000001.SZ、sz000001；多个用列表或英文逗号分隔。",
            ),
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="all",
                description=(
                    "Stock scope. Supports one or many values: all, main, star, chinext, bse, cdr. "
                    "Multiple scopes can be a list or comma-separated string."
                ),
                description_zh="股票范围：all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all。",
            ),
        ),
        fields=(
            RequestField(
                name="instrument_id",
                dtype="string",
                description="AxData security code, for example 000001.SZ.",
                description_zh="AxData 统一证券代码，例如 000001.SZ。",
            ),
            RequestField(
                name="symbol",
                dtype="string",
                description="Raw six-digit security code.",
                description_zh="交易所原始六位代码。",
            ),
            RequestField(
                name="tdx_code",
                dtype="string",
                description="TDX market-prefixed code, for example sz000001.",
                description_zh="TDX 带市场前缀代码，例如 sz000001。",
            ),
            RequestField(
                name="exchange",
                dtype="string",
                description="AxData exchange code: SSE, SZSE, or BSE.",
                description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
            ),
            RequestField(
                name="name",
                dtype="string",
                description="Security short name.",
                description_zh="证券简称。",
            ),
            RequestField(
                name="market",
                dtype="string",
                description="Human-readable board name when the category is known.",
                description_zh="按规则识别的板块名称。",
            ),
        ),
        example=RequestExample(
            request={
                "params": {
                    "scope": "all",
                },
                "fields": ["instrument_id", "symbol", "tdx_code", "exchange", "name", "market"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "name": "平安银行",
                    "market": "主板",
                },
            ),
        ),
    ),
    "index_codes_tdx": SourceRequestInterface(
        name="index_codes_tdx",
        display_name_zh="指数列表",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信代码表，默认不入库。",
        source_ability="TDX 7709 index list preview",
        description=(
            "Query the TDX security code table and return index rows. By default this returns "
            "regular exchange/index-family codes. Set include_tdx_block_index=true to also "
            "include TDX block, industry, and theme index codes."
        ),
        parameters=(
            RequestParameter(name="name", dtype="string/list", required=False, description="Index short-name filter.", description_zh="指数简称过滤，例如 上证指数、沪深300。"),
            RequestParameter(name="code", dtype="string/list", required=False, description="Index code filter.", description_zh="指数代码过滤：支持 000001.SH、399001.SZ、sh000001。"),
            RequestParameter(name="exchange", dtype="string/list", required=False, default="all", description="Exchange filter: all, SSE, SZSE, or BSE.", description_zh="交易所过滤：all 全部、SSE 上交所、SZSE 深交所、BSE 北交所；默认 all。"),
            RequestParameter(name="include_tdx_block_index", dtype="boolean", required=False, default=False, description="Whether to include TDX block, industry, and theme index codes.", description_zh="是否包含通达信板块/行业/题材指数；默认 false。"),
        ),
        fields=INDEX_CODE_FIELDS,
        example=RequestExample(
            request={
                "params": {"code": ["000001.SH", "399001.SZ", "899050.BJ"]},
                "fields": ["instrument_id", "symbol", "tdx_code", "exchange", "name", "index_type", "previous_close"],
                "persist": False,
            },
            response=(
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "name": "上证指数", "index_type": "official_index", "previous_close": 4108.0762},
                {"instrument_id": "399001.SZ", "symbol": "399001", "tdx_code": "sz399001", "exchange": "SZSE", "name": "深证成指", "index_type": "official_index", "previous_close": 15880.9512},
                {"instrument_id": "899050.BJ", "symbol": "899050", "tdx_code": "bj899050", "exchange": "BSE", "name": "北证50", "index_type": "official_index", "previous_close": 1280.246},
            ),
        ),
    ),
    "index_realtime_snapshot_tdx": SourceRequestInterface(
        name="index_realtime_snapshot_tdx",
        display_name_zh="指数实时快照",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指数快照，默认不入库。",
        source_ability="TDX 7709 explicit-code index realtime quote snapshot",
        description="Request current index quote snapshots for a small explicit code list. This is source_request only and does not write local data.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="Index code.", description_zh="指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传列表或英文逗号分隔。"),
        ),
        fields=INDEX_SNAPSHOT_FIELDS,
        example=RequestExample(
            request={
                "params": {"code": ["000001.SH", "399001.SZ", "899050.BJ"]},
                "fields": ["instrument_id", "last_price", "pre_close", "open", "high", "low", "change_pct", "volume", "amount"],
                "persist": False,
            },
            response=(
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "last_price": 4092.76, "pre_close": 4108.08, "open": 4094.23, "high": 4117.45, "low": 4080.29, "change": -15.32, "change_pct": -0.3729, "open_change_pct": -0.3372, "high_change_pct": 0.2281, "low_change_pct": -0.6764, "amplitude_pct": 0.9046, "volume": 428544019, "current_volume": None, "amount": 1003780374528.0, "open_amount": None, "rise_speed": None, "activity": None},
                {"instrument_id": "399001.SZ", "symbol": "399001", "tdx_code": "sz399001", "exchange": "SZSE", "last_price": 15970.86, "pre_close": 15880.95, "open": 15826.79, "high": 16075.6, "low": 15825.32, "change": 89.91, "change_pct": 0.5662, "open_change_pct": -0.3408, "high_change_pct": 1.2269, "low_change_pct": -0.3503, "amplitude_pct": 1.576, "volume": 504870820, "current_volume": None, "amount": 1132737855488.0, "open_amount": None, "rise_speed": None, "activity": None},
            ),
        ),
    ),
    "index_realtime_rank_tdx": SourceRequestInterface(
        name="index_realtime_rank_tdx",
        display_name_zh="指数实时榜单",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指数榜单，默认不入库。",
        source_ability="TDX 7709 index category realtime quote ranking",
        description="Request the current TDX index ranking page by sort field.",
        parameters=(
            RequestParameter(name="sort", dtype="string/integer", required=False, default="change_pct", description="Sort field.", description_zh="排序字段，默认涨跌幅；常用 change_pct、amount、volume、rise_speed。"),
            RequestParameter(name="start", dtype="integer", required=False, default=0, description="Zero-based page offset.", description_zh="高级分页起点，从 0 开始；一般不用传。"),
            RequestParameter(name="count", dtype="integer", required=False, default=80, description="Requested row count.", description_zh="返回前多少条，默认 80。"),
            RequestParameter(name="ascending", dtype="boolean", required=False, default=False, description="Whether to sort ascending.", description_zh="是否升序；默认 false，表示按排序字段降序；升序为 true。"),
        ),
        fields=INDEX_RANK_FIELDS,
        example=RequestExample(
            request={"params": {"sort": "change_pct", "count": 5}, "fields": ["rank", "instrument_id", "last_price", "change_pct", "amount"], "persist": False},
            response=(
                {"rank": 1, "instrument_id": "399363.SZ", "symbol": "399363", "tdx_code": "sz399363", "exchange": "SZSE", "last_price": 16048.85, "pre_close": 15403.71, "open": 15488.34, "high": 16089.62, "low": 15488.34, "change": 645.14, "change_pct": 4.1884, "open_change_pct": 0.5494, "high_change_pct": 4.4532, "low_change_pct": 0.5494, "amplitude_pct": 3.9038, "volume": None, "current_volume": None, "amount": 295172800512.0, "open_amount": None, "rise_speed": None, "activity": None},
                {"rank": 2, "instrument_id": "000682.SH", "symbol": "000682", "tdx_code": "sh000682", "exchange": "SSE", "last_price": 3112.72, "pre_close": 2996.3, "open": 3009.6, "high": 3128.27, "low": 3009.6, "change": 116.42, "change_pct": 3.8855, "open_change_pct": 0.4439, "high_change_pct": 4.4035, "low_change_pct": 0.4439, "amplitude_pct": 3.96, "volume": None, "current_volume": None, "amount": 150859415552.0, "open_amount": None, "rise_speed": None, "activity": None},
            ),
        ),
    ),
    "index_quote_refresh_tdx": SourceRequestInterface(
        name="index_quote_refresh_tdx",
        display_name_zh="指数实时增量行情",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指数刷新数据，默认不入库。",
        source_ability="TDX 7709 index quote refresh",
        description="Request one realtime refresh snapshot for one or more indexes. This is the HTTP source-request form of the refresh capability; long-lived streaming can wrap the same fields later.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="Index code.", description_zh="指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传列表或英文逗号分隔。"),
        ),
        fields=INDEX_SNAPSHOT_FIELDS,
        example=RequestExample(
            request={"params": {"code": ["000001.SH", "000300.SH"]}, "fields": ["instrument_id", "last_price", "change_pct", "amount"], "persist": False},
            response=(
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "last_price": 4092.76, "pre_close": 4108.08, "open": 4094.23, "high": 4117.45, "low": 4080.29, "change": -15.32, "change_pct": -0.3729, "open_change_pct": -0.3372, "high_change_pct": 0.2281, "low_change_pct": -0.6764, "amplitude_pct": 0.9046, "volume": 428544019, "current_volume": None, "amount": 1003780374528.0, "open_amount": None, "rise_speed": None, "activity": None},
            ),
        ),
    ),
    "index_kline_tdx": SourceRequestInterface(
        name="index_kline_tdx",
        display_name_zh="指数K线",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指数 K 线，默认不入库。",
        source_ability="TDX 7709 index kline",
        description="Request index K-line bars for one index or a small explicit code list. Default count is 120 for safe preview; pass count explicitly for larger samples. This is source_request only and does not write local data.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="Index code.", description_zh="指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传列表或英文逗号分隔。"),
            RequestParameter(name="period", dtype="string", required=False, default="day", description="K-line period.", description_zh="K线周期：day、week、month、quarter、year、1m、5m、15m、30m、60m；默认 day。"),
            RequestParameter(name="count", dtype="integer", required=False, default=120, description="Requested bar count.", description_zh="返回条数，默认 120，适合源端直取预览；需要更长历史时显式传 count。"),
        ),
        fields=INDEX_KLINE_FIELDS,
        example=RequestExample(
            request={"params": {"code": "000001.SH", "period": "day", "count": 3}, "fields": ["instrument_id", "trade_time", "period", "open", "close", "up_count", "down_count"], "persist": False},
            response=(
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "trade_time": "2026-06-16T15:00:00+08:00", "period": "day", "open": 4094.21, "high": 4103.93, "low": 4077.87, "close": 4091.89, "volume": 6156682.88, "amount": 1369613008896.0, "up_count": 1087, "down_count": 1222},
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "trade_time": "2026-06-17T15:00:00+08:00", "period": "day", "open": 4074.29, "high": 4109.96, "low": 4073.73, "close": 4108.08, "volume": 6080774.4, "amount": 1403145945088.0, "up_count": 785, "down_count": 1534},
            ),
        ),
    ),
    "index_intraday_today_tdx": SourceRequestInterface(
        name="index_intraday_today_tdx",
        display_name_zh="指数当日分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指数当日分时，默认不入库。",
        source_ability="TDX 7709 index current-day intraday chart",
        description="Request current-day index intraday points.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="Index code.", description_zh="指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传列表或英文逗号分隔。"),
        ),
        fields=INTRADAY_TODAY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "000001.SH"}, "fields": ["instrument_id", "time_label", "price", "avg_price", "volume"], "persist": False},
            response=(
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "time_label": "09:31", "minute_index": 0, "price": 4096.11, "avg_price": 4094.1612, "volume": 4434416},
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "time_label": "09:32", "minute_index": 1, "price": 4097.48, "avg_price": 4093.3912, "volume": 3362027},
            ),
        ),
    ),
    "index_intraday_history_tdx": SourceRequestInterface(
        name="index_intraday_history_tdx",
        display_name_zh="指数历史分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指数历史分时，默认不入库。",
        source_ability="TDX 7709 index historical intraday trace",
        description="Request historical index intraday points for one trading day. This source returns price and volume; it does not carry intraday average price.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="Index code.", description_zh="指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传列表或英文逗号分隔。"),
            RequestParameter(name="trade_date", dtype="date/string", required=True, description="Trading date.", description_zh="交易日期，YYYYMMDD 或 YYYY-MM-DD。"),
        ),
        fields=INTRADAY_HISTORY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "000001.SH", "trade_date": "20260617"}, "fields": ["instrument_id", "trade_time", "price", "volume", "prev_close"], "persist": False},
            response=(
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "trade_date": "20260617", "trade_time": "2026-06-17T09:31:00+08:00", "minute_index": 0, "price": 4079.36, "volume": 8184626, "prev_close": None},
                {"instrument_id": "000001.SH", "symbol": "000001", "tdx_code": "sh000001", "exchange": "SSE", "trade_date": "20260617", "trade_time": "2026-06-17T09:32:00+08:00", "minute_index": 1, "price": 4079.21, "volume": 6265905, "prev_close": None},
            ),
        ),
    ),
    "etf_codes_tdx": SourceRequestInterface(
        name="etf_codes_tdx",
        display_name_zh="ETF列表",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信代码表，筛出 ETF，默认不入库。",
        source_ability="TDX 7709 ETF list preview",
        description=(
            "Query the TDX security code table and return ETF rows. ETF codes are matched by "
            "TDX market-prefixed prefixes: sh51/sh56/sh58 for SSE ETFs and sz15 for SZSE ETFs."
        ),
        parameters=(
            RequestParameter(name="name", dtype="string/list", required=False, description="ETF short-name filter.", description_zh="ETF 简称过滤，例如 50ETF、沪深300ETF。"),
            RequestParameter(name="code", dtype="string/list", required=False, description="ETF code filter.", description_zh="ETF 代码过滤：支持 510050.SH、159915.SZ、sh510050。"),
            RequestParameter(name="exchange", dtype="string/list", required=False, default="all", description="Exchange filter: all, SSE, or SZSE.", description_zh="交易所过滤：all 全部、SSE 上交所、SZSE 深交所；默认 all。"),
        ),
        fields=ETF_CODE_FIELDS,
        example=RequestExample(
            request={
                "params": {"code": ["510050.SH", "159915.SZ"]},
                "fields": ["instrument_id", "symbol", "tdx_code", "exchange", "name", "previous_close"],
                "persist": False,
            },
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "name": "50ETF", "previous_close": 3.012},
                {"instrument_id": "159915.SZ", "symbol": "159915", "tdx_code": "sz159915", "exchange": "SZSE", "name": "创业板ETF", "previous_close": 2.456},
            ),
        ),
    ),
    "etf_realtime_snapshot_tdx": SourceRequestInterface(
        name="etf_realtime_snapshot_tdx",
        display_name_zh="ETF实时快照",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 快照，默认不入库。",
        source_ability="TDX 7709 explicit-code ETF realtime quote snapshot",
        description="Request current ETF quote snapshots for a small explicit code list. This is source_request only and does not write local data.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code.", description_zh="ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传列表或英文逗号分隔。"),
        ),
        fields=ETF_SNAPSHOT_FIELDS,
        example=RequestExample(
            request={
                "params": {"code": ["510050.SH", "159915.SZ"]},
                "fields": ["instrument_id", "last_price", "pre_close", "open", "high", "low", "change_pct", "volume", "amount"],
                "persist": False,
            },
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "last_price": 3.025, "pre_close": 3.012, "open": 3.015, "high": 3.038, "low": 3.009, "change": 0.013, "change_pct": 0.4316, "open_change_pct": 0.0996, "high_change_pct": 0.8632, "low_change_pct": -0.0996, "amplitude_pct": 0.9628, "volume": 1284560, "current_volume": None, "amount": 388234240.0, "open_amount": None, "rise_speed": None, "activity": None},
                {"instrument_id": "159915.SZ", "symbol": "159915", "tdx_code": "sz159915", "exchange": "SZSE", "last_price": 2.471, "pre_close": 2.456, "open": 2.458, "high": 2.482, "low": 2.451, "change": 0.015, "change_pct": 0.6107, "open_change_pct": 0.0814, "high_change_pct": 1.0586, "low_change_pct": -0.2036, "amplitude_pct": 1.2622, "volume": 2156780, "current_volume": None, "amount": 532145600.0, "open_amount": None, "rise_speed": None, "activity": None},
            ),
        ),
    ),
    "etf_realtime_rank_tdx": SourceRequestInterface(
        name="etf_realtime_rank_tdx",
        display_name_zh="ETF实时榜单",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 榜单，默认不入库。",
        source_ability="TDX 7709 ETF category realtime quote ranking",
        description="Request the current TDX ETF ranking page by sort field. AxData scans the ETF category (TDX category 0x2afd) and ranks by the requested sort field.",
        parameters=(
            RequestParameter(name="sort", dtype="string/integer", required=False, default="change_pct", description="Sort field.", description_zh="排序字段，默认涨跌幅；常用 change_pct、amount、volume、rise_speed。"),
            RequestParameter(name="start", dtype="integer", required=False, default=0, description="Zero-based page offset.", description_zh="高级分页起点，从 0 开始；一般不用传。"),
            RequestParameter(name="count", dtype="integer", required=False, default=80, description="Requested row count.", description_zh="返回前多少条，默认 80。"),
            RequestParameter(name="ascending", dtype="boolean", required=False, default=False, description="Whether to sort ascending.", description_zh="是否升序；默认 false，表示按排序字段降序；升序为 true。"),
        ),
        fields=ETF_RANK_FIELDS,
        example=RequestExample(
            request={"params": {"sort": "change_pct", "count": 5}, "fields": ["rank", "instrument_id", "last_price", "change_pct", "amount"], "persist": False},
            response=(
                {"rank": 1, "instrument_id": "159915.SZ", "symbol": "159915", "tdx_code": "sz159915", "exchange": "SZSE", "last_price": 2.495, "pre_close": 2.456, "open": 2.458, "high": 2.498, "low": 2.455, "change": 0.039, "change_pct": 1.5879, "open_change_pct": 0.0814, "high_change_pct": 1.7101, "low_change_pct": -0.0407, "amplitude_pct": 1.7508, "volume": None, "current_volume": None, "amount": 632145600.0, "open_amount": None, "rise_speed": None, "activity": None},
                {"rank": 2, "instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "last_price": 3.038, "pre_close": 3.012, "open": 3.015, "high": 3.042, "low": 3.009, "change": 0.026, "change_pct": 0.8632, "open_change_pct": 0.0996, "high_change_pct": 0.996, "low_change_pct": -0.0996, "amplitude_pct": 1.0956, "volume": None, "current_volume": None, "amount": 488234240.0, "open_amount": None, "rise_speed": None, "activity": None},
            ),
        ),
    ),
    "etf_kline_tdx": SourceRequestInterface(
        name="etf_kline_tdx",
        display_name_zh="ETFK线",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF K 线，默认不入库。",
        source_ability="TDX 7709 ETF kline",
        description="Request ETF K-line bars for one ETF or a small explicit code list. Default count is 120 for safe preview; pass count explicitly for larger samples. This is source_request only and does not write local data.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code.", description_zh="ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传列表或英文逗号分隔。"),
            RequestParameter(name="period", dtype="string", required=False, default="day", description="K-line period.", description_zh="K线周期：day、week、month、quarter、year、1m、5m、15m、30m、60m；默认 day。"),
            RequestParameter(name="count", dtype="integer", required=False, default=120, description="Requested bar count.", description_zh="返回条数，默认 120，适合源端直取预览；需要更长历史时显式传 count。"),
        ),
        fields=ETF_KLINE_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH", "period": "day", "count": 3}, "fields": ["instrument_id", "trade_time", "period", "open", "high", "low", "close", "volume", "amount"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "trade_time": "2026-06-16T15:00:00+08:00", "period": "day", "open": 3.005, "high": 3.028, "low": 2.998, "close": 3.012, "volume": 1356420.0, "amount": 408234240.0, "up_count": None, "down_count": None},
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "trade_time": "2026-06-17T15:00:00+08:00", "period": "day", "open": 3.010, "high": 3.035, "low": 3.006, "close": 3.025, "volume": 1284560.0, "amount": 388234240.0, "up_count": None, "down_count": None},
            ),
        ),
    ),
    "etf_intraday_today_tdx": SourceRequestInterface(
        name="etf_intraday_today_tdx",
        display_name_zh="ETF当日分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 当日分时，默认不入库。",
        source_ability="TDX 7709 ETF current-day intraday chart",
        description="Request current-day ETF intraday points.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code.", description_zh="ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传列表或英文逗号分隔。"),
        ),
        fields=INTRADAY_TODAY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH"}, "fields": ["instrument_id", "time_label", "price", "avg_price", "volume"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "time_label": "09:31", "minute_index": 0, "price": 3.016, "avg_price": 3.0155, "volume": 28440},
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "time_label": "09:32", "minute_index": 1, "price": 3.018, "avg_price": 3.0162, "volume": 19820},
            ),
        ),
    ),
    "etf_intraday_history_tdx": SourceRequestInterface(
        name="etf_intraday_history_tdx",
        display_name_zh="ETF历史分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 历史分时，默认不入库。",
        source_ability="TDX 7709 ETF historical intraday trace",
        description="Request historical ETF intraday points for one trading day. This source returns price and volume; it does not carry intraday average price.",
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code.", description_zh="ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传列表或英文逗号分隔。"),
            RequestParameter(name="trade_date", dtype="date/string", required=True, description="Trading date.", description_zh="交易日期，YYYYMMDD 或 YYYY-MM-DD。"),
        ),
        fields=INTRADAY_HISTORY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH", "trade_date": "20260617"}, "fields": ["instrument_id", "trade_time", "price", "volume", "prev_close"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "trade_date": "20260617", "trade_time": "2026-06-17T09:31:00+08:00", "minute_index": 0, "price": 3.014, "volume": 31250, "prev_close": None},
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "trade_date": "20260617", "trade_time": "2026-06-17T09:32:00+08:00", "minute_index": 1, "price": 3.016, "volume": 21840, "prev_close": None},
            ),
        ),
    ),
    "etf_trades_today_tdx": SourceRequestInterface(
        name="etf_trades_today_tdx",
        display_name_zh="ETF当日成交明细",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 当前交易日成交明细，默认不入库。",
        source_ability="TDX 7709 0x0fc5 today trade-detail request",
        description=(
            "Request TDX ETF trade-detail records for the current trading day. The public "
            "interface only requires code; AxData handles TDX pagination internally and "
            "does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code, for example 510050, 510050.SH, or sh510050.", description_zh="ETF 代码：支持 510050、510050.SH、sh510050；批量可传列表或英文逗号分隔字符串。"),
        ),
        fields=TRADE_DETAIL_TODAY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH"}, "fields": ["instrument_id", "trade_time", "price", "volume", "order_count", "side"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "trade_time": "14:08", "trade_index": 0, "price": 3.025, "volume": 156, "order_count": 12, "side": "buy"},
            ),
        ),
    ),
    "etf_trades_history_tdx": SourceRequestInterface(
        name="etf_trades_history_tdx",
        display_name_zh="ETF历史成交明细",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 指定交易日成交明细，默认不入库。",
        source_ability="TDX 7709 0x0fc6 historical trade-detail request",
        description=(
            "Request TDX ETF trade-detail records for one or more ETFs on one trading date. "
            "This returns transaction-detail rows, not OHLC K-line bars; AxData handles "
            "TDX pagination internally and does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code, for example 510050, 510050.SH, or sh510050.", description_zh="ETF 代码：支持 510050、510050.SH、sh510050；批量可传列表或英文逗号分隔字符串。"),
            RequestParameter(name="trade_date", dtype="string", required=True, description="Trading date, YYYYMMDD or YYYY-MM-DD.", description_zh="交易日期，格式 YYYYMMDD 或 YYYY-MM-DD。"),
        ),
        fields=TRADE_DETAIL_HISTORY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH", "trade_date": "20260511"}, "fields": ["instrument_id", "trade_datetime", "price", "volume", "order_count", "side"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "trade_date": "20260511", "trade_time": "14:12", "trade_datetime": "2026-05-11T14:12:00+08:00", "trade_index": 0, "price": 3.025, "volume": 156, "order_count": 12, "side": "buy"},
            ),
        ),
    ),
    "etf_auction_process_tdx": SourceRequestInterface(
        name="etf_auction_process_tdx",
        display_name_zh="ETF竞价明细",
        source_code="tdx",
        source_name_zh="通达信",
        category="竞价数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 集合竞价明细，默认不入库。",
        source_ability="TDX 7709 0x056a call-auction process detail",
        description=(
            "Request TDX auction/process detail for one or more ETFs. It returns time, "
            "price, matched volume, unmatched volume, and the raw unmatched direction marker. "
            "Measured samples commonly include the opening auction before 09:25 and the closing "
            "auction around 14:57 to about 15:00."
        ),
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code, for example 510050, 510050.SH, or sh510050.", description_zh="ETF 代码：支持 510050、510050.SH、sh510050；批量可传列表或英文逗号分隔字符串。"),
        ),
        fields=AUCTION_PROCESS_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH"}, "fields": ["instrument_id", "auction_time", "price", "matched_volume", "matched_amount_estimated", "unmatched_volume", "unmatched_amount_estimated", "unmatched_direction"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "auction_time": "09:15:00", "auction_index": 0, "price": 3.015, "matched_volume": 5680, "matched_amount_estimated": 1712520.0, "unmatched_volume": 1230, "unmatched_amount_estimated": 370845.0, "unmatched_direction": 1},
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "auction_time": "09:15:09", "auction_index": 1, "price": 3.016, "matched_volume": 8820, "matched_amount_estimated": 2660112.0, "unmatched_volume": 640, "unmatched_amount_estimated": 193024.0, "unmatched_direction": -1},
            ),
        ),
    ),
    "etf_auction_result_tdx": SourceRequestInterface(
        name="etf_auction_result_tdx",
        display_name_zh="ETF竞价结果",
        source_code="tdx",
        source_name_zh="通达信",
        category="竞价数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 ETF 当日成交明细，并筛选 09:25 竞价结果，默认不入库。",
        source_ability="TDX 7709 0x0fc5 today trade-detail 09:25 record",
        description=(
            "Request current-day TDX ETF trade-detail records and keep only the 09:25 opening "
            "auction result row. This is the final auction result, not the call-auction "
            "process series returned by etf_auction_process_tdx."
        ),
        parameters=(
            RequestParameter(name="code", dtype="string/list", required=True, description="ETF code, for example 510050, 510050.SH, or sh510050.", description_zh="ETF 代码：支持 510050、510050.SH、sh510050；批量可传列表或英文逗号分隔字符串。"),
        ),
        fields=AUCTION_RESULT_TODAY_FIELDS,
        example=RequestExample(
            request={"params": {"code": "510050.SH"}, "fields": ["instrument_id", "auction_time", "price", "volume", "amount", "order_count"], "persist": False},
            response=(
                {"instrument_id": "510050.SH", "symbol": "510050", "tdx_code": "sh510050", "exchange": "SSE", "auction_time": "09:25", "trade_index": 0, "price": 3.015, "volume": 5680, "amount": 1712520.0, "order_count": 42},
            ),
        ),
    ),
    "stock_st_list_tdx": SourceRequestInterface(
        name="stock_st_list_tdx",
        display_name_zh="最新ST股票列表",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时扫描通达信当前股票列表，筛出 ST / *ST 股票，默认不入库。",
        source_ability="TDX 7709 current ST stock list scan",
        description=(
            "Scan the current TDX A-share stock universe and return stocks whose "
            "current short name starts with ST or *ST. This is a current-list request, "
            "not a historical ST status-change table."
        ),
        parameters=(
            RequestParameter(
                name="name",
                dtype="string/list",
                required=False,
                description="Security short name. Supports one or many values as a list or comma-separated string.",
                description_zh="股票简称：例如 平安银行、浦发银行。",
            ),
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description=(
                    "Security code. Supports one or many codes such as 000001, 000001.SZ, "
                    "or sz000001."
                ),
                description_zh="股票代码：支持 000001、000001.SZ、sz000001。",
            ),
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="all",
                description=(
                    "Stock scope. Supports one or many values: all, main, star, chinext, bse, cdr. "
                    "Multiple scopes can be a list or comma-separated string."
                ),
                description_zh="股票范围：all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all。",
            ),
        ),
        fields=(
            RequestField(
                name="instrument_id",
                dtype="string",
                description="AxData security code, for example 000004.SZ.",
                description_zh="AxData 统一证券代码，例如 000004.SZ。",
            ),
            RequestField(
                name="symbol",
                dtype="string",
                description="Raw six-digit security code.",
                description_zh="交易所原始六位代码。",
            ),
            RequestField(
                name="tdx_code",
                dtype="string",
                description="TDX market-prefixed code, for example sz000004.",
                description_zh="TDX 带市场前缀代码，例如 sz000004。",
            ),
            RequestField(
                name="exchange",
                dtype="string",
                description="AxData exchange code: SSE, SZSE, or BSE.",
                description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
            ),
            RequestField(
                name="name",
                dtype="string",
                description="Security short name.",
                description_zh="证券简称。",
            ),
            RequestField(
                name="market",
                dtype="string",
                description="Human-readable board name when the category is known.",
                description_zh="按规则识别的板块名称。",
            ),
            RequestField(
                name="st_type",
                dtype="string",
                description="Detected ST name flag: ST or *ST.",
                description_zh="识别出的 ST 类型：ST 或 *ST。",
            ),
        ),
        example=RequestExample(
            request={
                "params": {
                    "scope": "all",
                },
                "fields": [
                    "instrument_id",
                    "symbol",
                    "tdx_code",
                    "exchange",
                    "name",
                    "market",
                    "st_type",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000004.SZ",
                    "symbol": "000004",
                    "tdx_code": "sz000004",
                    "exchange": "SZSE",
                    "name": "*ST国华",
                    "market": "主板",
                    "st_type": "*ST",
                },
            ),
        ),
    ),
    "stock_suspensions_tdx": SourceRequestInterface(
        name="stock_suspensions_tdx",
        display_name_zh="最新停牌列表",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时扫描通达信当前停牌列表，默认不入库。",
        source_ability="TDX 7709 current suspension scan",
        description=(
            "Scan the current TDX A-share stock universe and return the stocks currently "
            "reported as suspended. This is a real-time source request, not a historical "
            "suspension-date table."
        ),
        parameters=(
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="all",
                description=(
                    "Stock scope. Defaults to all. Supports all, main, star, chinext, bse, cdr. "
                    "Multiple scopes can be a list or comma-separated string."
                ),
                description_zh="股票范围：默认 all 全市场；可传 main、star、chinext、bse、cdr 用于调试缩小范围。",
            ),
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description=(
                    "Optional debug filter. Supports one or many codes such as 000001, "
                    "000001.SZ, or sz000001."
                ),
                description_zh="调试用股票代码过滤：支持 000001、000001.SZ、sz000001。",
            ),
            RequestParameter(
                name="name",
                dtype="string/list",
                required=False,
                description="Optional debug name filter.",
                description_zh="调试用股票简称过滤。",
            ),
        ),
        fields=(
            RequestField(
                name="instrument_id",
                dtype="string",
                description="AxData security code, for example 000004.SZ.",
                description_zh="AxData 统一证券代码，例如 000004.SZ。",
            ),
            RequestField(
                name="symbol",
                dtype="string",
                description="Raw six-digit security code.",
                description_zh="交易所原始六位代码。",
            ),
            RequestField(
                name="tdx_code",
                dtype="string",
                description="TDX market-prefixed code, for example sz000004.",
                description_zh="TDX 带市场前缀代码，例如 sz000004。",
            ),
            RequestField(
                name="exchange",
                dtype="string",
                description="AxData exchange code: SSE, SZSE, or BSE.",
                description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
            ),
            RequestField(
                name="name",
                dtype="string",
                description="Security short name.",
                description_zh="证券简称。",
            ),
            RequestField(
                name="market",
                dtype="string",
                description="Human-readable board name when the category is known.",
                description_zh="按规则识别的板块名称。",
            ),
        ),
        example=RequestExample(
            request={
                "params": {
                    "scope": "all",
                },
                "fields": [
                    "instrument_id",
                    "symbol",
                    "tdx_code",
                    "exchange",
                    "name",
                    "market",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000004.SZ",
                    "symbol": "000004",
                    "tdx_code": "sz000004",
                    "exchange": "SZSE",
                    "name": "*ST国华",
                    "market": "主板",
                },
            ),
        ),
    ),
    "stock_daily_share_tdx": SourceRequestInterface(
        name="stock_daily_share_tdx",
        display_name_zh="每日股本（盘前）",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信财务快照，并使用 AxData 项目缓存统计资源生成盘前股本口径，默认不入库。",
        source_ability="TDX 7709 finance snapshot + AxData cached tdxstat statistics",
        description=(
            "Return pre-market share-capital snapshot rows. Missing code or code=all expands to the "
            "full stock scope and the finance snapshot is requested internally in batches. trade_date uses "
            "the business date inside the statistics resource rather than the file download time. "
            "finance_updated_date is the per-symbol finance snapshot update date, not a request timestamp."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description="Security code. Missing, empty, all, or * means full market by scope.",
                description_zh="证券代码：可选；不传或传 all 表示按股票范围返回全量。也支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="all",
                description="Stock scope used only when code is missing or all. Supports all, main, star, chinext, bse, cdr.",
                description_zh="股票范围：只在 code 不传或传 all 时生效；all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all。",
            ),
            RequestParameter(
                name="stats_cache_root",
                dtype="string",
                required=False,
                description="Optional AxData statistics cache directory used by automatic refresh.",
                description_zh="可选缓存目录：自动下载的 zhb.zip 和 zhb.meta.json 会保存到这里；不传时使用项目 cache/tdx/stats。",
            ),
            RequestParameter(
                name="refresh_stats",
                dtype="boolean",
                required=False,
                description="Whether to force-refresh AxData cached statistics resource from the TDX source before calculation.",
                description_zh="是否强制从源端刷新 AxData 项目缓存里的统计资源；默认 false，缓存缺失或当天未刷新时会自动刷新。",
            ),
        ),
        fields=DAILY_SHARE_FIELDS,
        example=RequestExample(
            request={
                "params": {"code": "000001.SZ"},
                "fields": ["trade_date", "instrument_id", "total_share", "float_share", "free_float_share_z"],
                "persist": False,
            },
            response=(
                {
                    "trade_date": "20260615",
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "total_share": 19405918750.0,
                    "float_share": 19405601250.0,
                    "free_float_share_z": 8160481200.0,
                    "finance_updated_date": "20260425",
                    "share_source": "finance_snapshot+tdxstat",
                },
            ),
        ),
    ),
    "stock_daily_price_limit_tdx": SourceRequestInterface(
        name="stock_daily_price_limit_tdx",
        display_name_zh="涨跌停价格",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求快照或日 K，并按目标交易日生成涨跌停价格，默认不入库。",
        source_ability="TDX realtime snapshot and daily K-line",
        description=(
            "Return the limit-up and limit-down list for target trade_date T. Missing code or code=all "
            "expands to the full stock scope. When trade_date is omitted, AxData uses the official "
            "exchange calendar and realtime snapshot base price to produce the latest full-market list "
            "(intraday uses snapshot pre_close; non-trading days and after close use the latest price "
            "as the most recent close). When trade_date is provided, AxData uses the actual previous "
            "daily K-line close. Board, ST, and new-stock rules are applied; N/C name flags are returned "
            "as no_price_limit."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description="Security code. Missing, empty, all, or * means full market by scope.",
                description_zh="证券代码：可选；不传或传 all 表示按股票范围返回全量。也支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="all",
                description="Stock scope used only when code is missing or all. Supports all, main, star, chinext, bse, cdr.",
                description_zh="股票范围：只在 code 不传或传 all 时生效；all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all。",
            ),
            RequestParameter(
                name="trade_date",
                dtype="string",
                required=False,
                description=(
                    "Target trade date T, YYYYMMDD or YYYY-MM-DD. If omitted, AxData returns the "
                    "latest full-market list from realtime snapshot base price. If provided, AxData "
                    "uses daily K-line history for that fixed date."
                ),
                description_zh="目标交易日 T，格式 YYYYMMDD 或 YYYY-MM-DD；不传时默认返回最新全量，用实时快照昨收计算；传入时走日 K 历史精确计算。",
            ),
        ),
        fields=DAILY_PRICE_LIMIT_FIELDS,
        example=RequestExample(
            request={
                "params": {"code": "000001.SZ", "trade_date": "20260617"},
                "fields": [
                    "trade_date",
                    "instrument_id",
                    "pre_close_trade_date",
                    "pre_close",
                    "limit_up_price",
                    "limit_down_price",
                    "limit_rule",
                    "limit_status",
                ],
                "persist": False,
            },
            response=(
                {
                    "trade_date": "20260617",
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "name": "平安银行",
                    "name_flag": None,
                    "pre_close_trade_date": "20260616",
                    "pre_close": 10.94,
                    "pre_close_source": "tdx_daily_kline",
                    "limit_up_price": 12.03,
                    "limit_down_price": 9.85,
                    "limit_ratio_pct": 10.0,
                    "limit_rule": "main_10pct",
                    "limit_status": "normal",
                },
            ),
        ),
    ),
    "stock_capital_changes_tdx": SourceRequestInterface(
        name="stock_capital_changes_tdx",
        display_name_zh="股本变迁",
        source_code="tdx",
        source_name_zh="通达信",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 0x000f 股本变迁/除权除息原始记录，默认不入库。",
        source_ability="TDX 7709 0x000f capital-change and XDXR records",
        description=(
            "Request raw TDX 0x000f capital-change records for one or more stocks. "
            "These records are the source evidence used by stock_adj_factor_tdx. "
            "category can filter TDX event types by any raw integer category code; "
            "category=1 or category=xdxr returns dividend/split XDXR records used in "
            "the first adjustment-factor implementation. "
            f"{CAPITAL_CHANGE_CATEGORY_REFERENCE_ZH}"
        ),
        parameters=(
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="all",
                description=(
                    "Stock scope used when code is omitted or set to all: all, main, star, "
                    "chinext, bse, or cdr. Default all."
                ),
                description_zh="股票范围：code 不传或为 all 时生效；all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all。",
            ),
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string. If omitted, "
                    "AxData expands the stock pool by scope."
                ),
                description_zh="证券代码：可选；支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。不填则按股票范围请求全量。",
            ),
            RequestParameter(
                name="category",
                dtype="integer/string/list",
                required=False,
                description=(
                    "Optional TDX event category filter. Pass any TDX raw integer category code; "
                    "common aliases include 1 or xdxr for dividend/split records, 5 or equity for "
                    "share-capital changes, and 15 or restructure for restructuring adjustments. "
                    "Only category=1 directly feeds the current adjustment-factor calculation."
                ),
                description_zh=(
                    "可选 TDX 事件类别过滤：可传任意 TDX 原始类别码；常用别名："
                    "1/xdxr 为除权除息，5/equity 为股本变化，15/restructure 为重整调整。"
                    "当前复权因子只直接使用 category=1，其余类别作为股本变迁和公司行为证据保留。"
                ),
            ),
        ),
        fields=CAPITAL_CHANGE_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "category": "xdxr",
                },
                "fields": ["ts_code", "event_date", "category_name", "c1", "c2", "c3", "c4"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "event_date": "20240614",
                    "category_raw": 1,
                    "category_name": "除权除息",
                    "c1": 7.19,
                    "c2": 0.0,
                    "c3": 0.0,
                    "c4": 0.0,
                    "c1_raw_hex": "0000e640",
                    "c2_raw_hex": "00000000",
                    "c3_raw_hex": "00000000",
                    "c4_raw_hex": "00000000",
                    "record_hex": None,
                },
            ),
        ),
    ),
    "stock_adj_factor_tdx": SourceRequestInterface(
        name="stock_adj_factor_tdx",
        display_name_zh="复权因子",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信 category=1 除权除息事件和未复权日 K，计算每日复权因子，默认不入库。",
        source_ability="TDX 7709 0x000f category=1 XDXR events plus daily K-line factor calculation",
        description=(
            "Build daily adjustment factors from TDX 0x000f category=1 XDXR records and "
            "unadjusted daily K-lines. This is an AxData-calculated factor based on the raw "
            "stock_capital_changes_tdx event records; it is not guaranteed to match the TDX "
            "built-in adjusted K-line output because different vendors use different adjustment "
            "and rounding口径. adjust=qfq returns front-adjustment factors; adjust=hfq returns "
            "back-adjustment factors. anchor_date is optional for adjust=qfq."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="adjust",
                dtype="string",
                required=False,
                default="qfq",
                description="Adjustment factor method: qfq or hfq. Default qfq.",
                description_zh="复权方向：qfq 前复权因子，hfq 后复权因子；默认 qfq。",
            ),
            RequestParameter(
                name="anchor_date",
                dtype="string",
                required=False,
                description="Optional qfq anchor date, YYYYMMDD or YYYY-MM-DD. Only supported when adjust=qfq.",
                description_zh="可选的前复权锚点日期，格式 YYYYMMDD 或 YYYY-MM-DD；仅 adjust=qfq 时使用。",
            ),
        ),
        fields=ADJ_FACTOR_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "adjust": "qfq",
                },
                "fields": ["ts_code", "trade_date", "adj_factor"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_date": "20240531",
                    "adj_factor": 0.825,
                },
            ),
        ),
    ),
    "stock_limit_ladder_tdx": SourceRequestInterface(
        name="stock_limit_ladder_tdx",
        display_name_zh="连板天梯",
        source_code="tdx",
        source_name_zh="通达信",
        category="短线数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信实时榜单和盘前统计资源，计算当前连板天梯，默认不入库。",
        source_ability="TDX 7709 0x054b realtime ranking + in-memory tdxstat/tdxstat2 statistics + optional F10 topic exposure",
        description=(
            "Return the current limit-up ladder for A-share stocks. The interface requests the "
            "current realtime ranking, calculates each stock's price-limit status from its quote "
            "and price-limit rule, and combines prior limit-up statistics for ladder level and "
            "N-days/M-limit-up text. By default it returns sealed limit-up rows only; include_touched "
            "also includes touched/opened-board rows. The primary and secondary themes are sorted "
            "by current ladder strength first and then stock relevance, with broad holding/index "
            "style labels filtered out. This is a "
            "source request calculation and does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(
                name="count",
                dtype="integer/string",
                required=False,
                default="all",
                description="Returned ladder rows. Default all; pass an integer to return only the first N rows, maximum 500.",
                description_zh="返回数量；默认 all 返回完整天梯，也可传数字只返回前 N 条，最大 500。",
            ),
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="main",
                description=(
                    "Stock scope. Defaults to main board. Supports main, all, star, chinext, bse, cdr. "
                    "Multiple scopes can be a list or comma-separated string."
                ),
                description_zh="股票范围；默认 main 主板。可传 all、star 科创板、chinext 创业板、bse 北交所、cdr CDR，也可传数组或英文逗号分隔。",
            ),
            RequestParameter(
                name="include_touched",
                dtype="boolean",
                required=False,
                default=False,
                description="Whether to include touched/opened-board stocks. Default false returns sealed limit-up stocks only.",
                description_zh="是否包含盘中触及涨停但当前未封住的股票；默认 false，只返回当前封住涨停的股票。",
            ),
            RequestParameter(
                name="topic_type",
                dtype="string",
                required=False,
                default="theme",
                description="Topic type used for theme lookup: theme or sector. Default theme.",
                description_zh="题材类型：theme 主题题材，sector 板块题材；默认 theme。",
            ),
        ),
        fields=LIMIT_LADDER_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "count": "all",
                    "scope": "main",
                    "include_touched": False,
                },
                "fields": [
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
                ],
                "persist": False,
            },
            response=(
                {
                    "ladder_level": 4,
                    "limit_board_text": "8天6板",
                    "trade_date": "20260617",
                    "limit_status": "sealed",
                    "instrument_id": "002971.SZ",
                    "symbol": "002971",
                    "exchange": "SZSE",
                    "name": "和远气体",
                    "last_price": 55.76,
                    "pre_close": 50.69,
                    "limit_up_price": 55.76,
                    "change_pct": 10.001973,
                    "amount": 2521050000.0,
                    "seal_amount": 453790000.0,
                    "free_float_market_value": 6520440000.0,
                    "seal_to_amount_ratio": 0.18,
                    "year_limit_up_days": 9,
                    "primary_theme": "氢能源",
                    "secondary_themes": "机器人+储能",
                },
            ),
        ),
    ),
    "stock_theme_strength_rank_tdx": SourceRequestInterface(
        name="stock_theme_strength_rank_tdx",
        display_name_zh="题材强度排行",
        source_code="tdx",
        source_name_zh="通达信",
        category="短线数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信实时榜单、盘前统计资源和个股题材，计算当前题材强度排行，默认不入库。",
        source_ability="TDX 7709 realtime ranking + in-memory limit-up statistics + F10 topic exposure",
        description=(
            "Return the current theme strength ranking calculated from the same sealed limit-up "
            "pool used by stock_limit_ladder_tdx. The ranking excludes ST/*ST stocks, defaults to "
            "main-board stocks, and sorts by limit-up count, highest ladder level, lianban stock "
            "count, and seal amount. count can be all or an integer. This is a source request "
            "calculation and does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(
                name="count",
                dtype="integer/string",
                required=False,
                default="all",
                description="Returned theme rows. Default all; pass an integer to return only the first N rows, maximum 500.",
                description_zh="返回数量；默认 all 返回完整题材排行，也可传数字只返回前 N 条，最大 500。",
            ),
            RequestParameter(
                name="scope",
                dtype="string/list",
                required=False,
                default="main",
                description=(
                    "Stock scope. Defaults to main board. Supports main, all, star, chinext, bse, cdr. "
                    "Multiple scopes can be a list or comma-separated string."
                ),
                description_zh="股票范围；默认 main 主板。可传 all、star 科创板、chinext 创业板、bse 北交所、cdr CDR，也可传数组或英文逗号分隔。",
            ),
            RequestParameter(
                name="topic_type",
                dtype="string",
                required=False,
                default="theme",
                description="Topic type used for ranking: theme or sector. Default theme.",
                description_zh="题材类型：theme 主题题材，sector 板块题材；默认 theme。",
            ),
        ),
        fields=THEME_STRENGTH_RANK_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "count": "all",
                    "scope": "main",
                },
                "fields": [
                    "rank",
                    "trade_date",
                    "topic_name",
                    "theme_strength_score",
                    "limit_up_count",
                    "highest_ladder_level",
                    "lianban_stock_count",
                    "leader_name",
                    "top_stock_summary",
                ],
                "persist": False,
            },
            response=(
                {
                    "rank": 1,
                    "trade_date": "20260618",
                    "topic_type": "theme",
                    "topic_name": "不可减持(新规)",
                    "topic_id": "2965",
                    "theme_strength_score": 2255.0,
                    "limit_up_count": 22,
                    "highest_ladder_level": 3,
                    "lianban_stock_count": 5,
                    "first_board_count": 17,
                    "leader_instrument_id": "002141.SZ",
                    "leader_name": "贤丰控股",
                    "leader_ladder_level": 3,
                    "leader_limit_board_text": "3天3板",
                    "leader_seal_amount": 213785958.0,
                    "seal_amount_sum": 3927163397.0,
                    "amount_sum": 18376688992.0,
                    "top_stock_summary": "贤丰控股（3天3板） 中天精装（3天3板） 通鼎互联（2天2板） 中京电子（2天2板） 立航科技（4天3板）",
                },
            ),
        ),
    ),
    "stock_realtime_rank_tdx": SourceRequestInterface(
        name="stock_realtime_rank_tdx",
        display_name_zh="实时榜单",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信分类行情列表，默认不入库。",
        source_ability="TDX 7709 0x054b category realtime quote ranking",
        description=(
            "Request a bounded realtime ranking page. Default count is 80 for preview; "
            'count="all" must be explicit. The server decides which securities belong to each page. '
            "This is source_request only and does not write local data."
        ),
        parameters=(
            RequestParameter(
                name="category",
                dtype="string/integer",
                required=False,
                default="a_share",
                description=(
                    "Ranking range. Common stock aliases include a_share, sse, szse, star, "
                    "chinext, and bse. Raw TDX integer category values are also accepted."
                ),
                description_zh=(
                    "股票榜单范围，默认全部 A 股。常用范围包括沪市、深市、科创板、创业板、"
                    "北交所；也可传 TDX 原始整数类别。"
                ),
            ),
            RequestParameter(
                name="sort",
                dtype="string/integer",
                required=False,
                default="change_pct",
                description=(
                    "Sort field. Common aliases include change_pct, amount, volume, rise_speed, "
                    "open_amount, locked_amount, opening_rush, min2_amount, short_turnover, "
                    "vol_rise_speed, entrust_ratio, and activity. Raw TDX sort_type values are also accepted."
                ),
                description_zh=(
                    "排序字段，默认涨跌幅。常用排序包括成交额、成交量、涨速、开盘金额、封单额、"
                    "开盘抢筹、2 分钟金额、短换手、量涨速、委比和活跃度；也可传 TDX 原始排序值。"
                ),
            ),
            RequestParameter(
                name="start",
                dtype="integer",
                required=False,
                default=0,
                description="Zero-based offset of the ranking page.",
                description_zh="高级分页起点，从 0 开始；一般不用传。",
            ),
            RequestParameter(
                name="count",
                dtype="integer/string",
                required=False,
                default=80,
                description='Requested row count. Use "all" to request the complete current ranking.',
                description_zh='返回数量，默认 80；传 "all" 表示取完整当前榜单。',
            ),
            RequestParameter(
                name="ascending",
                dtype="boolean",
                required=False,
                default=False,
                description="Whether to sort ascending. Default false means descending for sortable fields.",
                description_zh="是否升序；默认 false，表示按排序字段降序；升序为 true。",
            ),
            RequestParameter(
                name="filters",
                dtype="string/list/integer",
                required=False,
                description=(
                    "Optional exclude filters. Common aliases include exclude_new, exclude_kcb, "
                    "exclude_st, exclude_cyb, and exclude_bj. A raw bitmask is also accepted."
                ),
                description_zh=(
                    "可选排除条件。可排除次新、科创板、ST、创业板或北交所；也可传原始过滤位图。"
                ),
            ),
        ),
        fields=REALTIME_RANK_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "category": "a_share",
                    "sort": "change_pct",
                    "start": 0,
                    "count": 2,
                },
                "fields": ["rank", "instrument_id", "last_price", "change_pct", "amount"],
                "persist": False,
            },
            response=(
                {
                    "rank": 1,
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "last_price": 10.14,
                    "pre_close": 10.28,
                    "open": 10.13,
                    "high": 10.2,
                    "low": 10.08,
                    "change": -0.14,
                    "change_pct": -1.361868,
                    "open_change_pct": -1.459144,
                    "high_change_pct": -0.77821,
                    "low_change_pct": -1.945525,
                    "amplitude_pct": 1.167315,
                    "average_price": 10.14,
                    "average_change_pct": -1.361868,
                    "drawdown_pct": 0.583658,
                    "attack_pct": 0.583658,
                    "volume": 1000,
                    "current_volume": 15,
                    "amount": 1014000.0,
                    "inside_volume": 400,
                    "outside_volume": 600,
                    "inside_outside_ratio": 0.666667,
                    "open_amount": 10000.0,
                    "open_amount_ratio_pct": 0.986193,
                    "bid1_price": 10.13,
                    "bid1_volume": 320,
                    "ask1_price": 10.14,
                    "ask1_volume": 428,
                    "locked_amount": 324160.0,
                    "bid1_ask1_volume_diff": -108,
                    "bid1_ask1_balance_pct": -14.438503,
                    "rise_speed": 0.21,
                    "short_turnover": 0.08,
                    "min2_amount": 320000.0,
                    "opening_rush": 0.12,
                    "vol_rise_speed": 1.25,
                    "entrust_ratio": 18.5,
                    "activity": 11,
                },
            ),
        ),
    ),
    "stock_realtime_snapshot_tdx": SourceRequestInterface(
        name="stock_realtime_snapshot_tdx",
        display_name_zh="实时快照",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当前行情快照，默认不入库。",
        source_ability="TDX 7709 0x054c explicit-code realtime quote snapshot",
        description=(
            "Request current quote snapshots for one stock or a small explicit code list. "
            "Each security returns one row. "
            "This is source_request only: it does not write raw/staging/core/factor data "
            "and is not part of any Collector task template."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=REALTIME_SNAPSHOT_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": [
                    "instrument_id",
                    "last_price",
                    "change_pct",
                    "volume",
                    "amount",
                    "bid1_price",
                    "ask1_price",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "last_price": 10.14,
                    "pre_close": 10.28,
                    "open": 10.13,
                    "high": 10.2,
                    "low": 10.08,
                    "change": -0.14,
                    "change_pct": -1.361868,
                    "open_change_pct": -1.459144,
                    "high_change_pct": -0.77821,
                    "low_change_pct": -1.945525,
                    "amplitude_pct": 1.167315,
                    "average_price": 10.14,
                    "average_change_pct": -1.361868,
                    "drawdown_pct": 0.583658,
                    "attack_pct": 0.583658,
                    "volume": 1000,
                    "current_volume": 15,
                    "amount": 1014000.0,
                    "inside_volume": 400,
                    "outside_volume": 600,
                    "inside_outside_ratio": 0.666667,
                    "open_amount": 10000.0,
                    "open_amount_ratio_pct": 0.986193,
                    "bid1_price": 10.13,
                    "bid1_volume": 320,
                    "ask1_price": 10.14,
                    "ask1_volume": 428,
                    "locked_amount": 324160.0,
                    "bid1_ask1_volume_diff": -108,
                    "bid1_ask1_balance_pct": -14.438503,
                    "rise_speed": 0.21,
                    "short_turnover": 0.08,
                    "min2_amount": 320000.0,
                    "opening_rush": 0.12,
                    "vol_rise_speed": 1.25,
                    "entrust_ratio": 18.5,
                    "activity": 11,
                },
            ),
        ),
    ),
    "stock_order_book_tdx": SourceRequestInterface(
        name="stock_order_book_tdx",
        display_name_zh="五档盘口",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当前五档盘口，默认不入库。",
        source_ability="TDX 7709 current five-level order book snapshot",
        description=(
            "Request the current five-level order book for one stock or a small explicit code list. "
            "Each security returns one row per level. "
            "This is source_request only and does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=ORDER_BOOK_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": [
                    "instrument_id",
                    "level",
                    "bid_price",
                    "bid_volume",
                    "ask_price",
                    "ask_volume",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "level": 1,
                    "bid_price": 10.13,
                    "bid_volume": 320,
                    "ask_price": 10.14,
                    "ask_volume": 428,
                },
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "level": 2,
                    "bid_price": 10.12,
                    "bid_volume": 118,
                    "ask_price": 10.15,
                    "ask_volume": 260,
                },
            ),
        ),
    ),
    "stock_intraday_buy_sell_strength_tdx": SourceRequestInterface(
        name="stock_intraday_buy_sell_strength_tdx",
        display_name_zh="买卖力道",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当前个股分时副图买卖力道，默认不入库。",
        source_ability="TDX 7709 0x051b current intraday buy/sell strength subchart",
        description=(
            "Request the current TDX intraday subchart buy/sell strength series. "
            "The request accepts code only; TDX 0x051b does not accept a date or time parameter. "
            "This is a current intraday auxiliary chart series, not a historical K-line or trade-detail interface."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=INTRADAY_BUY_SELL_STRENGTH_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": ["instrument_id", "minute_time", "minute_index", "bid_order", "ask_order"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "minute_time": "09:30",
                    "minute_index": 0,
                    "bid_order": 10326,
                    "ask_order": 4866,
                },
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "minute_time": "09:31",
                    "minute_index": 1,
                    "bid_order": 6321,
                    "ask_order": 20068,
                },
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "minute_time": "10:55",
                    "minute_index": 85,
                    "bid_order": 12397,
                    "ask_order": 27555,
                },
            ),
        ),
    ),
    "stock_intraday_volume_comparison_tdx": SourceRequestInterface(
        name="stock_intraday_volume_comparison_tdx",
        display_name_zh="成交对比",
        source_code="tdx",
        source_name_zh="通达信",
        category="实时数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当前个股分时副图成交对比，默认不入库。",
        source_ability="TDX 7709 0x051b current intraday volume-comparison subchart",
        description=(
            "Request the current TDX intraday volume-comparison subchart. "
            "The request accepts code only; TDX 0x051b does not accept a date or time parameter. "
            "It returns the current-day cumulative volume, previous-day same-point cumulative volume, "
            "absolute change, and percentage change displayed by the TDX volume-comparison subchart."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=INTRADAY_VOLUME_COMPARISON_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": [
                    "instrument_id",
                    "minute_time",
                    "minute_index",
                    "today_volume",
                    "yesterday_volume",
                    "volume_change",
                    "volume_change_pct",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "minute_time": "09:31",
                    "minute_index": 1,
                    "today_volume": 126062.0,
                    "yesterday_volume": 87433.0,
                    "volume_change": 38629.0,
                    "volume_change_pct": 44.181259,
                },
            ),
        ),
    ),
    "stock_auction_process_tdx": SourceRequestInterface(
        name="stock_auction_process_tdx",
        display_name_zh="竞价明细",
        source_code="tdx",
        source_name_zh="通达信",
        category="竞价数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信集合竞价明细，默认不入库。",
        source_ability="TDX 7709 0x056a call-auction process detail",
        description=(
            "Request TDX auction/process detail for one or more securities. It returns time, "
            "price, matched volume, unmatched volume, and the raw unmatched direction marker. "
            "Measured samples commonly include the opening auction before 09:25 and the closing "
            "auction around 14:57 to about 15:00. The 09:25 opening trade result still belongs to trade "
            "detail data, so this interface does not replace trade-detail interfaces."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=AUCTION_PROCESS_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000988.SZ",
                },
                "fields": [
                    "instrument_id",
                    "auction_time",
                    "price",
                    "matched_volume",
                    "matched_amount_estimated",
                    "unmatched_volume",
                    "unmatched_amount_estimated",
                    "unmatched_direction",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000988.SZ",
                    "symbol": "000988",
                    "tdx_code": "sz000988",
                    "exchange": "SZSE",
                    "auction_time": "09:15:00",
                    "auction_index": 0,
                    "price": 162.12,
                    "matched_volume": 2568,
                    "matched_amount_estimated": 41632416.0,
                    "unmatched_volume": 2433,
                    "unmatched_amount_estimated": 394442.0,
                    "unmatched_direction": 1,
                },
                {
                    "instrument_id": "000988.SZ",
                    "symbol": "000988",
                    "tdx_code": "sz000988",
                    "exchange": "SZSE",
                    "auction_time": "09:15:09",
                    "auction_index": 1,
                    "price": 162.12,
                    "matched_volume": 6630,
                    "matched_amount_estimated": 107485560.0,
                    "unmatched_volume": 1115,
                    "unmatched_amount_estimated": 180763.8,
                    "unmatched_direction": -1,
                },
            ),
        ),
    ),
    "stock_auction_result_tdx": SourceRequestInterface(
        name="stock_auction_result_tdx",
        display_name_zh="竞价结果",
        source_code="tdx",
        source_name_zh="通达信",
        category="竞价数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当日成交明细，并筛选 09:25 竞价结果，默认不入库。",
        source_ability="TDX 7709 0x0fc5 today trade-detail 09:25 record",
        description=(
            "Request current-day TDX trade-detail records and keep only the 09:25 opening "
            "auction result row. This is the final auction result, not the call-auction "
            "process series returned by stock_auction_process_tdx."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=AUCTION_RESULT_TODAY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": ["instrument_id", "auction_time", "price", "volume", "amount", "order_count"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "auction_time": "09:25",
                    "trade_index": 0,
                    "price": 10.86,
                    "volume": 1200,
                    "amount": 1303200.0,
                    "order_count": 28,
                },
            ),
        ),
    ),
    "stock_auction_result_history_tdx": SourceRequestInterface(
        name="stock_auction_result_history_tdx",
        display_name_zh="历史竞价结果",
        source_code="tdx",
        source_name_zh="通达信",
        category="竞价数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指定交易日成交明细，并筛选 09:25 竞价结果，默认不入库。",
        source_ability="TDX 7709 0x0fc6 historical trade-detail 09:25 record",
        description=(
            "Request TDX historical trade-detail records for one trading date and keep only "
            "the 09:25 opening auction result row. This returns a compact auction-result "
            "view derived from trade detail."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="trade_date",
                dtype="string",
                required=True,
                description="Trading date, YYYYMMDD or YYYY-MM-DD.",
                description_zh="交易日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
        ),
        fields=AUCTION_RESULT_HISTORY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "trade_date": "20260511",
                },
                "fields": ["instrument_id", "auction_datetime", "price", "volume", "amount", "order_count"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_date": "20260511",
                    "auction_time": "09:25",
                    "auction_datetime": "2026-05-11T09:25:00+08:00",
                    "trade_index": 0,
                    "price": 10.86,
                    "volume": 1200,
                    "amount": 1303200.0,
                    "order_count": 28,
                },
            ),
        ),
    ),
    "stock_shortline_indicators_tdx": SourceRequestInterface(
        name="stock_shortline_indicators_tdx",
        display_name_zh="短线指标",
        source_code="tdx",
        source_name_zh="通达信",
        category="短线数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信实时快照、日 K、财务快照，并使用 AxData 项目缓存统计资源计算短线指标，默认不入库。",
        source_ability="TDX 7709 realtime snapshot + daily K-line + finance snapshot + AxData cached tdxstat/tdxstat2 statistics",
        description=(
            "Return opening-auction strength indicators for one or more stocks. The interface "
            "combines current realtime snapshot values, recent daily K-line volume, finance "
            "float-share data, and AxData cached tdxstat/tdxstat2 historical statistics. Cache "
            "parameters are optional for ordinary use because AxData refreshes the project cache "
            "when it is missing or has not refreshed today. It is a source request calculation "
            "and does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="stats_root",
                dtype="string",
                required=False,
                description="Optional override directory or zhb.zip path containing tdxstat.cfg and tdxstat2.cfg.",
                description_zh="可选覆盖路径：可传包含 tdxstat.cfg/tdxstat2.cfg 的目录，或直接传 zhb.zip 文件路径。",
            ),
            RequestParameter(
                name="stats_cache_root",
                dtype="string",
                required=False,
                description="Optional AxData statistics cache directory used by automatic refresh.",
                description_zh="可选缓存目录：自动下载的 zhb.zip 和 zhb.meta.json 会保存到这里；不传时使用项目 cache/tdx/stats。",
            ),
            RequestParameter(
                name="refresh_stats",
                dtype="boolean",
                required=False,
                description="Whether to force-refresh AxData cached statistics resource from the TDX source before calculation.",
                description_zh="是否强制从源端刷新 AxData 项目缓存里的统计资源；默认 false，缓存缺失或当天未刷新时会自动刷新。",
            ),
        ),
        fields=AUCTION_INDICATOR_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "002971.SZ",
                },
                "fields": [
                    "instrument_id",
                    "open_amount",
                    "open_volume_ratio",
                    "open_turnover_z",
                    "open_prev_amount_ratio",
                    "auction_prev_volume_ratio",
                    "open_prev_seal_ratio",
                    "limit_board_text",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "002971.SZ",
                    "symbol": "002971",
                    "tdx_code": "sz002971",
                    "exchange": "SZSE",
                    "stats_date": "20260612",
                    "open_price": 55.76,
                    "pre_close": 50.69,
                    "open_change_pct": 10.001973,
                    "open_amount": 121491000.0,
                    "open_volume_hand": 21788.199426,
                    "open_volume_ratio": 17.55,
                    "open_turnover_z": 1.895,
                    "open_prev_amount_ratio": 3.653,
                    "auction_prev_volume_ratio": 0.6548,
                    "opening_rush": 6.01,
                    "open_prev_seal_ratio": 2677.25,
                    "prev_amount": 3325475300.0,
                    "prev_seal_amount": 4537900.0,
                    "prev2_seal_amount": 186197000.0,
                    "prev_open_volume_hand": 33272.0,
                    "prev_open_amount": 182996000.0,
                    "float_shares": 114984000.0,
                    "float_market_value": 6520440000.0,
                    "free_float_shares": 114984000.0,
                    "free_float_market_value": 6520440000.0,
                    "seal_amount": 453790000.0,
                    "seal_to_amount_ratio": 0.18,
                    "seal_to_float_ratio": 6.96,
                    "seal_prev_ratio": 100.0,
                    "limit_stat_days": 7,
                    "limit_up_count_in_stat_days": 5,
                    "limit_board_text": "7天5板",
                    "limit_up_streak_days": 4,
                    "year_limit_up_days": 13,
                },
            ),
        ),
    ),
    "stock_intraday_today_tdx": SourceRequestInterface(
        name="stock_intraday_today_tdx",
        display_name_zh="当日分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当前交易日分时图，默认不入库。",
        source_ability="TDX 7709 0x0537 current-day intraday chart",
        description=(
            "Request the TDX current-day intraday chart for one or more stocks. "
            "This is not a K-line interface: it returns minute intraday price, "
            "intraday average price, and minute volume, without OHLC fields or "
            "adjustment calculation. The response does not carry a date; point "
            "time is derived from the minute index."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=INTRADAY_TODAY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": ["instrument_id", "time_label", "price", "avg_price", "volume"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "time_label": "09:31",
                    "price": 10.86,
                    "avg_price": 10.8417,
                    "volume": 120,
                },
            ),
        ),
    ),
    "stock_intraday_history_tdx": SourceRequestInterface(
        name="stock_intraday_history_tdx",
        display_name_zh="历史分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指定交易日历史分时数据，默认不入库。",
        source_ability="TDX 7709 0x0fb4 historical intraday trace",
        description=(
            "Request the TDX historical intraday trace for one or more stocks on one trading date. "
            "This is not a K-line interface: it returns minute intraday price points, minute volume, "
            "and previous close, without OHLC fields or adjustment calculation."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="trade_date",
                dtype="string",
                required=True,
                description="Trading date, YYYYMMDD or YYYY-MM-DD.",
                description_zh="交易日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
        ),
        fields=INTRADAY_HISTORY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "trade_date": "20260519",
                },
                "fields": ["instrument_id", "trade_time", "price", "volume", "prev_close"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_date": "20260519",
                    "trade_time": "2026-05-19T09:31:00+08:00",
                    "minute_index": 0,
                    "price": 10.13,
                    "volume": 120,
                    "prev_close": 10.08,
                },
            ),
        ),
    ),
    "stock_intraday_recent_history_tdx": SourceRequestInterface(
        name="stock_intraday_recent_history_tdx",
        display_name_zh="近期历史分时",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信近期历史分时图数据，默认不入库。",
        source_ability="TDX 7709 0x0feb recent historical intraday chart",
        description=(
            "Request the TDX recent historical intraday chart for one or more stocks on one trading date. "
            "Compared with the standard historical intraday interface, this response also carries intraday "
            "average price and open price, and is intended for recent trading dates."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="trade_date",
                dtype="string",
                required=True,
                description="Trading date, YYYYMMDD or YYYY-MM-DD.",
                description_zh="交易日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
        ),
        fields=INTRADAY_RECENT_HISTORY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "trade_date": "20260519",
                },
                "fields": ["instrument_id", "trade_time", "price", "avg_price", "volume", "open_price"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_date": "20260519",
                    "trade_time": "2026-05-19T09:31:00+08:00",
                    "time_label": "09:31",
                    "minute_index": 0,
                    "price": 10.13,
                    "avg_price": 10.115,
                    "volume": 120,
                    "prev_close": 10.08,
                    "open_price": 10.12,
                },
            ),
        ),
    ),
    "stock_trades_today_tdx": SourceRequestInterface(
        name="stock_trades_today_tdx",
        display_name_zh="当日成交明细",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信当前交易日成交明细，默认不入库。",
        source_ability="TDX 7709 0x0fc5 today trade-detail request",
        description=(
            "Request TDX trade-detail records for the current trading day. The public "
            "interface only requires code; AxData handles TDX pagination internally and "
            "does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
        ),
        fields=TRADE_DETAIL_TODAY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "fields": ["instrument_id", "trade_time", "price", "volume", "order_count", "side"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_time": "14:08",
                    "trade_index": 0,
                    "price": 10.86,
                    "volume": 89,
                    "order_count": 9,
                    "side": "buy",
                },
            ),
        ),
    ),
    "stock_trades_history_tdx": SourceRequestInterface(
        name="stock_trades_history_tdx",
        display_name_zh="历史成交明细",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信指定交易日成交明细，默认不入库。",
        source_ability="TDX 7709 0x0fc6 historical trade-detail request",
        description=(
            "Request TDX trade-detail records for one or more stocks on one trading date. "
            "This returns transaction-detail rows, not OHLC K-line bars; AxData handles "
            "TDX pagination internally and does not write raw/staging/core/factor data."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="trade_date",
                dtype="string",
                required=True,
                description="Trading date, YYYYMMDD or YYYY-MM-DD.",
                description_zh="交易日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
        ),
        fields=TRADE_DETAIL_HISTORY_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "trade_date": "20260511",
                },
                "fields": ["instrument_id", "trade_datetime", "price", "volume", "order_count", "side"],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_date": "20260511",
                    "trade_time": "14:12",
                    "trade_datetime": "2026-05-11T14:12:00+08:00",
                    "trade_index": 0,
                    "price": 10.86,
                    "volume": 89,
                    "order_count": 9,
                    "side": "buy",
                },
            ),
        ),
    ),
    "stock_finance_summary_tdx": _finance_interface(
        name="stock_finance_summary_tdx",
        display_name_zh="财务基础摘要",
        view_zh="基础财务摘要",
        fields=FINANCE_SUMMARY_FIELDS,
        example_fields=("instrument_id", "updated_date", "total_assets", "net_profit", "eps"),
    ),
    "stock_share_capital_tdx": _finance_interface(
        name="stock_share_capital_tdx",
        display_name_zh="股本结构",
        view_zh="股本结构",
        fields=FINANCE_SHARE_CAPITAL_FIELDS,
        example_fields=("instrument_id", "updated_date", "total_share", "float_share", "shareholder_count"),
    ),
    "stock_balance_summary_tdx": _finance_interface(
        name="stock_balance_summary_tdx",
        display_name_zh="资产负债摘要",
        view_zh="资产负债摘要",
        fields=FINANCE_BALANCE_FIELDS,
        example_fields=("instrument_id", "updated_date", "total_assets", "net_assets", "inventory"),
    ),
    "stock_profit_cashflow_summary_tdx": _finance_interface(
        name="stock_profit_cashflow_summary_tdx",
        display_name_zh="利润现金流摘要",
        view_zh="利润现金流摘要",
        fields=FINANCE_PROFIT_CASHFLOW_FIELDS,
        example_fields=("instrument_id", "updated_date", "revenue", "net_profit", "operating_cashflow"),
    ),
    "stock_finance_profile_tdx": _finance_interface(
        name="stock_finance_profile_tdx",
        display_name_zh="财务资料标签",
        view_zh="财务资料标签",
        fields=FINANCE_PROFILE_FIELDS,
        example_fields=(
            "instrument_id",
            "updated_date",
            "ipo_date",
            "province_name",
            "tdx_industry_name",
            "tdx_research_industry_name",
        ),
        parameters=(FINANCE_CODE_PARAMETER, FINANCE_MAP_ROOT_PARAMETER),
        description_extra=(
            " Finance profile mapping fields use AxData's bundled TDX code-table snapshot "
            "by default. Pass map_root to read a user's local TDX incon.dat, tdxzs.cfg, "
            "and tdxhy.cfg files for refreshed region and industry names."
        ),
    ),
    "stock_kline_second_tdx": SourceRequestInterface(
        name="stock_kline_second_tdx",
        display_name_zh="秒K线",
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy="临时请求通达信秒级 K 线，默认不入库。",
        source_ability="TDX 7709 second-level K-line request",
        description=(
            "Request AxData-normalized second-level K-line bars from TDX. "
            "Code accepts a single security, a list, or a comma-separated string; "
            "requests default to full history and do not write raw/staging/core/factor data. "
            f"{KLINE_RETENTION_NOTES['stock_kline_second_tdx']}"
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string/list",
                required=True,
                description=(
                    "Security code, for example 000001, 000001.SZ, or sz000001. "
                    "Multiple codes can be a list or comma-separated string."
                ),
                description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
            ),
            RequestParameter(
                name="seconds",
                dtype="integer",
                required=False,
                default=5,
                description=(
                    "Aggregation seconds. Custom integer from 1 to 60; "
                    "recommended values: 3, 4, 5, 10, 15, 30, 60. Default 5."
                ),
                description_zh="聚合秒数：1-60 内可自定义；推荐 3、4、5、10、15、30、60；默认 5。",
            ),
            RequestParameter(
                name="adjust",
                dtype="string",
                required=False,
                default="none",
                description="Adjustment mode: none, qfq, hfq, or fixed_qfq. Second-level adjustment depends on live validation.",
                description_zh="复权参数：none 不复权，qfq 前复权，hfq 后复权，fixed_qfq 定点前复权；默认 none，秒级复权以实测结果为准。",
            ),
            RequestParameter(
                name="anchor_date",
                dtype="string",
                required=False,
                description="Anchor date for fixed_qfq, YYYYMMDD or YYYY-MM-DD.",
                description_zh="定点前复权锚点日期，仅 adjust=fixed_qfq 时使用，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
        ),
        fields=(
            RequestField(
                name="instrument_id",
                dtype="string",
                description="AxData security code, for example 000001.SZ.",
                description_zh="AxData 统一证券代码，例如 000001.SZ。",
            ),
            RequestField(
                name="symbol",
                dtype="string",
                description="Raw six-digit security code.",
                description_zh="交易所原始六位代码。",
            ),
            RequestField(
                name="tdx_code",
                dtype="string",
                description="TDX market-prefixed code, for example sz000001.",
                description_zh="TDX 带市场前缀代码，例如 sz000001。",
            ),
            RequestField(
                name="exchange",
                dtype="string",
                description="AxData exchange code: SSE, SZSE, or BSE.",
                description_zh="AxData 交易所代码：SSE、SZSE 或 BSE。",
            ),
            RequestField(
                name="trade_time",
                dtype="datetime/string",
                description=(
                    "Bar end timestamp. Second K-lines use second precision; minute and custom-minute "
                    "K-lines use minute precision; daily and higher periods use the period-end trading "
                    "day at 15:00:00+08:00."
                ),
                description_zh="K 线结束时间；秒 K 精确到秒，分钟/自定义分钟精确到分钟，日线及以上为周期结束交易日 15:00:00+08:00。",
            ),
            RequestField(
                name="period",
                dtype="string",
                description="Period name, for example 5s.",
                description_zh="周期名称，例如 5s。",
            ),
            RequestField(
                name="open",
                dtype="number",
                description="Open price.",
                description_zh="开盘价。",
            ),
            RequestField(
                name="high",
                dtype="number",
                description="High price.",
                description_zh="最高价。",
            ),
            RequestField(
                name="low",
                dtype="number",
                description="Low price.",
                description_zh="最低价。",
            ),
            RequestField(
                name="close",
                dtype="number",
                description="Close price.",
                description_zh="收盘价。",
            ),
            RequestField(
                name="volume",
                dtype="number",
                description="Volume in lots.",
                description_zh="成交量，单位：手。",
            ),
            RequestField(
                name="amount",
                dtype="number",
                description="Decoded TDX amount value.",
                description_zh="成交额解码值。",
            ),
        ),
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                    "seconds": 5,
                },
                "fields": [
                    "instrument_id",
                    "trade_time",
                    "period",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_time": "2026-05-19T13:39:50+08:00",
                    "period": "5s",
                    "open": 10.13,
                    "high": 10.15,
                    "low": 10.12,
                    "close": 10.14,
                    "volume": 100.0,
                    "amount": 101400.0,
                },
            ),
        ),
    ),
}


def _kline_params(*extra: RequestParameter, default_count: int) -> tuple[RequestParameter, ...]:
    return (
        RequestParameter(
            name="code",
            dtype="string/list",
            required=True,
            description=(
                "Security code, for example 000001, 000001.SZ, or sz000001. "
                "Multiple codes can be a list or comma-separated string."
            ),
            description_zh="证券代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串。",
        ),
        *extra,
        RequestParameter(
            name="adjust",
            dtype="string",
            required=False,
            default="none",
            description="Adjustment mode: none, qfq, hfq, or fixed_qfq.",
            description_zh="复权参数：none 不复权，qfq 前复权，hfq 后复权，fixed_qfq 定点前复权；默认 none。",
        ),
        RequestParameter(
            name="anchor_date",
            dtype="string",
            required=False,
            description="Anchor date for fixed_qfq, YYYYMMDD or YYYY-MM-DD.",
            description_zh="定点前复权锚点日期，仅 adjust=fixed_qfq 时使用，格式 YYYYMMDD 或 YYYY-MM-DD。",
        ),
    )


def _kline_interface(
    *,
    name: str,
    display_name_zh: str,
    period_zh: str,
    retention_note: str,
    params: tuple[RequestParameter, ...],
    example_params: dict[str, object],
    example_period: str,
) -> SourceRequestInterface:
    fields = INTERFACES["stock_kline_second_tdx"].fields
    return SourceRequestInterface(
        name=name,
        display_name_zh=display_name_zh,
        source_code="tdx",
        source_name_zh="通达信",
        category="行情数据",
        request_mode="source_request",
        first_stage_strategy=f"临时请求通达信{period_zh}，默认不入库。",
        source_ability="TDX 7709 K-line request",
        description=(
            "Request AxData-normalized K-line bars for the selected period from TDX. "
            "Code accepts a single security, a list, or a comma-separated string; "
            "requests default to full history and do not write raw/staging/core/factor data. "
            f"{retention_note}"
        ),
        parameters=params,
        fields=fields,
        example=RequestExample(
            request={
                "params": example_params,
                "fields": [
                    "instrument_id",
                    "trade_time",
                    "period",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                ],
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "tdx_code": "sz000001",
                    "exchange": "SZSE",
                    "trade_time": "2026-05-19T15:00:00+08:00",
                    "period": example_period,
                    "open": 10.13,
                    "high": 10.15,
                    "low": 10.12,
                    "close": 10.14,
                    "volume": 100.0,
                    "amount": 101400.0,
                },
            ),
        ),
    )


INTERFACES.update(
    {
        "stock_kline_minute_tdx": _kline_interface(
            name="stock_kline_minute_tdx",
            display_name_zh="分钟K线",
            period_zh="固定分钟 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_minute_tdx"],
            params=_kline_params(
                RequestParameter(
                    name="period",
                    dtype="string",
                    required=False,
                    default="1m",
                    description=(
                        "Fixed minute period: 1m, 5m, 15m, 30m, or 60m. "
                        "Use stock_kline_nminute_tdx for other minute counts."
                    ),
                    description_zh="固定分钟周期：1m、5m、15m、30m、60m；默认 1m。其他分钟数请使用自定义分钟K线。",
                ),
                default_count=800,
            ),
            example_params={"code": "000001.SZ", "period": "1m"},
            example_period="1m",
        ),
        "stock_kline_nminute_tdx": _kline_interface(
            name="stock_kline_nminute_tdx",
            display_name_zh="自定义分钟K线",
            period_zh="自定义分钟扩展周期 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_nminute_tdx"],
            params=_kline_params(
                RequestParameter(
                    name="minutes",
                    dtype="integer",
                    required=True,
                    description=(
                        "Aggregation minutes, range 2-1440. Smoke-tested values include "
                        "2, 3, 10, 20, 120, and 1440."
                    ),
                    description_zh="聚合分钟数：范围 2-1440；已抽测 2、3、10、20、120、1440 分钟可返回。",
                ),
                default_count=800,
            ),
            example_params={"code": "000001.SZ", "minutes": 10},
            example_period="10m",
        ),
        "stock_kline_daily_tdx": _kline_interface(
            name="stock_kline_daily_tdx",
            display_name_zh="日K线",
            period_zh="日 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_daily_tdx"],
            params=_kline_params(default_count=800),
            example_params={"code": "000001.SZ"},
            example_period="day",
        ),
        "stock_kline_nday_tdx": _kline_interface(
            name="stock_kline_nday_tdx",
            display_name_zh="自定义日K线",
            period_zh="自定义日扩展周期 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_nday_tdx"],
            params=_kline_params(
                RequestParameter(
                    name="days",
                    dtype="integer",
                    required=True,
                    description="Aggregation days, range 2-365. Smoke-tested values include 2, 45, and 365.",
                    description_zh="聚合日数：范围 2-365；已抽测 2、45、365 日可返回。",
                ),
                default_count=800,
            ),
            example_params={"code": "000001.SZ", "days": 45},
            example_period="45d",
        ),
        "stock_kline_weekly_tdx": _kline_interface(
            name="stock_kline_weekly_tdx",
            display_name_zh="周K线",
            period_zh="周 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_weekly_tdx"],
            params=_kline_params(default_count=300),
            example_params={"code": "000001.SZ"},
            example_period="week",
        ),
        "stock_kline_monthly_tdx": _kline_interface(
            name="stock_kline_monthly_tdx",
            display_name_zh="月K线",
            period_zh="月 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_monthly_tdx"],
            params=_kline_params(default_count=240),
            example_params={"code": "000001.SZ"},
            example_period="month",
        ),
        "stock_kline_quarterly_tdx": _kline_interface(
            name="stock_kline_quarterly_tdx",
            display_name_zh="季K线",
            period_zh="季 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_quarterly_tdx"],
            params=_kline_params(default_count=120),
            example_params={"code": "000001.SZ"},
            example_period="quarter",
        ),
        "stock_kline_yearly_tdx": _kline_interface(
            name="stock_kline_yearly_tdx",
            display_name_zh="年K线",
            period_zh="年 K 线",
            retention_note=KLINE_RETENTION_NOTES["stock_kline_yearly_tdx"],
            params=_kline_params(default_count=40),
            example_params={"code": "000001.SZ"},
            example_period="year",
        ),
    }
)

INTERFACES.update({name: _f10_interface(name) for name in F10_CATALOG_SPECS})
