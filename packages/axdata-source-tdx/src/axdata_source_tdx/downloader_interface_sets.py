"""TDX downloader interface groups used by adapter factory rules."""

from __future__ import annotations


DOWNLOADER_PARALLEL_SUSPENSION_INTERFACES = frozenset({"stock_suspensions_tdx"})

DOWNLOADER_STATS_RESOURCE_INTERFACES = frozenset(
    {
        "stock_daily_share_tdx",
        "stock_limit_ladder_tdx",
        "stock_theme_strength_rank_tdx",
        "stock_shortline_indicators_tdx",
    }
)

DOWNLOADER_F10_TOPIC_PREFILL_INTERFACES = frozenset(
    {
        "stock_limit_ladder_tdx",
        "stock_theme_strength_rank_tdx",
    }
)

DOWNLOADER_RUNTIME_SOURCE_SERVER_MAX_INTERFACES = frozenset(
    {
        "stock_daily_share_tdx",
        "stock_daily_price_limit_tdx",
    }
)
