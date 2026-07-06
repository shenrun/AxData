"""TDX code and market normalization helpers."""

from __future__ import annotations

from typing import Any

from axdata_core.source_errors import SourceRequestValidationError

EXCHANGE_TO_MARKET = {
    "SSE": "sh",
    "SH": "sh",
    "SHA": "sh",
    "SHSE": "sh",
    "SZSE": "sz",
    "SZ": "sz",
    "SZA": "sz",
    "BSE": "bj",
    "BJ": "bj",
}
MARKET_TO_EXCHANGE = {"sh": "SSE", "sz": "SZSE", "bj": "BSE"}
MARKET_TO_SUFFIX = {"sh": ".SH", "sz": ".SZ", "bj": ".BJ"}
SUFFIX_TO_MARKET = {"SH": "sh", "SZ": "sz", "BJ": "bj"}
MARKET_TO_ID = {"sz": 0, "sh": 1, "bj": 2}


def tdx_code_to_instrument_id(code: str) -> str:
    text = str(code or "").strip().lower()
    if len(text) == 8 and text[:2] in MARKET_TO_SUFFIX and text[2:].isdigit():
        return f"{text[2:]}{MARKET_TO_SUFFIX[text[:2]]}"
    if len(text) == 9 and text[6] == ".":
        return text[:6] + "." + text[7:].upper()
    return text.upper()


def instrument_id_to_tdx_code(instrument_id: str) -> str:
    text = str(instrument_id or "").strip()
    if not text:
        raise SourceRequestValidationError("instrument_id is required")

    normalized = text.lower()
    if len(normalized) == 8 and normalized[:2] in MARKET_TO_SUFFIX and normalized[2:].isdigit():
        return normalized

    symbol, sep, suffix = text.partition(".")
    if sep:
        market = SUFFIX_TO_MARKET.get(suffix.upper())
        if market is None or len(symbol) != 6 or not symbol.isdigit():
            raise SourceRequestValidationError(f"Invalid instrument_id: {instrument_id!r}")
        return market + symbol

    if len(symbol) != 6 or not symbol.isdigit():
        raise SourceRequestValidationError(f"Invalid instrument_id: {instrument_id!r}")
    if symbol.startswith(("6", "9")):
        return "sh" + symbol
    if symbol.startswith(("0", "1", "2", "3")):
        return "sz" + symbol
    if symbol.startswith(("8", "92")):
        return "bj" + symbol
    raise SourceRequestValidationError(f"Unable to infer exchange for instrument_id: {instrument_id!r}")


def exchange_to_market(exchange: Any) -> str:
    text = str(exchange or "").strip().upper()
    try:
        return EXCHANGE_TO_MARKET[text]
    except KeyError as exc:
        raise SourceRequestValidationError(
            f"Invalid exchange {exchange!r}. Use SSE, SZSE, or BSE."
        ) from exc
