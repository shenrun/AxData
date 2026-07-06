"""Corporate action command builders and parsers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._market import ID_TO_MARKET
from axdata_source_tdx._tdx_wire._code_utils import normalize_code as _normalize_code, split_code as _split_code
from axdata_source_tdx._tdx_wire._command_layouts import (
    CAPITAL_CHANGE_CATEGORY_NAMES,
    CAPITAL_CHANGE_RECORD_SIZE,
)
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_CAPITAL_CHANGES = command_code("capital_changes")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.corporate"
_BINARY_EXPORTS = {"date_from_yyyymmdd", "little_f32", "little_u16", "little_u32", "tdx_quantity_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"CapitalChangeBlock", "CapitalChangeRecord"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _capital_change_block_cls():
    return import_module(_MODEL_MODULE).CapitalChangeBlock


def _capital_change_record_cls():
    return import_module(_MODEL_MODULE).CapitalChangeRecord


def build_capital_changes_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    data = b"\x01\x00" + bytes([market_id]) + number.encode("ascii")
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_CAPITAL_CHANGES, data=data)


def parse_capital_changes_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> CapitalChangeBlock:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 11:
        raise _protocol_error()("invalid capital changes payload")

    binary = _binary()
    block_count = binary.little_u16(payload[:2])
    market_id = payload[2]
    exchange = ID_TO_MARKET.get(market_id, "unknown")
    try:
        code = payload[3:9].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid capital changes code") from exc
    record_count = binary.little_u16(payload[9:11])
    expected_length = 11 + record_count * CAPITAL_CHANGE_RECORD_SIZE
    if len(payload) < expected_length:
        raise _protocol_error()("truncated capital changes payload")

    records: list[CapitalChangeRecord] = []
    offset = 11
    for _ in range(record_count):
        record = payload[offset : offset + CAPITAL_CHANGE_RECORD_SIZE]
        offset += CAPITAL_CHANGE_RECORD_SIZE
        records.append(_parse_capital_change_record(record))
    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing capital changes payload bytes: {len(payload) - offset}")

    return _capital_change_block_cls()(
        exchange=exchange,
        market_id=market_id,
        code=code,
        block_count=block_count,
        records=tuple(records),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def _parse_capital_change_record(record: bytes) -> CapitalChangeRecord:
    if len(record) != CAPITAL_CHANGE_RECORD_SIZE:
        raise _protocol_error()("invalid capital change record length")
    market_id = record[0]
    exchange = ID_TO_MARKET.get(market_id, "unknown")
    try:
        code = record[1:7].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid capital changes record code") from exc
    binary = _binary()
    date_raw = binary.little_u32(record[8:12])
    category_raw = record[12]
    c1_raw = record[13:17]
    c2_raw = record[17:21]
    c3_raw = record[21:25]
    c4_raw = record[25:29]
    c1_float = binary.little_f32(c1_raw)
    c2_float = binary.little_f32(c2_raw)
    c3_float = binary.little_f32(c3_raw)
    c4_float = binary.little_f32(c4_raw)
    c1_quantity = binary.tdx_quantity_u32(c1_raw)
    c2_quantity = binary.tdx_quantity_u32(c2_raw)
    c3_quantity = binary.tdx_quantity_u32(c3_raw)
    c4_quantity = binary.tdx_quantity_u32(c4_raw)
    return _capital_change_record_cls()(
        exchange=exchange,
        market_id=market_id,
        code=code,
        reserved_7=record[7],
        date_raw=date_raw,
        date=binary.date_from_yyyymmdd(date_raw),
        category_raw=category_raw,
        category_name=CAPITAL_CHANGE_CATEGORY_NAMES.get(category_raw),
        c1_raw=c1_raw,
        c2_raw=c2_raw,
        c3_raw=c3_raw,
        c4_raw=c4_raw,
        c1_float=c1_float,
        c2_float=c2_float,
        c3_float=c3_float,
        c4_float=c4_float,
        c1_quantity=c1_quantity,
        c2_quantity=c2_quantity,
        c3_quantity=c3_quantity,
        c4_quantity=c4_quantity,
        record_hex=record.hex(),
    )


def split_code(code: str) -> tuple[int, str, str]:
    return _split_code(code)


def normalize_code(code: str) -> str:
    return _normalize_code(code)


def __getattr__(name: str) -> Any:
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _MODEL_EXPORTS | _BINARY_EXPORTS)
