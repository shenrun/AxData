"""Base contracts for market data collection adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

Row = dict[str, Any]
FetchParams = Mapping[str, Any]

STOCK_BASIC = "stock_basic_exchange"
TRADE_CAL = "trade_cal"
DAILY = "daily"
ADJ_FACTOR = "adj_factor"

SUPPORTED_DATASETS = frozenset(
    {
        STOCK_BASIC,
        TRADE_CAL,
        DAILY,
        ADJ_FACTOR,
    }
)

DATASET_ALIASES = {
    "stock-basic": STOCK_BASIC,
    "stock_basic": STOCK_BASIC,
    "stock-basic-exchange": STOCK_BASIC,
    "stock_basic_exchange": STOCK_BASIC,
    "trade-cal": TRADE_CAL,
    "trade_cal": TRADE_CAL,
    "daily": DAILY,
    "adj-factor": ADJ_FACTOR,
    "adj_factor": ADJ_FACTOR,
}


def normalize_dataset(dataset: str) -> str:
    """Return the canonical dataset name used by collector and worker jobs."""
    normalized = DATASET_ALIASES.get(dataset.strip().lower())
    if normalized is None:
        allowed = ", ".join(sorted(SUPPORTED_DATASETS))
        raise ValueError(f"Unsupported dataset '{dataset}'. Expected one of: {allowed}")
    return normalized


class CollectorAdapter(ABC):
    """Base class for collector adapters.

    Adapters should implement :meth:`fetch` and return a list of row dictionaries.
    Helper methods provide the stable dataset-specific API expected by workers.
    """

    source = "base"

    @abstractmethod
    def fetch(self, dataset: str, params: FetchParams | None = None) -> list[Row]:
        """Fetch rows for a canonical dataset name."""

    def fetch_stock_basic(self, **params: Any) -> list[Row]:
        return self.fetch(STOCK_BASIC, params)

    def fetch_stock_basic_exchange(self, **params: Any) -> list[Row]:
        return self.fetch(STOCK_BASIC, params)

    def fetch_trade_cal(self, **params: Any) -> list[Row]:
        return self.fetch(TRADE_CAL, params)

    def fetch_daily(self, **params: Any) -> list[Row]:
        return self.fetch(DAILY, params)

    def fetch_adj_factor(self, **params: Any) -> list[Row]:
        return self.fetch(ADJ_FACTOR, params)
