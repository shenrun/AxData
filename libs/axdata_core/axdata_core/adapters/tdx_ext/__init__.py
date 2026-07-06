"""TDX extended market source adapter package."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS: dict[str, tuple[str, str]] = {
    "ConnectionClosedError": (".exceptions", "ConnectionClosedError"),
    "ProtocolError": (".exceptions", "ProtocolError"),
    "ResponseTimeoutError": (".exceptions", "ResponseTimeoutError"),
    "TdxExtError": (".exceptions", "TdxExtError"),
    "TdxExtCachePaths": (".local_cache", "TdxExtCachePaths"),
    "TdxExtClient": (".client", "TdxExtClient"),
    "TdxExtGuiMarket": (".local_cache", "TdxExtGuiMarket"),
    "TdxExtInstrument": (".models", "TdxExtInstrument"),
    "TdxExtLocalInstrument": (".local_cache", "TdxExtLocalInstrument"),
    "TdxExtLocalMarket": (".local_cache", "TdxExtLocalMarket"),
    "TdxExtMarket": (".models", "TdxExtMarket"),
    "TdxExtProductSpec": (".local_cache", "TdxExtProductSpec"),
    "TdxExtQuote": (".models", "TdxExtQuote"),
    "TdxExtQuoteLevel": (".models", "TdxExtQuoteLevel"),
    "TdxExtRequestAdapter": (".request", "TdxExtRequestAdapter"),
    "TdxExtServer": (".servers", "TdxExtServer"),
    "create_tdx_ext_client": (".client", "create_tdx_ext_client"),
    "discover_tdx_ext_cache_paths": (".local_cache", "discover_tdx_ext_cache_paths"),
    "load_tdx_ext_local_instruments": (".local_cache", "load_tdx_ext_local_instruments"),
    "load_tdx_ext_local_markets": (".local_cache", "load_tdx_ext_local_markets"),
    "resolve_tdx_ext_cache_paths": (".local_cache", "resolve_tdx_ext_cache_paths"),
}

__all__ = [
    "ConnectionClosedError",
    "ProtocolError",
    "ResponseTimeoutError",
    "TdxExtError",
    "TdxExtCachePaths",
    "TdxExtClient",
    "TdxExtGuiMarket",
    "TdxExtInstrument",
    "TdxExtLocalInstrument",
    "TdxExtLocalMarket",
    "TdxExtMarket",
    "TdxExtProductSpec",
    "TdxExtQuote",
    "TdxExtQuoteLevel",
    "TdxExtRequestAdapter",
    "TdxExtServer",
    "create_tdx_ext_client",
    "discover_tdx_ext_cache_paths",
    "load_tdx_ext_local_instruments",
    "load_tdx_ext_local_markets",
    "resolve_tdx_ext_cache_paths",
]


def __getattr__(name: str) -> Any:
    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = export
    module = import_module(module_name, __name__)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
