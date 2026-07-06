"""Call-auction process models for the private TDX 7709 wire client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True, slots=True)
class AuctionProcessRecord:
    index: int
    auction_time: time
    minute_of_day_raw: int
    second_raw: int
    price: float
    price_milli: int
    matched_volume: int
    unmatched_signed_raw: int
    unmatched_volume: int
    unmatched_direction: int
    reserved_zero_0e: int
    record_hex: str = ""

    @property
    def time_seconds(self) -> int:
        return self.minute_of_day_raw * 60 + self.second_raw

    @property
    def matched_amount_estimated(self) -> float:
        return self.price * self.matched_volume * 100.0

    @property
    def unmatched_amount_estimated(self) -> float:
        return self.price * self.unmatched_volume * 100.0

    @property
    def unmatched_direction_raw(self) -> int:
        return self.unmatched_direction


@dataclass(frozen=True, slots=True)
class AuctionProcessSeries:
    exchange: str
    market_id: int
    code: str
    mode_or_selector_raw: int
    start: int
    request_count: int
    records: tuple[AuctionProcessRecord, ...]
    raw_payload: bytes = b""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def count(self) -> int:
        return len(self.records)
