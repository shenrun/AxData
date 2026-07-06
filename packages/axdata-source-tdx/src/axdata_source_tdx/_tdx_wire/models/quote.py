"""Quote snapshot models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuoteLevel:
    price: float
    volume: int


@dataclass(frozen=True, slots=True)
class PriceLimitRecord:
    exchange: str
    market_id: int
    code: str
    code_num: int
    limit_up_price: float
    limit_down_price: float
    record_hex: str = ""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"


@dataclass(frozen=True, slots=True)
class LegacyQuote:
    exchange: str
    market_id: int
    code: str
    active1: int
    close: float
    pre_close: float
    open: float
    high: float
    low: float
    server_time_raw: int
    total_hand: int
    current_hand: int
    amount_raw: int
    inside_dish: int
    outer_disc: int
    bid_vol_sum: int
    ask_vol_sum: int
    trading_status_raw: int
    active2: int | None = None
    bid_levels: tuple[QuoteLevel, ...] = ()
    ask_levels: tuple[QuoteLevel, ...] = ()

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def trading_status_hex(self) -> str:
        return f"0x{self.trading_status_raw:04x}"

    @property
    def suspend_bit_0x20(self) -> bool:
        return bool(self.trading_status_raw & 0x20)


@dataclass(frozen=True, slots=True)
class ExplicitQuote:
    exchange: str
    market_id: int
    code: str
    active1: int
    last_price: float
    pre_close: float
    open: float
    high: float
    low: float
    time_raw: int
    total_hand: int
    current_hand: int
    amount_raw: int
    amount: float
    inside_dish: int
    outer_disc: int
    open_amount_raw: int
    open_amount: float
    bid1_price: float
    bid1_volume: int
    ask1_price: float
    ask1_volume: int
    rise_speed: float | None
    short_turnover: float | None
    min2_amount: float | None
    opening_rush: float | None
    vol_rise_speed: float | None
    entrust_ratio: float | None
    active2: int | None
    unknown_tail_raw: int | None = None

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def activity(self) -> int:
        return self.active2 if self.active2 is not None else self.active1

    @property
    def change(self) -> float | None:
        if self.pre_close == 0:
            return None
        return self.last_price - self.pre_close

    @property
    def change_pct(self) -> float | None:
        if self.pre_close == 0:
            return None
        return (self.last_price - self.pre_close) / self.pre_close * 100.0

    @property
    def amplitude_pct(self) -> float | None:
        if self.pre_close == 0:
            return None
        return (self.high - self.low) / self.pre_close * 100.0


@dataclass(frozen=True, slots=True)
class CategoryQuote:
    exchange: str
    market_id: int
    code: str
    active1: int
    active2: int | None
    last_price: float
    pre_close: float
    open: float
    high: float
    low: float
    time_raw: int
    total_hand: int
    current_hand: int
    amount_raw: int
    amount: float
    inside_dish: int
    outer_disc: int
    open_amount_raw: int
    open_amount: float
    bid1_price: float
    bid1_volume: int
    ask1_price: float
    ask1_volume: int
    rise_speed: float | None
    short_turnover: float | None
    min2_amount: float | None
    opening_rush: float | None
    vol_rise_speed: float | None
    entrust_ratio: float | None
    after_outer_raw: int | None = None
    status_or_sort_raw: int | None = None

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def activity(self) -> int:
        return self.active2 if self.active2 is not None else self.active1

    @property
    def change(self) -> float | None:
        if self.pre_close == 0:
            return None
        return self.last_price - self.pre_close

    @property
    def change_pct(self) -> float | None:
        if self.pre_close == 0:
            return None
        return (self.last_price - self.pre_close) / self.pre_close * 100.0

    @property
    def amplitude_pct(self) -> float | None:
        if self.pre_close == 0:
            return None
        return (self.high - self.low) / self.pre_close * 100.0


@dataclass(frozen=True, slots=True)
class CategoryQuotePage:
    category: int
    sort_type: int
    start: int
    request_count: int
    sort_reverse: int
    filter_raw: int
    header: int
    records: tuple[CategoryQuote, ...]

    @property
    def count(self) -> int:
        return len(self.records)


@dataclass(frozen=True, slots=True)
class QuoteRefreshCursor:
    exchange: str
    market_id: int
    code: str
    last_update_time_raw: int = 0

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"


@dataclass(frozen=True, slots=True)
class QuoteRefreshRecord:
    exchange: str
    market_id: int
    code: str
    active: int
    last_price: float
    pre_close: float
    open: float
    high: float
    low: float
    update_time_raw: int
    status_or_reserved_raw: int
    total_hand: int
    current_hand: int
    amount_raw: int
    amount: float
    inside_dish: int
    outer_disc: int
    open_amount_raw: int
    open_amount: float
    bid_levels: tuple[QuoteLevel, ...] = ()
    ask_levels: tuple[QuoteLevel, ...] = ()

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def change(self) -> float | None:
        if self.pre_close == 0:
            return None
        return self.last_price - self.pre_close

    @property
    def change_pct(self) -> float | None:
        if self.pre_close == 0:
            return None
        return (self.last_price - self.pre_close) / self.pre_close * 100.0


@dataclass(frozen=True, slots=True)
class QuoteRefreshBatch:
    records: tuple[QuoteRefreshRecord, ...]

    @property
    def count(self) -> int:
        return len(self.records)
