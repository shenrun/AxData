"""Minimal TDX 7709 client used by AxData source code-table requests."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib import import_module
from typing import TYPE_CHECKING, Any

from ._connection_defaults import DEFAULT_PROBE_TIMEOUT, DEFAULT_PROBE_WORKERS
from ._request_defaults import DEFAULT_CODE_PAGE_SIZE, DEFAULT_FILE_CHUNK_SIZE, DEFAULT_QUOTE_BATCH_SIZE

if TYPE_CHECKING:
    from .api.auction import AuctionApi
    from .api.bars import BarApi
    from .api.codes import CodeApi
    from .api.corporate import CorporateApi
    from .api.finance import FinanceApi
    from .api.intraday import IntradayApi
    from .api.quotes import QuoteApi
    from .api.resources import ResourceApi
    from .api.session import SessionApi
    from .api.trades import TradeApi
    from .models.auction import AuctionProcessSeries
    from .models.corporate import CapitalChangeBlock
    from .models.finance import FinanceInfoBlock
    from .models.intraday import (
        HistoricalIntradaySeries,
        RecentHistoricalIntradaySeries,
        TodayIntradaySeries,
    )
    from .models.kline import KlineSeries
    from .models.quote import CategoryQuotePage, ExplicitQuote, LegacyQuote, QuoteRefreshBatch
    from .models.resource import FileContentChunk
    from .models.security import SecurityCode
    from .models.subchart import IntradaySubchartSeries
    from .models.trade import TradeDetailSeries
    from .transport.base import Transport


@dataclass(slots=True)
class TdxClient:
    """Small client for the TDX security code table.

    Higher-level quote, kline, minute, trade, F10, and helper APIs are
    intentionally not exposed here. Add them back one interface at a time when
    AxData has a concrete product contract for them.
    """

    transport: Transport | None = None
    host: str | None = None
    hosts: Sequence[str] | None = None
    timeout: float = 8.0
    pool_size: int = 1
    probe_hosts: bool = False
    probe_timeout: float = DEFAULT_PROBE_TIMEOUT
    probe_workers: int = DEFAULT_PROBE_WORKERS
    heartbeat_interval: float | None = None
    _auction: AuctionApi | None = field(default=None, init=False, repr=False)
    _session: SessionApi | None = field(default=None, init=False, repr=False)
    _bars: BarApi | None = field(default=None, init=False, repr=False)
    _codes: CodeApi | None = field(default=None, init=False, repr=False)
    _corporate: CorporateApi | None = field(default=None, init=False, repr=False)
    _finance: FinanceApi | None = field(default=None, init=False, repr=False)
    _intraday: IntradayApi | None = field(default=None, init=False, repr=False)
    _quotes: QuoteApi | None = field(default=None, init=False, repr=False)
    _resources: ResourceApi | None = field(default=None, init=False, repr=False)
    _trades: TradeApi | None = field(default=None, init=False, repr=False)
    _code_count_cache: dict[str, int] = field(init=False, repr=False)
    _codes_all_cache: dict[str, list[SecurityCode]] = field(init=False, repr=False)

    @classmethod
    def from_hosts(
        cls,
        hosts: list[str] | tuple[str, ...] | None = None,
        *,
        timeout: float = 8.0,
        pool_size: int = 1,
        probe_hosts: bool = False,
        probe_timeout: float = DEFAULT_PROBE_TIMEOUT,
        probe_workers: int = DEFAULT_PROBE_WORKERS,
        heartbeat_interval: float | None = None,
    ) -> TdxClient:
        """Create a client backed by one or more real TDX 7709 hosts."""

        from .transport.pool import PooledSocketTransport

        return cls(
            transport=PooledSocketTransport(
                hosts=hosts,
                timeout=timeout,
                pool_size=pool_size,
                probe_hosts=probe_hosts,
                probe_timeout=probe_timeout,
                probe_workers=probe_workers,
                heartbeat_interval=heartbeat_interval,
            ),
            hosts=hosts,
            timeout=timeout,
            pool_size=pool_size,
            probe_hosts=probe_hosts,
            probe_timeout=probe_timeout,
            probe_workers=probe_workers,
            heartbeat_interval=heartbeat_interval,
        )

    @classmethod
    def in_memory(cls) -> TdxClient:
        """Create a deterministic client for tests."""

        from .transport.memory import InMemoryTransport

        return cls(transport=InMemoryTransport())

    def __post_init__(self) -> None:
        if self.transport is None:
            from .transport.pool import PooledSocketTransport

            resolved_hosts = _resolve_hosts(self.host, self.hosts)
            self.transport = PooledSocketTransport(
                hosts=resolved_hosts or None,
                timeout=self.timeout,
                pool_size=self.pool_size,
                probe_hosts=self.probe_hosts,
                probe_timeout=self.probe_timeout,
                probe_workers=self.probe_workers,
                heartbeat_interval=self.heartbeat_interval,
            )
        self._code_count_cache = {}
        self._codes_all_cache = {}

    def _api(self, cache_name: str, module_name: str, class_name: str) -> Any:
        value = getattr(self, cache_name)
        if value is None:
            module = import_module(f"{__package__}.{module_name}")
            api_cls = getattr(module, class_name)
            value = api_cls(self.transport)
            setattr(self, cache_name, value)
        return value

    @property
    def auction(self) -> AuctionApi:
        return self._api("_auction", "api.auction", "AuctionApi")

    @auction.setter
    def auction(self, value: AuctionApi) -> None:
        self._auction = value

    @property
    def session(self) -> SessionApi:
        return self._api("_session", "api.session", "SessionApi")

    @session.setter
    def session(self, value: SessionApi) -> None:
        self._session = value

    @property
    def bars(self) -> BarApi:
        return self._api("_bars", "api.bars", "BarApi")

    @bars.setter
    def bars(self, value: BarApi) -> None:
        self._bars = value

    @property
    def codes(self) -> CodeApi:
        return self._api("_codes", "api.codes", "CodeApi")

    @codes.setter
    def codes(self, value: CodeApi) -> None:
        self._codes = value

    @property
    def corporate(self) -> CorporateApi:
        return self._api("_corporate", "api.corporate", "CorporateApi")

    @corporate.setter
    def corporate(self, value: CorporateApi) -> None:
        self._corporate = value

    @property
    def finance(self) -> FinanceApi:
        return self._api("_finance", "api.finance", "FinanceApi")

    @finance.setter
    def finance(self, value: FinanceApi) -> None:
        self._finance = value

    @property
    def intraday(self) -> IntradayApi:
        return self._api("_intraday", "api.intraday", "IntradayApi")

    @intraday.setter
    def intraday(self, value: IntradayApi) -> None:
        self._intraday = value

    @property
    def quotes(self) -> QuoteApi:
        return self._api("_quotes", "api.quotes", "QuoteApi")

    @quotes.setter
    def quotes(self, value: QuoteApi) -> None:
        self._quotes = value

    @property
    def resources(self) -> ResourceApi:
        return self._api("_resources", "api.resources", "ResourceApi")

    @resources.setter
    def resources(self, value: ResourceApi) -> None:
        self._resources = value

    @property
    def trades(self) -> TradeApi:
        return self._api("_trades", "api.trades", "TradeApi")

    @trades.setter
    def trades(self, value: TradeApi) -> None:
        self._trades = value

    def connect(self) -> None:
        self.transport.connect()

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> TdxClient:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def ping(self) -> str:
        return self.session.ping()

    def clear_cache(self) -> None:
        self._code_count_cache.clear()
        self._codes_all_cache.clear()

    def get_count(self, exchange, *, refresh: bool = False) -> int:
        market = _normalize_market(exchange)
        if not refresh and market in self._code_count_cache:
            return self._code_count_cache[market]
        count = self.codes.count(market)
        self._code_count_cache[market] = count
        return count

    def get_codes(self, exchange, *, start: int = 0, limit: int | None = DEFAULT_CODE_PAGE_SIZE):
        market = _normalize_market(exchange)
        if start < 0:
            raise ValueError("start must be >= 0")
        if limit is None:
            return self.codes.all(market)[start:]
        if limit < 0:
            raise ValueError("limit must be >= 0")
        return self.codes.list(market, start=start, limit=limit)

    def get_codes_all(self, exchange, *, refresh: bool = False) -> list[SecurityCode]:
        market = _normalize_market(exchange)
        if not refresh and market in self._codes_all_cache:
            return list(self._codes_all_cache[market])
        items = list(self.codes.all(market))
        self._codes_all_cache[market] = items
        self._code_count_cache[market] = len(items)
        return list(items)

    def get_legacy_quotes(
        self,
        securities: Sequence[tuple[str, str]],
        *,
        batch_size: int = DEFAULT_QUOTE_BATCH_SIZE,
    ) -> list[LegacyQuote]:
        normalized = [(_normalize_market(market), str(code)) for market, code in securities]
        return self.quotes.legacy_all(normalized, batch_size=batch_size)

    def get_explicit_quotes(
        self,
        securities: Sequence[tuple[str, str]],
        *,
        batch_size: int = DEFAULT_QUOTE_BATCH_SIZE,
    ) -> list[ExplicitQuote]:
        normalized = [(_normalize_market(market), str(code)) for market, code in securities]
        return self.quotes.explicit_all(normalized, batch_size=batch_size)

    def get_quote_refresh(
        self,
        cursors: Sequence[tuple[str, str, int] | tuple[str, str]],
    ) -> QuoteRefreshBatch:
        normalized = []
        for item in cursors:
            if len(item) == 2:
                market, code = item
                cursor = 0
            else:
                market, code, cursor = item
            normalized.append((_normalize_market(market), str(code), int(cursor)))
        return self.quotes.refresh(normalized)

    def download_file_resource_chunk(
        self,
        path: str,
        *,
        offset: int = 0,
        size: int = DEFAULT_FILE_CHUNK_SIZE,
    ) -> FileContentChunk:
        return self.resources.download_chunk(path, offset=offset, size=size)

    def download_file_resource(
        self,
        path: str,
        *,
        chunk_size: int = DEFAULT_FILE_CHUNK_SIZE,
        max_bytes: int | None = None,
    ) -> bytes:
        return self.resources.download_file(path, chunk_size=chunk_size, max_bytes=max_bytes)

    def get_category_quotes(
        self,
        *,
        category: int = 6,
        sort_type: int = 0,
        start: int = 0,
        count: int = 80,
        ascending: bool = False,
        filter_raw: int = 0,
    ) -> CategoryQuotePage:
        return self.quotes.category(
            category=category,
            sort_type=sort_type,
            start=start,
            count=count,
            ascending=ascending,
            filter_raw=filter_raw,
        )

    def get_price_limits(self, *, start_index: int = 0):
        return self.quotes.price_limits(start_index=start_index)

    def get_price_limits_all(self):
        return self.quotes.price_limits_all()

    def get_auction_process(
        self,
        code: str,
        *,
        mode_or_selector_raw: int = 3,
        start: int = 0,
        count: int = 500,
        include_raw: bool = False,
    ) -> AuctionProcessSeries:
        return self.auction.process(
            code,
            mode_or_selector_raw=mode_or_selector_raw,
            start=start,
            count=count,
            include_raw=include_raw,
        )

    def get_kline(
        self,
        code: str,
        *,
        period: str = "day",
        start: int = 0,
        count: int = 800,
        adjust: str | None = None,
        anchor_date=None,
        kind: str = "stock",
        include_raw: bool = False,
    ) -> KlineSeries:
        return self.bars.get(
            code,
            period=period,
            start=start,
            count=count,
            adjust=adjust,
            anchor_date=anchor_date,
            kind=kind,
            include_raw=include_raw,
        )

    def get_capital_changes(self, code: str, *, include_raw: bool = False) -> CapitalChangeBlock:
        return self.corporate.capital_changes(code, include_raw=include_raw)

    def get_finance_info(self, code, *, include_raw: bool = False) -> FinanceInfoBlock:
        return self.finance.info(code, include_raw=include_raw)

    def get_historical_intraday(
        self,
        code: str,
        *,
        trade_date,
        include_raw: bool = False,
    ) -> HistoricalIntradaySeries:
        return self.intraday.historical(code, trade_date=trade_date, include_raw=include_raw)

    def get_recent_historical_intraday(
        self,
        code: str,
        *,
        trade_date,
        include_raw: bool = False,
    ) -> RecentHistoricalIntradaySeries:
        return self.intraday.recent_historical(code, trade_date=trade_date, include_raw=include_raw)

    def get_today_intraday(
        self,
        code: str,
        *,
        include_raw: bool = False,
    ) -> TodayIntradaySeries:
        return self.intraday.today(code, include_raw=include_raw)

    def get_intraday_subchart(
        self,
        code: str,
        *,
        selector=0,
        include_raw: bool = False,
    ) -> IntradaySubchartSeries:
        return self.intraday.subchart(code, selector=selector, include_raw=include_raw)

    def get_today_trades(
        self,
        code: str,
        *,
        start: int = 0,
        count: int = 115,
        include_raw: bool = False,
    ) -> TradeDetailSeries:
        return self.trades.today(code, start=start, count=count, include_raw=include_raw)

    def get_historical_trades(
        self,
        code: str,
        *,
        trade_date,
        start: int = 0,
        count: int = 900,
        include_raw: bool = False,
    ) -> TradeDetailSeries:
        return self.trades.historical(
            code,
            trade_date=trade_date,
            start=start,
            count=count,
            include_raw=include_raw,
        )


def _resolve_hosts(host: str | None, hosts: Sequence[str] | None) -> list[str]:
    if hosts is None:
        resolved_hosts = []
    elif isinstance(hosts, str):
        resolved_hosts = [hosts]
    else:
        resolved_hosts = list(hosts)
    if host is not None:
        resolved_hosts.insert(0, host)
    return resolved_hosts


def _normalize_market(value) -> str:
    from ._market import normalize_market

    return normalize_market(value)


Client = TdxClient
