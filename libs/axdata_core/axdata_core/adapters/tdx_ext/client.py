"""Short-connection client for TDX extended market source requests."""

from __future__ import annotations

import socket
import struct
import zlib
from collections.abc import Sequence
from dataclasses import dataclass

from .exceptions import ConnectionClosedError, ProtocolError, ResponseTimeoutError
from .models import (
    TdxExtIntradayPoint,
    TdxExtInstrument,
    TdxExtKlineBar,
    TdxExtMarket,
    TdxExtQuote,
    TdxExtQuoteLevel,
    TdxExtTrade,
)
from .servers import TdxExtServer


LOGIN_BODY = bytes.fromhex(
    "e5 bb 1c 2f af e5 25 94 1f 32 c6 e5 d5 3d fb 41"
    "5b 73 4c c9 cd bf 0a c9 20 21 bf dd 1e b0 6d 22"
    "d0 08 88 4c 16 11 cb 13 78 f6 ab d8 24 d8 99 d2"
    "1f 32 c6 e5 d5 3d fb 41 1f 32 c6 e5 d5 3d fb 41"
    "a9 32 5a c9 35 dc 08 37 33 5a 16 e4 ce 17 c1 bb"
)


@dataclass(slots=True)
class TdxExtClient:
    """Small request/response client for extended market data."""

    servers: Sequence[TdxExtServer] | None = None
    timeout: float = 6.0
    setup_on_connect: bool = False
    _socket: socket.socket | None = None
    _connected_server: TdxExtServer | None = None
    _initialized: bool = False

    @classmethod
    def from_config(
        cls,
        *,
        tdx_root: str | None = None,
        server_cache_root: str | None = None,
        timeout: float = 6.0,
    ) -> "TdxExtClient":
        _ = tdx_root
        servers = _configured_extended_servers(cache_root=server_cache_root)
        return cls(servers=servers, timeout=timeout)

    @property
    def connected_server(self) -> TdxExtServer | None:
        return self._connected_server

    def connect(self) -> None:
        if self._socket is not None:
            return
        candidates = _primary_first(tuple(self.servers or _configured_extended_servers()))
        last_error: OSError | None = None
        for server in candidates:
            try:
                sock = socket.create_connection((server.host, server.port), timeout=self.timeout)
                sock.settimeout(self.timeout)
            except OSError as exc:
                last_error = exc
                continue
            self._socket = sock
            self._connected_server = server
            try:
                if self.setup_on_connect:
                    self.login()
            except Exception:
                self.close()
                continue
            return
        raise ConnectionClosedError("unable to connect to any TDX extended market server") from last_error

    def close(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            finally:
                self._socket = None
                self._connected_server = None
                self._initialized = False

    def __enter__(self) -> "TdxExtClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def login(self) -> dict[str, object]:
        response = parse_login_response(self._execute_raw(_package(0x2454, LOGIN_BODY)))
        self._initialized = True
        return response

    def get_server_info(self) -> dict[str, object]:
        return parse_server_info_response(self._execute_once(_package(0x2455)))

    def get_markets(self) -> tuple[TdxExtMarket, ...]:
        return parse_markets_response(self._execute_once(_package(0x23F4)))

    def get_instrument_count(self) -> int:
        return parse_instrument_count_response(self._execute_once(_package(0x23F0)))

    def get_instrument_info(self, start: int = 0, count: int = 100) -> tuple[TdxExtInstrument, ...]:
        if start < 0:
            raise ValueError("start must be >= 0")
        if count < 0:
            raise ValueError("count must be >= 0")
        package = _package(0x23F5, struct.pack("<IH", int(start), int(count)))
        return parse_instrument_info_response(self._execute_once(package))

    def get_instruments_all(self, *, page_size: int = 1000) -> tuple[TdxExtInstrument, ...]:
        total = self.get_instrument_count()
        rows: list[TdxExtInstrument] = []
        start = 0
        while start < total:
            page = self.get_instrument_info(start=start, count=min(page_size, total - start))
            if not page:
                break
            rows.extend(page)
            start += len(page)
        return tuple(rows)

    def get_instrument_quote(self, market: int, code: str) -> tuple[TdxExtQuote, ...]:
        encoded = str(code).encode("gbk", errors="ignore")
        body = struct.pack("<B9s", int(market), encoded[:9])
        package = _package(0x23FA, body)
        return parse_instrument_quote_response(self._execute_once(package))

    def get_quote_list(
        self,
        market: int,
        *,
        start: int = 0,
        count: int = 100,
        sort_type: int = 0,
        reverse: bool = False,
    ) -> tuple[TdxExtQuote, ...]:
        body = struct.pack("<BHHHH", int(market), int(sort_type), int(start), int(count), 2 if reverse else 1)
        package = _package(0x2484, body)
        return parse_quotes_list_response(self._execute_once(package))

    def get_quote_multi(self, code_list: Sequence[tuple[int, str]]) -> tuple[TdxExtQuote, ...]:
        if not code_list:
            raise ValueError("code_list must not be empty")
        body = bytearray(struct.pack("<B7xH", 5, len(code_list)))
        for market, code in code_list:
            body.extend(struct.pack("<B23s", int(market), str(code).encode("gbk", errors="ignore")[:23]))
        package = _package(0x248A, bytes(body))
        return parse_quotes_multi_response(self._execute_once(package))

    def get_quote_multi2(self, code_list: Sequence[tuple[int, str]]) -> tuple[TdxExtQuote, ...]:
        if not code_list:
            raise ValueError("code_list must not be empty")
        body = bytearray(struct.pack("<HHHHH", 2, 3148, 0, 600, len(code_list)))
        for market, code in code_list:
            body.extend(struct.pack("<B23s", int(market), str(code).encode("gbk", errors="ignore")[:23]))
        package = _package(0x23FB, bytes(body))
        return parse_quotes_multi_response(self._execute_once(package))

    def get_kline(
        self,
        market: int,
        code: str,
        period: int,
        *,
        times: int = 1,
        start: int = 0,
        count: int = 800,
    ) -> tuple[TdxExtKlineBar, ...]:
        body = struct.pack("<B9sHHIH", int(market), str(code).encode("gbk", errors="ignore")[:9], int(period), int(times), int(start), int(count))
        package = _package(0x23FF, body)
        return parse_kline_response(self._execute_once(package))

    def get_kline2(
        self,
        market: int,
        code: str,
        period: int,
        *,
        times: int = 1,
        start: int = 0,
        count: int = 800,
    ) -> tuple[TdxExtKlineBar, ...]:
        body = struct.pack("<B23sHHII16x", int(market), str(code).encode("gbk", errors="ignore")[:23], int(period), int(times), int(start), int(count))
        package = _package(0x2489, body)
        return parse_kline2_response(self._execute_once(package))

    def get_tick_chart(self, market: int, code: str) -> tuple[TdxExtIntradayPoint, ...]:
        body = struct.pack("<B23s8x", int(market), str(code).encode("gbk", errors="ignore")[:23])
        package = _package(0x248B, body)
        return parse_tick_chart_response(self._execute_once(package))

    def get_history_tick_chart(self, market: int, code: str, query_date: str | int) -> tuple[TdxExtIntradayPoint, ...]:
        date_int = int(str(query_date).replace("-", ""))
        body = struct.pack("<IB23s6sH", date_int, int(market), str(code).encode("gbk", errors="ignore")[:23], b"", 0)
        package = _package(0x248C, body)
        return parse_history_tick_chart_response(self._execute_once(package))

    def get_history_transaction(
        self,
        market: int,
        code: str,
        query_date: str | int,
        *,
        start: int = 0,
        count: int = 1800,
        price_scale: int | None = None,
    ) -> tuple[TdxExtTrade, ...]:
        if start < 0:
            raise ValueError("start must be >= 0")
        if count <= 0:
            raise ValueError("count must be > 0")
        date_int = int(str(query_date).replace("-", ""))
        encoded = str(code).encode("gbk", errors="ignore")[:9]
        body = struct.pack("<IB9siH", date_int, int(market), encoded, int(start), int(count))
        package = _package(0x2406, body)
        return parse_history_transaction_response(
            self._execute_once(package),
            trade_date=str(date_int),
            price_scale=price_scale,
        )

    def get_today_transaction(
        self,
        market: int,
        code: str,
        *,
        start: int = 0,
        count: int = 1800,
        price_scale: int | None = None,
    ) -> tuple[TdxExtTrade, ...]:
        if start < 0:
            raise ValueError("start must be >= 0")
        if count <= 0:
            raise ValueError("count must be > 0")
        encoded = str(code).encode("gbk", errors="ignore")[:9]
        body = struct.pack("<B9siH", int(market), encoded, int(start), int(count))
        package = _package(0x23FC, body)
        return parse_transaction_response(self._execute_once(package), price_scale=price_scale)

    def _execute_once(self, package: bytes) -> bytes:
        if self._socket is not None:
            return self._execute(package)
        self.connect()
        try:
            return self._execute(package)
        finally:
            self.close()

    def _execute(self, package: bytes) -> bytes:
        self.connect()
        assert self._socket is not None
        if not self._initialized:
            self.login()
        return self._execute_raw(package)

    def _execute_raw(self, package: bytes) -> bytes:
        self.connect()
        assert self._socket is not None
        try:
            self._socket.sendall(package)
            return _read_body(self._socket)
        except socket.timeout as exc:
            raise ResponseTimeoutError("TDX extended market response timed out") from exc
        except OSError as exc:
            self.close()
            raise ConnectionClosedError("TDX extended market socket closed") from exc


def create_tdx_ext_client(**kwargs) -> TdxExtClient:
    return TdxExtClient.from_config(**kwargs)


def effective_servers(kind: str, *, cache_root: str | None = None) -> Sequence[object]:
    """Return configured extended servers through the shared server config lazily."""

    from .host_config import effective_servers as resolve_servers

    return resolve_servers(kind, cache_root=cache_root)


def _configured_extended_servers(*, cache_root: str | None = None) -> tuple[TdxExtServer, ...]:
    from .host_config import configured_extended_servers

    return configured_extended_servers(
        cache_root=cache_root,
        effective_servers_func=effective_servers,
        unavailable_error=ConnectionClosedError,
    )


def parse_login_response(body: bytes) -> dict[str, object]:
    if len(body) < 299:
        raise ProtocolError("truncated extended market login response")
    _, _, year, month, day, minute, hour, ms, second, server_name, u1, u2, u3, u4, u5, desc, u6, u7, u8, ip = struct.unpack(
        "<B52sHBBBBBB21sfBHHH151sBBB52s",
        body[:299],
    )
    return {
        "date_time": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}",
        "server_name": _decode_text(server_name),
        "desc": _decode_text(desc),
        "ip": _decode_text(ip),
        "unknown": [u1, u2, u3, u4, u5, u6, u7, u8],
    }


