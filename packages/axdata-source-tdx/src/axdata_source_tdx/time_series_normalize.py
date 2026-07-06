"""TDX K-line, intraday, trade, and auction row normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .codes import MARKET_TO_EXCHANGE, tdx_code_to_instrument_id
from .normalize_utils import (
    format_datetime,
    format_time,
    format_time_seconds,
    get_value,
    intraday_subchart_minute_time,
    locked_amount,
    round_optional_float,
    volume_change,
    volume_change_pct,
)
from .snapshot_normalize import DEFAULT_PRICE_DECIMAL


def kline_row_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("instrument_id") or ""),
        str(row.get("period") or ""),
        str(row.get("trade_time") or ""),
    )


def trade_row_sort_key(row: Mapping[str, Any]) -> tuple[str, str, int]:
    return (
        str(row.get("instrument_id") or ""),
        str(row.get("trade_time") or ""),
        int(row.get("trade_index") or 0),
    )


def auction_result_row_sort_key(row: Mapping[str, Any]) -> tuple[str, str, int]:
    return (
        str(row.get("instrument_id") or ""),
        str(row.get("auction_datetime") or row.get("auction_time") or ""),
        int(row.get("trade_index") or 0),
    )


def normalize_index_kline_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "instrument_id": row.get("instrument_id"),
        "symbol": row.get("symbol"),
        "tdx_code": row.get("tdx_code"),
        "exchange": row.get("exchange"),
        "trade_time": row.get("trade_time"),
        "period": row.get("period"),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "volume": row.get("volume"),
        "amount": row.get("amount"),
        "up_count": row.get("up_count"),
        "down_count": row.get("down_count"),
    }


def normalize_stock_kline_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "instrument_id": row.get("instrument_id"),
        "symbol": row.get("symbol"),
        "tdx_code": row.get("tdx_code"),
        "exchange": row.get("exchange"),
        "trade_time": row.get("trade_time"),
        "period": row.get("period"),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "volume": row.get("volume"),
        "amount": row.get("amount"),
    }


def normalize_kline_row(series: Any, bar: Any) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    symbol = str(get_value(series, "code") or instrument_id.split(".", 1)[0])
    exchange = MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper())
    return {
        "instrument_id": instrument_id,
        "symbol": symbol,
        "tdx_code": tdx_code,
        "exchange": exchange,
        "trade_time": format_datetime(get_value(bar, "time")),
        "period": get_value(series, "period_name"),
        "open": get_value(bar, "open"),
        "high": get_value(bar, "high"),
        "low": get_value(bar, "low"),
        "close": get_value(bar, "close"),
        "volume": get_value(bar, "volume_lots"),
        "amount": get_value(bar, "amount"),
        "up_count": get_value(bar, "up_count"),
        "down_count": get_value(bar, "down_count"),
    }


def normalize_intraday_history_row(
    series: Any,
    point: Any,
    *,
    decimal: int = DEFAULT_PRICE_DECIMAL,
) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    trade_date = get_value(point, "trade_date", get_value(series, "trade_date"))
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper()),
        "trade_date": trade_date.strftime("%Y%m%d") if hasattr(trade_date, "strftime") else trade_date,
        "trade_time": format_datetime(get_value(point, "time")),
        "minute_index": get_value(point, "minute_index"),
        "price": price_from_raw(get_value(point, "price_acc_raw"), decimal, get_value(point, "price")),
        "volume": get_value(point, "volume"),
        "prev_close": round_optional_float(get_value(series, "prev_close")),
    }


def normalize_intraday_recent_history_row(
    series: Any,
    point: Any,
    *,
    decimal: int = DEFAULT_PRICE_DECIMAL,
) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    trade_date = get_value(point, "trade_date", get_value(series, "trade_date"))
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper()),
        "trade_date": trade_date.strftime("%Y%m%d") if hasattr(trade_date, "strftime") else trade_date,
        "trade_time": format_datetime(get_value(point, "time")),
        "time_label": get_value(point, "time_label"),
        "minute_index": get_value(point, "minute_index"),
        "price": price_from_raw(get_value(point, "price_raw"), decimal, get_value(point, "price")),
        "avg_price": avg_price_from_raw(get_value(point, "avg_raw"), decimal, get_value(point, "avg_price")),
        "volume": get_value(point, "volume"),
        "prev_close": round_optional_float(get_value(series, "prev_close")),
        "open_price": round_optional_float(get_value(series, "open_price")),
    }


def normalize_intraday_today_row(
    series: Any,
    point: Any,
    *,
    decimal: int = DEFAULT_PRICE_DECIMAL,
) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper()),
        "time_label": get_value(point, "time_label"),
        "minute_index": get_value(point, "minute_index"),
        "price": price_from_raw(get_value(point, "price_raw"), decimal, get_value(point, "price")),
        "avg_price": avg_price_from_raw(get_value(point, "avg_raw"), decimal, get_value(point, "avg_price")),
        "volume": get_value(point, "volume"),
    }


def normalize_intraday_subchart_row(series: Any, point: Any) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    previous_volume = get_value(point, "previous_day_cumulative_volume")
    current_volume = get_value(point, "current_day_cumulative_volume")
    minute_index = get_value(point, "index")
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper()),
        "minute_time": intraday_subchart_minute_time(minute_index),
        "minute_index": minute_index,
        "bid_order": get_value(point, "bid_order"),
        "ask_order": get_value(point, "ask_order"),
        "today_volume": round_optional_float(current_volume),
        "yesterday_volume": round_optional_float(previous_volume),
        "volume_change": volume_change(current_volume, previous_volume),
        "volume_change_pct": volume_change_pct(current_volume, previous_volume),
    }


def normalize_auction_process_row(series: Any, record: Any) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper()),
        "auction_time": format_time_seconds(get_value(record, "auction_time")),
        "auction_index": get_value(record, "index"),
        "_sort_time_seconds": get_value(record, "time_seconds"),
        "price": round_optional_float(get_value(record, "price")),
        "matched_volume": get_value(record, "matched_volume"),
        "matched_amount_estimated": round_optional_float(get_value(record, "matched_amount_estimated")),
        "unmatched_volume": get_value(record, "unmatched_volume"),
        "unmatched_amount_estimated": round_optional_float(
            get_value(record, "unmatched_amount_estimated")
            if get_value(record, "unmatched_amount_estimated") is not None
            else locked_amount(get_value(record, "price"), get_value(record, "unmatched_volume"))
        ),
        "unmatched_direction": get_value(record, "unmatched_direction"),
    }


def price_from_raw(raw: Any, decimal: int, decoded: Any) -> float | None:
    """Recompute a price from its raw integer using ``10 ** decimal``.

    The wire layer decodes some prices with a hardcoded divisor that is only
    correct for ``decimal == 2`` securities. When the raw integer is available
    we rescale it with the security's true decimal places; otherwise we fall
    back to the value the wire layer already decoded.
    """
    if isinstance(raw, int):
        return round(raw / (10 ** decimal), 6)
    return round_optional_float(decoded)


def avg_price_from_raw(raw: Any, decimal: int, decoded: Any) -> float | None:
    """Recompute an intraday average price from its raw integer.

    Average prices carry two extra decimal places over the trade price, so the
    correct divisor is ``10 ** (decimal + 2)`` (legacy hardcoded ``/ 10000``
    only matched ``decimal == 2``).
    """
    if isinstance(raw, int):
        return round(raw / (10 ** (decimal + 2)), 6)
    return round_optional_float(decoded)


def normalize_trade_row(
    series: Any,
    record: Any,
    *,
    decimal: int = DEFAULT_PRICE_DECIMAL,
) -> dict[str, Any]:
    tdx_code = str(get_value(series, "full_code") or "").lower()
    if not tdx_code:
        exchange = str(get_value(series, "exchange") or "").lower()
        symbol = str(get_value(series, "code") or "")
        tdx_code = f"{exchange}{symbol}" if exchange and symbol else ""
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    trade_date = get_value(record, "trade_date", get_value(series, "trade_date"))
    trade_datetime = get_value(record, "trade_datetime")
    return {
        "instrument_id": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(series, "exchange") or "").upper()),
        "trade_date": trade_date.strftime("%Y%m%d") if hasattr(trade_date, "strftime") else trade_date,
        "trade_time": format_time(get_value(record, "trade_time")),
        "trade_datetime": format_datetime(trade_datetime),
        "trade_index": get_value(record, "absolute_index", get_value(record, "index")),
        "price": price_from_raw(get_value(record, "price_acc_raw"), decimal, get_value(record, "price")),
        "volume": get_value(record, "volume"),
        "order_count": get_value(record, "order_count"),
        "side": get_value(record, "side"),
    }


def is_opening_auction_result_trade(row: Mapping[str, Any]) -> bool:
    return str(row.get("trade_time") or "") == "09:25"


def normalize_auction_result_row(row: Mapping[str, Any], *, include_datetime: bool) -> dict[str, Any]:
    price = round_optional_float(row.get("price"))
    volume = row.get("volume")
    amount = auction_result_amount(price, volume)
    result = {
        "instrument_id": row.get("instrument_id"),
        "symbol": row.get("symbol"),
        "tdx_code": row.get("tdx_code"),
        "exchange": row.get("exchange"),
        "auction_time": row.get("trade_time"),
        "trade_index": row.get("trade_index"),
        "price": price,
        "volume": volume,
        "amount": amount,
        "order_count": row.get("order_count"),
    }
    if include_datetime:
        result["trade_date"] = row.get("trade_date")
        result["auction_datetime"] = row.get("trade_datetime")
    return result


def auction_result_amount(price: float | None, volume: Any) -> float | None:
    if price is None or volume in (None, ""):
        return None
    try:
        return round(price * float(volume) * 100.0, 6)
    except (TypeError, ValueError):
        return None


def kline_bars(series: Any) -> list[Any]:
    bars = get_value(series, "bars", ())
    if bars is None:
        return []
    if isinstance(bars, list):
        return bars
    if isinstance(bars, tuple):
        return list(bars)
    return list(bars)


def intraday_points(series: Any) -> list[Any]:
    points = get_value(series, "points", ())
    if points is None:
        return []
    if isinstance(points, list):
        return points
    if isinstance(points, tuple):
        return list(points)
    return list(points)


def subchart_points(series: Any) -> list[Any]:
    return intraday_points(series)


def trade_records(series: Any) -> list[Any]:
    records = get_value(series, "records", ())
    if records is None:
        return []
    if isinstance(records, list):
        return records
    if isinstance(records, tuple):
        return list(records)
    return list(records)
