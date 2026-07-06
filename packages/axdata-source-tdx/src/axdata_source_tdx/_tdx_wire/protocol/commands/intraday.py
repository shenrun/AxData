"""Today and historical intraday command builders and parsers."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._command_defaults import (
    DEFAULT_TODAY_INTRADAY_RESERVED_TAIL,
    RECENT_HISTORICAL_INTRADAY_DATE_BASE,
)
from axdata_source_tdx._tdx_wire._code_utils import split_code

from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_HISTORICAL_INTRADAY = command_code("historical_intraday")
TYPE_RECENT_HISTORICAL_INTRADAY = command_code("recent_historical_intraday")
TYPE_TODAY_INTRADAY = command_code("today_intraday")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.intraday"
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
_MODEL_EXPORTS = {
    "HistoricalIntradayPoint",
    "HistoricalIntradaySeries",
    "RecentHistoricalIntradayPoint",
    "RecentHistoricalIntradaySeries",
    "TodayIntradayPoint",
    "TodayIntradaySeries",
}
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


def _model_cls(name: str):
    return getattr(import_module(_MODEL_MODULE), name)


def _shanghai_tz():
    return import_module(_TIME_UTILS_MODULE).SHANGHAI_TZ


def build_today_intraday_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    reserved_tail = today_intraday_reserved_tail(payload.get("reserved_tail_raw"))
    data = market_id.to_bytes(2, "little", signed=False) + number.encode("ascii") + reserved_tail
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_TODAY_INTRADAY, data=data)


def build_historical_intraday_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    trade_date_raw = historical_intraday_trade_date(payload)
    data = (
        trade_date_raw.to_bytes(4, "little", signed=False)
        + market_id.to_bytes(1, "little", signed=False)
        + number.encode("ascii")
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_HISTORICAL_INTRADAY, data=data)


def build_recent_historical_intraday_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    date_selector_raw = recent_historical_intraday_date_selector(payload)
    data = (
        date_selector_raw.to_bytes(4, "little", signed=False)
        + market_id.to_bytes(1, "little", signed=False)
        + number.encode("ascii")
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_RECENT_HISTORICAL_INTRADAY, data=data)


def parse_today_intraday_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> TodayIntradaySeries:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 4:
        raise _protocol_error()("invalid today intraday payload")

    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    reserved_tail = today_intraday_reserved_tail(request_payload.get("reserved_tail_raw"))
    count = _little_u16(payload[:2])
    reserved_zero = _little_u16(payload[2:4])
    offset = 4
    first_price = None
    first_avg = None
    today_intraday_point = _model_cls("TodayIntradayPoint")
    points: list[TodayIntradayPoint] = []
    for minute_index in range(count):
        record_start = offset
        price_field, offset = _consume_tdx_signed_varint(payload, offset)
        avg_field, offset = _consume_tdx_signed_varint(payload, offset)
        volume, offset = _consume_tdx_signed_varint(payload, offset)
        if first_price is None:
            first_price = price_field
        if first_avg is None:
            first_avg = avg_field
        price_raw = price_field if minute_index == 0 else first_price + price_field
        avg_raw = avg_field if minute_index == 0 else first_avg + avg_field
        points.append(
            today_intraday_point(
                time_label=intraday_time_label(minute_index),
                minute_index=minute_index,
                price=price_raw / 100.0,
                avg_price=avg_raw / 10000.0,
                price_raw=price_raw,
                avg_raw=avg_raw,
                price_field=price_field,
                avg_field=avg_field,
                volume=volume,
                record_hex=payload[record_start:offset].hex(),
            )
        )

    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing today intraday payload bytes: {len(payload) - offset}")

    return _model_cls("TodayIntradaySeries")(
        exchange=exchange,
        market_id=market_id,
        code=number,
        reserved_tail_raw=reserved_tail,
        reserved_zero=reserved_zero,
        points=tuple(points),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def parse_historical_intraday_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> HistoricalIntradaySeries:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 6:
        raise _protocol_error()("invalid historical intraday payload")

    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    trade_date_raw = historical_intraday_trade_date(request_payload)
    trade_date = _date_from_yyyymmdd(trade_date_raw)
    if trade_date is None:
        raise _protocol_error()(f"invalid historical intraday trade_date: {trade_date_raw}")

    count = _little_u16(payload[:2])
    prev_close = float(_little_f32(payload[2:6]))
    offset = 6
    price_acc_raw = 0
    historical_intraday_point = _model_cls("HistoricalIntradayPoint")
    points: list[HistoricalIntradayPoint] = []
    for minute_index in range(count):
        record_start = offset
        price_delta_raw, offset = _consume_tdx_signed_varint(payload, offset)
        aux_delta_raw, offset = _consume_tdx_signed_varint(payload, offset)
        volume, offset = _consume_tdx_varint(payload, offset)
        price_acc_raw += price_delta_raw
        points.append(
            historical_intraday_point(
                time=historical_intraday_time(trade_date_raw, minute_index),
                trade_date=trade_date,
                minute_index=minute_index,
                price=price_acc_raw / 100.0,
                price_acc_raw=price_acc_raw,
                price_delta_raw=price_delta_raw,
                aux_delta_raw=aux_delta_raw,
                volume=volume,
                record_hex=payload[record_start:offset].hex(),
            )
        )

    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing historical intraday payload bytes: {len(payload) - offset}")

    return _model_cls("HistoricalIntradaySeries")(
        exchange=exchange,
        market_id=market_id,
        code=number,
        trade_date=trade_date,
        prev_close=prev_close,
        points=tuple(points),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def parse_recent_historical_intraday_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> RecentHistoricalIntradaySeries:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 10:
        raise _protocol_error()("invalid recent historical intraday payload")

    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    date_selector_raw = recent_historical_intraday_date_selector(request_payload)
    trade_date = recent_historical_intraday_trade_date_from_selector(date_selector_raw)

    count = _little_u16(payload[:2])
    prev_close = float(_little_f32(payload[2:6]))
    open_price = float(_little_f32(payload[6:10]))
    offset = 10
    first_price = None
    first_avg = None
    recent_historical_intraday_point = _model_cls("RecentHistoricalIntradayPoint")
    points: list[RecentHistoricalIntradayPoint] = []
    for minute_index in range(count):
        record_start = offset
        price_field, offset = _consume_tdx_signed_varint(payload, offset)
        avg_field, offset = _consume_tdx_signed_varint(payload, offset)
        volume, offset = _consume_tdx_signed_varint(payload, offset)
        if first_price is None:
            first_price = price_field
        if first_avg is None:
            first_avg = avg_field
        price_raw = price_field if minute_index == 0 else first_price + price_field
        avg_raw = avg_field if minute_index == 0 else first_avg + avg_field
        points.append(
            recent_historical_intraday_point(
                time=historical_intraday_time(_yyyymmdd(trade_date), minute_index),
                trade_date=trade_date,
                time_label=intraday_time_label(minute_index),
                minute_index=minute_index,
                price=price_raw / 100.0,
                avg_price=avg_raw / 10000.0,
                price_raw=price_raw,
                avg_raw=avg_raw,
                price_field=price_field,
                avg_field=avg_field,
                volume=volume,
                record_hex=payload[record_start:offset].hex(),
            )
        )

    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing recent historical intraday payload bytes: {len(payload) - offset}")

    return _model_cls("RecentHistoricalIntradaySeries")(
        exchange=exchange,
        market_id=market_id,
        code=number,
        trade_date=trade_date,
        date_selector_raw=date_selector_raw,
        prev_close=prev_close,
        open_price=open_price,
        points=tuple(points),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def historical_intraday_trade_date(payload: dict[str, Any]) -> int:
    value = payload.get("trade_date", payload.get("date"))
    if value in (None, "", 0, "0"):
        raise _protocol_error()("historical intraday trade_date is required")
    return _yyyymmdd(value)


def recent_historical_intraday_date_selector(payload: dict[str, Any]) -> int:
    value = payload.get("trade_date", payload.get("date"))
    if value in (None, "", 0, "0"):
        raise _protocol_error()("recent historical intraday trade_date is required")
    trade_date = _date_from_yyyymmdd(_yyyymmdd(value))
    if trade_date is None:
        raise _protocol_error()(f"invalid recent historical intraday trade_date: {value}")
    return RECENT_HISTORICAL_INTRADAY_DATE_BASE - trade_date.toordinal()


def recent_historical_intraday_trade_date_from_selector(date_selector_raw: int) -> date:
    try:
        return date.fromordinal(RECENT_HISTORICAL_INTRADAY_DATE_BASE - int(date_selector_raw))
    except ValueError as exc:
        raise _protocol_error()(f"invalid recent historical intraday date selector: {date_selector_raw}") from exc


def historical_intraday_time(trade_date_raw: int, minute_index: int) -> datetime:
    trade_date = _date_from_yyyymmdd(trade_date_raw)
    if trade_date is None:
        raise _protocol_error()(f"invalid historical intraday trade_date: {trade_date_raw}")

    if minute_index < 0:
        raise _protocol_error()(f"invalid historical intraday minute index: {minute_index}")
    if minute_index < 120:
        minute_time = datetime.combine(trade_date, time(9, 30), tzinfo=_shanghai_tz())
        return minute_time + timedelta(minutes=minute_index + 1)
    minute_time = datetime.combine(trade_date, time(13, 0), tzinfo=_shanghai_tz())
    return minute_time + timedelta(minutes=minute_index - 119)


def intraday_time_label(minute_index: int) -> str:
    if minute_index < 0:
        raise _protocol_error()(f"invalid intraday minute index: {minute_index}")
    if minute_index < 120:
        minute_time = datetime(2000, 1, 1, 9, 30) + timedelta(minutes=minute_index + 1)
    else:
        minute_time = datetime(2000, 1, 1, 13, 0) + timedelta(minutes=minute_index - 119)
    return minute_time.strftime("%H:%M")


def today_intraday_reserved_tail(value: Any) -> bytes:
    if value in (None, ""):
        return DEFAULT_TODAY_INTRADAY_RESERVED_TAIL
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, bytearray):
        raw = bytes(value)
    else:
        text = str(value).strip().lower().replace("0x", "").replace(" ", "")
        try:
            raw = bytes.fromhex(text)
        except ValueError as exc:
            raise _protocol_error()("today intraday reserved_tail_raw must be 4 hex bytes") from exc
    if len(raw) != 4:
        raise _protocol_error()("today intraday reserved_tail_raw must be 4 bytes")
    return raw


def __getattr__(name: str) -> Any:
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    if name in _MODEL_EXPORTS:
        value = _model_cls(name)
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