def parse_server_info_response(body: bytes) -> dict[str, object]:
    if len(body) < 327:
        raise ProtocolError("truncated extended market server info response")
    maybe_delay, _, _, _, info, version = struct.unpack("<4I25s29s", body[:70])
    server_sign, _ = struct.unpack("<13sB", body[117:131])
    name, = struct.unpack("<30s", body[159:189])
    server_sign2, = struct.unpack("<13s", body[240:253])
    return {
        "delay": maybe_delay,
        "info": _decode_text(info),
        "version": _decode_text(version),
        "server_sign": _decode_text(server_sign),
        "server_sign2": _decode_text(server_sign2),
        "name": _decode_text(name),
        "time_now": None,
    }


def parse_markets_response(body: bytes) -> tuple[TdxExtMarket, ...]:
    if len(body) < 2:
        return ()
    count = struct.unpack("<H", body[:2])[0]
    pos = 2
    rows: list[TdxExtMarket] = []
    for _ in range(count):
        if pos + 64 > len(body):
            raise ProtocolError("truncated extended market list response")
        category, raw_name, market, raw_short_name = struct.unpack("<B32sB2s26s2s", body[pos : pos + 64])[:4]
        pos += 64
        if category == 0 and market == 0:
            continue
        rows.append(
            TdxExtMarket(
                category=category,
                market=market,
                name=_decode_text(raw_name),
                short_name=_decode_text(raw_short_name),
            )
        )
    return tuple(rows)


