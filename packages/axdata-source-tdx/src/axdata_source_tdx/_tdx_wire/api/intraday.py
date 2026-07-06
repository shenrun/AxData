"""Intraday trace API."""

from __future__ import annotations

from .base import ApiBase


class IntradayApi(ApiBase):
    def today(self, code: str, *, include_raw: bool = False):
        return self._execute(
            "today_intraday",
            code=code,
            include_raw=include_raw,
        )

    def subchart(self, code: str, *, selector=0, include_raw: bool = False):
        return self._execute(
            "intraday_subchart",
            code=code,
            selector=selector,
            include_raw=include_raw,
        )

    def historical(self, code: str, *, trade_date, include_raw: bool = False):
        return self._execute(
            "historical_intraday",
            code=code,
            trade_date=trade_date,
            include_raw=include_raw,
        )

    def recent_historical(self, code: str, *, trade_date, include_raw: bool = False):
        return self._execute(
            "recent_historical_intraday",
            code=code,
            trade_date=trade_date,
            include_raw=include_raw,
        )
