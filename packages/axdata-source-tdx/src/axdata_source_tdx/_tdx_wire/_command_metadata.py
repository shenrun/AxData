"""Provider-owned command registry metadata facts."""

COMMAND_METADATA_ITEMS: tuple[tuple[str, str, str, bool, str], ...] = (
    ("heartbeat", "session", "heartbeat", True, "0x0004-心跳保活接口.md"),
    ("handshake", "session", "handshake", True, "0x000d-连接握手接口.md"),
    ("capital_changes", "corporate", "capital_changes", False, "0x000f-股本变迁查询接口.md"),
    ("finance_info", "finance", "info", False, "0x0010-财务信息批量查询&下发接口.md"),
    ("security_list", "codes", "list", True, "0x044d-代码表分页接口.md"),
    ("security_count", "codes", "count", True, "0x044e-代码数量接口.md"),
    ("price_limits", "quotes", "price_limits", False, "0x0452-特殊品种涨跌停限制表接口.md"),
    ("intraday_subchart", "intraday", "subchart", False, "0x051b-个股分时副图数据接口.md"),
    ("klines", "bars", "get", False, "0x052d-K线周期数据接口.md"),
    ("today_intraday", "intraday", "today", False, "0x0537-个股当前日分时图接口.md"),
    ("legacy_quotes", "quotes", "legacy", False, "0x053e-旧版批量行情快照接口.md"),
    ("refresh_quotes", "quotes", "refresh", False, "0x0547-行情增量刷新推送接口.md"),
    ("category_quotes", "quotes", "category", False, "0x054b-分类行情列表分页接口.md"),
    ("explicit_quotes", "quotes", "explicit", False, "0x054c-显式代码批量行情快照接口.md"),
    ("auction_process", "auction", "process", False, "0x056a-集合竞价明细接口.md"),
    ("file_content", "resources", "download_chunk", False, "0x06b9-文件资源下载接口.md"),
    ("historical_intraday", "intraday", "historical", False, "0x0fb4-历史分时数据接口.md"),
    ("today_trades", "trades", "today", False, "0x0fc5-当日成交明细分页接口.md"),
    ("historical_trades", "trades", "historical", False, "0x0fc6-历史成交明细增强分页接口.md"),
    (
        "recent_historical_intraday",
        "intraday",
        "recent_historical",
        False,
        "0x0feb-近期历史分时图接口.md",
    ),
)

__all__ = ["COMMAND_METADATA_ITEMS"]