def parse_instrument_count_response(body: bytes) -> int:
    if len(body) < 23:
        raise ProtocolError("truncated extended instrument count response")
    return struct.unpack("<I", body[19:23])[0]


def parse_instrument_info_response(body: bytes) -> tuple[TdxExtInstrument, ...]:
    if len(body) < 6:
        return ()
    _, count = struct.unpack("<IH", body[:6])
    pos = 6
    rows: list[TdxExtInstrument] = []
    for _ in range(count):
        if pos + 64 > len(body):
            raise ProtocolError("truncated extended instrument info response")
        category, market, _, raw_code, raw_name, raw_desc = struct.unpack("<BB3s9s17s9s", body[pos : pos + 40])
        rows.append(
            TdxExtInstrument(
                category=category,
                market=market,
                code=_decode_text(raw_code),
                name=_decode_text(raw_name),
                desc=_decode_text(raw_desc),
            )
        )
        pos += 64
    return tuple(rows)


def parse_instrument_quote_response(body: bytes) -> tuple[TdxExtQuote, ...]:
    if len(body) < 300:
        return ()
    return (_parse_quote_row(body, code_len=9),)


def parse_quotes_list_response(body: bytes) -> tuple[TdxExtQuote, ...]:
    if len(body) < 10:
        return ()
    _, _, count = struct.unpack("<IIH", body[:10])
    rows: list[TdxExtQuote] = []
    for i in range(count):
        start = 10 + 314 * i
        end = start + 314
        if end > len(body):
            raise ProtocolError("truncated extended quotes list response")
        rows.append(_parse_quote_row(body[start:end], code_len=23))
    return tuple(rows)


