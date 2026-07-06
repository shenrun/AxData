"""Calendar helpers for TDX daily price-limit requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class PriceLimitCalendarDates:
    target_trade_date: str
    pre_close_trade_date: str | None
    source: str
    snapshot_base_field: str = "pre_close"


def latest_daily_price_limit_calendar_dates(
    *,
    today: date | None = None,
    now: datetime | None = None,
    request_interface: Callable[..., Any],
    default_trade_date: Callable[[str], str | None],
    before_daily_close_buffer: Callable[[datetime], bool],
) -> PriceLimitCalendarDates:
    now_value = now or datetime.now()
    today_value = today or now_value.date()
    today_text = today_value.strftime("%Y%m%d")
    start_date = (today_value - timedelta(days=7)).strftime("%Y%m%d")
    end_date = (today_value + timedelta(days=14)).strftime("%Y%m%d")
    try:
        result = request_interface(
            "stock_trade_calendar_exchange",
            params={"start_date": start_date, "end_date": end_date},
            fields=["cal_date", "is_open", "pretrade_date", "next_trade_date"],
            persist=False,
        )
        rows = result.records
    except Exception:
        target_trade_date = default_trade_date(today_text) or today_text
        return PriceLimitCalendarDates(
            target_trade_date=target_trade_date,
            pre_close_trade_date=None,
            source="local_date_fallback",
            snapshot_base_field="pre_close",
        )

    by_date = _calendar_rows_by_date(rows)
    today_row = by_date.get(today_text)
    if today_row is None:
        return PriceLimitCalendarDates(
            target_trade_date=today_text,
            pre_close_trade_date=None,
            source="exchange_calendar_missing_today_fallback",
            snapshot_base_field="pre_close",
        )

    if bool(today_row.get("is_open")):
        target_trade_date = today_text
        pre_close_trade_date = str(today_row.get("pretrade_date") or "") or None
        snapshot_base_field = "pre_close" if before_daily_close_buffer(now_value) else "last_price"
    else:
        target_trade_date = str(today_row.get("next_trade_date") or "") or today_text
        target_row = by_date.get(target_trade_date)
        pre_close_trade_date = (
            str(target_row.get("pretrade_date") or "") or None if target_row is not None else None
        )
        if pre_close_trade_date is None:
            pre_close_trade_date = str(today_row.get("pretrade_date") or "") or None
        snapshot_base_field = "last_price"

    return PriceLimitCalendarDates(
        target_trade_date=target_trade_date,
        pre_close_trade_date=pre_close_trade_date,
        source="exchange_calendar",
        snapshot_base_field=snapshot_base_field,
    )


def latest_calendar_dates_from_source_request(
    *,
    today: date | None = None,
    request_interface: Callable[..., Any] | None = None,
    default_trade_date: Callable[[str], str | None],
    before_daily_close_buffer: Callable[[datetime], bool],
) -> PriceLimitCalendarDates:
    if request_interface is None:
        from axdata_core.source_request import request_interface as current_request_interface
    else:
        current_request_interface = request_interface

    return latest_daily_price_limit_calendar_dates(
        today=today,
        request_interface=current_request_interface,
        default_trade_date=default_trade_date,
        before_daily_close_buffer=before_daily_close_buffer,
    )


def _calendar_rows_by_date(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row.get("cal_date") or ""): row
        for row in rows
        if row.get("cal_date") not in (None, "")
    }
