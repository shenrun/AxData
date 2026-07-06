from __future__ import annotations

import sys
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.constants import TYPE_KLINES
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_build_klines_frame_uses_052d_second_period_mapping():
    frame = build_command_frame(
        TYPE_KLINES,
        {"code": "000001.SZ", "period": "5s", "start": 0, "count": 420},
        13,
    )

    assert frame.msg_type == TYPE_KLINES
    assert frame.data.hex() == (
        "0000"
        "303030303031"
        "0d00"
        "0500"
        "0000"
        "a401"
        "0000"
        "00000000"
        "0000000000000000000000000000000000000000"
    )


def test_parse_klines_payload_decodes_second_time_and_prices():
    payload = (
        (1).to_bytes(2, "little")
        + (5).to_bytes(4, "little")
        + bytes([10, 2, 3, 0x41])
        + b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_KLINES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_KLINES,
        response,
        {"code": "sz000001", "period": "5s", "start": 0, "count": 1},
    )

    assert series.full_code == "sz000001"
    assert series.period_name == "5s"
    assert series.count == 1
    assert series.bars[0].time.isoformat() == "2003-12-31T00:00:05+08:00"
    assert series.bars[0].open == 0.01
    assert series.bars[0].close == 0.012
    assert series.bars[0].high == 0.013
    assert series.bars[0].low == 0.009