def parse_quotes_multi_response(body: bytes) -> tuple[TdxExtQuote, ...]:
    return parse_quotes_list_response(body)


def parse_kline_response(body: bytes) -> tuple[TdxExtKlineBar, ...]:
    if len(body) < 20:
        return ()
    market, raw_code, period, times, _, count = struct.unpack("<B9sHHIH", body[:20])
    rows: list[TdxExtKlineBar] = []
    for i in range(count):
        start = 20 + 32 * i
        end = start + 32
        if end > len(body):
            raise ProtocolError("truncated extended kline response")
        date_num, open_, high, low, close, open_interest, volume, settlement = struct.unpack("<IffffIIf", body[start:end])
        rows.append(
            TdxExtKlineBar(
                market=market,
                code=_decode_text(raw_code),
                trade_time=str(date_num),
                period=str(period),
                open=_none_zero_price(open_),
                high=_none_zero_price(high),
                low=_none_zero_price(low),
                close=_none_zero_price(close),
                amount=None,
                volume=int(volume),
                open_interest=int(open_interest),
                settlement=_none_zero_price(settlement),
            )
        )
    return tuple(rows)


def parse_kline2_response(body: bytes) -> tuple[TdxExtKlineBar, ...]:
    if len(body) < 42:
        return ()
    market, raw_code, period, times, start, _, _, count = struct.unpack("<B23sHHIIIH", body[:42])
    rows: list[TdxExtKlineBar] = []
    for i in range(count):
        start_pos = 42 + 32 * i
        end_pos = start_pos + 32
        if end_pos > len(body):
            raise ProtocolError("truncated extended kline2 response")
        date_num, open_, high, low, close, open_interest, volume, settlement = struct.unpack("<IffffIIf", body[start_pos:end_pos])
        rows.append(
            TdxExtKlineBar(
                market=market,
                code=_decode_text(raw_code),
                trade_time=str(date_num),
                period=str(period),
                open=_none_zero_price(open_),
                high=_none_zero_price(high),
                low=_none_zero_price(low),
                close=_none_zero_price(close),
                amount=None,
                volume=int(volume),
                open_interest=int(open_interest),
                settlement=_none_zero_price(settlement),
            )
        )
    return tuple(rows)


