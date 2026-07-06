"""Per-instrument series request helpers for TDX extended markets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .request_normalize import (
    bar_to_row,
    intraday_to_row,
    macro_bar_to_row,
    trade_price_scale,
    trade_to_row,
)

if TYPE_CHECKING:
    from .local_cache import TdxExtLocalInstrument


def request_trade_rows_for_item(
    client: Any,
    item: TdxExtLocalInstrument,
    *,
    is_history: bool,
    trade_date: str | None,
    all_rows: bool,
    limit: int,
    page_size: int,
    flatten_results: Any,
) -> list[dict[str, Any]]:
    start = 0
    remaining = limit
    item_pages: list[list[dict[str, Any]]] = []
    while remaining > 0:
        request_count = page_size if all_rows else min(page_size, remaining)
        if is_history:
            trades = client.get_history_transaction(
                item.market_id,
                item.symbol,
                trade_date,
                start=start,
                count=request_count,
                price_scale=trade_price_scale(item),
            )
        else:
            trades = client.get_today_transaction(
                item.market_id,
                item.symbol,
                start=start,
                count=request_count,
                price_scale=trade_price_scale(item),
            )
        if not trades:
            break
        page_rows: list[dict[str, Any]] = []
        for trade in trades[:remaining]:
            page_rows.append(trade_to_row(trade, item))
        item_pages.append(page_rows)
        if len(trades) < request_count:
            break
        start += len(trades)
        remaining -= len(trades)
    if all_rows:
        item_pages.reverse()
    return flatten_results(item_pages)


def request_kline_rows_for_item(
    client: Any,
    item: TdxExtLocalInstrument,
    *,
    interface_name: str,
    period_raw: int,
    period_name: str,
    count: int,
) -> list[dict[str, Any]]:
    bars = client.get_kline2(item.market_id, item.symbol, period_raw, count=count)
    rows: list[dict[str, Any]] = []
    for bar in bars:
        if interface_name == "macro_indicator_series_tdx":
            rows.append(macro_bar_to_row(bar, item, period_name=period_name))
        else:
            rows.append(bar_to_row(bar, item, period_name=period_name))
    return rows


def request_intraday_rows_for_item(
    client: Any,
    item: TdxExtLocalInstrument,
    *,
    is_history: bool,
    trade_date: str | None,
) -> list[dict[str, Any]]:
    points = (
        client.get_history_tick_chart(item.market_id, item.symbol, trade_date)
        if is_history and trade_date is not None
        else client.get_tick_chart(item.market_id, item.symbol)
    )
    return [intraday_to_row(point, item) for point in points]
