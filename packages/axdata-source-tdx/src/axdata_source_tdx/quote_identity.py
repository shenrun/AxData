"""TDX quote identity and simple stock-list row helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError

from .codes import MARKET_TO_EXCHANGE, exchange_to_market


def quote_security(row: Mapping[str, Any]) -> tuple[str, str]:
    tdx_code = str(row.get("tdx_code") or "").lower()
    if len(tdx_code) == 8 and tdx_code[:2] in MARKET_TO_EXCHANGE and tdx_code[2:].isdigit():
        return tdx_code[:2], tdx_code[2:]

    exchange = str(row.get("exchange") or "")
    symbol = str(row.get("symbol") or "")
    return exchange_to_market(exchange), symbol


def quote_security_from_tdx_code(tdx_code: str) -> tuple[str, str]:
    text = str(tdx_code or "").strip().lower()
    if len(text) != 8 or text[:2] not in MARKET_TO_EXCHANGE or not text[2:].isdigit():
        raise SourceRequestValidationError(f"Invalid TDX code: {tdx_code!r}")
    return text[:2], text[2:]


def normalize_suspension_row(stock_row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "instrument_id": stock_row.get("instrument_id"),
        "symbol": stock_row.get("symbol"),
        "tdx_code": stock_row.get("tdx_code"),
        "exchange": stock_row.get("exchange"),
        "name": stock_row.get("name"),
        "market": stock_row.get("market"),
    }


def normalize_st_row(stock_row: Mapping[str, Any], st_type: str) -> dict[str, Any]:
    return {
        "instrument_id": stock_row.get("instrument_id"),
        "symbol": stock_row.get("symbol"),
        "tdx_code": stock_row.get("tdx_code"),
        "exchange": stock_row.get("exchange"),
        "name": stock_row.get("name"),
        "market": stock_row.get("market"),
        "st_type": st_type,
    }
