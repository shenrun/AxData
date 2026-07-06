"""TDX extended-market interface groups."""

from __future__ import annotations


EXT_ASSET_INTERFACE_TO_TYPE = {
    "futures_contracts_tdx": "futures",
    "option_contracts_tdx": "option",
    "fund_codes_tdx": "fund",
    "bond_codes_tdx": "bond",
    "fx_codes_tdx": "fx",
    "macro_indicators_tdx": "macro",
}

QUOTE_INTERFACE_TO_TYPE = {
    "futures_realtime_snapshot_tdx": "futures",
    "option_realtime_snapshot_tdx": "option",
    "bond_realtime_snapshot_tdx": "bond",
    "fx_realtime_snapshot_tdx": "fx",
    "macro_indicator_snapshot_tdx": "macro",
}

KLINE_INTERFACE_TO_TYPE = {
    "futures_kline_tdx": "futures",
    "option_kline_tdx": "option",
    "fund_nav_series_tdx": "fund",
    "bond_kline_tdx": "bond",
    "fx_kline_tdx": "fx",
    "macro_indicator_series_tdx": "macro",
}

INTRADAY_INTERFACE_TO_TYPE = {
    "futures_intraday_today_tdx": "futures",
    "futures_intraday_history_tdx": "futures",
    "option_intraday_today_tdx": "option",
    "option_intraday_history_tdx": "option",
    "fx_intraday_today_tdx": "fx",
    "fx_intraday_history_tdx": "fx",
}

TRADES_HISTORY_INTERFACE_TO_TYPE = {
    "futures_trades_history_tdx": "futures",
    "fx_trades_history_tdx": "fx",
}

TRADES_TODAY_INTERFACE_TO_TYPE = {
    "futures_trades_today_tdx": "futures",
    "fx_trades_today_tdx": "fx",
}

OPTION_CHAIN_INTERFACE = "option_chain_tdx"
FUND_NAV_INTERFACE = "fund_nav_tdx"

SUPPORTED_INTERFACES = {
    "tdx_ext_markets_tdx",
    "tdx_ext_instruments_tdx",
    *EXT_ASSET_INTERFACE_TO_TYPE,
    *QUOTE_INTERFACE_TO_TYPE,
    *KLINE_INTERFACE_TO_TYPE,
    *INTRADAY_INTERFACE_TO_TYPE,
    *TRADES_HISTORY_INTERFACE_TO_TYPE,
    *TRADES_TODAY_INTERFACE_TO_TYPE,
    OPTION_CHAIN_INTERFACE,
    FUND_NAV_INTERFACE,
}
