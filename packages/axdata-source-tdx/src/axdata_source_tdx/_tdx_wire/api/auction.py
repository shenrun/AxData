"""Call-auction process API."""

from __future__ import annotations

from .base import ApiBase


class AuctionApi(ApiBase):
    def process(
        self,
        code: str,
        *,
        mode_or_selector_raw: int = 3,
        start: int = 0,
        count: int = 500,
        include_raw: bool = False,
    ):
        return self._execute(
            "auction_process",
            code=code,
            mode_or_selector_raw=mode_or_selector_raw,
            start=start,
            count=count,
            include_raw=include_raw,
        )
