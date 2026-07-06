"""Compatibility shim for axdata_core._tdx_wire.models.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from .._shim import load_provider_first


_EXPORT_MODULES = {
    "AuctionProcessRecord": "axdata_source_tdx._tdx_wire.models.auction",
    "AuctionProcessSeries": "axdata_source_tdx._tdx_wire.models.auction",
    "CapitalChangeBlock": "axdata_source_tdx._tdx_wire.models.corporate",
    "CapitalChangeRecord": "axdata_source_tdx._tdx_wire.models.corporate",
    "CategoryQuote": "axdata_source_tdx._tdx_wire.models.quote",
    "CategoryQuotePage": "axdata_source_tdx._tdx_wire.models.quote",
    "ExplicitQuote": "axdata_source_tdx._tdx_wire.models.quote",
    "FileContentChunk": "axdata_source_tdx._tdx_wire.models.resource",
    "FinanceInfoBlock": "axdata_source_tdx._tdx_wire.models.finance",
    "FinanceInfoRecord": "axdata_source_tdx._tdx_wire.models.finance",
    "HandshakeInfo": "axdata_source_tdx._tdx_wire.models.session",
    "HeartbeatAck": "axdata_source_tdx._tdx_wire.models.session",
    "HistoricalIntradayPoint": "axdata_source_tdx._tdx_wire.models.intraday",
    "HistoricalIntradaySeries": "axdata_source_tdx._tdx_wire.models.intraday",
    "IntradaySubchartPoint": "axdata_source_tdx._tdx_wire.models.subchart",
    "IntradaySubchartSeries": "axdata_source_tdx._tdx_wire.models.subchart",
    "KlineBar": "axdata_source_tdx._tdx_wire.models.kline",
    "KlineSeries": "axdata_source_tdx._tdx_wire.models.kline",
    "LegacyQuote": "axdata_source_tdx._tdx_wire.models.quote",
    "PriceLimitRecord": "axdata_source_tdx._tdx_wire.models.quote",
    "QuoteLevel": "axdata_source_tdx._tdx_wire.models.quote",
    "QuoteRefreshBatch": "axdata_source_tdx._tdx_wire.models.quote",
    "QuoteRefreshCursor": "axdata_source_tdx._tdx_wire.models.quote",
    "QuoteRefreshRecord": "axdata_source_tdx._tdx_wire.models.quote",
    "RecentHistoricalIntradayPoint": "axdata_source_tdx._tdx_wire.models.intraday",
    "RecentHistoricalIntradaySeries": "axdata_source_tdx._tdx_wire.models.intraday",
    "SecurityCode": "axdata_source_tdx._tdx_wire.models.security",
    "TodayIntradayPoint": "axdata_source_tdx._tdx_wire.models.intraday",
    "TodayIntradaySeries": "axdata_source_tdx._tdx_wire.models.intraday",
    "TradeDetailRecord": "axdata_source_tdx._tdx_wire.models.trade",
    "TradeDetailSeries": "axdata_source_tdx._tdx_wire.models.trade",
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
    implementation = load_provider_first(module_name)
    value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
