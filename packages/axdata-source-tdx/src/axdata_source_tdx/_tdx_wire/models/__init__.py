"""Data models exposed by the minimal TDX code-table protocol."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MODULES = {
    "AuctionProcessRecord": ".auction",
    "AuctionProcessSeries": ".auction",
    "CapitalChangeBlock": ".corporate",
    "CapitalChangeRecord": ".corporate",
    "CategoryQuote": ".quote",
    "CategoryQuotePage": ".quote",
    "ExplicitQuote": ".quote",
    "FileContentChunk": ".resource",
    "FinanceInfoBlock": ".finance",
    "FinanceInfoRecord": ".finance",
    "HandshakeInfo": ".session",
    "HeartbeatAck": ".session",
    "HistoricalIntradayPoint": ".intraday",
    "HistoricalIntradaySeries": ".intraday",
    "IntradaySubchartPoint": ".subchart",
    "IntradaySubchartSeries": ".subchart",
    "KlineBar": ".kline",
    "KlineSeries": ".kline",
    "LegacyQuote": ".quote",
    "PriceLimitRecord": ".quote",
    "QuoteLevel": ".quote",
    "QuoteRefreshBatch": ".quote",
    "QuoteRefreshCursor": ".quote",
    "QuoteRefreshRecord": ".quote",
    "RecentHistoricalIntradayPoint": ".intraday",
    "RecentHistoricalIntradaySeries": ".intraday",
    "SecurityCode": ".security",
    "TodayIntradayPoint": ".intraday",
    "TodayIntradaySeries": ".intraday",
    "TradeDetailRecord": ".trade",
    "TradeDetailSeries": ".trade",
}

__all__ = [
    "AuctionProcessRecord",
    "AuctionProcessSeries",
    "CapitalChangeBlock",
    "CapitalChangeRecord",
    "FinanceInfoBlock",
    "FinanceInfoRecord",
    "HandshakeInfo",
    "HeartbeatAck",
    "HistoricalIntradayPoint",
    "HistoricalIntradaySeries",
    "RecentHistoricalIntradayPoint",
    "RecentHistoricalIntradaySeries",
    "TodayIntradayPoint",
    "TodayIntradaySeries",
    "IntradaySubchartPoint",
    "IntradaySubchartSeries",
    "KlineBar",
    "KlineSeries",
    "CategoryQuote",
    "CategoryQuotePage",
    "ExplicitQuote",
    "FileContentChunk",
    "LegacyQuote",
    "PriceLimitRecord",
    "QuoteLevel",
    "QuoteRefreshBatch",
    "QuoteRefreshCursor",
    "QuoteRefreshRecord",
    "SecurityCode",
    "TradeDetailRecord",
    "TradeDetailSeries",
]


def __getattr__(name: str):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
