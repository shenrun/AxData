"""TDX quote snapshot normalization helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from axdata_core.source_errors import SourceUnavailableError

from .codes import MARKET_TO_EXCHANGE, tdx_code_to_instrument_id
from .normalize_utils import (
    attack_pct,
    average_price,
    balance_pct,
    drawdown_pct,
    get_value,
    locked_amount,
    optional_int,
    optional_int_diff,
    percent_change,
    round_optional_float,
    safe_ratio,
    safe_ratio_pct,
)


# Default price decimal places when the security code table has no entry.
# Stocks/indexes use 2 (price = raw / 100), which matches legacy behavior.
DEFAULT_PRICE_DECIMAL = 2


INDEX_SNAPSHOT_FIELDS = (
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
    "volume",
    "current_volume",
    "amount",
    "open_amount",
    "rise_speed",
    "activity",
)


def tdx_codes(client: Any, market: str, *, start: int, limit: int) -> Any:
    if hasattr(client, "get_codes"):
        return client.get_codes(market, start=start, limit=limit)
    if hasattr(client, "codes"):
        return client.codes.list(market, start=start, limit=limit)
    raise SourceUnavailableError("TDX client does not expose code list requests.")


def tdx_codes_all(client: Any, market: str, *, page_size: int = 1600) -> list[Any]:
    if hasattr(client, "get_codes_all"):
        return as_list(client.get_codes_all(market))
    if hasattr(client, "codes") and hasattr(client.codes, "all"):
        return as_list(client.codes.all(market))
    rows: list[Any] = []
    current_start = 0
    while True:
        page = as_list(tdx_codes(client, market, start=current_start, limit=page_size))
        if not page:
            break
        rows.extend(page)
        if len(page) < page_size:
            break
        current_start += len(page)
    return rows


def price_decimal(client: Any, tdx_code: str) -> int:
    """Return the price decimal places for a tdx_code such as ``sh510050``.

    The correct price divisor is ``10 ** decimal`` (stocks/indexes use 2,
    ETFs use 3). The security code table is read through ``tdx_codes_all``,
    which is served from the client's in-memory cache once the table has been
    fetched (no extra network round-trip in that case). Returns
    ``DEFAULT_PRICE_DECIMAL`` when the code or its code table entry cannot be
    resolved, so price scaling degrades to legacy behavior rather than failing.

    This performs a linear scan of one market's code table. Callers that
    normalize many records for the same security should resolve the decimal
    once and reuse it rather than calling this per record.
    """
    text = str(tdx_code or "").strip().lower()
    if len(text) < 3:
        return DEFAULT_PRICE_DECIMAL
    market = text[:2]
    code = text[2:]
    if market not in MARKET_TO_EXCHANGE:
        return DEFAULT_PRICE_DECIMAL
    try:
        for item in tdx_codes_all(client, market):
            if str(get_value(item, "code")) == code:
                decimal = get_value(item, "decimal")
                return decimal if isinstance(decimal, int) else DEFAULT_PRICE_DECIMAL
    except Exception:
        return DEFAULT_PRICE_DECIMAL
    return DEFAULT_PRICE_DECIMAL


def quote_tdx_code(quote: Any) -> str:
    tdx_code = str(get_value(quote, "full_code") or "").lower()
    if tdx_code:
        return tdx_code
    exchange = str(get_value(quote, "exchange") or "").lower()
    symbol = str(get_value(quote, "code") or "")
    return f"{exchange}{symbol}" if exchange and symbol else ""


def quote_level_at(levels: Sequence[Any], index: int) -> Any | None:
    try:
        return levels[index]
    except IndexError:
        return None


def normalize_realtime_snapshot_row(quote: Any, *, client: Any = None) -> dict[str, Any]:
    tdx_code = quote_tdx_code(quote)
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    symbol = instrument_id.split(".", 1)[0]
    exchange = MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(quote, "exchange") or "").upper())
    # The wire layer decoded these prices as raw/100, which is only correct for
    # decimal==2 securities. Rescale by 10**(2-decimal) so ETFs (decimal=3) and
    # any other precision are corrected; for decimal==2 the factor is 1 (no-op).
    # Percentage fields below are scale-invariant, so only absolute prices need it.
    decimal = price_decimal(client, tdx_code) if client is not None else DEFAULT_PRICE_DECIMAL
    open_price = rescale_price(get_value(quote, "open"), decimal)
    pre_close = rescale_price(get_value(quote, "pre_close"), decimal)
    bid_levels = list(get_value(quote, "bid_levels", ()) or ())
    ask_levels = list(get_value(quote, "ask_levels", ()) or ())
    bid1_level = quote_level_at(bid_levels, 0)
    ask1_level = quote_level_at(ask_levels, 0)
    bid1_price = rescale_price(get_value(quote, "bid1_price", get_value(bid1_level, "price")), decimal)
    bid1_volume = get_value(quote, "bid1_volume", get_value(bid1_level, "volume"))
    ask1_price = rescale_price(get_value(quote, "ask1_price", get_value(ask1_level, "price")), decimal)
    ask1_volume = get_value(quote, "ask1_volume", get_value(ask1_level, "volume"))
    amount = get_value(quote, "amount")
    open_amount = get_value(quote, "open_amount")
    volume = get_value(quote, "total_hand")
    high_price = rescale_price(get_value(quote, "high"), decimal)
    low_price = rescale_price(get_value(quote, "low"), decimal)
    last_price = rescale_price(get_value(quote, "last_price"), decimal)
    activity = get_value(quote, "activity", get_value(quote, "active"))
    average = average_price(amount, volume)
    locked = locked_amount(bid1_price, bid1_volume)
    change = (last_price - pre_close) if (last_price is not None and pre_close is not None) else None
    return {
        "instrument_id": instrument_id,
        "symbol": symbol,
        "tdx_code": tdx_code,
        "exchange": exchange,
        "last_price": round_optional_float(last_price),
        "pre_close": round_optional_float(pre_close),
        "open": round_optional_float(open_price),
        "high": round_optional_float(high_price),
        "low": round_optional_float(low_price),
        "change": round_optional_float(change),
        "change_pct": round_optional_float(get_value(quote, "change_pct")),
        "open_change_pct": percent_change(open_price, pre_close),
        "high_change_pct": percent_change(high_price, pre_close),
        "low_change_pct": percent_change(low_price, pre_close),
        "amplitude_pct": round_optional_float(get_value(quote, "amplitude_pct")),
        "average_price": average,
        "average_change_pct": percent_change(average, pre_close),
        "drawdown_pct": drawdown_pct(high_price, last_price, pre_close),
        "attack_pct": attack_pct(last_price, low_price, pre_close),
        "volume": optional_int(get_value(quote, "total_hand")),
        "current_volume": optional_int(get_value(quote, "current_hand")),
        "amount": round_optional_float(get_value(quote, "amount")),
        "inside_volume": optional_int(get_value(quote, "inside_dish")),
        "outside_volume": optional_int(get_value(quote, "outer_disc")),
        "inside_outside_ratio": safe_ratio(get_value(quote, "inside_dish"), get_value(quote, "outer_disc")),
        "open_amount": round_optional_float(open_amount),
        "open_amount_ratio_pct": safe_ratio_pct(open_amount, amount),
        "bid1_price": round_optional_float(bid1_price),
        "bid1_volume": optional_int(bid1_volume),
        "ask1_price": round_optional_float(ask1_price),
        "ask1_volume": optional_int(ask1_volume),
        "locked_amount": locked,
        "bid1_ask1_volume_diff": optional_int_diff(bid1_volume, ask1_volume),
        "bid1_ask1_balance_pct": balance_pct(bid1_volume, ask1_volume),
        "rise_speed": round_optional_float(get_value(quote, "rise_speed")),
        "short_turnover": round_optional_float(get_value(quote, "short_turnover")),
        "min2_amount": round_optional_float(get_value(quote, "min2_amount")),
        "opening_rush": round_optional_float(get_value(quote, "opening_rush")),
        "vol_rise_speed": round_optional_float(get_value(quote, "vol_rise_speed")),
        "entrust_ratio": round_optional_float(get_value(quote, "entrust_ratio")),
        "activity": optional_int(activity),
    }


def normalize_index_snapshot_row(quote: Any, *, client: Any = None) -> dict[str, Any]:
    row = normalize_realtime_snapshot_row(quote, client=client)
    return {field: row.get(field) for field in INDEX_SNAPSHOT_FIELDS}


def rescale_price(value: Any, decimal: int) -> float | None:
    """Rescale a price the wire layer decoded as ``raw / 100`` to true decimal.

    Snapshot quotes keep no raw integer, only the value already divided by 100.
    Multiplying by ``10 ** (2 - decimal)`` corrects it: a no-op for decimal==2
    and a ``/ 10`` for ETFs (decimal=3). Returns None for missing values.
    """
    if value is None:
        return None
    try:
        return round(float(value) * (10 ** (2 - decimal)), 6)
    except (TypeError, ValueError):
        return None


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
