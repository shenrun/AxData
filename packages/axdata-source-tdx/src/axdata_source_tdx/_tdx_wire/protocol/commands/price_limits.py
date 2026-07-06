"""Special security price-limit table command."""

from __future__ import annotations

from importlib import import_module

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._market import ID_TO_MARKET
from axdata_source_tdx._tdx_wire._command_layouts import PRICE_LIMIT_RECORD_SIZE
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_PRICE_LIMITS = command_code("price_limits")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.quote"
_BINARY_EXPORTS = {"little_f32", "little_u16", "little_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"PriceLimitRecord"}
_STDLIB_EXPORTS = {"struct"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _struct_module():
    module = import_module("struct")
    globals()["struct"] = module
    return module


def _price_limit_record_cls():
    return import_module(_MODEL_MODULE).PriceLimitRecord


def build_price_limits_frame(payload: dict, msg_id: int) -> RequestFrame:
    start_index = _u16(payload.get("start_index", payload.get("start", 0)), "start_index")
    body = _struct_module().pack("<HIII", start_index, 0, 0, 0)
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_PRICE_LIMITS, data=body)


def parse_price_limits_payload(
    response: ResponseFrame,
    request_payload: dict | None = None,
) -> tuple[PriceLimitRecord, ...]:
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid price limit payload")
    binary = _binary()
    count = binary.little_u16(payload[:2])
    expected_length = 2 + count * PRICE_LIMIT_RECORD_SIZE
    if len(payload) != expected_length:
        raise _protocol_error()(f"invalid price limit payload length: expected {expected_length}, got {len(payload)}")

    price_limit_record = _price_limit_record_cls()
    records: list[PriceLimitRecord] = []
    offset = 2
    for _ in range(count):
        record = payload[offset : offset + PRICE_LIMIT_RECORD_SIZE]
        offset += PRICE_LIMIT_RECORD_SIZE
        market_id = record[0]
        exchange = ID_TO_MARKET.get(market_id)
        if exchange is None:
            raise _protocol_error()(f"invalid price limit market id: {market_id!r}")
        code_num = binary.little_u32(record[1:5])
        records.append(
            price_limit_record(
                exchange=exchange,
                market_id=market_id,
                code=f"{code_num:06d}",
                code_num=code_num,
                limit_up_price=float(binary.little_f32(record[5:9])),
                limit_down_price=float(binary.little_f32(record[9:13])),
                record_hex=record.hex(),
            )
        )
    return tuple(records)


def _u16(value, name: str) -> int:
    number = int(value)
    if number < 0 or number > 0xFFFF:
        raise ValueError(f"{name} must be between 0 and 65535")
    return number


def __getattr__(name: str):
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    if name in _MODEL_EXPORTS:
        value = getattr(import_module(_MODEL_MODULE), name)
        globals()[name] = value
        return value
    if name in _BINARY_EXPORTS:
        value = getattr(import_module(_BINARY_MODULE), name)
        globals()[name] = value
        return value
    if name == "struct":
        return _struct_module()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _MODEL_EXPORTS | _BINARY_EXPORTS | _STDLIB_EXPORTS)
