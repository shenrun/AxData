"""Session command builders and parsers."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_HANDSHAKE = command_code("handshake")
TYPE_HEARTBEAT = command_code("heartbeat")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.session"
_BINARY_EXPORTS = {"date_from_yyyymmdd", "decode_gbk_text", "little_u16", "little_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"HandshakeInfo", "HeartbeatAck"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _handshake_info_cls():
    return import_module(_MODEL_MODULE).HandshakeInfo


def _heartbeat_ack_cls():
    return import_module(_MODEL_MODULE).HeartbeatAck


def build_handshake_frame(payload: dict, msg_id: int) -> RequestFrame:
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_HANDSHAKE, data=b"\x01")


def parse_handshake_payload(response: ResponseFrame) -> HandshakeInfo:
    payload = response.data
    if len(payload) < 189:
        raise _protocol_error()(f"invalid handshake payload length: {len(payload)}")

    binary = _binary()
    server_datetime = _parse_server_datetime(payload)
    session_minutes_1 = _parse_session_minutes(payload[9:25])
    session_minutes_2 = _parse_session_minutes(payload[25:41])
    date_1_raw = binary.little_u32(payload[42:46])
    date_2_raw = binary.little_u32(payload[50:54])

    return _handshake_info_cls()(
        server_datetime=server_datetime,
        session_minutes_1=session_minutes_1,
        session_minutes_2=session_minutes_2,
        server_date_1=binary.date_from_yyyymmdd(date_1_raw),
        server_date_2=binary.date_from_yyyymmdd(date_2_raw),
        server_name=binary.decode_gbk_text(payload[68:152]),
        product_tag=binary.decode_gbk_text(payload[160:189]),
        unknown_time_1_raw=binary.little_u32(payload[46:50]),
        unknown_time_2_raw=binary.little_u32(payload[54:58]),
        flags_raw=payload[58:68],
        tail_control_raw=payload[152:160],
        raw_payload=payload,
    )


def build_heartbeat_frame(payload: dict, msg_id: int) -> RequestFrame:
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_HEARTBEAT)


def parse_heartbeat_payload(response: ResponseFrame) -> HeartbeatAck:
    payload = response.data
    if len(payload) < 10:
        raise _protocol_error()(f"invalid heartbeat payload length: {len(payload)}")

    binary = _binary()
    server_date_raw = binary.little_u32(payload[6:10])
    return _heartbeat_ack_cls()(
        reserved=payload[:6],
        server_date_raw=server_date_raw,
        server_date=binary.date_from_yyyymmdd(server_date_raw),
        raw_payload=payload,
    )


def _parse_server_datetime(payload: bytes) -> datetime | None:
    binary = _binary()
    try:
        return datetime(
            binary.little_u16(payload[1:3]),
            payload[4],
            payload[3],
            payload[6],
            payload[5],
            payload[8],
        )
    except (ValueError, IndexError):
        return None


def _parse_session_minutes(payload: bytes) -> tuple[str, ...]:
    binary = _binary()
    values = []
    for offset in range(0, min(len(payload), 16), 2):
        minute = binary.little_u16(payload[offset : offset + 2])
        values.append(f"{minute // 60:02d}:{minute % 60:02d}")
    return tuple(values)


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
