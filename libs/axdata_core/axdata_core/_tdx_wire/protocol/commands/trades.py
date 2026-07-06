"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.trades.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command/layout facts are exposed without loading the full trade
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.trades"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_PROVIDER_LAYOUTS_MODULE = "axdata_source_tdx._tdx_wire._command_layouts"


_codes_impl = None
_layout_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _load_layout_impl():
    return load_provider_first_cached(
        globals(),
        "_layout_impl",
        _PROVIDER_LAYOUTS_MODULE,
    )


def _command_codes() -> dict[str, int]:
    command_codes = _load_codes_impl().COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def _command_code(name: str) -> int:
    return _load_codes_impl().command_code(name)

__all__ = [
    "Any",
    "COMMAND_CODES",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "SHANGHAI_TZ",
    "SIDE_MAP",
    "TYPE_HISTORICAL_TRADES",
    "TYPE_TODAY_TRADES",
    "TradeDetailRecord",
    "TradeDetailSeries",
    "annotations",
    "build_historical_trades_frame",
    "build_today_trades_frame",
    "consume_tdx_signed_varint",
    "consume_tdx_varint",
    "date_from_yyyymmdd",
    "datetime",
    "historical_trade_date",
    "little_f32",
    "little_u16",
    "normalize_trade_count",
    "normalize_trade_start",
    "parse_historical_trades_payload",
    "parse_today_trades_payload",
    "parse_trade_records",
    "split_code",
    "time",
    "trade_time_from_minutes",
    "yyyymmdd",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str) -> Any:
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "SIDE_MAP":
        value = _load_layout_impl().SIDE_MAP
    elif name == "TYPE_HISTORICAL_TRADES":
        value = _command_code("historical_trades")
    elif name == "TYPE_TODAY_TRADES":
        value = _command_code("today_trades")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
