"""TDX realtime rank category/sort/filter parameter rules."""

from __future__ import annotations

from typing import Any

from .request_filters import string_values
from axdata_core.source_errors import SourceRequestValidationError


TDX_RANK_CATEGORY_ALIASES = {
    "a_share": 6,
    "ashare": 6,
    "a": 6,
    "all": 6,
    "全部": 6,
    "a股": 6,
    "sse": 0,
    "sh": 0,
    "sh_a": 0,
    "上证a": 0,
    "上证a股": 0,
    "szse": 2,
    "sz": 2,
    "sz_a": 2,
    "深证a": 2,
    "深证a股": 2,
    "b_share": 7,
    "b股": 7,
    "star": 8,
    "kcb": 8,
    "科创板": 8,
    "bse": 12,
    "bj": 12,
    "北证a": 12,
    "北证a股": 12,
    "chinext": 14,
    "cyb": 14,
    "创业板": 14,
    "hgt": 0x2AF9,
    "沪股通": 0x2AF9,
    "sgt": 0x2B01,
    "深股通": 0x2B01,
    "etf": 0x2AFD,
    "lof": 0x2B04,
    "index": 0x2B2C,
    "指数": 0x2B2C,
    "industry": 10001,
    "行业一级": 10001,
    "industry2": 10002,
    "行业二级": 10002,
    "concept": 10004,
    "概念": 10004,
    "style": 10005,
    "风格": 10005,
    "region": 10006,
    "地区": 10006,
}

TDX_RANK_SORT_ALIASES = {
    "code": 0x0000,
    "last_price": 0x0006,
    "price": 0x0006,
    "close": 0x0006,
    "volume": 0x0009,
    "total_hand": 0x0009,
    "amount": 0x000A,
    "change_pct": 0x000E,
    "pct_chg": 0x000E,
    "amplitude_pct": 0x000F,
    "pe_dynamic": 0x0011,
    "entrust_ratio": 0x0012,
    "inside_outside_ratio": 0x0015,
    "locked_ratio": 0x001B,
    "seal_fill_ratio": 0x001B,
    "locked_amount": 0x001C,
    "open_amount": 0x001D,
    "open_turnover": 0x001E,
    "volume_ratio": 0x0023,
    "vol_ratio": 0x0023,
    "turnover_rate": 0x0024,
    "float_market_cap": 0x0026,
    "total_market_cap": 0x0027,
    "strength": 0x002D,
    "rise_speed": 0x002E,
    "activity": 0x002F,
    "short_turnover": 0x00CC,
    "vol_rise_speed": 0x00D0,
    "main_net_amount": 0x00D4,
    "opening_rush": 0x010A,
    "min2_amount": 0x010C,
    "open_change_pct": 0x0119,
    "high_change_pct": 0x011A,
    "low_change_pct": 0x011B,
    "drawdown_pct": 0x011E,
    "attack_pct": 0x011F,
}

TDX_RANK_FILTER_ALIASES = {
    "new": 1,
    "exclude_new": 1,
    "次新": 1,
    "未开板次新": 1,
    "kcb": 2,
    "star": 2,
    "exclude_kcb": 2,
    "科创板": 2,
    "st": 4,
    "exclude_st": 4,
    "st股": 4,
    "cyb": 8,
    "chinext": 8,
    "exclude_cyb": 8,
    "创业板": 8,
    "bj": 16,
    "bse": 16,
    "exclude_bj": 16,
    "北证a": 16,
}


def rank_category_param(value: Any) -> int:
    if value in (None, ""):
        return TDX_RANK_CATEGORY_ALIASES["a_share"]
    text = str(value).strip()
    key = text.lower()
    if key in TDX_RANK_CATEGORY_ALIASES:
        return TDX_RANK_CATEGORY_ALIASES[key]
    try:
        parsed = int(text, 0)
    except ValueError as exc:
        raise SourceRequestValidationError(
            "category must be a supported realtime rank category alias or TDX raw category integer"
        ) from exc
    if not 0 <= parsed <= 0xFFFF:
        raise SourceRequestValidationError("category must be between 0 and 65535")
    return parsed


def rank_sort_param(value: Any) -> int:
    if value in (None, ""):
        return TDX_RANK_SORT_ALIASES["change_pct"]
    text = str(value).strip()
    key = text.lower()
    if key in TDX_RANK_SORT_ALIASES:
        return TDX_RANK_SORT_ALIASES[key]
    try:
        parsed = int(text, 0)
    except ValueError as exc:
        raise SourceRequestValidationError(
            "sort must be a supported realtime rank sort alias or TDX raw sort_type integer"
        ) from exc
    if not 0 <= parsed <= 0xFFFF:
        raise SourceRequestValidationError("sort must be between 0 and 65535")
    return parsed


def rank_filter_param(value: Any) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, int):
        if not 0 <= value <= 0xFFFF:
            raise SourceRequestValidationError("filters must be between 0 and 65535")
        return value
    filter_raw = 0
    for item in string_values(value):
        key = item.strip().lower()
        if not key:
            continue
        if key in TDX_RANK_FILTER_ALIASES:
            filter_raw |= TDX_RANK_FILTER_ALIASES[key]
            continue
        try:
            filter_raw |= int(key, 0)
        except ValueError as exc:
            raise SourceRequestValidationError(
                "filters must be filter aliases, a list of aliases, or a TDX raw filter bitmask"
            ) from exc
    if not 0 <= filter_raw <= 0xFFFF:
        raise SourceRequestValidationError("filters must be between 0 and 65535")
    return filter_raw
