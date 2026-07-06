"""Intraday subchart models for the private TDX 7709 wire client."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntradaySubchartPoint:
    index: int
    bid_order: int | None = None
    ask_order: int | None = None
    previous_day_cumulative_volume: float | None = None
    current_day_cumulative_volume: float | None = None
    cumulative_volume: float | None = None
    series_a_varint: int | None = None
    series_b_varint: int | None = None
    series_a_f32: float | None = None
    series_b_f32: float | None = None
    record_hex: str = ""


@dataclass(frozen=True, slots=True)
class IntradaySubchartSeries:
    exchange: str
    market_id: int
    code: str
    selector_raw: int
    selector_name: str
    points: tuple[IntradaySubchartPoint, ...]
    raw_payload: bytes = b""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def count(self) -> int:
        return len(self.points)
