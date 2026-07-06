"""Quote snapshot and category-list command builders and parsers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from importlib import import_module

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._market import ID_TO_MARKET, market_to_id
from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_LEGACY_QUOTES = command_code("legacy_quotes")
TYPE_REFRESH_QUOTES = command_code("refresh_quotes")
TYPE_CATEGORY_QUOTES = command_code("category_quotes")
TYPE_EXPLICIT_QUOTES = command_code("explicit_quotes")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.quote"
_BINARY_EXPORTS = {"decode_compact_float", "little_f32", "little_u16", "little_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {
    "CategoryQuote",
    "CategoryQuotePage",
    "ExplicitQuote",
    "LegacyQuote",
    "QuoteLevel",
    "QuoteRefreshBatch",
    "QuoteRefreshRecord",
}
_STDLIB_EXPORTS = {"struct"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _decode_compact_float(value: int) -> float:
    return _binary().decode_compact_float(value)


def _little_f32(data: bytes) -> float:
    return _binary().little_f32(data)


def _little_u16(data: bytes) -> int:
    return _binary().little_u16(data)


def _little_u32(data: bytes) -> int:
    return _binary().little_u32(data)


def _model_cls(name: str):
    return getattr(import_module(_MODEL_MODULE), name)


def _struct_module():
    module = import_module("struct")
    globals()["struct"] = module
    return module


def build_legacy_quotes_frame(payload: dict, msg_id: int) -> RequestFrame:
    return _build_quote_request_frame(payload, msg_id, TYPE_LEGACY_QUOTES)


def build_explicit_quotes_frame(payload: dict, msg_id: int) -> RequestFrame:
    return _build_quote_request_frame(payload, msg_id, TYPE_EXPLICIT_QUOTES)


def build_category_quotes_frame(payload: dict, msg_id: int) -> RequestFrame:
    category = _u16(payload.get("category", 6), "category")
    sort_type = _u16(payload.get("sort_type", payload.get("sort", 0)), "sort_type")
    start = _u16(payload.get("start", 0), "start")
    count = _u16(payload.get("count", 80), "count")
    if "sort_reverse" in payload:
        sort_reverse = _u16(payload["sort_reverse"], "sort_reverse")
    else:
        ascending = bool(payload.get("ascending", False))
        sort_reverse = 0 if sort_type == 0 else (2 if ascending else 1)
    filter_raw = _u16(payload.get("filter_raw", payload.get("filters", 0)), "filter_raw")
    body = _struct_module().pack("<9H", category, sort_type, start, count, sort_reverse, 5, filter_raw, 1, 0)
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_CATEGORY_QUOTES, data=body)


def build_refresh_quotes_frame(payload: dict, msg_id: int) -> RequestFrame:
    items = payload.get("items", payload.get("cursors", payload.get("securities")))
    if items is None:
        items = _normalize_securities(payload)

    normalized: list[tuple[int, str, int]] = []
    for item in _iter_securities(items):
        if isinstance(item, dict):
            market = item.get("market", item.get("market_id", item.get("exchange", "sz")))
            code = item.get("code", item.get("symbol"))
            cursor = item.get("last_update_time_raw", item.get("cursor", 0))
        else:
            parts = tuple(item)
            if len(parts) == 2:
                market, code = parts
                cursor = 0
            elif len(parts) == 3:
                market, code, cursor = parts
            else:
                raise ValueError(f"invalid refresh cursor item: {item!r}")
        market_id = market_to_id(market)
        code_text = str(code or "").strip()
        if len(code_text) != 6 or not code_text.isdigit():
            raise ValueError(f"invalid security code: {code!r}")
        cursor_raw = _u32(cursor, "last_update_time_raw")
        normalized.append((market_id, code_text, cursor_raw))

    count = len(normalized)
    if count <= 0:
        raise ValueError("refresh cursor count must > 0")
    if count > 0xFFFF:
        raise ValueError("refresh cursor count must <= 65535")

    body = bytearray(count.to_bytes(2, "little", signed=False))
    for market_id, code, cursor_raw in normalized:
        body.extend(bytes([market_id]))
        body.extend(code.encode("ascii"))
        body.extend(cursor_raw.to_bytes(4, "little", signed=False))
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_REFRESH_QUOTES, data=bytes(body))


def _build_quote_request_frame(payload: dict, msg_id: int, msg_type: int) -> RequestFrame:
    securities = _normalize_securities(payload)
    count = len(securities)
    if count <= 0:
        raise ValueError("securities count must > 0")
    if count > 0xFFFF:
        raise ValueError("securities count must <= 65535")

    body = bytearray(b"\x05\x00\x00\x00\x00\x00\x00\x00")
    body.extend(count.to_bytes(2, "little", signed=False))
    for market_id, code in securities:
        body.extend(bytes([market_id]))
        body.extend(code.encode("ascii"))
    return RequestFrame(msg_id=msg_id, msg_type=msg_type, data=bytes(body))


def parse_legacy_quotes_payload(
    response: ResponseFrame,
    request_payload: dict | None = None,
) -> list[LegacyQuote]:
    payload = response.data
    if len(payload) < 4:
        raise _protocol_error()("invalid legacy quote payload")

    count = _little_u16(payload[2:4])
    offset = 4
    quotes: list[LegacyQuote] = []
    for _ in range(count):
        quote, offset = _parse_legacy_quote_record(payload, offset)
        quotes.append(quote)
    return quotes


def parse_explicit_quotes_payload(
    response: ResponseFrame,
    request_payload: dict | None = None,
) -> list[ExplicitQuote]:
    payload = response.data
    if len(payload) < 4:
        raise _protocol_error()("invalid explicit quote payload")

    count = _little_u16(payload[2:4])
    offset = 4
    request_markers = _explicit_request_markers(request_payload)
    quotes: list[ExplicitQuote] = []
    for index in range(count):
        next_marker = request_markers[index + 1] if len(request_markers) > index + 1 else None
        record_end = _explicit_record_end(payload, offset, count - index - 1, next_marker)
        quote = _parse_explicit_quote_record(payload, offset, record_end)
        quotes.append(quote)
        offset = record_end
    return quotes


def parse_category_quotes_payload(
    response: ResponseFrame,
    request_payload: dict | None = None,
) -> CategoryQuotePage:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 4:
        raise _protocol_error()("invalid category quote payload")

    header = _little_u16(payload[:2])
    count = _little_u16(payload[2:4])
    offset = 4
    quotes: list[CategoryQuote] = []
    for _ in range(count):
        quote, offset = _parse_category_quote_record(payload, offset)
        quotes.append(quote)
    if offset != len(payload):
        raise _protocol_error()(f"unexpected trailing category quote payload bytes: {len(payload) - offset}")

    sort_type = _u16(request_payload.get("sort_type", request_payload.get("sort", 0)), "sort_type")
    if "sort_reverse" in request_payload:
        sort_reverse = _u16(request_payload["sort_reverse"], "sort_reverse")
    else:
        sort_reverse = 0 if sort_type == 0 else (2 if bool(request_payload.get("ascending", False)) else 1)

    return _model_cls("CategoryQuotePage")(
        category=_u16(request_payload.get("category", 6), "category"),
        sort_type=sort_type,
        start=_u16(request_payload.get("start", 0), "start"),
        request_count=_u16(request_payload.get("count", 80), "count"),
        sort_reverse=sort_reverse,
        filter_raw=_u16(request_payload.get("filter_raw", request_payload.get("filters", 0)), "filter_raw"),
        header=header,
        records=tuple(quotes),
    )


def parse_refresh_quotes_payload(
    response: ResponseFrame,
    request_payload: dict | None = None,
) -> QuoteRefreshBatch:
    decoded = bytes(byte ^ 0x93 for byte in response.data)
    if len(decoded) < 2:
        raise _protocol_error()("invalid refresh quote payload")
    count = _little_u16(decoded[:2])
    if count == 0:
        return _model_cls("QuoteRefreshBatch")(records=())

    offset = 2
    records: list[QuoteRefreshRecord] = []
    for index in range(count):
        record_end = _refresh_record_end(decoded, offset, count - index - 1)
        records.append(_parse_refresh_quote_record(decoded, offset, record_end))
        offset = record_end
    if offset != len(decoded):
        raise _protocol_error()(f"unexpected trailing refresh quote payload bytes: {len(decoded) - offset}")
    return _model_cls("QuoteRefreshBatch")(records=tuple(records))


def _parse_legacy_quote_record(payload: bytes, offset: int) -> tuple[LegacyQuote, int]:
    if len(payload) < offset + 9:
        raise _protocol_error()("truncated legacy quote record header")

    market_id = payload[offset]
    exchange = ID_TO_MARKET.get(market_id)
    if exchange is None:
        raise _protocol_error()(f"invalid legacy quote market id: {market_id!r}")
    try:
        code = payload[offset + 1 : offset + 7].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid legacy quote code") from exc
    active1 = _little_u16(payload[offset + 7 : offset + 9])
    pos = offset + 9

    close_raw, pos = _read_tdx_varint(payload, pos)
    pre_close_diff_raw, pos = _read_tdx_varint(payload, pos)
    open_diff_raw, pos = _read_tdx_varint(payload, pos)
    high_diff_raw, pos = _read_tdx_varint(payload, pos)
    low_diff_raw, pos = _read_tdx_varint(payload, pos)

    close = close_raw / 100.0
    pre_close = (close_raw + pre_close_diff_raw) / 100.0
    open_ = (close_raw + open_diff_raw) / 100.0
    high = (close_raw + high_diff_raw) / 100.0
    low = (close_raw + low_diff_raw) / 100.0

    server_time_raw, pos = _read_tdx_varint(payload, pos)
    _neg_price_or_aux_raw, pos = _read_tdx_varint(payload, pos)
    total_hand, pos = _read_tdx_varint(payload, pos)
    current_hand, pos = _read_tdx_varint(payload, pos)

    if len(payload) < pos + 4:
        raise _protocol_error()("truncated legacy quote amount")
    amount_raw = _little_u32(payload[pos : pos + 4])
    pos += 4

    inside_dish, pos = _read_tdx_varint(payload, pos)
    outer_disc, pos = _read_tdx_varint(payload, pos)
    _unknown_after_outer_raw, pos = _read_tdx_varint(payload, pos)
    _open_amount_raw, pos = _read_tdx_varint(payload, pos)

    bid_vol_sum = 0
    ask_vol_sum = 0
    quote_level = _model_cls("QuoteLevel")
    bid_levels: list[QuoteLevel] = []
    ask_levels: list[QuoteLevel] = []
    for _ in range(5):
        bid_diff_raw, pos = _read_tdx_varint(payload, pos)
        ask_diff_raw, pos = _read_tdx_varint(payload, pos)
        bid_vol_raw, pos = _read_tdx_varint(payload, pos)
        ask_vol_raw, pos = _read_tdx_varint(payload, pos)
        bid_levels.append(
            quote_level(price=(close_raw + bid_diff_raw) / 100.0, volume=bid_vol_raw)
        )
        ask_levels.append(
            quote_level(price=(close_raw + ask_diff_raw) / 100.0, volume=ask_vol_raw)
        )
        bid_vol_sum += bid_vol_raw
        ask_vol_sum += ask_vol_raw

    if len(payload) < pos + 2:
        raise _protocol_error()("truncated legacy quote trading status")
    trading_status_raw = _little_u16(payload[pos : pos + 2])
    pos += 2

    # Older quote records have four varint tail metrics before rise_speed/active2.
    # Keep parsing them only to land on the next record boundary.
    for _ in range(4):
        _tail_metric_raw, pos = _read_tdx_varint(payload, pos)

    active2 = None
    if len(payload) >= pos + 4:
        pos += 2
        active2 = _little_u16(payload[pos : pos + 2])
        pos += 2

    return (
        _model_cls("LegacyQuote")(
            exchange=exchange,
            market_id=market_id,
            code=code,
            active1=active1,
            close=close,
            pre_close=pre_close,
            open=open_,
            high=high,
            low=low,
            server_time_raw=server_time_raw,
            total_hand=total_hand,
            current_hand=current_hand,
            amount_raw=amount_raw,
            inside_dish=inside_dish,
            outer_disc=outer_disc,
            bid_vol_sum=bid_vol_sum,
            ask_vol_sum=ask_vol_sum,
            trading_status_raw=trading_status_raw,
            active2=active2,
            bid_levels=tuple(bid_levels),
            ask_levels=tuple(ask_levels),
        ),
        pos,
    )


def _parse_category_quote_record(payload: bytes, offset: int) -> tuple[CategoryQuote, int]:
    if len(payload) < offset + 9:
        raise _protocol_error()("truncated category quote record header")

    market_id = payload[offset]
    exchange = ID_TO_MARKET.get(market_id)
    if exchange is None:
        raise _protocol_error()(f"invalid category quote market id: {market_id!r}")
    try:
        code = payload[offset + 1 : offset + 7].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid category quote code") from exc
    active1 = _little_u16(payload[offset + 7 : offset + 9])
    pos = offset + 9

    close_raw, pos = _read_tdx_varint(payload, pos)
    pre_close_diff_raw, pos = _read_tdx_varint(payload, pos)
    open_diff_raw, pos = _read_tdx_varint(payload, pos)
    high_diff_raw, pos = _read_tdx_varint(payload, pos)
    low_diff_raw, pos = _read_tdx_varint(payload, pos)

    last_price = close_raw / 100.0
    pre_close = (close_raw + pre_close_diff_raw) / 100.0
    open_ = (close_raw + open_diff_raw) / 100.0
    high = (close_raw + high_diff_raw) / 100.0
    low = (close_raw + low_diff_raw) / 100.0

    time_raw, pos = _read_tdx_varint(payload, pos)
    _neg_price_raw, pos = _read_tdx_varint(payload, pos)
    total_hand, pos = _read_tdx_varint(payload, pos)
    current_hand, pos = _read_tdx_varint(payload, pos)

    if len(payload) < pos + 4:
        raise _protocol_error()("truncated category quote amount")
    amount_raw = _little_u32(payload[pos : pos + 4])
    amount = _decode_compact_float(amount_raw)
    pos += 4

    inside_dish, pos = _read_tdx_varint(payload, pos)
    outer_disc, pos = _read_tdx_varint(payload, pos)
    after_outer_raw, pos = _read_tdx_varint(payload, pos)
    open_amount_raw, pos = _read_tdx_varint(payload, pos)

    bid1_diff_raw, pos = _read_tdx_varint(payload, pos)
    ask1_diff_raw, pos = _read_tdx_varint(payload, pos)
    bid1_volume, pos = _read_tdx_varint(payload, pos)
    ask1_volume, pos = _read_tdx_varint(payload, pos)

    if len(payload) < pos + 56:
        raise _protocol_error()("truncated category quote tail")
    tail = payload[pos : pos + 56]
    pos += 56
    tail_fields = _parse_category_quote_tail(tail)

    return (
        _model_cls("CategoryQuote")(
            exchange=exchange,
            market_id=market_id,
            code=code,
            active1=active1,
            last_price=last_price,
            pre_close=pre_close,
            open=open_,
            high=high,
            low=low,
            time_raw=time_raw,
            total_hand=total_hand,
            current_hand=current_hand,
            amount_raw=amount_raw,
            amount=amount,
            inside_dish=inside_dish,
            outer_disc=outer_disc,
            after_outer_raw=after_outer_raw,
            open_amount_raw=open_amount_raw,
            open_amount=float(open_amount_raw) * 100.0,
            bid1_price=(close_raw + bid1_diff_raw) / 100.0,
            bid1_volume=bid1_volume,
            ask1_price=(close_raw + ask1_diff_raw) / 100.0,
            ask1_volume=ask1_volume,
            **tail_fields,
        ),
        pos,
    )


def _parse_explicit_quote_record(payload: bytes, offset: int, record_end: int) -> ExplicitQuote:
    if record_end < offset + 9:
        raise _protocol_error()("truncated explicit quote record header")

    market_id = payload[offset]
    exchange = ID_TO_MARKET.get(market_id)
    if exchange is None:
        raise _protocol_error()(f"invalid explicit quote market id: {market_id!r}")
    try:
        code = payload[offset + 1 : offset + 7].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid explicit quote code") from exc
    active1 = _little_u16(payload[offset + 7 : offset + 9])
    pos = offset + 9

    close_raw, pos = _read_tdx_varint(payload, pos)
    pre_close_diff_raw, pos = _read_tdx_varint(payload, pos)
    open_diff_raw, pos = _read_tdx_varint(payload, pos)
    high_diff_raw, pos = _read_tdx_varint(payload, pos)
    low_diff_raw, pos = _read_tdx_varint(payload, pos)

    last_price = close_raw / 100.0
    pre_close = (close_raw + pre_close_diff_raw) / 100.0
    open_ = (close_raw + open_diff_raw) / 100.0
    high = (close_raw + high_diff_raw) / 100.0
    low = (close_raw + low_diff_raw) / 100.0

    time_raw, pos = _read_tdx_varint(payload, pos)
    _unknown_after_time_raw, pos = _read_tdx_varint(payload, pos)
    total_hand, pos = _read_tdx_varint(payload, pos)
    current_hand, pos = _read_tdx_varint(payload, pos)

    if record_end < pos + 4:
        raise _protocol_error()("truncated explicit quote amount")
    amount_raw = _little_u32(payload[pos : pos + 4])
    amount = _decode_compact_float(amount_raw)
    pos += 4

    inside_dish, pos = _read_tdx_varint(payload, pos)
    outer_disc, pos = _read_tdx_varint(payload, pos)
    _unknown_after_outer_raw, pos = _read_tdx_varint(payload, pos)
    open_amount_raw, pos = _read_tdx_varint(payload, pos)

    bid1_diff_raw, pos = _read_tdx_varint(payload, pos)
    ask1_diff_raw, pos = _read_tdx_varint(payload, pos)
    bid1_volume, pos = _read_tdx_varint(payload, pos)
    ask1_volume, pos = _read_tdx_varint(payload, pos)

    tail = payload[pos:record_end]
    tail_fields = _parse_explicit_quote_tail(tail)

    return _model_cls("ExplicitQuote")(
        exchange=exchange,
        market_id=market_id,
        code=code,
        active1=active1,
        last_price=last_price,
        pre_close=pre_close,
        open=open_,
        high=high,
        low=low,
        time_raw=time_raw,
        total_hand=total_hand,
        current_hand=current_hand,
        amount_raw=amount_raw,
        amount=amount,
        inside_dish=inside_dish,
        outer_disc=outer_disc,
        open_amount_raw=open_amount_raw,
        open_amount=float(open_amount_raw) * 100.0,
        bid1_price=(close_raw + bid1_diff_raw) / 100.0,
        bid1_volume=bid1_volume,
        ask1_price=(close_raw + ask1_diff_raw) / 100.0,
        ask1_volume=ask1_volume,
        **tail_fields,
    )


def _parse_refresh_quote_record(payload: bytes, offset: int, record_end: int) -> QuoteRefreshRecord:
    if record_end < offset + 9:
        raise _protocol_error()("truncated refresh quote record header")

    market_id = payload[offset]
    exchange = ID_TO_MARKET.get(market_id)
    if exchange is None:
        raise _protocol_error()(f"invalid refresh quote market id: {market_id!r}")
    try:
        code = payload[offset + 1 : offset + 7].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid refresh quote code") from exc

    active = _little_u16(payload[offset + 7 : offset + 9])
    pos = offset + 9

    close_raw, pos = _read_tdx_varint(payload, pos)
    pre_close_diff_raw, pos = _read_tdx_varint(payload, pos)
    open_diff_raw, pos = _read_tdx_varint(payload, pos)
    high_diff_raw, pos = _read_tdx_varint(payload, pos)
    low_diff_raw, pos = _read_tdx_varint(payload, pos)

    last_price = close_raw / 100.0
    pre_close = (close_raw + pre_close_diff_raw) / 100.0
    open_ = (close_raw + open_diff_raw) / 100.0
    high = (close_raw + high_diff_raw) / 100.0
    low = (close_raw + low_diff_raw) / 100.0

    if record_end < pos + 4:
        raise _protocol_error()("truncated refresh quote update time")
    update_time_raw = _little_u32(payload[pos : pos + 4])
    pos += 4

    status_or_reserved_raw, pos = _read_tdx_varint(payload, pos)
    total_hand, pos = _read_tdx_varint(payload, pos)
    current_hand, pos = _read_tdx_varint(payload, pos)

    if record_end < pos + 4:
        raise _protocol_error()("truncated refresh quote amount")
    amount_raw = _little_u32(payload[pos : pos + 4])
    amount = _decode_compact_float(amount_raw)
    pos += 4

    inside_dish, pos = _read_tdx_varint(payload, pos)
    outer_disc, pos = _read_tdx_varint(payload, pos)
    _unknown_after_outer_raw, pos = _read_tdx_varint(payload, pos)
    open_amount_raw, pos = _read_tdx_varint(payload, pos)

    quote_level = _model_cls("QuoteLevel")
    bid_levels: list[QuoteLevel] = []
    ask_levels: list[QuoteLevel] = []
    for _ in range(5):
        bid_diff_raw, pos = _read_tdx_varint(payload, pos)
        ask_diff_raw, pos = _read_tdx_varint(payload, pos)
        bid_volume, pos = _read_tdx_varint(payload, pos)
        ask_volume, pos = _read_tdx_varint(payload, pos)
        bid_levels.append(quote_level(price=(close_raw + bid_diff_raw) / 100.0, volume=bid_volume))
        ask_levels.append(quote_level(price=(close_raw + ask_diff_raw) / 100.0, volume=ask_volume))

    return _model_cls("QuoteRefreshRecord")(
        exchange=exchange,
        market_id=market_id,
        code=code,
        active=active,
        last_price=last_price,
        pre_close=pre_close,
        open=open_,
        high=high,
        low=low,
        update_time_raw=update_time_raw,
        status_or_reserved_raw=status_or_reserved_raw,
        total_hand=total_hand,
        current_hand=current_hand,
        amount_raw=amount_raw,
        amount=amount,
        inside_dish=inside_dish,
        outer_disc=outer_disc,
        open_amount_raw=open_amount_raw,
        open_amount=float(open_amount_raw) * 10.0,
        bid_levels=tuple(bid_levels),
        ask_levels=tuple(ask_levels),
    )


def _parse_explicit_quote_tail(tail: bytes) -> dict[str, object]:
    fields: dict[str, object] = {
        "rise_speed": None,
        "short_turnover": None,
        "min2_amount": None,
        "opening_rush": None,
        "vol_rise_speed": None,
        "entrust_ratio": None,
        "active2": None,
        "unknown_tail_raw": None,
    }
    if len(tail) < 2:
        return fields

    fields["unknown_tail_raw"] = _little_u16(tail[0:2])
    if len(tail) >= 6:
        fields["rise_speed"] = _little_i16(tail[2:4]) / 100.0
        fields["short_turnover"] = _little_i16(tail[4:6]) / 100.0
    if len(tail) >= 10:
        fields["min2_amount"] = float(_little_f32(tail[6:10]))
    if len(tail) >= 12:
        fields["opening_rush"] = _little_i16(tail[10:12]) / 100.0
    if len(tail) >= 26:
        fields["vol_rise_speed"] = float(_little_f32(tail[22:26]))
    if len(tail) >= 30:
        fields["entrust_ratio"] = float(_little_f32(tail[26:30]))
    if len(tail) >= 56:
        fields["active2"] = _little_u16(tail[54:56])
    elif len(tail) >= 2:
        fields["active2"] = _little_u16(tail[-2:])
    return fields


def _parse_category_quote_tail(tail: bytes) -> dict[str, object]:
    if len(tail) != 56:
        raise _protocol_error()(f"invalid category quote tail length: {len(tail)}")
    (
        status_or_sort_raw,
        rise_speed_raw,
        short_turnover_raw,
        min2_amount,
        opening_rush_raw,
        _extra_pair_raw,
        vol_rise_speed,
        entrust_ratio,
        _extra_meta_raw,
        active2,
    ) = _struct_module().unpack("<Hhhfh10sff24sH", tail)
    return {
        "status_or_sort_raw": status_or_sort_raw,
        "rise_speed": rise_speed_raw / 100.0,
        "short_turnover": short_turnover_raw / 100.0,
        "min2_amount": float(min2_amount),
        "opening_rush": opening_rush_raw / 100.0,
        "vol_rise_speed": float(vol_rise_speed),
        "entrust_ratio": float(entrust_ratio),
        "active2": active2,
    }


def _explicit_record_end(
    payload: bytes,
    offset: int,
    remaining_records: int,
    next_marker: bytes | None,
) -> int:
    if remaining_records <= 0:
        return len(payload)

    minimum = offset + 9
    if next_marker is not None:
        marker_pos = payload.find(next_marker, minimum)
        if marker_pos >= 0:
            return marker_pos

    for pos in range(minimum, len(payload) - 8):
        if payload[pos] not in ID_TO_MARKET:
            continue
        code_raw = payload[pos + 1 : pos + 7]
        if len(code_raw) == 6 and code_raw.isdigit():
            return pos
    raise _protocol_error()("unable to locate next explicit quote record")


def _refresh_record_end(payload: bytes, offset: int, remaining_records: int) -> int:
    if remaining_records <= 0:
        return len(payload)
    minimum = offset + 9
    for pos in range(minimum, len(payload) - 6):
        if payload[pos] not in ID_TO_MARKET:
            continue
        code_raw = payload[pos + 1 : pos + 7]
        if len(code_raw) == 6 and code_raw.isdigit():
            return pos
    raise _protocol_error()("unable to locate next refresh quote record")


def _little_i16(data: bytes) -> int:
    return int.from_bytes(data, "little", signed=True)


def _explicit_request_markers(request_payload: dict | None) -> list[bytes]:
    if not request_payload:
        return []
    try:
        securities = _normalize_securities(request_payload)
    except (TypeError, ValueError):
        return []
    return [bytes([market_id]) + code.encode("ascii") for market_id, code in securities]


def _normalize_securities(payload: dict) -> list[tuple[int, str]]:
    securities = payload.get("securities")
    if securities is None:
        market = payload.get("market", payload.get("market_id", "sz"))
        code = payload.get("code")
        if code is None:
            securities = []
        else:
            securities = [(market, code)]

    normalized: list[tuple[int, str]] = []
    for item in _iter_securities(securities):
        if isinstance(item, dict):
            market = item.get("market", item.get("market_id", item.get("exchange", "sz")))
            code = item.get("code", item.get("symbol"))
        else:
            market, code = item
        market_id = market_to_id(market)
        code_text = str(code or "").strip()
        if len(code_text) != 6 or not code_text.isdigit():
            raise ValueError(f"invalid security code: {code!r}")
        normalized.append((market_id, code_text))
    return normalized


def _iter_securities(securities: object) -> Iterable[object]:
    if securities is None:
        return ()
    if isinstance(securities, Sequence) and not isinstance(securities, (str, bytes, bytearray)):
        return securities
    return (securities,)


def _u16(value: object, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if not 0 <= parsed <= 0xFFFF:
        raise ValueError(f"{field_name} must be between 0 and 65535")
    return parsed


def _u32(value: object, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if not 0 <= parsed <= 0xFFFFFFFF:
        raise ValueError(f"{field_name} must be between 0 and 4294967295")
    return parsed


def _read_tdx_varint(data: bytes, pos: int) -> tuple[int, int]:
    if pos >= len(data):
        raise _protocol_error()("truncated TDX varint")

    shift = 6
    first = data[pos]
    value = first & 0x3F
    negative = bool(first & 0x40)
    if first & 0x80:
        while True:
            pos += 1
            if pos >= len(data):
                raise _protocol_error()("truncated TDX varint")
            current = data[pos]
            value += (current & 0x7F) << shift
            shift += 7
            if not current & 0x80:
                break
    pos += 1

    if negative:
        value = -value
    return value, pos


def __getattr__(name: str):
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    if name in _MODEL_EXPORTS:
        value = _model_cls(name)
        globals()[name] = value
        return value
    if name in _BINARY_EXPORTS:
        value = getattr(import_module(_BINARY_MODULE), name)
        globals()[name] = value
        return value
    if name == "struct":
        return _struct_module()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _MODEL_EXPORTS | _BINARY_EXPORTS | _STDLIB_EXPORTS)
