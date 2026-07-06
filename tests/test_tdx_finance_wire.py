from __future__ import annotations

import sys
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

import struct

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.constants import TYPE_FINANCE_INFO
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_build_finance_info_frame_uses_0010_payload():
    frame = build_command_frame(TYPE_FINANCE_INFO, {"code": ["000001.SZ", "600000.SH"]}, 9)

    assert frame.msg_type == TYPE_FINANCE_INFO
    assert frame.data.hex() == "02000030303030303101363030303030"


def test_parse_finance_info_payload_decodes_units_and_dates():
    payload = (1).to_bytes(2, "little") + _finance_record()
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_FINANCE_INFO,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    block = parse_command_response(TYPE_FINANCE_INFO, response, {"code": "sz000001"})

    assert block.count == 1
    record = block.records[0]
    assert record.full_code == "sz000001"
    assert record.updated_date.isoformat() == "2026-04-25"
    assert record.ipo_date.isoformat() == "1991-04-03"
    assert round(record.float_share / 100000000, 2) == 194.06
    assert round(record.total_share / 100000000, 2) == 194.06
    assert record.shareholder_count == 457610
    assert round(record.eps, 2) == 0.67
    assert round(record.revenue / 100000000, 2) == 352.77
    assert round(record.net_profit / 100000000, 2) == 145.23
    assert round(record.bps, 2) == 23.91


def test_parse_finance_info_empty_record_marks_invalid_code():
    empty_info = b"\x00" * 136
    raw_record = b"\x00" + b"999999" + empty_info
    payload = (1).to_bytes(2, "little") + raw_record
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_FINANCE_INFO,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    block = parse_command_response(TYPE_FINANCE_INFO, response, {"code": "sz999999"})

    assert block.records[0].full_code == "sz999999"
    assert block.records[0].is_empty is True


def _finance_record() -> bytes:
    info = (
        struct.pack("<f", 1940560.125)
        + (18).to_bytes(2, "little")
        + (101).to_bytes(2, "little")
        + (20260425).to_bytes(4, "little")
        + (19910403).to_bytes(4, "little")
        + struct.pack("<f", 1940591.875)
        + struct.pack("<f", 0.0)
        + struct.pack("<f", 0.0)
        + struct.pack("<f", 0.0)
        + struct.pack("<f", 0.0)
        + struct.pack("<f", 0.0)
        + struct.pack("<f", 0.67)
        + struct.pack("<f", 35277000.0)
        + struct.pack("<f", 1000.0)
        + struct.pack("<f", 2000.0)
        + struct.pack("<f", 3000.0)
        + struct.pack("<f", 457610.0)
        + struct.pack("<f", 4000.0)
        + struct.pack("<f", 5000.0)
        + struct.pack("<f", 6000.0)
        + struct.pack("<f", 7000.0)
        + struct.pack("<f", 35277000.0)
        + struct.pack("<f", 8000.0)
        + struct.pack("<f", 9000.0)
        + struct.pack("<f", 10000.0)
        + struct.pack("<f", 11000.0)
        + struct.pack("<f", 12000.0)
        + struct.pack("<f", 13000.0)
        + struct.pack("<f", 14000.0)
        + struct.pack("<f", 15000.0)
        + struct.pack("<f", 16000.0)
        + struct.pack("<f", 14523000.0)
        + struct.pack("<f", 17000.0)
        + struct.pack("<f", 23.91)
        + struct.pack("<f", 0.0)
    )
    assert len(info) == 136
    return b"\x00" + b"000001" + info
