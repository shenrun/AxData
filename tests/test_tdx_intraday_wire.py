from __future__ import annotations

import sys
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

import struct

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.constants import (
    TYPE_HISTORICAL_INTRADAY,
    TYPE_INTRADAY_SUBCHART,
    TYPE_RECENT_HISTORICAL_INTRADAY,
    TYPE_TODAY_INTRADAY,
)
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_build_today_intraday_frame_uses_0537_payload():
    frame = build_command_frame(
        TYPE_TODAY_INTRADAY,
        {"code": "000988.SZ"},
        12,
    )

    assert frame.msg_type == TYPE_TODAY_INTRADAY
    assert frame.data.hex() == "000030303039383800000093"


def test_parse_today_intraday_payload_decodes_prices_avg_and_times():
    payload = (
        (3).to_bytes(2, "little")
        + (0).to_bytes(2, "little")
        + _signed_varint(1086)
        + _signed_varint(108417)
        + _signed_varint(120)
        + _signed_varint(2)
        + _signed_varint(10)
        + _signed_varint(80)
        + _signed_varint(-1)
        + _signed_varint(-20)
        + _signed_varint(90)
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_TODAY_INTRADAY,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_TODAY_INTRADAY,
        response,
        {"code": "sz000988"},
    )

    assert series.full_code == "sz000988"
    assert series.reserved_zero == 0
    assert series.reserved_tail_hex == "00000093"
    assert series.count == 3
    assert [point.time_label for point in series.points] == ["09:31", "09:32", "09:33"]
    assert [point.price for point in series.points] == [10.86, 10.88, 10.85]
    assert [point.avg_price for point in series.points] == [10.8417, 10.8427, 10.8397]
    assert [point.volume for point in series.points] == [120, 80, 90]


def test_parse_today_intraday_payload_maps_afternoon_time():
    records = b"".join(_signed_varint(1000) + _signed_varint(100000) + _signed_varint(0) for _ in range(121))
    payload = (121).to_bytes(2, "little") + (0).to_bytes(2, "little") + records
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_TODAY_INTRADAY,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_TODAY_INTRADAY,
        response,
        {"code": "sz000001"},
    )

    assert series.points[119].time_label == "11:30"
    assert series.points[120].time_label == "13:01"


def test_build_historical_intraday_frame_uses_0fb4_payload():
    frame = build_command_frame(
        TYPE_HISTORICAL_INTRADAY,
        {"code": "000001.SZ", "trade_date": "20260519"},
        13,
    )

    assert frame.msg_type == TYPE_HISTORICAL_INTRADAY
    assert frame.data.hex() == "a726350100303030303031"


def test_parse_historical_intraday_payload_decodes_prices_and_times():
    payload = (
        (3).to_bytes(2, "little")
        + struct.pack("<f", 10.08)
        + _signed_varint(1013)
        + _signed_varint(0)
        + _varint(120)
        + _signed_varint(2)
        + _signed_varint(-1)
        + _varint(80)
        + _signed_varint(-1)
        + _signed_varint(1)
        + _varint(90)
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_HISTORICAL_INTRADAY,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_HISTORICAL_INTRADAY,
        response,
        {"code": "sz000001", "trade_date": "20260519"},
    )

    assert series.full_code == "sz000001"
    assert series.trade_date.isoformat() == "2026-05-19"
    assert round(series.prev_close, 2) == 10.08
    assert series.count == 3
    assert [point.time.isoformat() for point in series.points] == [
        "2026-05-19T09:31:00+08:00",
        "2026-05-19T09:32:00+08:00",
        "2026-05-19T09:33:00+08:00",
    ]
    assert [point.price for point in series.points] == [10.13, 10.15, 10.14]
    assert [point.volume for point in series.points] == [120, 80, 90]
    assert series.points[1].aux_delta_raw == -1


def test_parse_historical_intraday_payload_maps_afternoon_time():
    records = b"".join(_signed_varint(0) + _signed_varint(0) + _varint(0) for _ in range(121))
    payload = (121).to_bytes(2, "little") + struct.pack("<f", 10.08) + records
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_HISTORICAL_INTRADAY,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_HISTORICAL_INTRADAY,
        response,
        {"code": "sz000001", "trade_date": "20260519"},
    )

    assert series.points[119].time.isoformat() == "2026-05-19T11:30:00+08:00"
    assert series.points[120].time.isoformat() == "2026-05-19T13:01:00+08:00"


