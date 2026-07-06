from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

import pytest

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.commands.resources import FILE_PATH_FIELD_SIZE
from axdata_source_tdx._tdx_wire.protocol.constants import TYPE_FILE_CONTENT
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_build_file_content_frame_encodes_06b9_payload():
    frame = build_command_frame(
        TYPE_FILE_CONTENT,
        {"path": "zhb.zip", "offset": 30000, "size": 12000},
        17,
    )

    assert frame.msg_id == 17
    assert frame.msg_type == TYPE_FILE_CONTENT
    assert frame.data[:8] == (30000).to_bytes(4, "little") + (12000).to_bytes(4, "little")
    assert frame.data[8 : 8 + FILE_PATH_FIELD_SIZE].rstrip(b"\x00") == b"zhb.zip"


def test_parse_file_content_payload_decodes_chunk():
    body = b"abc123"
    payload = len(body).to_bytes(4, "little") + body
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_FILE_CONTENT,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    chunk = parse_command_response(
        TYPE_FILE_CONTENT,
        response,
        {"path": "zhb.zip", "offset": 10, "size": 30000},
    )

    assert chunk.path == "zhb.zip"
    assert chunk.offset == 10
    assert chunk.request_size == 30000
    assert chunk.chunk_len == 6
    assert chunk.content == body
    assert chunk.is_last is True


def test_build_file_content_frame_rejects_non_ascii_path():
    protocol_error = import_module("axdata_source_tdx._tdx_wire.exceptions").ProtocolError
    with pytest.raises(protocol_error, match="ASCII"):
        build_command_frame(TYPE_FILE_CONTENT, {"path": "统计.zip"}, 1)
