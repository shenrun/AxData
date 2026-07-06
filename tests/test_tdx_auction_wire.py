from __future__ import annotations

import sys
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

import struct

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.constants import TYPE_AUCTION_PROCESS
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_build_auction_process_frame_uses_056a_payload():
    frame = build_command_frame(
        TYPE_AUCTION_PROCESS,
        {"code": "000988.SZ"},
        13,
    )

    assert frame.msg_type == TYPE_AUCTION_PROCESS
    assert frame.data.hex() == "000030303039383800000000030000000000000000000000f4010000"


def test_parse_auction_process_payload_decodes_time_price_volume_and_direction():
    payload = (
        (3).to_bytes(2, "little")
        + _auction_record(9 * 60 + 15, 162.12, 2568, 2433, 0)
        + _auction_record(9 * 60 + 15, 162.12, 6630, -1115, 9)
        + _auction_record(9 * 60 + 15, 162.12, 6630, 0, 18)
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_AUCTION_PROCESS,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(TYPE_AUCTION_PROCESS, response, {"code": "sz000988"})

    assert series.full_code == "sz000988"
    assert series.mode_or_selector_raw == 3
    assert series.start == 0
    assert series.request_count == 500
    assert series.count == 3
    assert [record.auction_time.isoformat(timespec="seconds") for record in series.records] == [
        "09:15:00",
        "09:15:09",
        "09:15:18",
    ]
    assert [round(record.price, 3) for record in series.records] == [162.12, 162.12, 162.12]
    assert [record.price_milli for record in series.records] == [162120, 162120, 162120]
    assert [record.matched_volume for record in series.records] == [2568, 6630, 6630]
    assert [record.unmatched_signed_raw for record in series.records] == [2433, -1115, 0]
    assert [record.unmatched_volume for record in series.records] == [2433, 1115, 0]
    assert [record.unmatched_direction for record in series.records] == [1, -1, 0]
    assert [record.time_seconds for record in series.records] == [33300, 33309, 33318]
    assert round(series.records[0].matched_amount_estimated, 2) == 41632414.75


def _auction_record(
    minute_of_day: int,
    price: float,
    matched_volume: int,
    unmatched_signed: int,
    second: int,
) -> bytes:
    return (
        minute_of_day.to_bytes(2, "little")
        + struct.pack("<f", price)
        + matched_volume.to_bytes(4, "little", signed=False)
        + unmatched_signed.to_bytes(4, "little", signed=True)
        + b"\x00"
        + second.to_bytes(1, "little")
    )
