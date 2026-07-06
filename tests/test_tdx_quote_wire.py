from __future__ import annotations

import sys
from pathlib import Path

_TDX_PROVIDER_SRC = str(Path(__file__).resolve().parents[1] / "packages" / "axdata-source-tdx" / "src")
sys.path.insert(0, _TDX_PROVIDER_SRC)

import struct

from axdata_source_tdx._tdx_wire.protocol.commands import build_command_frame, parse_command_response
from axdata_source_tdx._tdx_wire.protocol.constants import (
    TYPE_CATEGORY_QUOTES,
    TYPE_EXPLICIT_QUOTES,
    TYPE_LEGACY_QUOTES,
    TYPE_PRICE_LIMITS,
    TYPE_REFRESH_QUOTES,
)
from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

if sys.path and sys.path[0] == _TDX_PROVIDER_SRC:
    sys.path.pop(0)



def test_parse_legacy_quote_payload_decodes_five_level_order_book():
    levels = [
        (-1, 0, 320, 428),
        (-2, 1, 118, 260),
        (-3, 2, 94, 136),
        (-4, 3, 87, 92),
        (-5, 4, 66, 71),
    ]
    record = bytearray()
    record.extend(bytes([0]))
    record.extend(b"000001")
    record.extend((7).to_bytes(2, "little"))
    record.extend(_signed_varint(1014))
    record.extend(_signed_varint(-14))
    record.extend(_signed_varint(-1))
    record.extend(_signed_varint(6))
    record.extend(_signed_varint(-10))
    record.extend(_signed_varint(103000))
    record.extend(_signed_varint(-1014))
    record.extend(_signed_varint(1000))
    record.extend(_signed_varint(15))
    record.extend((12345678).to_bytes(4, "little"))
    record.extend(_signed_varint(400))
    record.extend(_signed_varint(600))
    record.extend(_signed_varint(0))
    record.extend(_signed_varint(100))
    for bid_diff, ask_diff, bid_volume, ask_volume in levels:
        record.extend(_signed_varint(bid_diff))
        record.extend(_signed_varint(ask_diff))
        record.extend(_signed_varint(bid_volume))
        record.extend(_signed_varint(ask_volume))
    record.extend((0).to_bytes(2, "little"))
    for _ in range(4):
        record.extend(_signed_varint(0))
    record.extend((21).to_bytes(2, "little", signed=True))
    record.extend((8).to_bytes(2, "little"))

    payload = (0x0701).to_bytes(2, "little") + (1).to_bytes(2, "little") + bytes(record)
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_LEGACY_QUOTES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    quotes = parse_command_response(TYPE_LEGACY_QUOTES, response, {"securities": [("sz", "000001")]})

    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.full_code == "sz000001"
    assert quote.close == 10.14
    assert [level.price for level in quote.bid_levels] == [10.13, 10.12, 10.11, 10.1, 10.09]
    assert [level.volume for level in quote.bid_levels] == [320, 118, 94, 87, 66]
    assert [level.price for level in quote.ask_levels] == [10.14, 10.15, 10.16, 10.17, 10.18]
    assert [level.volume for level in quote.ask_levels] == [428, 260, 136, 92, 71]
    assert quote.bid_vol_sum == 685
    assert quote.ask_vol_sum == 987
    assert quote.active2 == 8


def test_parse_explicit_quote_payload_decodes_realtime_snapshot():
    first = _explicit_quote_record(0, "000001")
    second = _explicit_quote_record(1, "600000", close_raw=842, total_hand=2100)
    payload = (0).to_bytes(2, "little") + (2).to_bytes(2, "little") + first + second
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_EXPLICIT_QUOTES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    quotes = parse_command_response(
        TYPE_EXPLICIT_QUOTES,
        response,
        {"securities": [("sz", "000001"), ("sh", "600000")]},
    )

    assert [quote.full_code for quote in quotes] == ["sz000001", "sh600000"]
    quote = quotes[0]
    assert quote.last_price == 10.14
    assert quote.pre_close == 10.0
    assert quote.open == 10.13
    assert quote.high == 10.2
    assert quote.low == 10.04
    assert quote.change == 0.14000000000000057
    assert round(quote.change_pct or 0, 6) == 1.4
    assert round(quote.amplitude_pct or 0, 6) == 1.6
    assert quote.total_hand == 1000
    assert quote.current_hand == 15
    assert quote.amount == 0.0
    assert quote.inside_dish == 400
    assert quote.outer_disc == 600
    assert quote.open_amount == 10000.0
    assert quote.bid1_price == 10.13
    assert quote.bid1_volume == 320
    assert quote.ask1_price == 10.14
    assert quote.ask1_volume == 428
    assert quote.rise_speed == 0.21
    assert quote.short_turnover == 0.08
    assert quote.min2_amount == 320000.0
    assert quote.opening_rush == 0.12
    assert quote.vol_rise_speed == 1.25
    assert quote.entrust_ratio == 18.5
    assert quote.active2 == 11
    assert quote.activity == 11


