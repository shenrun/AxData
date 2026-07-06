"""TDX command layout facts shared by provider-owned wire commands."""

AUCTION_RECORD_SIZE = 16
CAPITAL_CHANGE_RECORD_SIZE = 29
FINANCE_INFO_RECORD_SIZE = 143
FINANCE_INFO_BODY_SIZE = 136
PRICE_LIMIT_RECORD_SIZE = 13
CODE_RECORD_SIZE = 37

INDEX_PREFIXES = ("sh000", "sh880", "sh881", "sh999", "sz399", "bj899")
ETF_PREFIXES = (
    "sh510",
    "sh511",
    "sh512",
    "sh513",
    "sh515",
    "sh516",
    "sh517",
    "sh518",
    "sh520",
    "sh560",
    "sh561",
    "sh562",
    "sh563",
    "sh588",
    "sz158",
    "sz159",
)
FUND_PREFIXES = (
    "sh501",
    "sh502",
    "sh506",
    "sh508",
    "sz150",
    "sz160",
    "sz161",
    "sz162",
    "sz163",
    "sz164",
    "sz165",
    "sz166",
    "sz167",
    "sz184",
)
SSE_A_SHARE_PREFIXES = ("sh600", "sh601", "sh603", "sh605", "sh688")
SZSE_A_SHARE_PREFIXES = ("sz000", "sz001", "sz002", "sz003", "sz004", "sz300", "sz301")

INTRADAY_SUBCHART_BUY_SELL_STRENGTH = 0x00
INTRADAY_SUBCHART_VOLUME_COMPARISON = 0x0B
INTRADAY_SUBCHART_SELECTOR_NAMES = {
    INTRADAY_SUBCHART_BUY_SELL_STRENGTH: "buy_sell_strength",
    INTRADAY_SUBCHART_VOLUME_COMPARISON: "volume_comparison",
}

SIDE_MAP = {
    0: "buy",
    1: "sell",
    2: "neutral",
}

CAPITAL_CHANGE_CATEGORY_NAMES = {
    1: "\u9664\u6743\u9664\u606f",
    2: "\u9001\u914d\u80a1\u4e0a\u5e02",
    3: "\u975e\u6d41\u901a\u80a1\u4e0a\u5e02",
    4: "\u672a\u77e5\u80a1\u672c\u53d8\u52a8",
    5: "\u80a1\u672c\u53d8\u5316",
    6: "\u589e\u53d1\u65b0\u80a1",
    7: "\u80a1\u4efd\u56de\u8d2d",
    8: "\u589e\u53d1\u65b0\u80a1\u4e0a\u5e02",
    9: "\u8f6c\u914d\u80a1\u4e0a\u5e02",
    10: "\u53ef\u8f6c\u503a\u4e0a\u5e02",
    11: "\u6269\u7f29\u80a1",
    12: "\u975e\u6d41\u901a\u80a1\u7f29\u80a1",
    13: "\u9001\u8ba4\u8d2d\u6743\u8bc1",
    14: "\u9001\u8ba4\u6cbd\u6743\u8bc1",
    15: "\u91cd\u6574\u8c03\u6574",
}

__all__ = [
    "AUCTION_RECORD_SIZE",
    "CAPITAL_CHANGE_CATEGORY_NAMES",
    "CAPITAL_CHANGE_RECORD_SIZE",
    "CODE_RECORD_SIZE",
    "ETF_PREFIXES",
    "FINANCE_INFO_BODY_SIZE",
    "FINANCE_INFO_RECORD_SIZE",
    "FUND_PREFIXES",
    "INDEX_PREFIXES",
    "INTRADAY_SUBCHART_BUY_SELL_STRENGTH",
    "INTRADAY_SUBCHART_SELECTOR_NAMES",
    "INTRADAY_SUBCHART_VOLUME_COMPARISON",
    "PRICE_LIMIT_RECORD_SIZE",
    "SIDE_MAP",
    "SSE_A_SHARE_PREFIXES",
    "SZSE_A_SHARE_PREFIXES",
]
