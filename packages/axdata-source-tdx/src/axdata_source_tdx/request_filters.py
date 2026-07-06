"""TDX request parameter parsing and row filtering helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .codes import instrument_id_to_tdx_code, tdx_code_to_instrument_id
from .security_codes import SCOPE_TO_BOARDS
from axdata_core.source_errors import SourceRequestValidationError


def requested_exchanges(exchange: Any) -> list[str]:
    if exchange in (None, ""):
        return ["SSE", "SZSE", "BSE"]
    if isinstance(exchange, str):
        values = [item.strip() for item in exchange.split(",") if item.strip()]
    elif isinstance(exchange, Sequence):
        values = [str(item).strip() for item in exchange if str(item).strip()]
    else:
        values = [str(exchange)]
    if any(item.lower() in {"all", "*"} for item in values):
        return ["SSE", "SZSE", "BSE"]
    return values


def requested_boards(scope: Any) -> set[str] | None:
    if scope in (None, ""):
        return None
    boards: set[str] = set()
    for key in string_values(scope):
        try:
            resolved = SCOPE_TO_BOARDS[key]
        except KeyError as exc:
            allowed = "all/main/star/chinext/bse/cdr"
            raise SourceRequestValidationError(f"Invalid scope {scope!r}. Use {allowed}.") from exc
        if resolved is None:
            return None
        boards.update(resolved)
    return boards or None


def requested_codes(code: Any) -> set[str] | None:
    if code in (None, ""):
        return None
    return {normalize_code_filter(value) for value in string_values(code) if value}


def is_all_codes_value(code: Any) -> bool:
    if code in (None, ""):
        return True
    values = [str(value).strip().lower() for value in string_values(code)]
    return not values or any(value in {"all", "*"} for value in values)


def scope_meta_value(scope: Any) -> str:
    if scope in (None, ""):
        return "all"
    values = [str(value).strip().lower() for value in string_values(scope) if str(value).strip()]
    return ",".join(values) if values else "all"


def requested_kline_codes(code: Any) -> list[str]:
    if code in (None, ""):
        raise SourceRequestValidationError("code is required")
    requested: list[str] = []
    seen: set[str] = set()
    for value in string_values(code):
        tdx_code = instrument_id_to_tdx_code(value)
        if tdx_code in seen:
            continue
        seen.add(tdx_code)
        requested.append(tdx_code)
    if not requested:
        raise SourceRequestValidationError("code is required")
    return requested


def requested_f10_codes(code: Any) -> list[str]:
    if code in (None, ""):
        raise SourceRequestValidationError("code is required")
    requested: list[str] = []
    seen: set[str] = set()
    for value in string_values(code):
        tdx_code = instrument_id_to_tdx_code(value)
        instrument_id = tdx_code_to_instrument_id(tdx_code)
        if instrument_id in seen:
            continue
        seen.add(instrument_id)
        requested.append(instrument_id)
    if not requested:
        raise SourceRequestValidationError("code is required")
    return requested


def requested_names(name: Any) -> set[str] | None:
    if name in (None, ""):
        return None
    return {value.lower() for value in string_values(name) if value}


def string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Sequence):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def normalize_code_filter(value: str) -> str:
    text = value.strip().lower()
    if not text:
        return ""
    if "." in text:
        symbol, _, suffix = text.partition(".")
        return f"{symbol}.{suffix.upper()}"
    return text


def code_matches(row: Mapping[str, Any], requested_codes: set[str] | None) -> bool:
    if not requested_codes:
        return True
    candidates = {
        str(row.get("symbol") or "").lower(),
        str(row.get("tdx_code") or "").lower(),
        str(row.get("instrument_id") or ""),
    }
    return any(code in candidates for code in requested_codes)


def name_matches(row: Mapping[str, Any], requested_names: set[str] | None) -> bool:
    if not requested_names:
        return True
    name = str(row.get("name") or "").lower()
    return any(requested_name in name for requested_name in requested_names)


def exchanges_for_boards(boards: set[str] | None) -> str:
    if boards is None:
        return "all"
    exchanges = []
    if boards & {"sse_main_board", "sse_star_market", "sse_cdr"}:
        exchanges.append("SSE")
    if boards & {"szse_main_board", "szse_chinext"}:
        exchanges.append("SZSE")
    if boards & {"bse_listed_stock"}:
        exchanges.append("BSE")
    return ",".join(exchanges) or "all"


def board_matches(board: Any, boards: set[str] | None) -> bool:
    if boards is None:
        return True
    return str(board) in boards
