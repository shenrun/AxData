"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.intraday.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command/default facts are exposed without loading the full intraday
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.intraday"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_PROVIDER_DEFAULTS_MODULE = "axdata_source_tdx._tdx_wire._command_defaults"


_codes_impl = None
_defaults_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _load_defaults_impl():
    return load_provider_first_cached(
        globals(),
        "_defaults_impl",
        _PROVIDER_DEFAULTS_MODULE,
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
    "DEFAULT_TODAY_INTRADAY_RESERVED_TAIL",
    "HistoricalIntradayPoint",
    "HistoricalIntradaySeries",
    "ProtocolError",
    "RECENT_HISTORICAL_INTRADAY_DATE_BASE",
    "RecentHistoricalIntradayPoint",
    "RecentHistoricalIntradaySeries",
    "RequestFrame",
    "ResponseFrame",
    "SHANGHAI_TZ",
    "TYPE_HISTORICAL_INTRADAY",
    "TYPE_RECENT_HISTORICAL_INTRADAY",
    "TYPE_TODAY_INTRADAY",
    "TodayIntradayPoint",
    "TodayIntradaySeries",
    "annotations",
    "build_historical_intraday_frame",
    "build_recent_historical_intraday_frame",
    "build_today_intraday_frame",
    "consume_tdx_signed_varint",
    "consume_tdx_varint",
    "date",
    "date_from_yyyymmdd",
    "datetime",
    "historical_intraday_time",
    "historical_intraday_trade_date",
    "intraday_time_label",
    "little_f32",
    "little_u16",
    "parse_historical_intraday_payload",
    "parse_recent_historical_intraday_payload",
    "parse_today_intraday_payload",
    "recent_historical_intraday_date_selector",
    "recent_historical_intraday_trade_date_from_selector",
    "split_code",
    "time",
    "timedelta",
    "today_intraday_reserved_tail",
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
    if name == "DEFAULT_TODAY_INTRADAY_RESERVED_TAIL":
        value = _load_defaults_impl().DEFAULT_TODAY_INTRADAY_RESERVED_TAIL
    elif name == "RECENT_HISTORICAL_INTRADAY_DATE_BASE":
        value = _load_defaults_impl().RECENT_HISTORICAL_INTRADAY_DATE_BASE
    elif name == "TYPE_HISTORICAL_INTRADAY":
        value = _command_code("historical_intraday")
    elif name == "TYPE_RECENT_HISTORICAL_INTRADAY":
        value = _command_code("recent_historical_intraday")
    elif name == "TYPE_TODAY_INTRADAY":
        value = _command_code("today_intraday")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
