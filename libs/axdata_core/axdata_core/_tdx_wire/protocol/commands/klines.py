"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.klines.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command code facts are exposed without loading the full K-line
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.klines"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"


_codes_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _command_codes() -> dict[str, int]:
    command_codes = _load_codes_impl().COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def _command_code(name: str) -> int:
    return _load_codes_impl().command_code(name)

__all__ = [
    "ADJUST_TO_RAW",
    "Any",
    "COMMAND_CODES",
    "KlineBar",
    "KlineSeries",
    "PERIOD_ALIASES",
    "ProtocolError",
    "RAW_TO_ADJUST",
    "RequestFrame",
    "ResponseFrame",
    "SHANGHAI_TZ",
    "TYPE_KLINES",
    "annotations",
    "build_klines_frame",
    "consume_tdx_signed_varint",
    "consume_varint",
    "date",
    "date_from_yyyymmdd",
    "datetime",
    "decode_compact_float",
    "decode_kline_datetime",
    "little_u16",
    "little_u32",
    "market_to_id",
    "math",
    "milli_to_float",
    "normalize_adjust",
    "normalize_anchor_date",
    "normalize_code",
    "normalize_period",
    "parse_klines_payload",
    "period_name",
    "re",
    "split_code",
    "timedelta",
    "timezone",
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
    if name == "TYPE_KLINES":
        value = _command_code("klines")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
