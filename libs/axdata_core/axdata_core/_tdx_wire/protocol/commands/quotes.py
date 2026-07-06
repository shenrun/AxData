"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.quotes.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command code facts are exposed without loading the full quote
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable, Sequence

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.quotes"
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
    "COMMAND_CODES",
    "CategoryQuote",
    "CategoryQuotePage",
    "ExplicitQuote",
    "ID_TO_MARKET",
    "Iterable",
    "LegacyQuote",
    "ProtocolError",
    "QuoteLevel",
    "QuoteRefreshBatch",
    "QuoteRefreshRecord",
    "RequestFrame",
    "ResponseFrame",
    "Sequence",
    "TYPE_CATEGORY_QUOTES",
    "TYPE_EXPLICIT_QUOTES",
    "TYPE_LEGACY_QUOTES",
    "TYPE_REFRESH_QUOTES",
    "annotations",
    "build_category_quotes_frame",
    "build_explicit_quotes_frame",
    "build_legacy_quotes_frame",
    "build_refresh_quotes_frame",
    "decode_compact_float",
    "little_f32",
    "little_u16",
    "little_u32",
    "market_to_id",
    "parse_category_quotes_payload",
    "parse_explicit_quotes_payload",
    "parse_legacy_quotes_payload",
    "parse_refresh_quotes_payload",
    "struct",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str):
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "TYPE_CATEGORY_QUOTES":
        value = _command_code("category_quotes")
    elif name == "TYPE_EXPLICIT_QUOTES":
        value = _command_code("explicit_quotes")
    elif name == "TYPE_LEGACY_QUOTES":
        value = _command_code("legacy_quotes")
    elif name == "TYPE_REFRESH_QUOTES":
        value = _command_code("refresh_quotes")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
