"""TDX adjustment-factor helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AdjustmentFactor:
    trade_date: date
    last_close_price_milli: int | None
    pre_last_close_price_milli: int | None
    qfq_factor: float
    hfq_factor: float


def build_adjustment_factors(
    day_kline: Any,
    capital_changes: Any,
    *,
    adjust: str,
    anchor_date: Any = None,
) -> tuple[AdjustmentFactor, ...]:
    """Build qfq/hfq factors from unadjusted daily bars and XDXR events."""

    bars = sorted(_bars(day_kline), key=lambda item: item.time)
    xdxr_records = sorted(
        (record for record in _records(capital_changes) if _record_date(record) is not None and _category(record) == 1),
        key=lambda item: _record_date(item) or date.min,
    )
    overrides: dict[date, int | None] = {}

    for record in xdxr_records:
        event_date = _record_date(record)
        if event_date is None:
            continue
        for bar in bars:
            bar_date = bar.time.date()
            if bar_date >= event_date:
                overrides[bar_date] = apply_xdxr_to_last_close(
                    getattr(bar, "last_close_price_milli", None),
                    record,
                )
                break

    factors: list[AdjustmentFactor] = []
    hfq_cumulative = 1.0
    for bar in bars:
        bar_date = bar.time.date()
        last_close = getattr(bar, "last_close_price_milli", None)
        pre_last_close = overrides.get(bar_date, last_close)
        hfq_cumulative *= _hfq_step(last_close, pre_last_close)
        factors.append(
            AdjustmentFactor(
                trade_date=bar_date,
                last_close_price_milli=last_close,
                pre_last_close_price_milli=pre_last_close,
                qfq_factor=1.0,
                hfq_factor=hfq_cumulative,
            )
        )

    if factors:
        qfq_cumulative = 1.0
        for index in range(len(factors) - 1, 0, -1):
            current = factors[index]
            qfq_cumulative *= _qfq_step(
                current.last_close_price_milli,
                current.pre_last_close_price_milli,
            )
            factors[index - 1] = replace(factors[index - 1], qfq_factor=qfq_cumulative)

    key = str(adjust or "qfq").strip().lower()
    if key == "qfq" and anchor_date not in (None, ""):
        factors = _normalize_qfq_anchor(factors, _normalize_date(anchor_date))
    return tuple(factors)


def apply_xdxr_to_last_close(last_close_milli: int | None, xdxr: Any) -> int | None:
    if last_close_milli in (None, 0):
        return last_close_milli

    fenhong = float(getattr(xdxr, "c1_float", getattr(xdxr, "fenhong", 0.0)) or 0.0)
    peigujia = float(getattr(xdxr, "c2_float", getattr(xdxr, "peigujia", 0.0)) or 0.0)
    songzhuangu = float(getattr(xdxr, "c3_float", getattr(xdxr, "songzhuangu", 0.0)) or 0.0)
    peigu = float(getattr(xdxr, "c4_float", getattr(xdxr, "peigu", 0.0)) or 0.0)
    numerator = ((last_close_milli / 1000.0) * 10.0 - fenhong) + (peigu * peigujia)
    denominator = 10.0 + songzhuangu + peigu
    if denominator == 0:
        return last_close_milli
    return int((numerator / denominator) * 1000.0)


def selected_factor_value(item: AdjustmentFactor, adjust: str) -> float:
    key = str(adjust or "qfq").strip().lower()
    if key == "hfq":
        return item.hfq_factor
    return item.qfq_factor


def _normalize_qfq_anchor(factors: list[AdjustmentFactor], anchor_date: date) -> list[AdjustmentFactor]:
    anchor = None
    for item in factors:
        if item.trade_date <= anchor_date:
            anchor = item
        else:
            break
    if anchor is None:
        raise ValueError("anchor_date is earlier than the first available trade_date")
    if anchor.qfq_factor == 0:
        raise ValueError("anchor_date qfq factor is zero")
    return [replace(item, qfq_factor=item.qfq_factor / anchor.qfq_factor) for item in factors]


def _qfq_step(last_close_milli: int | None, pre_last_close_milli: int | None) -> float:
    if last_close_milli in (None, 0) or pre_last_close_milli in (None, 0) or last_close_milli == pre_last_close_milli:
        return 1.0
    return pre_last_close_milli / last_close_milli


def _hfq_step(last_close_milli: int | None, pre_last_close_milli: int | None) -> float:
    if last_close_milli in (None, 0) or pre_last_close_milli in (None, 0) or last_close_milli == pre_last_close_milli:
        return 1.0
    return last_close_milli / pre_last_close_milli


def _normalize_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError("anchor_date must be YYYYMMDD or YYYY-MM-DD")
    try:
        return date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as exc:
        raise ValueError("anchor_date must be a valid date") from exc


def _bars(day_kline: Any) -> list[Any]:
    bars = getattr(day_kline, "bars", ())
    if bars is None:
        return []
    return list(bars)


def _records(capital_changes: Any) -> list[Any]:
    records = getattr(capital_changes, "records", getattr(capital_changes, "items", ()))
    if records is None:
        return []
    return list(records)


def _record_date(record: Any) -> date | None:
    return getattr(record, "date", None)


def _category(record: Any) -> int:
    return int(getattr(record, "category_raw", getattr(record, "category", 0)) or 0)

