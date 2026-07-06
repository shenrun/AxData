"""Compatibility binary helpers for 7709 command parsers."""

from __future__ import annotations

from datetime import date, datetime
from importlib import import_module


_BINARY_MODULE_NAME = "axdata_source_tdx._tdx_wire._binary"
_MARKET_MODULE_NAME = "axdata_source_tdx._tdx_wire._market"
_MARKET_EXPORTS = {"ID_TO_MARKET", "MARKET_TO_ID", "market_to_id", "normalize_market"}

_BINARY_MODULE = None
_MARKET_MODULE = None


def _load_binary_module():
    global _BINARY_MODULE
    if _BINARY_MODULE is None:
        _BINARY_MODULE = import_module(_BINARY_MODULE_NAME)
    return _BINARY_MODULE


def _load_market_module():
    global _MARKET_MODULE
    if _MARKET_MODULE is None:
        _MARKET_MODULE = import_module(_MARKET_MODULE_NAME)
    return _MARKET_MODULE


def little_u16(data: bytes) -> int:
    return _load_binary_module().little_u16(data)


def little_u32(data: bytes) -> int:
    return _load_binary_module().little_u32(data)


def little_f32(data: bytes) -> float:
    return _load_binary_module().little_f32(data)


def tdx_quantity_u32(data: bytes) -> float:
    return _load_binary_module().tdx_quantity_u32(data)


def tdx_quantity_from_u32(raw: int) -> float:
    return _load_binary_module().tdx_quantity_from_u32(raw)


def decode_gbk_text(data: bytes) -> str:
    return _load_binary_module().decode_gbk_text(data)


def yyyymmdd(value: str | int | date | datetime | None = None) -> int:
    return _load_binary_module().yyyymmdd(value)


def date_from_yyyymmdd(raw: int) -> date | None:
    return _load_binary_module().date_from_yyyymmdd(raw)


def consume_tdx_signed_varint(payload: bytes, offset: int) -> tuple[int, int]:
    return _load_binary_module().consume_tdx_signed_varint(payload, offset)


def consume_tdx_varint(payload: bytes, offset: int) -> tuple[int, int]:
    return _load_binary_module().consume_tdx_varint(payload, offset)


def __getattr__(name: str):
    if name in _MARKET_EXPORTS:
        value = getattr(_load_market_module(), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
