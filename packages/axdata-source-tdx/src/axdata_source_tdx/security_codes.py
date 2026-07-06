"""TDX security code-list classification and row normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .codes import MARKET_TO_EXCHANGE, tdx_code_to_instrument_id
from .normalize_utils import get_value


ASSET_TYPE_MAP = {
    "a_share": "stock",
    "b_share": "stock",
    "etf": "etf",
    "fund": "fund",
    "index": "index",
    "cdr": "cdr",
}

BOARD_MAP = {
    "sse_main_board": "主板",
    "sse_star_market": "科创板",
    "sse_cdr": "CDR",
    "szse_main_board": "主板",
    "szse_chinext": "创业板",
    "bse_listed_stock": "北交所",
    "none": None,
}

SCOPE_TO_BOARDS = {
    "all": None,
    "全部": None,
    "*": None,
    "main": {"sse_main_board", "szse_main_board"},
    "主板": {"sse_main_board", "szse_main_board"},
    "star": {"sse_star_market"},
    "科创板": {"sse_star_market"},
    "cdr": {"sse_cdr"},
    "CDR": {"sse_cdr"},
    "chinext": {"szse_chinext"},
    "创业板": {"szse_chinext"},
    "bse": {"bse_listed_stock"},
    "北交所": {"bse_listed_stock"},
}


def normalize_security(item: Any) -> dict[str, Any]:
    category = get_value(item, "category")
    board = get_value(item, "board")
    tdx_code = str(get_value(item, "full_code") or "").lower()
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    symbol = str(get_value(item, "code") or instrument_id.split(".", 1)[0])
    market = str(get_value(item, "exchange") or "").lower()
    asset_type = ASSET_TYPE_MAP.get(str(category), str(category or "unknown"))
    return {
        "instrument_id": instrument_id,
        "symbol": symbol,
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(market, market.upper()),
        "name": get_value(item, "name"),
        "asset_type": asset_type,
        "tdx_category": category,
        "tdx_category_reason": get_value(item, "category_reason"),
        "listing_status": "listed",
        "list_date": None,
        "market": BOARD_MAP.get(str(board), board),
        "market_code": board,
        "tdx_market_reason": get_value(item, "board_reason"),
        "tdx_decimal": get_value(item, "decimal"),
        "tdx_multiple": get_value(item, "multiple"),
        "tdx_previous_close_price": get_value(item, "previous_close_price"),
        "tdx_volume_ratio_base": get_value(item, "volume_ratio_base"),
    }


def board_from_tdx_code(tdx_code: Any) -> str | None:
    text = str(tdx_code or "").strip().lower()
    if len(text) != 8:
        return None
    market = text[:2]
    symbol = text[2:]
    if market == "bj":
        return "bse_listed_stock"
    if market == "sh":
        if symbol.startswith("688"):
            return "sse_star_market"
        if symbol.startswith("689"):
            return "sse_cdr"
        if symbol.startswith(("600", "601", "603", "605")):
            return "sse_main_board"
    if market == "sz":
        if symbol.startswith(("300", "301")):
            return "szse_chinext"
        if symbol.startswith(("000", "001", "002", "003", "004")):
            return "szse_main_board"
    return None


def index_type_from_tdx_code(tdx_code: str) -> str:
    code = str(tdx_code or "").lower()
    if code.startswith(("sh000", "sz399", "bj899")):
        return "official_index"
    if code.startswith(("sh880", "sh881", "sh999")):
        return "tdx_block_index"
    return "index"


def etf_type_from_tdx_code(tdx_code: str) -> str | None:
    code = str(tdx_code or "").lower()
    if code.startswith(("sh51", "sh56", "sh58")):
        return "sse_etf"
    if code.startswith("sz15"):
        return "szse_etf"
    return None


def normalize_index_code_row(row: Mapping[str, Any], index_type: str) -> dict[str, Any]:
    return {
        "instrument_id": row.get("instrument_id"),
        "symbol": row.get("symbol"),
        "tdx_code": row.get("tdx_code"),
        "exchange": row.get("exchange"),
        "name": row.get("name"),
        "index_type": index_type,
        "previous_close": row.get("tdx_previous_close_price"),
    }
