"""Trade-detail command builders and parsers."""

from __future__ import annotations

from datetime import datetime, time
from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._code_utils import split_code
from axdata_source_tdx._tdx_wire._command_layouts import SIDE_MAP

from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_HISTORICAL_TRADES = command_code("historical_trades")
TYPE_TODAY_TRADES = command_code("today_trades")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.trade"
_TIME_UTILS_MODULE = "axdata_source_tdx._tdx_wire._time_utils"
_BINARY_EXPORTS = {
    "consume_tdx_signed_varint",
    "consume_tdx_varint",
    "date_from_yyyymmdd",
    "little_f32",
    "little_u16",
    "yyyymmdd",
}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"TradeDetailRecord", "TradeDetailSeries"}
_TIME_EXPORTS = {"SHANGHAI_TZ"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _consume_tdx_signed_varint(payload: bytes, offset: int) -> tuple[int, int]:
    return _binary().consume_tdx_signed_varint(payload, offset)


def _consume_tdx_varint(payload: bytes, offset: int) -> tuple[int, int]:
    return _binary().consume_tdx_varint(payload, offset)


def _date_from_yyyymmdd(raw: int):
    return _binary().date_from_yyyymmdd(raw)


def _little_f32(data: bytes) -> float:
    return _binary().little_f32(data)


def _little_u16(data: bytes) -> int:
    return _binary().little_u16(data)


def _yyyymmdd(value) -> int:
    return _binary().yyyymmdd(value)


def _trade_detail_record_cls():
    return import_module(_MODEL_MODULE).TradeDetailRecord


def _trade_detail_series_cls():
    return import_module(_MODEL_MODULE).TradeDetailSeries


def _shanghai_tz():
    return import_module(_TIME_UTILS_MODULE).SHANGHAI_TZ


def build_today_trades_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    start = normalize_trade_start(payload.get("start", 0))
    count = normalize_trade_count(payload.get("count", 115))
    data = (
        market_id.to_bytes(1, "little", signed=False)
        + b"\x00"
        + number.encode("ascii")
        + start.to_bytes(2, "little", signed=False)
        + count.to_bytes(2, "little", signed=False)
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_TODAY_TRADES, data=data)


def build_historical_trades_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    trade_date_raw = historical_trade_date(payload)
    start = normalize_trade_start(payload.get("start", 0))
    count = normalize_trade_count(payload.get("count", 900))
    data = (
        trade_date_raw.to_bytes(4, "little", signed=False)
        + market_id.to_bytes(2, "little", signed=False)
        + number.encode("ascii")
        + start.to_bytes(2, "little", signed=False)
        + count.to_bytes(2, "little", signed=False)
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_HISTORICAL_TRADES, data=data)


def parse_today_trades_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> TradeDetailSeries:
    request_payload = request_payload or {}
    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    start = normalize_trade_start(request_payload.get("start", 0))
    count = normalize_trade_count(request_payload.get("count", 115))
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid today trades payload")

    record_count = _little_u16(payload[:2])
    records = parse_trade_records(payload, offset=2, record_count=record_count, start=start, trade_date_raw=None)
    return _trade_detail_series_cls()(
        exchange=exchange,
        market_id=market_id,
        code=number,
        start=start,
        request_count=count,
        records=tuple(records),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def parse_historical_trades_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> TradeDetailSeries:
    request_payload = request_payload or {}
    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    trade_date_raw = historical_trade_date(request_payload)
    trade_date = _date_from_yyyymmdd(trade_date_raw)
    if trade_date is None:
        raise _protocol_error()(f"invalid historical trades trade_date: {trade_date_raw}")
    start = normalize_trade_start(request_payload.get("start", 0))
    count = normalize_trade_count(request_payload.get("count", 900))
    payload = response.data
    if len(payload) < 6:
        raise _protocol_error()("invalid historical trades payload")

    record_count = _little_u16(payload[:2])
    price_base_raw_f32 = float(_little_f32(payload[2:6]))
    records = parse_trade_records(payload, offset=6, record_count=record_count, start=start, trade_date_raw=trade_date_raw)
    return _trade_detail_series_cls()(
        exchange=exchange,
        market_id=market_id,
        code=number,
        start=start,
        request_count=count,
        records=tuple(records),
        trade_date=trade_date,
        price_base_raw_f32=price_base_raw_f32,
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def parse_trade_records(
    payload: bytes,
    *,
    offset: int,
    record_count: int,
    start: int,
    trade_date_raw: int | None,
) -> list[TradeDetailRecord]:
    trade_date = _date_from_yyyymmdd(trade_date_raw) if trade_date_raw is not None else None
    trade_detail_record = _trade_detail_record_cls()
    records: list[TradeDetailRecord] = []
    price_acc_raw = 0
    for index in range(record_count):
        record_start = offset
        if offset + 2 > len(payload):
            raise _protocol_error()("truncated trade time field")
        time_minutes = _little_u16(payload[offset : offset + 2])
        offset += 2
        price_delta_raw, offset = _consume_tdx_signed_varint(payload, offset)
        volume, offset = _consume_tdx_varint(payload, offset)
        order_count, offset = _consume_tdx_varint(payload, offset)
        status_raw, offset = _consume_tdx_varint(payload, offset)
        tail_raw, offset = _consume_tdx_varint(payload, offset)
        price_acc_raw += price_delta_raw
        trade_time = trade_time_from_minutes(time_minutes)
        trade_datetime = (
            datetime.combine(trade_date, trade_time, tzinfo=_shanghai_tz())
            if trade_date is not None
            else None
        )
        records.append(
            trade_detail_record(
                trade_time=trade_time,
                trade_datetime=trade_datetime,
                trade_date=trade_date,
                index=index,
                absolute_index=start + index,
                time_minutes=time_minutes,
                price=price_acc_raw / 10000.0,
                price_acc_raw=price_acc_raw,
                price_delta_raw=price_delta_raw,
                volume=volume,
                order_count=order_count,
                status_raw=status_raw,
                side=SIDE_MAP.get(status_raw, f"status_{status_raw}"),
                tail_raw=tail_raw,
                record_hex=payload[record_start:offset].hex(),
            )
        )

    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing trade payload bytes: {len(payload) - offset}")
    return records


def trade_time_from_minutes(time_minutes: int) -> time:
    if time_minutes < 0 or time_minutes >= 24 * 60:
        raise _protocol_error()(f"invalid trade time minutes: {time_minutes}")
    return time(time_minutes // 60, time_minutes % 60)


def historical_trade_date(payload: dict[str, Any]) -> int:
    value = payload.get("trade_date", payload.get("date"))
    if value in (None, "", 0, "0"):
        raise _protocol_error()("historical trades trade_date is required")
    return _yyyymmdd(value)


def normalize_trade_start(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise _protocol_error()("start must be an integer") from exc
    if parsed < 0 or parsed > 0xFFFF:
        raise _protocol_error()("start must be between 0 and 65535")
    return parsed


def normalize_trade_count(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise _protocol_error()("count must be an integer") from exc
    if parsed <= 0 or parsed > 0xFFFF:
        raise _protocol_error()("count must be between 1 and 65535")
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
    if name in _TIME_EXPORTS:
        value = getattr(import_module(_TIME_UTILS_MODULE), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _MODEL_EXPORTS | _BINARY_EXPORTS | _TIME_EXPORTS)
