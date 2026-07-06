"""Compatibility shim for axdata_core._tdx_wire.api.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from .._shim import load_provider_first


_EXPORT_MODULES = {
    "AuctionApi": "axdata_source_tdx._tdx_wire.api.auction",
    "BarApi": "axdata_source_tdx._tdx_wire.api.bars",
    "CodeApi": "axdata_source_tdx._tdx_wire.api.codes",
    "CorporateApi": "axdata_source_tdx._tdx_wire.api.corporate",
    "FinanceApi": "axdata_source_tdx._tdx_wire.api.finance",
    "IntradayApi": "axdata_source_tdx._tdx_wire.api.intraday",
    "QuoteApi": "axdata_source_tdx._tdx_wire.api.quotes",
    "ResourceApi": "axdata_source_tdx._tdx_wire.api.resources",
    "SessionApi": "axdata_source_tdx._tdx_wire.api.session",
    "TradeApi": "axdata_source_tdx._tdx_wire.api.trades",
}

__all__ = [
    "AuctionApi",
    "BarApi",
    "CodeApi",
    "CorporateApi",
    "FinanceApi",
    "IntradayApi",
    "QuoteApi",
    "ResourceApi",
    "SessionApi",
    "TradeApi",
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
