"""Row normalization helpers for TDX extended market requests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .local_cache import TdxExtLocalInstrument


def instrument_to_row(item: TdxExtLocalInstrument, interface_name: str) -> dict[str, Any]:
    base = {
        "instrument_id": item.instrument_id,
        "symbol": item.symbol,
        "asset_type": item.asset_type,
        "exchange": item.exchange,
        "market_name": item.market_name,
        "market_group": item.market_group,
    }
    if interface_name == "futures_contracts_tdx":
        return {
            **base,
            "product_code": item.product_code,
            "product_name": item.product_name,
            "contract_month": item.contract_month,
            "contract_type": item.contract_type,
        }
    if interface_name == "option_contracts_tdx":
        return {
            **base,
            "product_code": item.product_code,
            "product_name": item.product_name,
            "contract_month": item.contract_month,
            "option_type": item.option_type,
            "strike_price": item.strike_price,
        }
    if interface_name == "fund_codes_tdx":
        return {
            **base,
            "fund_type": item.fund_type,
            "update_date": item.update_date,
            "nav": item.nav,
            "accumulated_nav": item.accumulated_nav,
        }
    if interface_name == "bond_codes_tdx":
        return {
            **base,
            "bond_type": item.bond_type,
        }
    if interface_name == "fx_codes_tdx":
        return {
            **base,
            "base_currency": item.base_currency,
            "quote_currency": item.quote_currency,
        }
    if interface_name == "macro_indicators_tdx":
        metadata = macro_metadata(item.symbol)
        return {
            **base,
            "indicator_category": item.indicator_category,
            "unit": metadata.get("unit"),
            "frequency": metadata.get("frequency"),
        }
    return {
        **base,
        "product_code": item.product_code,
        "product_name": item.product_name,
        "contract_month": item.contract_month,
        "contract_type": item.contract_type,
        "option_type": item.option_type,
        "strike_price": item.strike_price,
        "fund_type": item.fund_type,
        "bond_type": item.bond_type,
        "base_currency": item.base_currency,
        "quote_currency": item.quote_currency,
        "indicator_category": item.indicator_category,
    }


def quote_to_row(quote: Any, item: TdxExtLocalInstrument) -> dict[str, Any]:
    row = {
        "instrument_id": item.instrument_id,
        "symbol": item.symbol,
        "exchange": item.exchange,
        "name": item.product_name,
        "trade_date": quote.trade_date,
        "last_price": quote.last_price,
        "pre_close": quote.pre_close,
        "pre_settlement": quote.pre_settlement,
        "open": quote.open,
        "high": quote.high,
        "low": quote.low,
        "settlement": quote.settlement,
        "average_price": quote.average_price,
        "volume": quote.volume,
        "amount": quote.amount,
        "open_interest": quote.open_interest,
        "open_interest_change": quote.open_interest_change,
        "inside_volume": quote.inside_volume,
        "outside_volume": quote.outside_volume,
    }
    for level in range(1, 6):
        bid = quote.bid_levels[level - 1] if len(quote.bid_levels) >= level else None
        ask = quote.ask_levels[level - 1] if len(quote.ask_levels) >= level else None
        row[f"bid{level}_price"] = bid.price if bid else None
        row[f"bid{level}_volume"] = bid.volume if bid else None
        row[f"ask{level}_price"] = ask.price if ask else None
        row[f"ask{level}_volume"] = ask.volume if ask else None
    return row


def quote_snapshot_rows(
    instruments: Sequence[TdxExtLocalInstrument],
    quotes: Sequence[Any],
    *,
    macro_snapshot: bool = False,
    find_instrument: Callable[[str], TdxExtLocalInstrument | None],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    item_by_key = {(item.market_id, item.symbol): item for item in instruments}
    for quote in quotes:
        item = item_by_key.get((quote.market, quote.code)) or find_instrument(quote.code)
        if item is None:
            continue
        row = quote_to_row(quote, item)
        if macro_snapshot:
            row = macro_snapshot_row(row)
        rows.append(row)
    return rows


def empty_option_chain_row(item: TdxExtLocalInstrument) -> dict[str, Any]:
    row: dict[str, Any] = {
        "product_code": item.product_code,
        "product_name": item.product_name,
        "exchange": item.exchange,
        "contract_month": item.contract_month,
        "strike_price": item.strike_price,
    }
    for side in ("call", "put"):
        row[f"{side}_instrument_id"] = None
        row[f"{side}_symbol"] = None
        row[f"{side}_last_price"] = None
        for level in range(1, 6):
            row[f"{side}_bid{level}_price"] = None
            row[f"{side}_bid{level}_volume"] = None
            row[f"{side}_ask{level}_price"] = None
            row[f"{side}_ask{level}_volume"] = None
        row[f"{side}_volume"] = None
        row[f"{side}_open_interest"] = None
    return row


def option_chain_rows(
    contracts: Sequence[TdxExtLocalInstrument],
    quotes: Sequence[Any],
) -> list[dict[str, Any]]:
    item_by_key = {(item.market_id, item.symbol): item for item in contracts}
    quote_rows: dict[str, dict[str, Any]] = {}
    for quote in quotes:
        item = item_by_key.get((quote.market, quote.code))
        if item is None:
            continue
        quote_rows[item.instrument_id] = quote_to_row(quote, item)

    grouped: dict[tuple[str | None, str | None, float | None], dict[str, Any]] = {}
    for item in contracts:
        key = (item.product_code, item.contract_month, item.strike_price)
        row = grouped.setdefault(
            key,
            empty_option_chain_row(item),
        )
        side = item.option_type
        if side not in {"call", "put"}:
            continue
        quote_row = quote_rows.get(item.instrument_id, {})
        row[f"{side}_instrument_id"] = item.instrument_id
        row[f"{side}_symbol"] = item.symbol
        row[f"{side}_last_price"] = quote_row.get("last_price")
        for level in range(1, 6):
            row[f"{side}_bid{level}_price"] = quote_row.get(f"bid{level}_price")
            row[f"{side}_bid{level}_volume"] = quote_row.get(f"bid{level}_volume")
            row[f"{side}_ask{level}_price"] = quote_row.get(f"ask{level}_price")
            row[f"{side}_ask{level}_volume"] = quote_row.get(f"ask{level}_volume")
        row[f"{side}_volume"] = quote_row.get("volume")
        row[f"{side}_open_interest"] = quote_row.get("open_interest")

    rows = list(grouped.values())
    rows.sort(
        key=lambda row: (
            str(row.get("product_code") or ""),
            str(row.get("contract_month") or ""),
            float(row.get("strike_price") or 0),
        )
    )
    return rows


def macro_snapshot_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata = macro_metadata(row["symbol"])
    return {
        "indicator_id": row["instrument_id"],
        "symbol": row["symbol"],
        "name": row["name"],
        "indicator_category": macro_indicator_category_from_symbol(row["symbol"]),
        "value": row["last_price"],
        "period_date": row["trade_date"],
        "pre_value": row["pre_close"],
        "unit": metadata.get("unit"),
        "frequency": metadata.get("frequency"),
    }


def bar_to_row(bar: Any, item: TdxExtLocalInstrument, *, period_name: str) -> dict[str, Any]:
    return {
        "instrument_id": item.instrument_id,
        "symbol": item.symbol,
        "exchange": item.exchange,
        "name": item.product_name,
        "trade_time": bar.trade_time,
        "period": period_name,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
        "open_interest": bar.open_interest,
        "settlement": bar.settlement,
    }


def macro_bar_to_row(bar: Any, item: TdxExtLocalInstrument, *, period_name: str) -> dict[str, Any]:
    metadata = macro_metadata(item.symbol)
    return {
        "indicator_id": item.instrument_id,
        "symbol": item.symbol,
        "name": item.product_name,
        "period_date": bar.trade_time,
        "period": period_name,
        "value": bar.close,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "unit": metadata.get("unit"),
        "frequency": metadata.get("frequency"),
    }


def intraday_to_row(point: Any, item: TdxExtLocalInstrument) -> dict[str, Any]:
    return {
        "instrument_id": item.instrument_id,
        "symbol": item.symbol,
        "exchange": item.exchange,
        "name": item.product_name,
        "trade_date": point.trade_date,
        "time_label": point.time_label,
        "price": point.price,
        "average_price": point.average_price,
        "volume": point.volume,
    }


def trade_to_row(trade: Any, item: TdxExtLocalInstrument) -> dict[str, Any]:
    price = normalize_trade_price(trade.price, item)
    return {
        "instrument_id": item.instrument_id,
        "symbol": item.symbol,
        "exchange": item.exchange,
        "name": item.product_name,
        "trade_date": trade.trade_date,
        "time_label": trade.time_label,
        "price": price,
        "volume": trade.volume,
        "position_change": trade.position_change,
        "open_close_type": open_close_type(
            volume=trade.volume,
            position_change=trade.position_change,
            direction_marker=trade.direction_marker,
        ),
    }


def trade_price_scale(item: TdxExtLocalInstrument) -> int:
    if item.asset_type == "fx":
        return 10000
    return 1000


def normalize_trade_price(price: float | None, item: TdxExtLocalInstrument) -> float | None:
    if price is None:
        return None
    if item.asset_type == "fx":
        return round(float(price), 6)
    tick = price_tick(item) if item.asset_type == "futures" else None
    if tick and tick >= 1:
        return round(round(float(price) / tick) * tick, 6)
    if tick and tick > 0:
        decimals = max(0, min(6, tick_decimals(tick)))
        return round(round(float(price) / tick) * tick, decimals)
    return round(float(price), 6)


def price_tick(item: TdxExtLocalInstrument) -> float | None:
    if item.asset_type not in {"futures", "option"}:
        return None
    return item.price_tick


def tick_decimals(tick: float) -> int:
    text = f"{tick:.8f}".rstrip("0").rstrip(".")
    return len(text.split(".", 1)[1]) if "." in text else 0


def open_close_type(
    *,
    volume: int,
    position_change: int,
    direction_marker: int,
) -> str | None:
    if volume <= 0:
        return None
    if direction_marker == 0:
        if position_change > 0:
            return "多开" if volume > position_change else "双开"
        if position_change == 0:
            return "多换"
        return "双平" if volume == -position_change else "空平"
    if direction_marker == 1:
        if position_change > 0:
            return "空开" if volume > position_change else "双开"
        if position_change == 0:
            return "空换"
        return "双平" if volume == -position_change else "多平"
    if position_change > 0:
        return "开仓" if volume > position_change else "双开"
    if position_change < 0:
        return "平仓" if volume > -position_change else "双平"
    return "换手"


def macro_indicator_category_from_symbol(symbol: Any) -> str | None:
    text = str(symbol or "")
    if "_" not in text:
        return None
    category = text.split("_", 1)[0]
    return category or None


def macro_metadata(symbol: Any) -> dict[str, str | None]:
    key = str(symbol or "").strip().upper()
    metadata = {
        "1_GDP": {"unit": "亿元", "frequency": "年"},
        "2_CPI": {"unit": "元", "frequency": "月"},
    }
    return metadata.get(key, {"unit": None, "frequency": None})
