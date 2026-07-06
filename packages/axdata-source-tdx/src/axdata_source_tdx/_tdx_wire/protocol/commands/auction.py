"""Call-auction process command builder and parser."""

from __future__ import annotations

from datetime import time
from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._code_utils import split_code
from axdata_source_tdx._tdx_wire._command_defaults import DEFAULT_AUCTION_COUNT, DEFAULT_AUCTION_MODE
from axdata_source_tdx._tdx_wire._command_layouts import AUCTION_RECORD_SIZE

from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_AUCTION_PROCESS = command_code("auction_process")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.auction"
_BINARY_EXPORTS = {"little_f32", "little_u16", "little_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"AuctionProcessRecord", "AuctionProcessSeries"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _auction_process_record_cls():
    return import_module(_MODEL_MODULE).AuctionProcessRecord


def _auction_process_series_cls():
    return import_module(_MODEL_MODULE).AuctionProcessSeries


def build_auction_process_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    mode_or_selector_raw = normalize_auction_u32(payload.get("mode_or_selector_raw", DEFAULT_AUCTION_MODE), "mode")
    start = normalize_auction_u32(payload.get("start", 0), "start")
    count = normalize_auction_u32(payload.get("count", DEFAULT_AUCTION_COUNT), "count")
    data = (
        market_id.to_bytes(1, "little", signed=False)
        + b"\x00"
        + number.encode("ascii")
        + (0).to_bytes(4, "little", signed=False)
        + mode_or_selector_raw.to_bytes(4, "little", signed=False)
        + (0).to_bytes(4, "little", signed=False)
        + start.to_bytes(4, "little", signed=False)
        + count.to_bytes(4, "little", signed=False)
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_AUCTION_PROCESS, data=data)


def parse_auction_process_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> AuctionProcessSeries:
    request_payload = request_payload or {}
    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    mode_or_selector_raw = normalize_auction_u32(
        request_payload.get("mode_or_selector_raw", DEFAULT_AUCTION_MODE),
        "mode",
    )
    start = normalize_auction_u32(request_payload.get("start", 0), "start")
    count = normalize_auction_u32(request_payload.get("count", DEFAULT_AUCTION_COUNT), "count")
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid auction process payload")

    binary = _binary()
    record_count = binary.little_u16(payload[:2])
    expected_length = 2 + record_count * AUCTION_RECORD_SIZE
    if len(payload) != expected_length:
        raise _protocol_error()(
            f"invalid auction process payload length: expected {expected_length}, got {len(payload)}"
        )

    auction_process_record = _auction_process_record_cls()
    records: list[AuctionProcessRecord] = []
    offset = 2
    for index in range(record_count):
        record = payload[offset : offset + AUCTION_RECORD_SIZE]
        minute_of_day_raw = binary.little_u16(record[0:2])
        price = float(binary.little_f32(record[2:6]))
        matched_volume = binary.little_u32(record[6:10])
        unmatched_signed_raw = int.from_bytes(record[10:14], "little", signed=True)
        reserved_zero_0e = record[14]
        second_raw = record[15]
        unmatched_direction = 0
        if unmatched_signed_raw > 0:
            unmatched_direction = 1
        elif unmatched_signed_raw < 0:
            unmatched_direction = -1
        records.append(
            auction_process_record(
                index=start + index,
                auction_time=auction_time_from_raw(minute_of_day_raw, second_raw),
                minute_of_day_raw=minute_of_day_raw,
                second_raw=second_raw,
                price=price,
                price_milli=round(price * 1000),
                matched_volume=matched_volume,
                unmatched_signed_raw=unmatched_signed_raw,
                unmatched_volume=abs(unmatched_signed_raw),
                unmatched_direction=unmatched_direction,
                reserved_zero_0e=reserved_zero_0e,
                record_hex=record.hex(),
            )
        )
        offset += AUCTION_RECORD_SIZE

    return _auction_process_series_cls()(
        exchange=exchange,
        market_id=market_id,
        code=number,
        mode_or_selector_raw=mode_or_selector_raw,
        start=start,
        request_count=count,
        records=tuple(records),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def auction_time_from_raw(minute_of_day_raw: int, second_raw: int) -> time:
    if minute_of_day_raw < 0 or minute_of_day_raw >= 24 * 60:
        raise _protocol_error()(f"invalid auction minute: {minute_of_day_raw}")
    if second_raw < 0 or second_raw >= 60:
        raise _protocol_error()(f"invalid auction second: {second_raw}")
    return time(minute_of_day_raw // 60, minute_of_day_raw % 60, second_raw)


def normalize_auction_u32(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise _protocol_error()(f"{name} must be an integer") from exc
    if parsed < 0 or parsed > 0xFFFFFFFF:
        raise _protocol_error()(f"{name} must be between 0 and 4294967295")
    return parsed


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
