"""Lightweight TDX security code normalization helpers."""

from __future__ import annotations

from importlib import import_module

from axdata_source_tdx._tdx_wire._market import market_to_id

_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def split_code(code: str) -> tuple[int, str, str]:
    full_code = normalize_code(code)
    market = full_code[:2]
    number = full_code[2:]
    return market_to_id(market), market, number


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if len(text) == 8 and text[:2] in {"sz", "sh", "bj"} and text[2:].isdigit():
        return text
    if len(text) == 9 and text[6] == ".":
        symbol, suffix = text[:6], text[7:].upper()
        suffix_to_market = {"SH": "sh", "SZ": "sz", "BJ": "bj"}
        market = suffix_to_market.get(suffix)
        if market is None or not symbol.isdigit():
            raise _protocol_error()(f"invalid code: {code!r}")
        return market + symbol
    if len(text) != 6 or not text.isdigit():
        raise _protocol_error()(f"invalid code: {code!r}")
    if text.startswith(("6", "9")):
        return "sh" + text
    if text.startswith(("0", "1", "2", "3")):
        return "sz" + text
    if text.startswith(("8", "92")):
        return "bj" + text
    raise _protocol_error()(f"unable to infer market for code: {code!r}")
