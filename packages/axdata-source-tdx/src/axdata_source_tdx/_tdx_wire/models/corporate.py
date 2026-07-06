"""Corporate action models for the private TDX 7709 wire client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class CapitalChangeRecord:
    exchange: str
    market_id: int
    code: str
    reserved_7: int
    date_raw: int
    date: date | None
    category_raw: int
    category_name: str | None
    c1_raw: bytes
    c2_raw: bytes
    c3_raw: bytes
    c4_raw: bytes
    c1_float: float
    c2_float: float
    c3_float: float
    c4_float: float
    c1_quantity: float
    c2_quantity: float
    c3_quantity: float
    c4_quantity: float
    record_hex: str = ""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def time(self) -> datetime | None:
        if self.date is None:
            return None
        return datetime(self.date.year, self.date.month, self.date.day, 15, 0)


@dataclass(frozen=True, slots=True)
class CapitalChangeBlock:
    exchange: str
    market_id: int
    code: str
    block_count: int
    records: tuple[CapitalChangeRecord, ...]
    raw_payload: bytes = b""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def count(self) -> int:
        return len(self.records)