def parse_tick_chart_response(body: bytes) -> tuple[TdxExtIntradayPoint, ...]:
    if len(body) < 34:
        return ()
    market, raw_code, count = struct.unpack("<B31sH", body[:34])
    rows: list[TdxExtIntradayPoint] = []
    for i in range(count):
        start = 34 + 18 * i
        end = start + 18
        if end > len(body):
            raise ProtocolError("truncated extended tick chart response")
        minutes, price, avg, vol, _ = struct.unpack("<HffII", body[start:end])
        rows.append(
            TdxExtIntradayPoint(
                market=market,
                code=_decode_text(raw_code),
                trade_date=None,
                time_label=f"{minutes // 60:02d}:{minutes % 60:02d}",
                price=_none_zero_price(price),
                average_price=_none_zero_price(avg),
                volume=int(vol),
            )
        )
    return tuple(rows)


def parse_history_tick_chart_response(body: bytes) -> tuple[TdxExtIntradayPoint, ...]:
    if len(body) < 42:
        return ()
    market, raw_code, trade_date, avg_price, _, _, count = struct.unpack("<B23sIfIIH", body[:42])
    rows: list[TdxExtIntradayPoint] = []
    for i in range(count):
        start = 42 + 18 * i
        end = start + 18
        if end > len(body):
            raise ProtocolError("truncated extended history tick chart response")
        minutes, price, avg, vol, _ = struct.unpack("<HffII", body[start:end])
        rows.append(
            TdxExtIntradayPoint(
                market=market,
                code=_decode_text(raw_code),
                trade_date=str(trade_date),
                time_label=f"{minutes // 60:02d}:{minutes % 60:02d}",
                price=_none_zero_price(price),
                average_price=_none_zero_price(avg),
                volume=int(vol),
            )
        )
    return tuple(rows)


def parse_transaction_response(
    body: bytes,
    *,
    trade_date: str | None = None,
    price_scale: int | None = None,
) -> tuple[TdxExtTrade, ...]:
    if len(body) < 16:
        return ()
    market, name, _, count = struct.unpack("<B9s4sH", body[:16])
    scale = price_scale or _infer_trade_price_scale(market=market, start_price=None)
    rows: list[TdxExtTrade] = []
    for i in range(count):
        start = 16 + 16 * i
        end = start + 16
        if end > len(body):
            raise ProtocolError("truncated extended transaction response")
        minutes, price_raw, vol, position_change_raw, marker_raw = struct.unpack("<HIIIH", body[start:end])
        position_change = struct.unpack("<i", struct.pack("<I", position_change_raw))[0]
        seconds = int(marker_raw) % 10000
        if seconds > 59:
            seconds = 0
        direction_marker = int(marker_raw) // 10000
        price = price_raw / scale if scale > 0 else None
        rows.append(
            TdxExtTrade(
                market=market,
                code=_decode_text(name),
                trade_date=trade_date,
                time_label=f"{minutes // 60:02d}:{minutes % 60:02d}:{seconds:02d}",
                price_raw=int(price_raw),
                price=round(price, 6) if price is not None else None,
                volume=int(vol),
                position_change=int(position_change),
                direction_marker=int(direction_marker),
            )
        )
    return tuple(rows)


def parse_history_transaction_response(
    body: bytes,
    *,
    trade_date: str | None = None,
    price_scale: int | None = None,
) -> tuple[TdxExtTrade, ...]:
    return parse_transaction_response(body, trade_date=trade_date, price_scale=price_scale)


def _infer_trade_price_scale(*, market: int, start_price: float | None) -> int:
    if market == 10:
        return 10000
    if start_price and abs(start_price) < 100:
        return 1000
    return 1000


def _package(msg_id: int, body: bytes = b"") -> bytes:
    request_body = struct.pack("<H", msg_id) + body
    return struct.pack("<BIBHH", 1, 0, 1, len(request_body), len(request_body)) + request_body


