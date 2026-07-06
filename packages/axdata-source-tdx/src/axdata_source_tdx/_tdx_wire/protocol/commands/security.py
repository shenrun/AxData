"""Security code table command builders and parsers."""

from __future__ import annotations

from importlib import import_module

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._market import market_to_id, normalize_market
from axdata_source_tdx._tdx_wire._command_layouts import (
    CODE_RECORD_SIZE,
    ETF_PREFIXES,
    FUND_PREFIXES,
    INDEX_PREFIXES,
    SSE_A_SHARE_PREFIXES,
    SZSE_A_SHARE_PREFIXES,
)
from axdata_source_tdx._tdx_wire._security_classification import (
    classify_board,
    classify_security,
)
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_SECURITY_COUNT = command_code("security_count")
TYPE_SECURITY_LIST = command_code("security_list")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.security"
_BINARY_EXPORTS = {"decode_gbk_text", "little_f32", "little_u16", "yyyymmdd"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"SecurityCode"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _decode_gbk_text(data: bytes) -> str:
    return _binary().decode_gbk_text(data)


def _little_f32(data: bytes) -> float:
    return _binary().little_f32(data)


def _little_u16(data: bytes) -> int:
    return _binary().little_u16(data)


def _yyyymmdd(value) -> int:
    return _binary().yyyymmdd(value)


def _security_code_cls():
    return import_module(_MODEL_MODULE).SecurityCode


def build_security_count_frame(payload: dict, msg_id: int) -> RequestFrame:
    market_id = market_to_id(payload.get("market", payload.get("market_id", "sz")))
    client_date = _yyyymmdd(payload.get("client_date_yyyymmdd", payload.get("client_date")))
    data = market_id.to_bytes(2, "little", signed=False) + client_date.to_bytes(4, "little", signed=False)
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_SECURITY_COUNT, data=data)


def parse_security_count_payload(response: ResponseFrame) -> int:
    if len(response.data) < 2:
        raise _protocol_error()("invalid security count payload")
    return _little_u16(response.data[:2])


def build_security_list_frame(payload: dict, msg_id: int) -> RequestFrame:
    start = int(payload.get("start", 0))
    limit = int(payload.get("limit", 1600))
    if start < 0 or start > 0xFFFFFFFF:
        raise ValueError("start must be between 0 and 4294967295")
    if limit < 0 or limit > 0xFFFFFFFF:
        raise ValueError("limit must be between 0 and 4294967295")

    market_id = market_to_id(payload.get("market", payload.get("market_id", "sz")))
    data = (
        market_id.to_bytes(2, "little", signed=False)
        + start.to_bytes(4, "little", signed=False)
        + limit.to_bytes(4, "little", signed=False)
        + b"\x00" * 4
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_SECURITY_LIST, data=data)


def parse_security_list_payload(response: ResponseFrame, request_payload: dict | None = None) -> list[SecurityCode]:
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid security list payload")

    request_payload = request_payload or {}
    exchange = normalize_market(request_payload.get("market", request_payload.get("market_id", "sz")))
    market_id = market_to_id(exchange)
    count = _little_u16(payload[:2])
    expected_length = 2 + count * CODE_RECORD_SIZE
    if len(payload) < expected_length:
        raise _protocol_error()("truncated security list payload")

    security_code = _security_code_cls()
    items: list[SecurityCode] = []
    offset = 2
    for _ in range(count):
        record = payload[offset : offset + CODE_RECORD_SIZE]
        offset += CODE_RECORD_SIZE
        code = _decode_code(record[:6])
        unknown0_raw = record[24:28]
        previous_close_raw = record[29:33]
        full_code = f"{exchange}{code}"
        category, category_reason = classify_security(full_code)
        board, board_reason = classify_board(full_code, category)
        items.append(
            security_code(
                exchange=exchange,
                market_id=market_id,
                code=code,
                name=_decode_gbk_text(record[8:24]),
                multiple=_little_u16(record[6:8]),
                decimal=record[28],
                previous_close_price=_little_f32(previous_close_raw),
                volume_ratio_base=_little_f32(unknown0_raw),
                unknown0_raw=unknown0_raw,
                previous_close_raw=previous_close_raw,
                unknown3_raw=record[33:37],
                category=category,
                category_reason=category_reason,
                board=board,
                board_reason=board_reason,
            )
        )
    return items


def _decode_code(data: bytes) -> str:
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid security code") from exc


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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _MODEL_EXPORTS | _BINARY_EXPORTS)
