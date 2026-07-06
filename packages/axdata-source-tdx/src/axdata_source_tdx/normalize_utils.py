"""Small normalization utilities shared by TDX request helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def get_value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(name, default)
    if is_dataclass(item):
        try:
            return getattr(item, name)
        except AttributeError:
            data = asdict(item)
            return data.get(name, default)
    return getattr(item, name, default)


def optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def round_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def tenk_yuan(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) * 10000.0, 6)


def tenk_to_unit(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) * 10000.0, 6)


def tenk_shares_to_lots(value: Any) -> float | None:
    shares = tenk_to_unit(value)
    if shares is None:
        return None
    return round(shares / 100.0, 6)


def market_value(shares: Any, price: Any) -> float | None:
    if shares is None or price is None:
        return None
    return round(float(shares) * float(price), 6)


def auction_open_volume_hand(open_amount: Any, open_price: Any) -> float | None:
    if open_amount is None or open_price is None:
        return None
    price = float(open_price)
    if price == 0:
        return None
    return round(float(open_amount) / price / 100.0, 6)


def open_volume_ratio(open_volume_hand: Any, recent_daily_bars: Sequence[Any]) -> float | None:
    if open_volume_hand is None:
        return None
    volumes = [
        float(volume)
        for volume in (get_value(bar, "volume_lots") for bar in recent_daily_bars[:5])
        if volume not in (None, "")
    ]
    if len(volumes) < 5:
        return None
    average_minute_volume = sum(volumes) / (240.0 * 5.0)
    if average_minute_volume == 0:
        return None
    return round(float(open_volume_hand) / average_minute_volume, 6)


def limit_board_text(days: Any, count: Any) -> str | None:
    if days in (None, "") or count in (None, ""):
        return None
    day_int = int(days)
    count_int = int(count)
    if day_int <= 0 or count_int <= 0:
        return None
    return f"{day_int}天{count_int}板"


def bar_trade_date(bar: Any) -> str | None:
    value = get_value(bar, "time")
    if hasattr(value, "strftime"):
        return value.strftime("%Y%m%d")
    text = str(value or "").strip()
    if not text:
        return None
    digits = "".join(ch for ch in text[:10] if ch.isdigit())
    return digits if len(digits) == 8 else None


def percent_change(value: Any, base: Any) -> float | None:
    if value is None or base is None:
        return None
    base_float = float(base)
    if base_float == 0:
        return None
    return round((float(value) - base_float) / base_float * 100, 6)


def locked_amount(price: Any, volume: Any) -> float | None:
    if price is None or volume is None:
        return None
    return round(float(price) * float(volume) * 100.0, 6)


def average_price(amount: Any, volume: Any) -> float | None:
    if amount is None or volume is None:
        return None
    volume_float = float(volume)
    if volume_float == 0:
        return None
    return round(float(amount) / (volume_float * 100.0), 6)


def safe_ratio(numerator: Any, denominator: Any) -> float | None:
    if numerator is None or denominator is None:
        return None
    denominator_float = float(denominator)
    if denominator_float == 0:
        return None
    return round(float(numerator) / denominator_float, 6)


def safe_ratio_pct(numerator: Any, denominator: Any) -> float | None:
    if numerator is None or denominator is None:
        return None
    denominator_float = float(denominator)
    if denominator_float == 0:
        return None
    return round(float(numerator) / denominator_float * 100.0, 6)


def drawdown_pct(high_price: Any, last_price: Any, pre_close: Any) -> float | None:
    if high_price is None or last_price is None or pre_close is None:
        return None
    pre_close_float = float(pre_close)
    if pre_close_float == 0:
        return None
    return round((float(high_price) - float(last_price)) / pre_close_float * 100.0, 6)


def attack_pct(last_price: Any, low_price: Any, pre_close: Any) -> float | None:
    if last_price is None or low_price is None or pre_close is None:
        return None
    pre_close_float = float(pre_close)
    if pre_close_float == 0:
        return None
    return round((float(last_price) - float(low_price)) / pre_close_float * 100.0, 6)


def optional_int_diff(left: Any, right: Any) -> int | None:
    left_int = optional_int(left)
    right_int = optional_int(right)
    if left_int is None or right_int is None:
        return None
    return left_int - right_int


def balance_pct(left: Any, right: Any) -> float | None:
    left_int = optional_int(left)
    right_int = optional_int(right)
    if left_int is None or right_int is None:
        return None
    total = left_int + right_int
    if total == 0:
        return None
    return round((left_int - right_int) / total * 100.0, 6)


def volume_ratio_vs_previous_day(current_volume: Any, previous_volume: Any) -> float | None:
    if current_volume is None or previous_volume is None:
        return None
    previous = float(previous_volume)
    if previous == 0:
        return None
    return round(float(current_volume) / previous, 6)


def volume_change(current_volume: Any, previous_volume: Any) -> float | None:
    if current_volume is None or previous_volume is None:
        return None
    return round(float(current_volume) - float(previous_volume), 6)


def volume_change_pct(current_volume: Any, previous_volume: Any) -> float | None:
    if current_volume is None or previous_volume is None:
        return None
    previous = float(previous_volume)
    if previous == 0:
        return None
    return round((float(current_volume) - previous) / previous * 100, 6)


def intraday_subchart_minute_time(minute_index: Any) -> str | None:
    if minute_index is None:
        return None
    try:
        index = int(minute_index)
    except (TypeError, ValueError):
        return None
    if index < 0:
        return None
    if index < 120:
        hour = 9 + (30 + index) // 60
        minute = (30 + index) % 60
    else:
        afternoon_index = index - 120
        hour = 13 + afternoon_index // 60
        minute = afternoon_index % 60
    return f"{hour:02d}:{minute:02d}"


def bytes_hex(value: Any) -> str | None:
    if isinstance(value, bytes):
        return value.hex()
    return None


def format_datetime(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def format_time(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat(timespec="minutes")
    return value


def format_time_seconds(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat(timespec="seconds")
    return value
