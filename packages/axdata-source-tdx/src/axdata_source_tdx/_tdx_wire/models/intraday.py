"""Historical intraday models for the private TDX 7709 wire client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class TodayIntradayPoint:
    time_label: str
    minute_index: int
    price: float
    avg_price: float
    price_raw: int
    avg_raw: int
    price_field: int
    avg_field: int
    volume: int
    record_hex: str = ""


@dataclass(frozen=True, slots=True)
class TodayIntradaySeries:
    exchange: str
    market_id: int
    code: str
    reserved_tail_raw: bytes
    reserved_zero: int
    points: tuple[TodayIntradayPoint, ...]
    raw_payload: bytes = b""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def reserved_tail_hex(self) -> str:
        return self.reserved_tail_raw.hex()

    @property
    def count(self) -> int:
        return len(self.points)


@dataclass(frozen=True, slots=True)
class HistoricalIntradayPoint:
    time: datetime
    trade_date: date
    minute_index: int
    price: float
    price_acc_raw: int
    price_delta_raw: int
    aux_delta_raw: int
    volume: int
    record_hex: str = ""


@dataclass(frozen=True, slots=True)
class HistoricalIntradaySeries:
    exchange: str
    market_id: int
    code: str
    trade_date: date
    prev_close: float
    points: tuple[HistoricalIntradayPoint, ...]
    raw_payload: bytes = b""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def count(self) -> int:
        return len(self.points)


@dataclass(frozen=True, slots=True)
class RecentHistoricalIntradayPoint:
    time: datetime
    trade_date: date
    time_label: str
    minute_index: int
    price: float
    avg_price: float
    price_raw: int
    avg_raw: int
    price_field: int
    avg_field: int
    volume: int
    record_hex: str = ""


@dataclass(frozen=True, slots=True)
class RecentHistoricalIntradaySeries:
    exchange: str
    market_id: int
    code: str
    trade_date: date
    date_selector_raw: int
    prev_close: float
    open_price: float
    points: tuple[RecentHistoricalIntradayPoint, ...]
    raw_payload: bytes = b""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def count(self) -> int:
        return len(self.points)
