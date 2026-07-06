"""Intraday subchart command builder and parser."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._code_utils import split_code
from axdata_source_tdx._tdx_wire._command_layouts import (
    INTRADAY_SUBCHART_BUY_SELL_STRENGTH,
    INTRADAY_SUBCHART_SELECTOR_NAMES,
    INTRADAY_SUBCHART_VOLUME_COMPARISON,
)

from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_INTRADAY_SUBCHART = command_code("intraday_subchart")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.subchart"
_BINARY_EXPORTS = {"consume_tdx_signed_varint", "little_f32", "little_u16"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"IntradaySubchartPoint", "IntradaySubchartSeries"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _intraday_subchart_point_cls():
    return import_module(_MODEL_MODULE).IntradaySubchartPoint


def _intraday_subchart_series_cls():
    return import_module(_MODEL_MODULE).IntradaySubchartSeries


def build_intraday_subchart_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    market_id, _, number = split_code(payload["code"])
    selector = normalize_intraday_subchart_selector(payload.get("selector", 0))
    data = (
        market_id.to_bytes(2, "little", signed=False)
        + number.encode("ascii")
        + (b"\x00" * 19)
        + selector.to_bytes(1, "little", signed=False)
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_INTRADAY_SUBCHART, data=data)


def parse_intraday_subchart_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> IntradaySubchartSeries:
    request_payload = request_payload or {}
    requested_code = request_payload.get("code", "sz000001")
    market_id, exchange, number = split_code(requested_code)
    selector = normalize_intraday_subchart_selector(request_payload.get("selector", 0))
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid intraday subchart payload")

    count = _binary().little_u16(payload[:2])
    if selector == INTRADAY_SUBCHART_VOLUME_COMPARISON:
        points = _parse_volume_comparison_points(payload, count=count)
    else:
        points = _parse_buy_sell_strength_points(payload, count=count)

    return _intraday_subchart_series_cls()(
        exchange=exchange,
        market_id=market_id,
        code=number,
        selector_raw=selector,
        selector_name=INTRADAY_SUBCHART_SELECTOR_NAMES.get(selector, f"selector_{selector}"),
        points=tuple(points),
        raw_payload=payload if request_payload.get("include_raw") else b"",
    )


def _parse_buy_sell_strength_points(payload: bytes, *, count: int) -> list[IntradaySubchartPoint]:
    offset = 2
    intraday_subchart_point = _intraday_subchart_point_cls()
    points: list[IntradaySubchartPoint] = []
    binary = _binary()
    for index in range(count):
        record_start = offset
        bid_order, offset = binary.consume_tdx_signed_varint(payload, offset)
        ask_order, offset = binary.consume_tdx_signed_varint(payload, offset)
        points.append(
            intraday_subchart_point(
                index=index,
                bid_order=bid_order,
                ask_order=ask_order,
                series_a_varint=bid_order,
                series_b_varint=ask_order,
                record_hex=payload[record_start:offset].hex(),
            )
        )
    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing intraday subchart payload bytes: {len(payload) - offset}")
    return points


def _parse_volume_comparison_points(payload: bytes, *, count: int) -> list[IntradaySubchartPoint]:
    expected_length = 2 + count * 8
    if len(payload) != expected_length:
        raise _protocol_error()(
            f"invalid intraday volume comparison payload length: expected {expected_length}, got {len(payload)}"
        )

    offset = 2
    intraday_subchart_point = _intraday_subchart_point_cls()
    points: list[IntradaySubchartPoint] = []
    binary = _binary()
    for index in range(count):
        record = payload[offset : offset + 8]
        previous = float(binary.little_f32(record[:4]))
        current = float(binary.little_f32(record[4:8]))
        points.append(
            intraday_subchart_point(
                index=index,
                previous_day_cumulative_volume=previous,
                current_day_cumulative_volume=current,
                cumulative_volume=current,
                series_a_f32=previous,
                series_b_f32=current,
                record_hex=record.hex(),
            )
        )
        offset += 8
    return points


def normalize_intraday_subchart_selector(value: Any) -> int:
    if isinstance(value, str):
        text = value.strip().lower()
        aliases = {
            "buy_sell_strength": INTRADAY_SUBCHART_BUY_SELL_STRENGTH,
            "strength": INTRADAY_SUBCHART_BUY_SELL_STRENGTH,
            "0x00": INTRADAY_SUBCHART_BUY_SELL_STRENGTH,
            "volume_comparison": INTRADAY_SUBCHART_VOLUME_COMPARISON,
            "volume_compare": INTRADAY_SUBCHART_VOLUME_COMPARISON,
            "0x0b": INTRADAY_SUBCHART_VOLUME_COMPARISON,
        }
        if text in aliases:
            return aliases[text]
        try:
            parsed = int(text, 0)
        except ValueError as exc:
            raise _protocol_error()("selector must be an integer or known intraday subchart alias") from exc
    else:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise _protocol_error()("selector must be an integer or known intraday subchart alias") from exc
    if parsed < 0 or parsed > 0xFF:
        raise _protocol_error()("selector must be between 0 and 255")
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
