"""Structured models for TDX extended market responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TdxExtMarket:
    category: int
    market: int
    name: str
    short_name: str


@dataclass(frozen=True, slots=True)
class TdxExtInstrument:
    category: int
    market: int
    code: str
    name: str
    desc: str


@dataclass(frozen=True, slots=True)
class TdxExtQuoteLevel:
    price: float | None
    volume: int | None


@dataclass(frozen=True, slots=True)
class TdxExtQuote:
    market: int
    code: str
    active: int | None
    pre_close: float | None
    open: float | None
    high: float | None
    low: float | None
    last_price: float | None
    active_volume: int | None
    volume: int | None
    current_volume: int | None
    amount: float | None
    inside_volume: int | None
    outside_volume: int | None
    open_interest: int | None
    open_interest_change: int | None
    settlement: float | None
    average_price: float | None
    pre_settlement: float | None
    pre_volume: float | None
    trade_date: str | None
    raise_speed: float | None
    bid_levels: tuple[TdxExtQuoteLevel, ...]
    ask_levels: tuple[TdxExtQuoteLevel, ...]


@dataclass(frozen=True, slots=True)
class TdxExtKlineBar:
    market: int
    code: str
    trade_time: str
    period: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    amount: float | None
    volume: int | None
    open_interest: int | None = None
    settlement: float | None = None


@dataclass(frozen=True, slots=True)
class TdxExtIntradayPoint:
    market: int
    code: str
    trade_date: str | None
    time_label: str
    price: float | None
    average_price: float | None
    volume: int | None


@dataclass(frozen=True, slots=True)
class TdxExtTrade:
    market: int
    code: str
    trade_date: str | None
    time_label: str
    price_raw: int
    price: float | None
    volume: int
    position_change: int
    direction_marker: int
