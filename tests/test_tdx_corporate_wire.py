from __future__ import annotations

import sys
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

import struct

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.constants import TYPE_CAPITAL_CHANGES
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_build_capital_changes_frame_uses_000f_payload():
    frame = build_command_frame(TYPE_CAPITAL_CHANGES, {"code": "000001.SZ"}, 7)

    assert frame.msg_type == TYPE_CAPITAL_CHANGES
    assert frame.data.hex() == "010000303030303031"


def test_parse_capital_changes_payload_decodes_xdxr_record():
    record = (
        b"\x00"
        + b"000001"
        + b"\x00"
        + (20240603).to_bytes(4, "little")
        + b"\x01"
        + struct.pack("<ffff", 1.0, 0.0, 2.0, 0.0)
    )
    payload = (
        (1).to_bytes(2, "little")
        + b"\x00"
        + b"000001"
        + (1).to_bytes(2, "little")
        + record
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_CAPITAL_CHANGES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    block = parse_command_response(TYPE_CAPITAL_CHANGES, response, {"code": "sz000001"})

    assert block.full_code == "sz000001"
    assert block.count == 1
    assert block.records[0].date.isoformat() == "2024-06-03"
    assert block.records[0].category_name == "除权除息"
    assert block.records[0].c1_float == 1.0
    assert block.records[0].c3_float == 2.0


def test_parse_capital_changes_payload_interprets_share_capital_record():
    record = (
        b"\x01"
        + b"600300"
        + b"\x00"
        + (20010104).to_bytes(4, "little")
        + b"\x05"
        + struct.pack("<ffff", 5000.0, 33000.0, 9200.0, 33000.0)
    )
    payload = (
        (1).to_bytes(2, "little")
        + b"\x01"
        + b"600300"
        + (1).to_bytes(2, "little")
        + record
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_CAPITAL_CHANGES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    block = parse_command_response(TYPE_CAPITAL_CHANGES, response, {"code": "sh600300"})

    assert block.full_code == "sh600300"
    assert block.records[0].category_name == "股本变化"
    assert block.records[0].c1_quantity == 5000.0
    assert block.records[0].c2_quantity == 33000.0
    assert block.records[0].c3_quantity == 9200.0
    assert block.records[0].c4_quantity == 33000.0


def test_parse_capital_changes_payload_keeps_private_placement_as_float_slots():
    record = (
        b"\x01"
        + b"600887"
        + b"\x00"
        + (20020820).to_bytes(4, "little")
        + b"\x06"
        + struct.pack("<ffff", 0.0, 16.85, 4896.140137, 0.0)
    )
    payload = (
        (1).to_bytes(2, "little")
        + b"\x01"
        + b"600887"
        + (1).to_bytes(2, "little")
        + record
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_CAPITAL_CHANGES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    block = parse_command_response(TYPE_CAPITAL_CHANGES, response, {"code": "sh600887"})

    assert block.full_code == "sh600887"
    assert block.records[0].category_name == "增发新股"
    assert block.records[0].c1_float == 0.0
    assert round(block.records[0].c2_float, 2) == 16.85
    assert round(block.records[0].c3_float, 6) == 4896.140137
    assert block.records[0].c4_float == 0.0
