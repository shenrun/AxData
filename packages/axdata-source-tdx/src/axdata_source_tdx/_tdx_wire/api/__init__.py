"""Business-facing API modules for the minimal TDX code-table protocol."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MODULES = {
    "AuctionApi": ".auction",
    "BarApi": ".bars",
    "CodeApi": ".codes",
    "CorporateApi": ".corporate",
    "FinanceApi": ".finance",
    "IntradayApi": ".intraday",
    "QuoteApi": ".quotes",
    "ResourceApi": ".resources",
    "SessionApi": ".session",
    "TradeApi": ".trades",
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
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
