"""TDX price-limit and limit-up status rules."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .normalize_utils import get_value, round_optional_float


def price_limit_ratio_from_rule(tdx_code: str, name_flag: str | None) -> float | None:
    if name_flag in {"N", "C"}:
        return None
    if name_flag in {"ST", "*ST"}:
        return 5.0
    symbol = str(tdx_code[2:])
    if tdx_code.startswith("bj"):
        return 30.0
    if tdx_code.startswith("sh") and symbol.startswith("688"):
        return 20.0
    if tdx_code.startswith("sz") and (symbol.startswith("300") or symbol.startswith("301")):
        return 20.0
    return 10.0


def price_limit_rule(tdx_code: str, name_flag: str | None) -> str:
    if name_flag == "N":
        return "ipo_first_day"
    if name_flag == "C":
        return "ipo_first_5_days"
    if name_flag in {"ST", "*ST"}:
        return "st_5pct"
    symbol = str(tdx_code[2:])
    if tdx_code.startswith("bj"):
        return "bse_30pct"
    if tdx_code.startswith("sh") and symbol.startswith("688"):
        return "star_20pct"
    if tdx_code.startswith("sz") and (symbol.startswith("300") or symbol.startswith("301")):
        return "chinext_20pct"
    return "main_10pct"


def price_limit_name_flag(name: str | None) -> str | None:
    text = str(name or "").strip().upper()
    if not text:
        return None
    if text.startswith("*ST"):
        return "*ST"
    if text.startswith("ST"):
        return "ST"
    if text.startswith("N"):
        return "N"
    if text.startswith("C"):
        return "C"
    return None


def st_type_from_name(name: Any) -> str | None:
    text = str(name or "").strip().upper()
    if not text:
        return None
    if text.startswith("*ST") or text.startswith("S*ST"):
        return "*ST"
    if text.startswith("ST") or text.startswith("SST"):
        return "ST"
    return None


def price_limit_ratio(tdx_code: str, quote: Any) -> float:
    symbol = str(tdx_code[2:])
    name = str(get_value(quote, "name") or "")
    if "ST" in name.upper():
        return 5.0
    if tdx_code.startswith("bj"):
        return 30.0
    if tdx_code.startswith("sh") and symbol.startswith("688"):
        return 20.0
    if tdx_code.startswith("sz") and (symbol.startswith("300") or symbol.startswith("301")):
        return 20.0
    return 10.0


def rule_price_limits(pre_close: Any, limit_ratio: float) -> tuple[float | None, float | None]:
    if pre_close in (None, ""):
        return None, None
    close = float(pre_close)
    return (
        round_price(close * (1.0 + limit_ratio / 100.0)),
        round_price(close * (1.0 - limit_ratio / 100.0)),
    )


def special_limit_ratio(pre_close: Any, limit_up_price: Any, limit_down_price: Any) -> float | None:
    if pre_close in (None, "", 0) or limit_up_price in (None, ""):
        return None
    return round_optional_float((float(limit_up_price) / float(pre_close) - 1.0) * 100.0)


def round_price(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return round(float(value) + 1e-9, 2)


def positive_number(value: Any) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def price_close(left: Any, right: Any, *, tolerance: float = 0.0051) -> bool:
    if left in (None, "") or right in (None, ""):
        return False
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return False


def price_at_or_above(left: Any, right: Any, *, tolerance: float = 0.0051) -> bool:
    if left in (None, "") or right in (None, ""):
        return False
    try:
        return float(left) + tolerance >= float(right)
    except (TypeError, ValueError):
        return False


def limit_ladder_status(snapshot: Mapping[str, Any], limit_up_price: Any) -> str:
    if limit_up_price is None:
        return "none"
    if price_close(snapshot.get("last_price"), limit_up_price) and (
        price_close(snapshot.get("bid1_price"), limit_up_price)
        or (snapshot.get("locked_amount") not in (None, "") and float(snapshot.get("locked_amount") or 0) > 0)
    ):
        return "sealed"
    if price_at_or_above(snapshot.get("high"), limit_up_price) or price_at_or_above(
        snapshot.get("last_price"), limit_up_price
    ):
        return "touched"
    return "none"
