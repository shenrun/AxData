"""File resource command builders and parsers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._command_defaults import FILE_PATH_FIELD_SIZE
from axdata_source_tdx._tdx_wire._request_defaults import DEFAULT_FILE_CHUNK_SIZE
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_FILE_CONTENT = command_code("file_content")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.resource"
_BINARY_EXPORTS = {"little_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"FileContentChunk"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _file_content_chunk_cls():
    return import_module(_MODEL_MODULE).FileContentChunk


def build_file_content_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    path = _file_path(payload.get("path"))
    offset = _u32_param(payload.get("offset", 0), "offset")
    size = _u32_param(payload.get("size", DEFAULT_FILE_CHUNK_SIZE), "size")
    if size <= 0:
        raise _protocol_error()("file content size must be > 0")

    path_raw = path.encode("ascii")
    if len(path_raw) > FILE_PATH_FIELD_SIZE:
        raise _protocol_error()("file content path exceeds 300 ASCII bytes")
    data = (
        offset.to_bytes(4, "little", signed=False)
        + size.to_bytes(4, "little", signed=False)
        + path_raw.ljust(FILE_PATH_FIELD_SIZE, b"\x00")
    )
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_FILE_CONTENT, data=data)


def parse_file_content_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> FileContentChunk:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 4:
        raise _protocol_error()("invalid file content payload")
    chunk_len = import_module(_BINARY_MODULE).little_u32(payload[:4])
    if len(payload) < 4 + chunk_len:
        raise _protocol_error()(f"invalid file content payload length: expected {4 + chunk_len}, got {len(payload)}")

    return _file_content_chunk_cls()(
        path=_file_path(request_payload.get("path", "")),
        offset=_u32_param(request_payload.get("offset", 0), "offset"),
        request_size=_u32_param(request_payload.get("size", DEFAULT_FILE_CHUNK_SIZE), "size"),
        chunk_len=chunk_len,
        content=payload[4 : 4 + chunk_len],
    )


def _file_path(value: Any) -> str:
    path = str(value or "").strip().replace("\\", "/")
    if not path:
        raise _protocol_error()("file content path is required")
    try:
        path.encode("ascii")
    except UnicodeEncodeError as exc:
        raise _protocol_error()("file content path must be ASCII") from exc
    return path


def _u32_param(value: Any, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise _protocol_error()(f"file content {name} must be an integer") from exc
    if number < 0 or number > 0xFFFFFFFF:
        raise _protocol_error()(f"file content {name} out of uint32 range")
    return number


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