def test_parse_category_quote_payload_decodes_realtime_rank_page():
    first = _explicit_quote_record(0, "000001")
    second = _explicit_quote_record(1, "600000", close_raw=842, total_hand=2100)
    payload = (0).to_bytes(2, "little") + (2).to_bytes(2, "little") + first + second
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_CATEGORY_QUOTES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    page = parse_command_response(
        TYPE_CATEGORY_QUOTES,
        response,
        {"category": 6, "sort_type": 0x000E, "start": 80, "count": 2, "ascending": False, "filter_raw": 4},
    )

    assert page.category == 6
    assert page.sort_type == 0x000E
    assert page.start == 80
    assert page.request_count == 2
    assert page.sort_reverse == 1
    assert page.filter_raw == 4
    assert [quote.full_code for quote in page.records] == ["sz000001", "sh600000"]
    quote = page.records[0]
    assert quote.last_price == 10.14
    assert quote.pre_close == 10.0
    assert quote.open_amount == 10000.0
    assert quote.bid1_price == 10.13
    assert quote.ask1_price == 10.14
    assert quote.rise_speed == 0.21
    assert quote.short_turnover == 0.08
    assert quote.min2_amount == 320000.0
    assert quote.opening_rush == 0.12
    assert quote.vol_rise_speed == 1.25
    assert quote.entrust_ratio == 18.5
    assert quote.activity == 11


def test_build_price_limits_frame_encodes_start_index():
    frame = build_command_frame(TYPE_PRICE_LIMITS, {"start_index": 7}, msg_id=5)

    assert frame.msg_id == 5
    assert frame.msg_type == TYPE_PRICE_LIMITS
    assert frame.data == struct.pack("<HIII", 7, 0, 0, 0)


def test_parse_price_limits_payload_decodes_special_limit_record():
    record = bytes([0]) + (1).to_bytes(4, "little") + struct.pack("<ff", 12.34, 8.76)
    payload = (1).to_bytes(2, "little") + record
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_PRICE_LIMITS,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    records = parse_command_response(TYPE_PRICE_LIMITS, response, {"start_index": 0})

    assert len(records) == 1
    item = records[0]
    assert item.exchange == "sz"
    assert item.market_id == 0
    assert item.code == "000001"
    assert item.full_code == "sz000001"
    assert item.code_num == 1
    assert round(item.limit_up_price, 2) == 12.34
    assert round(item.limit_down_price, 2) == 8.76
    assert item.record_hex == record.hex()


def test_build_refresh_quote_frame_encodes_cursor_items():
    frame = build_command_frame(
        TYPE_REFRESH_QUOTES,
        {"cursors": [("sz", "000001", 123456), {"market": "sh", "code": "600000", "cursor": 654321}]},
        msg_id=7,
    )

    assert frame.msg_id == 7
    assert frame.msg_type == TYPE_REFRESH_QUOTES
    assert frame.data == (
        (2).to_bytes(2, "little")
        + b"\x00"
        + b"000001"
        + (123456).to_bytes(4, "little")
        + b"\x01"
        + b"600000"
        + (654321).to_bytes(4, "little")
    )


def test_parse_refresh_quote_payload_decodes_empty_batch():
    payload = bytes(byte ^ 0x93 for byte in (0).to_bytes(2, "little"))
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_REFRESH_QUOTES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    batch = parse_command_response(TYPE_REFRESH_QUOTES, response, {"cursors": [("sz", "000001", 0)]})

    assert batch.count == 0
    assert batch.records == ()


