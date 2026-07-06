"""Quote snapshot API."""

from __future__ import annotations

from collections.abc import Sequence

from axdata_source_tdx._tdx_wire._request_defaults import DEFAULT_QUOTE_BATCH_SIZE

from .base import ApiBase


class QuoteApi(ApiBase):
    def legacy(self, securities: Sequence[tuple[str, str]]):
        return self._execute("legacy_quotes", securities=securities)

    def explicit(self, securities: Sequence[tuple[str, str]]):
        return self._execute("explicit_quotes", securities=securities)

    def refresh(self, cursors: Sequence[tuple[str, str, int] | tuple[str, str]]):
        return self._execute("refresh_quotes", cursors=cursors)

    def category(
        self,
        *,
        category: int = 6,
        sort_type: int = 0,
        start: int = 0,
        count: int = 80,
        ascending: bool = False,
        filter_raw: int = 0,
    ):
        return self._execute(
            "category_quotes",
            category=category,
            sort_type=sort_type,
            start=start,
            count=count,
            ascending=ascending,
            filter_raw=filter_raw,
        )

    def price_limits(self, *, start_index: int = 0):
        return self._execute("price_limits", start_index=start_index)

    def price_limits_all(self):
        records = []
        start_index = 0
        while True:
            page = self.price_limits(start_index=start_index)
            if not page:
                break
            records.extend(page)
            start_index += len(page)
        return records

    def legacy_all(
        self,
        securities: Sequence[tuple[str, str]],
        *,
        batch_size: int = DEFAULT_QUOTE_BATCH_SIZE,
    ):
        batch_size = max(1, int(batch_size))
        quotes = []
        for start in range(0, len(securities), batch_size):
            quotes.extend(self.legacy(securities[start : start + batch_size]))
        return quotes

    def explicit_all(
        self,
        securities: Sequence[tuple[str, str]],
        *,
        batch_size: int = DEFAULT_QUOTE_BATCH_SIZE,
    ):
        batch_size = max(1, int(batch_size))
        quotes = []
        for start in range(0, len(securities), batch_size):
            quotes.extend(self.explicit(securities[start : start + batch_size]))
        return quotes
