"""Compatibility shim for ``axdata_core._tdx_wire.protocol.unit``.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This legacy module keeps old imports working while routing directly to the
provider-owned helper modules.
"""

from __future__ import annotations

from .._shim import load_provider_first_cached


_PROVIDER_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_PROVIDER_MARKET_MODULE = "axdata_source_tdx._tdx_wire._market"
_BINARY_EXPORTS = {
    "consume_tdx_signed_varint",
    "consume_tdx_varint",
    "date_from_yyyymmdd",
    "decode_gbk_text",
    "little_f32",
    "little_u16",
    "little_u32",
    "tdx_quantity_from_u32",
    "tdx_quantity_u32",
    "yyyymmdd",
}
_MARKET_EXPORTS = {
    "ID_TO_MARKET",
    "MARKET_TO_ID",
    "market_to_id",
    "normalize_market",
}


_BINARY_MODULE = None
_MARKET_MODULE = None


def _load_binary_module():
    return load_provider_first_cached(
        globals(),
        "_BINARY_MODULE",
        _PROVIDER_BINARY_MODULE,
    )


def _load_market_module():
    return load_provider_first_cached(
        globals(),
        "_MARKET_MODULE",
        _PROVIDER_MARKET_MODULE,
    )


def __getattr__(name: str):
    if name in _BINARY_EXPORTS:
        value = getattr(_load_binary_module(), name)
    elif name in _MARKET_EXPORTS:
        value = getattr(_load_market_module(), name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


__all__ = [
    "ID_TO_MARKET",
    "MARKET_TO_ID",
    "consume_tdx_signed_varint",
    "consume_tdx_varint",
    "date_from_yyyymmdd",
    "decode_gbk_text",
    "little_f32",
    "little_u16",
    "little_u32",
    "market_to_id",
    "normalize_market",
    "tdx_quantity_from_u32",
    "tdx_quantity_u32",
    "yyyymmdd",
]
