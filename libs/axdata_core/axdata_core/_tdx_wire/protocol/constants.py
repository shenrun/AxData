"""Compatibility constants for ``axdata_core._tdx_wire.protocol.constants``.

The provider-owned TDX wire stack is the primary implementation. This legacy
module keeps old constants imports working while reading the lightweight
provider facts directly, falling back only when the provider package is absent.
"""

from __future__ import annotations

from .._shim import load_provider_first_cached

_PROVIDER_COMMAND_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_PROVIDER_REQUEST_DEFAULTS_MODULE = "axdata_source_tdx._tdx_wire._request_defaults"
_PROVIDER_FRAME_CONSTANTS_MODULE = "axdata_source_tdx._tdx_wire.protocol._frame_constants"
_COMMAND_CODE_EXPORTS = {
    "TYPE_HEARTBEAT": "heartbeat",
    "TYPE_HANDSHAKE": "handshake",
    "TYPE_CAPITAL_CHANGES": "capital_changes",
    "TYPE_FINANCE_INFO": "finance_info",
    "TYPE_SECURITY_LIST": "security_list",
    "TYPE_SECURITY_COUNT": "security_count",
    "TYPE_PRICE_LIMITS": "price_limits",
    "TYPE_INTRADAY_SUBCHART": "intraday_subchart",
    "TYPE_KLINES": "klines",
    "TYPE_TODAY_INTRADAY": "today_intraday",
    "TYPE_LEGACY_QUOTES": "legacy_quotes",
    "TYPE_REFRESH_QUOTES": "refresh_quotes",
    "TYPE_CATEGORY_QUOTES": "category_quotes",
    "TYPE_EXPLICIT_QUOTES": "explicit_quotes",
    "TYPE_AUCTION_PROCESS": "auction_process",
    "TYPE_FILE_CONTENT": "file_content",
    "TYPE_HISTORICAL_INTRADAY": "historical_intraday",
    "TYPE_TODAY_TRADES": "today_trades",
    "TYPE_HISTORICAL_TRADES": "historical_trades",
    "TYPE_RECENT_HISTORICAL_INTRADAY": "recent_historical_intraday",
}
_REQUEST_DEFAULT_EXPORTS = {"DEFAULT_CODE_PAGE_SIZE", "DEFAULT_QUOTE_BATCH_SIZE"}
_FRAME_CONSTANT_EXPORTS = {"CONTROL_DEFAULT", "PREFIX", "PREFIX_RESP"}

_COMMAND_CODES = None
_REQUEST_DEFAULTS = None
_FRAME_CONSTANTS = None


def _load_command_codes():
    return load_provider_first_cached(
        globals(),
        "_COMMAND_CODES",
        _PROVIDER_COMMAND_CODES_MODULE,
    )


def _load_request_defaults():
    return load_provider_first_cached(
        globals(),
        "_REQUEST_DEFAULTS",
        _PROVIDER_REQUEST_DEFAULTS_MODULE,
    )


def _load_frame_constants():
    return load_provider_first_cached(
        globals(),
        "_FRAME_CONSTANTS",
        _PROVIDER_FRAME_CONSTANTS_MODULE,
    )


def _command_codes() -> dict[str, int]:
    command_codes = _load_command_codes().COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def _command_code(name: str) -> int:
    return _load_command_codes().command_code(name)


def __getattr__(name: str):
    if name == "COMMAND_CODES":
        return _command_codes()
    if name in _COMMAND_CODE_EXPORTS:
        value = _command_code(_COMMAND_CODE_EXPORTS[name])
    elif name in _REQUEST_DEFAULT_EXPORTS:
        value = getattr(_load_request_defaults(), name)
    elif name in _FRAME_CONSTANT_EXPORTS:
        value = getattr(_load_frame_constants(), name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

__all__ = [
    "COMMAND_CODES",
    "CONTROL_DEFAULT",
    "DEFAULT_CODE_PAGE_SIZE",
    "DEFAULT_QUOTE_BATCH_SIZE",
    "PREFIX",
    "PREFIX_RESP",
    "TYPE_AUCTION_PROCESS",
    "TYPE_CAPITAL_CHANGES",
    "TYPE_CATEGORY_QUOTES",
    "TYPE_EXPLICIT_QUOTES",
    "TYPE_FILE_CONTENT",
    "TYPE_FINANCE_INFO",
    "TYPE_HANDSHAKE",
    "TYPE_HEARTBEAT",
    "TYPE_HISTORICAL_INTRADAY",
    "TYPE_HISTORICAL_TRADES",
    "TYPE_INTRADAY_SUBCHART",
    "TYPE_KLINES",
    "TYPE_LEGACY_QUOTES",
    "TYPE_PRICE_LIMITS",
    "TYPE_RECENT_HISTORICAL_INTRADAY",
    "TYPE_REFRESH_QUOTES",
    "TYPE_SECURITY_COUNT",
    "TYPE_SECURITY_LIST",
    "TYPE_TODAY_INTRADAY",
    "TYPE_TODAY_TRADES",
]
