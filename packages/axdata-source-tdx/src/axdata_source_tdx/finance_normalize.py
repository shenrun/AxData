"""TDX finance snapshot and capital-change normalization helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError

from .codes import MARKET_TO_EXCHANGE, MARKET_TO_ID, SUFFIX_TO_MARKET, tdx_code_to_instrument_id
from .normalize_utils import bytes_hex, get_value, optional_int, round_optional_float
from .request_filters import string_values


def lookup_finance_profile_maps(
    code: str,
    *,
    market_id: int | None,
    province_raw: int | None,
    local_maps: Any | None = None,
) -> dict[str, Any]:
    from .finance_maps import lookup_finance_profile_maps as lookup_maps

    return lookup_maps(
        code,
        market_id=market_id,
        province_raw=province_raw,
        local_maps=local_maps,
    )


def normalize_capital_change_row(tdx_code: str, record: Any) -> dict[str, Any]:
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    event_date = get_value(record, "date")
    event_date_text = event_date.strftime("%Y%m%d") if hasattr(event_date, "strftime") else event_date
    category_raw = get_value(record, "category_raw")
    c1 = capital_change_value(record, 1)
    c2 = capital_change_value(record, 2)
    c3 = capital_change_value(record, 3)
    c4 = capital_change_value(record, 4)
    return {
        "instrument_id": instrument_id,
        "ts_code": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], tdx_code[:2].upper()),
        "event_date": event_date_text,
        "category_raw": category_raw,
        "category_name": get_value(record, "category_name"),
        "c1": c1,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "c1_raw_hex": bytes_hex(get_value(record, "c1_raw")),
        "c2_raw_hex": bytes_hex(get_value(record, "c2_raw")),
        "c3_raw_hex": bytes_hex(get_value(record, "c3_raw")),
        "c4_raw_hex": bytes_hex(get_value(record, "c4_raw")),
        "record_hex": get_value(record, "record_hex")
        or capital_change_record_key(tdx_code, event_date_text, category_raw, c1, c2, c3, c4),
    }


def normalize_finance_info_row(
    record: Any,
    *,
    enrich_profile: bool = False,
    finance_maps: Any | None = None,
    profile_lookup: Callable[..., dict[str, Any]] = lookup_finance_profile_maps,
) -> dict[str, Any]:
    tdx_code = str(get_value(record, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(record, "exchange") or "").lower()
        symbol = str(get_value(record, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    updated_date = get_value(record, "updated_date")
    ipo_date = get_value(record, "ipo_date")
    finance_profile_maps = (
        finance_profile_maps_for_record(
            record,
            tdx_code,
            instrument_id,
            finance_maps=finance_maps,
            profile_lookup=profile_lookup,
        )
        if enrich_profile
        else {}
    )
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(record, "exchange") or "").upper()),
        "updated_date": updated_date.strftime("%Y%m%d") if hasattr(updated_date, "strftime") else updated_date,
        "ipo_date": ipo_date.strftime("%Y%m%d") if hasattr(ipo_date, "strftime") else ipo_date,
        "total_share": round_optional_float(get_value(record, "total_share")),
        "float_share": round_optional_float(get_value(record, "float_share")),
        "state_share": round_optional_float(get_value(record, "state_share")),
        "founder_legal_person_share": round_optional_float(get_value(record, "founder_legal_person_share")),
        "legal_person_share": round_optional_float(get_value(record, "legal_person_share")),
        "b_share": round_optional_float(get_value(record, "b_share")),
        "h_share": round_optional_float(get_value(record, "h_share")),
        "shareholder_count": get_value(record, "shareholder_count"),
        "eps": round_optional_float(get_value(record, "eps")),
        "bps": round_optional_float(get_value(record, "bps")),
        "total_assets": round_optional_float(get_value(record, "total_assets")),
        "current_assets": round_optional_float(get_value(record, "current_assets")),
        "fixed_assets": round_optional_float(get_value(record, "fixed_assets")),
        "intangible_assets": round_optional_float(get_value(record, "intangible_assets")),
        "current_liabilities": round_optional_float(get_value(record, "current_liabilities")),
        "long_term_liabilities": round_optional_float(get_value(record, "long_term_liabilities")),
        "capital_reserve": round_optional_float(get_value(record, "capital_reserve")),
        "net_assets": round_optional_float(get_value(record, "net_assets")),
        "revenue": round_optional_float(get_value(record, "revenue")),
        "main_business_profit": round_optional_float(get_value(record, "main_business_profit")),
        "accounts_receivable": round_optional_float(get_value(record, "accounts_receivable")),
        "operating_profit": round_optional_float(get_value(record, "operating_profit")),
        "investment_income": round_optional_float(get_value(record, "investment_income")),
        "operating_cashflow": round_optional_float(get_value(record, "operating_cashflow")),
        "total_cashflow": round_optional_float(get_value(record, "total_cashflow")),
        "inventory": round_optional_float(get_value(record, "inventory")),
        "total_profit": round_optional_float(get_value(record, "total_profit")),
        "after_tax_profit": round_optional_float(get_value(record, "after_tax_profit")),
        "net_profit": round_optional_float(get_value(record, "net_profit")),
        "undistributed_profit": round_optional_float(get_value(record, "undistributed_profit")),
        "province_raw": get_value(record, "province_raw"),
        "province_name": get_value(record, "province_name") or finance_profile_maps.get("province_name"),
        "province_board_name": get_value(record, "province_board_name")
        or finance_profile_maps.get("province_board_name"),
        "province_board_code": get_value(record, "province_board_code")
        or finance_profile_maps.get("province_board_code"),
        "industry_raw": get_value(record, "industry_raw"),
        "tdx_industry_code": get_value(record, "tdx_industry_code")
        or finance_profile_maps.get("tdx_industry_code"),
        "tdx_industry_name": get_value(record, "tdx_industry_name")
        or finance_profile_maps.get("tdx_industry_name"),
        "tdx_industry_path": finance_path_value(
            get_value(record, "tdx_industry_path") or finance_profile_maps.get("tdx_industry_path")
        ),
        "tdx_research_industry_code": get_value(record, "tdx_research_industry_code")
        or finance_profile_maps.get("tdx_research_industry_code"),
        "tdx_research_industry_name": get_value(record, "tdx_research_industry_name")
        or finance_profile_maps.get("tdx_research_industry_name"),
        "tdx_research_industry_path": finance_path_value(
            get_value(record, "tdx_research_industry_path")
            or finance_profile_maps.get("tdx_research_industry_path")
        ),
    }


def finance_profile_maps_for_record(
    record: Any,
    tdx_code: str,
    instrument_id: str,
    *,
    finance_maps: Any | None = None,
    profile_lookup: Callable[..., dict[str, Any]] = lookup_finance_profile_maps,
) -> dict[str, Any]:
    symbol = str(get_value(record, "code") or "")
    if not symbol and len(tdx_code) == 8 and tdx_code[:2] in MARKET_TO_ID:
        symbol = tdx_code[2:]
    if not symbol and len(instrument_id) >= 6:
        symbol = instrument_id[:6]
    market_id = finance_market_id(record, tdx_code, instrument_id)
    province_raw = optional_int(get_value(record, "province_raw"))
    if not symbol or market_id is None:
        return {}
    return profile_lookup(
        symbol,
        market_id=market_id,
        province_raw=province_raw,
        local_maps=finance_maps,
    )


def finance_market_id(record: Any, tdx_code: str, instrument_id: str) -> int | None:
    for name in ("market_id", "exchange_raw"):
        value = optional_int(get_value(record, name))
        if value is not None:
            return value
    market = ""
    if len(tdx_code) == 8:
        market = tdx_code[:2]
    if not market and "." in instrument_id:
        market = SUFFIX_TO_MARKET.get(instrument_id.rsplit(".", 1)[-1].upper(), "")
    if not market:
        market = str(get_value(record, "exchange") or "").lower()
    return MARKET_TO_ID.get(market)


def finance_path_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value or None
    if not value:
        return None
    try:
        items = [str(item) for item in value if str(item)]
    except TypeError:
        return str(value)
    return " / ".join(items) if items else None


def capital_change_value(record: Any, index: int) -> float | None:
    category = int(get_value(record, "category_raw", 0) or 0)
    value_type = "quantity" if category in {2, 3, 4, 5, 7, 8, 9, 10} else "float"
    return round_optional_float(get_value(record, f"c{index}_{value_type}"))


def capital_change_record_key(
    tdx_code: str,
    event_date: Any,
    category_raw: Any,
    c1: Any,
    c2: Any,
    c3: Any,
    c4: Any,
) -> str:
    values = (
        tdx_code,
        "" if event_date is None else str(event_date),
        "" if category_raw is None else str(category_raw),
        "" if c1 is None else str(c1),
        "" if c2 is None else str(c2),
        "" if c3 is None else str(c3),
        "" if c4 is None else str(c4),
    )
    return "|".join(values)


def requested_capital_change_categories(value: Any) -> set[int] | None:
    if value in (None, ""):
        return None
    categories: set[int] = set()
    aliases = {
        "xdxr": 1,
        "dividend": 1,
        "除权除息": 1,
        "equity": 5,
        "股本变化": 5,
        "restructure": 15,
        "重整调整": 15,
    }
    for item in string_values(value):
        key = item.strip().lower()
        if not key:
            continue
        if key in aliases:
            categories.add(aliases[key])
            continue
        try:
            categories.add(int(key))
        except ValueError as exc:
            raise SourceRequestValidationError(
                "category must be a TDX raw integer category or one of: xdxr, dividend, equity, restructure"
            ) from exc
    return categories or None


def capital_change_category_matches(record: Any, categories: set[int] | None) -> bool:
    if categories is None:
        return True
    return int(get_value(record, "category_raw", 0) or 0) in categories


def finance_records(block: Any) -> list[Any]:
    records = get_value(block, "records", ())
    if records is None:
        return []
    if isinstance(records, list):
        return records
    if isinstance(records, tuple):
        return list(records)
    return list(records)