def test_parse_refresh_quote_payload_decodes_realtime_update_record():
    record = _refresh_quote_record(0, "000001")
    decoded = (1).to_bytes(2, "little") + record
    payload = bytes(byte ^ 0x93 for byte in decoded)
    response = ResponseFrame(
        control=0,
        msg_id=1,
        msg_type=TYPE_REFRESH_QUOTES,
        zip_length=len(payload),
        length=len(payload),
        data=payload,
        raw=b"",
    )

    batch = parse_command_response(TYPE_REFRESH_QUOTES, response, {"cursors": [("sz", "000001", 0)]})

    assert batch.count == 1
    quote = batch.records[0]
    assert quote.full_code == "sz000001"
    assert quote.active == 7
    assert quote.last_price == 10.14
    assert quote.pre_close == 10.0
    assert quote.open == 10.13
    assert quote.high == 10.2
    assert quote.low == 10.04
    assert quote.update_time_raw == 103000
    assert quote.status_or_reserved_raw == 0
    assert quote.total_hand == 1000
    assert quote.current_hand == 15
    assert quote.amount == 0.0
    assert quote.inside_dish == 400
    assert quote.outer_disc == 600
    assert quote.open_amount == 1000.0
    assert [level.price for level in quote.bid_levels] == [10.13, 10.12, 10.11, 10.1, 10.09]
    assert [level.volume for level in quote.bid_levels] == [320, 118, 94, 87, 66]
    assert [level.price for level in quote.ask_levels] == [10.14, 10.15, 10.16, 10.17, 10.18]
    assert [level.volume for level in quote.ask_levels] == [428, 260, 136, 92, 71]


def _explicit_quote_record(
    market_id: int,
    code: str,
    *,
    close_raw: int = 1014,
    total_hand: int = 1000,
) -> bytes:
    record = bytearray()
    record.extend(bytes([market_id]))
    record.extend(code.encode("ascii"))
    record.extend((7).to_bytes(2, "little"))
    record.extend(_signed_varint(close_raw))
    record.extend(_signed_varint(-14))
    record.extend(_signed_varint(-1))
    record.extend(_signed_varint(6))
    record.extend(_signed_varint(-10))
    record.extend(_signed_varint(103000))
    record.extend(_signed_varint(-close_raw))
    record.extend(_signed_varint(total_hand))
    record.extend(_signed_varint(15))
    record.extend((0).to_bytes(4, "little"))
    record.extend(_signed_varint(400))
    record.extend(_signed_varint(600))
    record.extend(_signed_varint(0))
    record.extend(_signed_varint(100))
    record.extend(_signed_varint(-1))
    record.extend(_signed_varint(0))
    record.extend(_signed_varint(320))
    record.extend(_signed_varint(428))
    record.extend(
        struct.pack(
            "<Hhhfh10sff24sH",
            9,
            21,
            8,
            320000.0,
            12,
            b"\x00" * 10,
            1.25,
            18.5,
            b"\x00" * 24,
            11,
        )
    )
    return bytes(record)


def _refresh_quote_record(
    market_id: int,
    code: str,
    *,
    close_raw: int = 1014,
    total_hand: int = 1000,
) -> bytes:
    levels = [
        (-1, 0, 320, 428),
        (-2, 1, 118, 260),
        (-3, 2, 94, 136),
        (-4, 3, 87, 92),
        (-5, 4, 66, 71),
    ]
    record = bytearray()
    record.extend(bytes([market_id]))
    record.extend(code.encode("ascii"))
    record.extend((7).to_bytes(2, "little"))
    record.extend(_signed_varint(close_raw))
    record.extend(_signed_varint(-14))
    record.extend(_signed_varint(-1))
    record.extend(_signed_varint(6))
    record.extend(_signed_varint(-10))
    record.extend((103000).to_bytes(4, "little"))
    record.extend(_signed_varint(0))
    record.extend(_signed_varint(total_hand))
    record.extend(_signed_varint(15))
    record.extend((0).to_bytes(4, "little"))
    record.extend(_signed_varint(400))
    record.extend(_signed_varint(600))
    record.extend(_signed_varint(0))
    record.extend(_signed_varint(100))
    for bid_diff, ask_diff, bid_volume, ask_volume in levels:
        record.extend(_signed_varint(bid_diff))
        record.extend(_signed_varint(ask_diff))
        record.extend(_signed_varint(bid_volume))
        record.extend(_signed_varint(ask_volume))
    return bytes(record)


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
