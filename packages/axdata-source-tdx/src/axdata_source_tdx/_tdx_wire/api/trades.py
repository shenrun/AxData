"""Trade-detail API."""

from __future__ import annotations

from .base import ApiBase


class TradeApi(ApiBase):
    def today(self, code: str, *, start: int = 0, count: int = 115, include_raw: bool = False):
        return self._execute(
            "today_trades",
            code=code,
            start=start,
            count=count,
            include_raw=include_raw,
        )

    def historical(
        self,
        code: str,
        *,
        trade_date,
        start: int = 0,
        count: int = 900,
        include_raw: bool = False,
    ):
        return self._execute(
            "historical_trades",
            code=code,
            trade_date=trade_date,
            start=start,
            count=count,
            include_raw=include_raw,
        )
