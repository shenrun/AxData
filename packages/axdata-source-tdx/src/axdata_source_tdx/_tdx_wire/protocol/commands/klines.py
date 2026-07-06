"""K-line command builder and parser."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._code_utils import normalize_code as _normalize_code, split_code as _split_code
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_KLINES = command_code("klines")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.kline"
_TIME_UTILS_MODULE = "axdata_source_tdx._tdx_wire._time_utils"
_BINARY_EXPORTS = {
    "consume_tdx_signed_varint",
    "date_from_yyyymmdd",
    "little_u16",
    "little_u32",
    "yyyymmdd",
}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"KlineBar", "KlineSeries"}
_TIME_EXPORTS = {"SHANGHAI_TZ"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _consume_tdx_signed_varint(payload: bytes, offset: int) -> tuple[int, int]:
    return _binary().consume_tdx_signed_varint(payload, offset)


def _date_from_yyyymmdd(raw: int):
    return _binary().date_from_yyyymmdd(raw)


def _decode_compact_float(value: int) -> float:
    return _binary().decode_compact_float(value)


def _little_u16(data: bytes) -> int:
    return _binary().little_u16(data)


def _little_u32(data: bytes) -> int:
    return _binary().little_u32(data)


def _yyyymmdd(value) -> int:
    return _binary().yyyymmdd(value)


def _kline_bar_cls():
    return import_module(_MODEL_MODULE).KlineBar


def _kline_series_cls():
    return import_module(_MODEL_MODULE).KlineSeries


def _shanghai_tz():
    return import_module(_TIME_UTILS_MODULE).SHANGHAI_TZ

PERIOD_ALIASES: dict[str, tuple[int, int]] = {
    "5m": (0, 1),
    "5min": (0, 1),
    "15m": (1, 1),
    "15min": (1, 1),
    "30m": (2, 1),
    "30min": (2, 1),
    "60m": (3, 1),
    "60min": (3, 1),
    "1h": (3, 1),
    "hour": (3, 1),
    "day": (4, 1),
    "1d": (4, 1),
    "d": (4, 1),
    "daily": (4, 1),
    "week": (5, 1),
    "1w": (5, 1),
    "w": (5, 1),
    "month": (6, 1),
    "1mo": (6, 1),
    "mo": (6, 1),
    "1m": (7, 1),
    "1min": (7, 1),
    "minute": (7, 1),
    "quarter": (10, 1),
    "1q": (10, 1),
    "q": (10, 1),
    "year": (11, 1),
    "1y": (11, 1),
    "y": (11, 1),
}

ADJUST_TO_RAW = {
    None: 0,
    "none": 0,
    "": 0,
    "qfq": 1,
    "front": 1,
    "hfq": 2,
    "back": 2,
    "fixed_qfq": 3,
    "fixed_front": 3,
    "fixed_hfq": 4,
    "fixed_back": 4,
}
RAW_TO_ADJUST = {0: "none", 1: "qfq", 2: "hfq", 3: "fixed_qfq", 4: "fixed_hfq"}


def build_klines_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    period_raw, period_param_raw = normalize_period(payload.get("period", "day"))
    start = int(payload.get("start", 0))
    count = int(payload.get("count", 800))
    if start < 0 or start > 0xFFFF:
        raise ValueError("start must be between 0 and 65535")
    if count <= 0 or count > 0xFFFF:
        raise ValueError("count must be between 1 and 65535")

    adjust_mode_raw = normalize_adjust(payload.get("adjust"))
    anchor_date_raw = normalize_anchor_date(payload.get("anchor_date", payload.get("anchor_date_raw", 0)))
    data = (
        market_id.to_bytes(2, "little", signed=False)
        + number.encode("ascii")
        + period_raw.to_bytes(2, "little", signed=False)
        + period_param_raw.to_bytes(2, "little", signed=False)
        + start.to_bytes(2, "little", signed=False)
        + count.to_bytes(2, "little", signed=False)
        + adjust_mode_raw.to_bytes(2, "little", signed=False)
        + anchor_date_raw.to_bytes(4, "little", signed=False)
        + b"\x00" * 20
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_KLINES, data=data)


def parse_klines_payload(response: ResponseFrame, request_payload: dict[str, Any] | None = None) -> KlineSeries:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid klines payload")

    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    period_raw, period_param_raw = normalize_period(request_payload.get("period", "day"))
    start = int(request_payload.get("start", 0))
    request_count = int(request_payload.get("count", 800))
    adjust_mode_raw = normalize_adjust(request_payload.get("adjust"))
    anchor_date_raw = normalize_anchor_date(request_payload.get("anchor_date", request_payload.get("anchor_date_raw", 0)))
    kind = str(request_payload.get("kind", "stock")).lower()
    index_mode = kind == "index"

    count = _little_u16(payload[:2])
    offset = 2
    last_close_milli = 0
    kline_bar = _kline_bar_cls()
    bars: list[KlineBar] = []
    for _ in range(count):
        record_start = offset
        if offset + 4 > len(payload):
            raise _protocol_error()("truncated kline time field")
        item_time = decode_kline_datetime(payload[offset : offset + 4], period_raw)
        offset += 4

        open_delta, offset = consume_varint(payload, offset)
        close_delta, offset = consume_varint(payload, offset)
        high_delta, offset = consume_varint(payload, offset)
        low_delta, offset = consume_varint(payload, offset)

        item_last_close = last_close_milli if bars else None
        open_milli = last_close_milli + open_delta
        close_milli = open_milli + close_delta
        high_milli = open_milli + high_delta
        low_milli = open_milli + low_delta
        last_close_milli = close_milli

        if offset + 8 > len(payload):
            raise _protocol_error()("truncated kline volume or amount field")
        volume_raw = _little_u32(payload[offset : offset + 4])
        volume_wire_value = decode_compact_float(volume_raw)
        offset += 4
        amount_raw = _little_u32(payload[offset : offset + 4])
        amount = decode_compact_float(amount_raw)
        offset += 4

        up_count = None
        down_count = None
        if index_mode:
            if offset + 4 > len(payload):
                raise _protocol_error()("truncated kline index breadth field")
            up_count = _little_u16(payload[offset : offset + 2])
            down_count = _little_u16(payload[offset + 2 : offset + 4])
            offset += 4

        bars.append(
            kline_bar(
                time=item_time,
                open=milli_to_float(open_milli),
                close=milli_to_float(close_milli),
                high=milli_to_float(high_milli),
                low=milli_to_float(low_milli),
                open_price_milli=open_milli,
                close_price_milli=close_milli,
                high_price_milli=high_milli,
                low_price_milli=low_milli,
                last_close_price_milli=item_last_close,
                volume_raw=volume_raw,
                amount_raw=amount_raw,
                volume_wire_value=volume_wire_value,
                volume_lots=volume_wire_value / 100.0,
                amount=amount,
                open_delta_raw=open_delta,
                close_delta_raw=close_delta,
                high_delta_raw=high_delta,
                low_delta_raw=low_delta,
                up_count=up_count,
                down_count=down_count,
                record_hex=payload[record_start:offset].hex(),
            )
        )

    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing kline payload bytes: {len(payload) - offset}")

    return _kline_series_cls()(
        exchange=exchange,
        market_id=market_id,
        code=number,
        period_raw=period_raw,
        period_param_raw=period_param_raw,
        period_name=period_name(period_raw, period_param_raw),
        start=start,
        request_count=request_count,
        adjust_mode_raw=adjust_mode_raw,
        adjust_mode=RAW_TO_ADJUST.get(adjust_mode_raw, f"unknown_{adjust_mode_raw}"),
        anchor_date_raw=anchor_date_raw,
        anchor_date=None if anchor_date_raw == 0 else _date_from_yyyymmdd(anchor_date_raw),
        bars=tuple(bars),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def normalize_period(value: Any) -> tuple[int, int]:
    if isinstance(value, tuple) and len(value) == 2:
        return int(value[0]), int(value[1])
    key = str(value).strip().lower()
    if key in PERIOD_ALIASES:
        return PERIOD_ALIASES[key]

    match = re.fullmatch(r"(\d+)(m|min|d|s)", key)
    if not match:
        raise _protocol_error()(f"invalid kline period: {value!r}")
    number = int(match.group(1))
    unit = match.group(2)
    if unit in {"m", "min"}:
        if number == 1:
            return 7, 1
        if number in {5, 15, 30, 60}:
            return PERIOD_ALIASES[f"{number}m"]
        return 8, number
    if unit == "d":
        if number == 1:
            return 4, 1
        return 9, number
    if unit == "s":
        return 13, number
    raise _protocol_error()(f"invalid kline period: {value!r}")


def period_name(period_raw: int, period_param_raw: int) -> str:
    names = {
        (0, 1): "5m",
        (1, 1): "15m",
        (2, 1): "30m",
        (3, 1): "60m",
        (4, 1): "day",
        (5, 1): "week",
        (6, 1): "month",
        (7, 1): "1m",
        (10, 1): "quarter",
        (11, 1): "year",
    }
    if (period_raw, period_param_raw) in names:
        return names[(period_raw, period_param_raw)]
    if period_raw == 8:
        return f"{period_param_raw}m"
    if period_raw == 9:
        return f"{period_param_raw}d"
    if period_raw == 13:
        return f"{period_param_raw}s"
    return f"{period_raw}/{period_param_raw}"


def normalize_adjust(value: Any) -> int:
    if isinstance(value, int):
        return value
    key = None if value is None else str(value).strip().lower()
    try:
        return ADJUST_TO_RAW[key]
    except KeyError as exc:
        raise _protocol_error()(f"invalid adjust mode: {value!r}") from exc


def normalize_anchor_date(value: Any) -> int:
    if value in (None, "", 0):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, (date, datetime)):
        return _yyyymmdd(value)
    return _yyyymmdd(str(value))


def split_code(code: str) -> tuple[int, str, str]:
    return _split_code(code)


def normalize_code(code: str) -> str:
    return _normalize_code(code)


def consume_varint(payload: bytes, offset: int) -> tuple[int, int]:
    return _consume_tdx_signed_varint(payload, offset)


def decode_kline_datetime(raw_value: bytes, period_raw: int) -> datetime:
    if len(raw_value) != 4:
        raise _protocol_error()("invalid kline time length")

    if period_raw in {0, 1, 2, 3, 7, 8}:
        date_packed = _little_u16(raw_value[:2])
        minute_of_day = _little_u16(raw_value[2:4])
        year = (date_packed >> 11) + 2004
        month = (date_packed % 2048) // 100
        day = (date_packed % 2048) % 100
        return datetime(
            year,
            month,
            day,
            minute_of_day // 60,
            minute_of_day % 60,
            tzinfo=_shanghai_tz(),
        )

    if period_raw == 13:
        epoch = datetime(2003, 12, 31, tzinfo=_shanghai_tz())
        return epoch + timedelta(seconds=_little_u32(raw_value))

    raw_date = _little_u32(raw_value)
    parsed = _date_from_yyyymmdd(raw_date)
    if parsed is None:
        raise _protocol_error()(f"invalid kline date: {raw_date}")
    return datetime(parsed.year, parsed.month, parsed.day, 15, 0, tzinfo=_shanghai_tz())


def decode_compact_float(value: int) -> float:
    return _decode_compact_float(value)


def milli_to_float(value: int) -> float:
    return value / 1000.0


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
