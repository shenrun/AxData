"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.auction.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command/default facts are exposed without loading the full auction
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from datetime import time
from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.auction"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_PROVIDER_DEFAULTS_MODULE = "axdata_source_tdx._tdx_wire._command_defaults"
_PROVIDER_LAYOUTS_MODULE = "axdata_source_tdx._tdx_wire._command_layouts"


_codes_impl = None
_defaults_impl = None
_layout_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _load_defaults_impl():
    return load_provider_first_cached(
        globals(),
        "_defaults_impl",
        _PROVIDER_DEFAULTS_MODULE,
    )


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
    "AUCTION_RECORD_SIZE",
    "Any",
    "AuctionProcessRecord",
    "AuctionProcessSeries",
    "COMMAND_CODES",
    "DEFAULT_AUCTION_COUNT",
    "DEFAULT_AUCTION_MODE",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "TYPE_AUCTION_PROCESS",
    "annotations",
    "auction_time_from_raw",
    "build_auction_process_frame",
    "little_f32",
    "little_u16",
    "little_u32",
    "normalize_auction_u32",
    "parse_auction_process_payload",
    "split_code",
    "time",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str) -> Any:
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "AUCTION_RECORD_SIZE":
        value = _load_layout_impl().AUCTION_RECORD_SIZE
    elif name == "DEFAULT_AUCTION_COUNT":
        value = _load_defaults_impl().DEFAULT_AUCTION_COUNT
    elif name == "DEFAULT_AUCTION_MODE":
        value = _load_defaults_impl().DEFAULT_AUCTION_MODE
    elif name == "TYPE_AUCTION_PROCESS":
        value = _command_code("auction_process")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