def _read_body(sock: socket.socket) -> bytes:
    header = _read_exact(sock, 16)
    if len(header) != 16:
        raise ConnectionClosedError("TDX extended market response header is incomplete")
    _, _, _, _, _, zip_size, unzip_size = struct.unpack("<IBIBHHH", header)
    payload = _read_exact(sock, zip_size)
    if zip_size == unzip_size:
        return payload
    return zlib.decompress(payload)


def _read_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = sock.recv(size - len(chunks))
        if not piece:
            raise ConnectionClosedError("socket closed by remote peer")
        chunks.extend(piece)
    return bytes(chunks)


def _decode_text(raw: bytes) -> str:
    return raw.decode("gb18030", errors="ignore").rstrip("\x00").strip()


def _none_zero_price(value: float) -> float | None:
    return None if value == 0 else float(value)


def _primary_first(servers: Sequence[TdxExtServer]) -> tuple[TdxExtServer, ...]:
    return tuple(sorted(servers, key=lambda server: (not server.is_primary, server.index)))


def _parse_quote_row(body: bytes, *, code_len: int) -> TdxExtQuote:
    if len(body) < 291 + code_len:
        raise ProtocolError("truncated extended quote response")
    market, raw_code = struct.unpack(f"<B{code_len}s", body[: 1 + code_len])
    (
        active,
        pre_close,
        open_price,
        high,
        low,
        close,
        open_interest_change,
        add_position,
        vol,
        curr_vol,
        amount,
        inside_volume,
        outside_volume,
        _u14,
        open_interest,
    ) = struct.unpack(f"<I5f4If4I", body[1 + code_len : 61 + code_len])
    handicap_list = struct.unpack("<5f5I5f5I", body[61 + code_len : 141 + code_len])
    _u1, settlement, _u2, avg, pre_settlement, *_rest = struct.unpack("<HfIffIIIIf", body[141 + code_len : 179 + code_len])
    _s1, pre_vol, *_tail = struct.unpack("<12sff12sff25sfIIff24sHB", body[179 + code_len : 291 + code_len])
    date_raw = _tail[6]
    raise_speed = _tail[8]
    bid_levels = tuple(
        TdxExtQuoteLevel(price=_none_zero_price(price), volume=volume)
        for price, volume in (
            (handicap_list[0], handicap_list[5]),
            (handicap_list[1], handicap_list[6]),
            (handicap_list[2], handicap_list[7]),
            (handicap_list[3], handicap_list[8]),
            (handicap_list[4], handicap_list[9]),
        )
    )
    ask_levels = tuple(
        TdxExtQuoteLevel(price=_none_zero_price(price), volume=volume)
        for price, volume in (
            (handicap_list[10], handicap_list[15]),
            (handicap_list[11], handicap_list[16]),
            (handicap_list[12], handicap_list[17]),
            (handicap_list[13], handicap_list[18]),
            (handicap_list[14], handicap_list[19]),
        )
    )
    return TdxExtQuote(
        market=market,
        code=_decode_text(raw_code),
        active=int(active),
        pre_close=_none_zero_price(pre_close),
        open=_none_zero_price(open_price),
        high=_none_zero_price(high),
        low=_none_zero_price(low),
        last_price=_none_zero_price(close),
        active_volume=int(add_position),
        volume=int(vol),
        current_volume=int(curr_vol),
        amount=float(amount),
        inside_volume=int(inside_volume),
        outside_volume=int(outside_volume),
        open_interest=int(open_interest),
        open_interest_change=int(open_interest_change),
        settlement=_none_zero_price(settlement),
        average_price=_none_zero_price(avg),
        pre_settlement=_none_zero_price(pre_settlement),
        pre_volume=_none_zero_price(pre_vol),
        trade_date=str(int(date_raw)) if date_raw else None,
        raise_speed=float(raise_speed) if raise_speed is not None else None,
        bid_levels=bid_levels,
        ask_levels=ask_levels,
    )
