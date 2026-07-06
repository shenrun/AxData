"""7709 TCP frame encoding and decoding."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


from ._frame_constants import CONTROL_DEFAULT, PREFIX, PREFIX_RESP


_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_EXCEPTION_EXPORTS = {"ConnectionClosedError", "ProtocolError"}
_STDLIB_EXPORTS = {"socket", "struct", "zlib"}


def _connection_closed_error():
    return import_module(_EXCEPTIONS_MODULE).ConnectionClosedError


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def __getattr__(name: str):
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    if name in _STDLIB_EXPORTS:
        value = import_module(name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _STDLIB_EXPORTS)


@dataclass(frozen=True, slots=True)
class RequestFrame:
    msg_id: int
    msg_type: int
    data: bytes = b""
    control: int = CONTROL_DEFAULT

    def to_bytes(self) -> bytes:
        import struct

        length = len(self.data) + 2
        return struct.pack("<BIBHHH", PREFIX, self.msg_id, self.control, length, length, self.msg_type) + self.data


@dataclass(frozen=True, slots=True)
class ResponseFrame:
    control: int
    msg_id: int
    msg_type: int
    zip_length: int
    length: int
    data: bytes
    raw: bytes
    response_header_reserved: int = 0


def read_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = sock.recv(size - len(chunks))
        if not piece:
            raise _connection_closed_error()("socket closed by remote peer")
        chunks.extend(piece)
    return bytes(chunks)


def read_response_frame(sock: socket.socket) -> bytes:
    window = bytearray(read_exact(sock, 4))
    while bytes(window) != PREFIX_RESP:
        window = window[1:] + read_exact(sock, 1)

    header = read_exact(sock, 12)
    zip_length = int.from_bytes(header[8:10], "little", signed=False)
    payload = read_exact(sock, zip_length)
    return bytes(window) + header + payload


def decode_response(raw: bytes) -> ResponseFrame:
    if len(raw) < 16:
        raise _protocol_error()(f"invalid response length: {len(raw)}")
    if raw[:4] != PREFIX_RESP:
        raise _protocol_error()(f"invalid response prefix: {raw[:4].hex()}")

    control = raw[4]
    msg_id = int.from_bytes(raw[5:9], "little", signed=False)
    reserved = raw[9]
    msg_type = int.from_bytes(raw[10:12], "little", signed=False)
    zip_length = int.from_bytes(raw[12:14], "little", signed=False)
    length = int.from_bytes(raw[14:16], "little", signed=False)
    payload = raw[16:]

    if len(payload) != zip_length:
        raise _protocol_error()(f"zip length mismatch: expected {zip_length}, got {len(payload)}")

    if zip_length != length:
        import zlib

        data = zlib.decompress(payload)
    else:
        data = payload
    if len(data) != length:
        raise _protocol_error()(f"decoded length mismatch: expected {length}, got {len(data)}")

    return ResponseFrame(
        control=control,
        msg_id=msg_id,
        msg_type=msg_type,
        zip_length=zip_length,
        length=length,
        data=data,
        raw=raw,
        response_header_reserved=reserved,
    )


__all__ = [
    "ConnectionClosedError",
    "CONTROL_DEFAULT",
    "PREFIX",
    "PREFIX_RESP",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "dataclass",
    "decode_response",
    "read_exact",
    "read_response_frame",
    "socket",
    "struct",
    "zlib",
]
