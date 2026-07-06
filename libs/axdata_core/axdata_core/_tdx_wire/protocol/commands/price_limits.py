"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.price_limits.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command code/layout facts are exposed without loading the full
price-limit command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

import struct

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.price_limits"
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
    "COMMAND_CODES",
    "ID_TO_MARKET",
    "PRICE_LIMIT_RECORD_SIZE",
    "PriceLimitRecord",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "TYPE_PRICE_LIMITS",
    "annotations",
    "build_price_limits_frame",
    "little_f32",
    "little_u16",
    "little_u32",
    "parse_price_limits_payload",
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
    if name == "PRICE_LIMIT_RECORD_SIZE":
        value = _load_layout_impl().PRICE_LIMIT_RECORD_SIZE
    elif name == "TYPE_PRICE_LIMITS":
        value = _command_code("price_limits")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
