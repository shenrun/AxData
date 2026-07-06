"""Finance summary models for the private TDX 7709 wire client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class FinanceInfoRecord:
    exchange: str
    market_id: int
    code: str
    exchange_raw: int
    updated_date_raw: int
    updated_date: date | None
    ipo_date_raw: int
    ipo_date: date | None
    province_raw: int
    industry_raw: int
    float_share: float
    total_share: float
    state_share: float
    founder_legal_person_share: float
    legal_person_share: float
    b_share: float
    h_share: float
    eps: float
    total_assets: float
    current_assets: float
    fixed_assets: float
    intangible_assets: float
    shareholder_count: int
    current_liabilities: float
    long_term_liabilities: float
    capital_reserve: float
    net_assets: float
    revenue: float
    main_business_profit: float
    accounts_receivable: float
    operating_profit: float
    investment_income: float
    operating_cashflow: float
    total_cashflow: float
    inventory: float
    total_profit: float
    after_tax_profit: float
    net_profit: float
    undistributed_profit: float
    bps: float
    reserved_2: float
    finance_info_hex: str = ""
    record_hex: str = ""

    @property
    def full_code(self) -> str:
        return f"{self.exchange}{self.code}"

    @property
    def is_empty(self) -> bool:
        return (
            self.updated_date_raw == 0
            and self.ipo_date_raw == 0
            and self.float_share == 0
            and self.total_share == 0
            and self.total_assets == 0
            and self.net_profit == 0
            and self.eps == 0
            and self.bps == 0
        )


@dataclass(frozen=True, slots=True)
class FinanceInfoBlock:
    records: tuple[FinanceInfoRecord, ...]
    raw_payload: bytes = b""

    @property
    def count(self) -> int:
        return len(self.records)