def test_build_recent_historical_intraday_frame_uses_0feb_payload():
    frame = build_command_frame(
        TYPE_RECENT_HISTORICAL_INTRADAY,
        {"code": "300308.SZ", "trade_date": "20260511"},
        14,
    )

    assert frame.msg_type == TYPE_RECENT_HISTORICAL_INTRADAY
    assert frame.data.hex() == "61d9cafe00333030333038"


def test_parse_recent_historical_intraday_payload_decodes_avg_open_and_times():
    payload = (
        (3).to_bytes(2, "little")
        + struct.pack("<f", 10.08)
        + struct.pack("<f", 10.12)
        + _signed_varint(1013)
        + _signed_varint(101150)
        + _signed_varint(120)
        + _signed_varint(2)
        + _signed_varint(130)
        + _signed_varint(80)
        + _signed_varint(-1)
        + _signed_varint(110)
        + _signed_varint(90)
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_RECENT_HISTORICAL_INTRADAY,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_RECENT_HISTORICAL_INTRADAY,
        response,
        {"code": "sz000001", "trade_date": "20260519"},
    )

    assert series.full_code == "sz000001"
    assert series.trade_date.isoformat() == "2026-05-19"
    assert round(series.prev_close, 2) == 10.08
    assert round(series.open_price, 2) == 10.12
    assert series.count == 3
    assert [point.time.isoformat() for point in series.points] == [
        "2026-05-19T09:31:00+08:00",
        "2026-05-19T09:32:00+08:00",
        "2026-05-19T09:33:00+08:00",
    ]
    assert [point.time_label for point in series.points] == ["09:31", "09:32", "09:33"]
    assert [point.price for point in series.points] == [10.13, 10.15, 10.12]
    assert [point.avg_price for point in series.points] == [10.115, 10.128, 10.126]
    assert [point.volume for point in series.points] == [120, 80, 90]


def test_build_intraday_subchart_frame_uses_051b_payload():
    frame = build_command_frame(
        TYPE_INTRADAY_SUBCHART,
        {"code": "000988.SZ", "selector": "volume_comparison"},
        14,
    )

    assert frame.msg_type == TYPE_INTRADAY_SUBCHART
    assert frame.data.hex() == "0000303030393838000000000000000000000000000000000000000b"


def test_parse_intraday_buy_sell_strength_subchart_payload():
    payload = (
        (2).to_bytes(2, "little")
        + _signed_varint(174)
        + _signed_varint(98)
        + _signed_varint(792)
        + _signed_varint(87)
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_INTRADAY_SUBCHART,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_INTRADAY_SUBCHART,
        response,
        {"code": "sz000988", "selector": "buy_sell_strength"},
    )

    assert series.full_code == "sz000988"
    assert series.selector_raw == 0
    assert series.selector_name == "buy_sell_strength"
    assert series.count == 2
    assert [point.bid_order for point in series.points] == [174, 792]
    assert [point.ask_order for point in series.points] == [98, 87]


def test_parse_intraday_volume_comparison_subchart_payload():
    payload = (
        (2).to_bytes(2, "little")
        + struct.pack("<f", 59153)
        + struct.pack("<f", 105552)
        + struct.pack("<f", 98511)
        + struct.pack("<f", 177336)
    )
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_INTRADAY_SUBCHART,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    series = parse_command_response(
        TYPE_INTRADAY_SUBCHART,
        response,
        {"code": "sz000988", "selector": 0x0B},
    )

    assert series.selector_raw == 0x0B
    assert series.selector_name == "volume_comparison"
    assert [point.previous_day_cumulative_volume for point in series.points] == [59153.0, 98511.0]
    assert [point.current_day_cumulative_volume for point in series.points] == [105552.0, 177336.0]
    assert [point.cumulative_volume for point in series.points] == [105552.0, 177336.0]


def _signed_varint(value: int) -> bytes:
    sign = 0x40 if value < 0 else 0
    remaining = abs(value)
    first_value = remaining & 0x3F
    remaining >>= 6
    first = first_value | sign
    if remaining:
        first |= 0x80
    out = [first]
    while remaining:
        byte = remaining & 0x7F
        remaining >>= 7
        if remaining:
            byte |= 0x80
        out.append(byte)
    return bytes(out)


def _varint(value: int) -> bytes:
    remaining = int(value)
    out = []
    while True:
        byte = remaining & 0x7F
        remaining >>= 7
        if remaining:
            byte |= 0x80
        out.append(byte)
        if not remaining:
            break
    return bytes(out)
