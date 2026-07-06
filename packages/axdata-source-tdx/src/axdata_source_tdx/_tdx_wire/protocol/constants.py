"""7709 protocol constants."""

from __future__ import annotations

from importlib import import_module


_COMMAND_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_FRAME_CONSTANTS_MODULE = "axdata_source_tdx._tdx_wire.protocol._frame_constants"
_REQUEST_DEFAULTS_MODULE = "axdata_source_tdx._tdx_wire._request_defaults"
_COMMAND_EXPORTS = {
    "TYPE_AUCTION_PROCESS": "auction_process",
    "TYPE_CAPITAL_CHANGES": "capital_changes",
    "TYPE_CATEGORY_QUOTES": "category_quotes",
    "TYPE_EXPLICIT_QUOTES": "explicit_quotes",
    "TYPE_FILE_CONTENT": "file_content",
    "TYPE_FINANCE_INFO": "finance_info",
    "TYPE_HANDSHAKE": "handshake",
    "TYPE_HEARTBEAT": "heartbeat",
    "TYPE_HISTORICAL_INTRADAY": "historical_intraday",
    "TYPE_HISTORICAL_TRADES": "historical_trades",
    "TYPE_INTRADAY_SUBCHART": "intraday_subchart",
    "TYPE_KLINES": "klines",
    "TYPE_LEGACY_QUOTES": "legacy_quotes",
    "TYPE_PRICE_LIMITS": "price_limits",
    "TYPE_RECENT_HISTORICAL_INTRADAY": "recent_historical_intraday",
    "TYPE_REFRESH_QUOTES": "refresh_quotes",
    "TYPE_SECURITY_COUNT": "security_count",
    "TYPE_SECURITY_LIST": "security_list",
    "TYPE_TODAY_INTRADAY": "today_intraday",
    "TYPE_TODAY_TRADES": "today_trades",
}
_FRAME_EXPORTS = {"CONTROL_DEFAULT", "PREFIX", "PREFIX_RESP"}
_REQUEST_DEFAULT_EXPORTS = {"DEFAULT_CODE_PAGE_SIZE", "DEFAULT_QUOTE_BATCH_SIZE"}


def _command_codes_module():
    return import_module(_COMMAND_CODES_MODULE)


def _frame_constants_module():
    return import_module(_FRAME_CONSTANTS_MODULE)


def _request_defaults_module():
    return import_module(_REQUEST_DEFAULTS_MODULE)


def __getattr__(name: str):
    if name in _COMMAND_EXPORTS:
        value = _command_codes_module().command_code(_COMMAND_EXPORTS[name])
    elif name == "command_code":
        value = _command_codes_module().command_code
    elif name == "COMMAND_CODES":
        value = _command_codes_module().COMMAND_CODES
    elif name in _FRAME_EXPORTS:
        value = getattr(_frame_constants_module(), name)
    elif name in _REQUEST_DEFAULT_EXPORTS:
        value = getattr(_request_defaults_module(), name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


__all__ = sorted(set(_COMMAND_EXPORTS) | _FRAME_EXPORTS | _REQUEST_DEFAULT_EXPORTS | {"COMMAND_CODES", "command_code"})
