"""ST and suspension status row helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable


@dataclass(frozen=True)
class StockStatusResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def stock_status_stock_params(params: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if key in {"scope", "code", "name"}}


def current_checked_at() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def stock_st_list_request_result(
    params: Mapping[str, Any],
    *,
    request_stock_rows: Callable[[Mapping[str, Any], int, int], list[dict[str, Any]]],
    st_type_from_name: Callable[[Any], str | None],
    normalize_st_row: Callable[[Mapping[str, Any], str], dict[str, Any]],
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> StockStatusResult:
    stock_rows = request_stock_rows(stock_status_stock_params(params), 20, 8)
    return stock_st_list_result(
        stock_rows,
        checked_at=current_checked_at(),
        st_type_from_name=st_type_from_name,
        normalize_st_row=normalize_st_row,
        emit_source_progress=emit_source_progress,
        progress_callback=progress_callback,
    )


def stock_st_list_result(
    stock_rows: Sequence[Mapping[str, Any]],
    *,
    checked_at: str,
    st_type_from_name: Callable[[Any], str | None],
    normalize_st_row: Callable[[Mapping[str, Any], str], dict[str, Any]],
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> StockStatusResult:
    emit_source_progress(
        progress_callback,
        62,
        f"已准备股票池，共 {len(stock_rows)} 只",
        progress_current=0,
        progress_total=len(stock_rows),
        progress_unit="只",
        eta_ms=None,
    )
    rows = st_rows_from_stock_rows(
        stock_rows,
        st_type_from_name=st_type_from_name,
        normalize_st_row=normalize_st_row,
    )
    emit_source_progress(
        progress_callback,
        68,
        f"已识别 ST 股票 {len(rows)} 只",
        progress_current=len(stock_rows),
        progress_total=len(stock_rows),
        progress_unit="只",
        eta_ms=None,
    )
    return StockStatusResult(
        rows=rows,
        meta={
            "tdx_scanned_count": len(stock_rows),
            "tdx_st_count": len(rows),
            "checked_at": checked_at,
        },
    )


def st_rows_from_stock_rows(
    stock_rows: Sequence[Mapping[str, Any]],
    *,
    st_type_from_name: Callable[[Any], str | None],
    normalize_st_row: Callable[[Mapping[str, Any], str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stock_row in stock_rows:
        st_type = st_type_from_name(stock_row.get("name"))
        if st_type is None:
            continue
        rows.append(normalize_st_row(stock_row, st_type))
    return rows


def stock_suspension_request_result(
    params: Mapping[str, Any],
    *,
    request_stock_rows: Callable[[Mapping[str, Any], int, int], list[dict[str, Any]]],
    request_quotes: Callable[..., Sequence[Any]],
    status_bit: int,
    quote_batch_size: int,
    get_value: Callable[[Any, str, Any], Any],
    normalize_suspension_row: Callable[[Mapping[str, Any]], dict[str, Any]],
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> StockStatusResult:
    stock_rows = request_stock_rows(stock_status_stock_params(params), 20, 8)
    return stock_suspension_result(
        stock_rows,
        checked_at=current_checked_at(),
        request_quotes=request_quotes,
        status_bit=status_bit,
        quote_batch_size=quote_batch_size,
        get_value=get_value,
        normalize_suspension_row=normalize_suspension_row,
        emit_source_progress=emit_source_progress,
        progress_callback=progress_callback,
    )


def stock_suspension_result(
    stock_rows: Sequence[Mapping[str, Any]],
    *,
    checked_at: str,
    request_quotes: Callable[..., Sequence[Any]],
    status_bit: int,
    quote_batch_size: int,
    get_value: Callable[[Any, str, Any], Any],
    normalize_suspension_row: Callable[[Mapping[str, Any]], dict[str, Any]],
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> StockStatusResult:
    meta = {
        "tdx_status_source": "tdx_0x053e",
        "tdx_status_bit": f"0x{status_bit:x}",
        "tdx_quote_batch_size": quote_batch_size,
        "tdx_scanned_count": len(stock_rows),
        "checked_at": checked_at,
    }
    if not stock_rows:
        return StockStatusResult(rows=[], meta=meta)

    emit_source_progress(
        progress_callback,
        28,
        f"已准备股票池，共 {len(stock_rows)} 只",
        progress_current=0,
        progress_total=len(stock_rows),
        progress_unit="只",
        eta_ms=None,
    )

    quotes = request_quotes(stock_rows, progress_callback=progress_callback)
    rows = suspension_rows_from_stock_rows(
        stock_rows,
        quotes,
        status_bit=status_bit,
        get_value=get_value,
        normalize_suspension_row=normalize_suspension_row,
    )
    emit_source_progress(
        progress_callback,
        68,
        f"停牌列表整理完成，命中 {len(rows)} 只",
        progress_current=len(stock_rows),
        progress_total=len(stock_rows),
        progress_unit="只",
        eta_ms=None,
    )

    return StockStatusResult(
        rows=rows,
        meta={
            **meta,
            "tdx_quote_count": len(quotes),
        },
    )


def suspension_rows_from_stock_rows(
    stock_rows: Sequence[Mapping[str, Any]],
    quotes: Sequence[Any],
    *,
    status_bit: int,
    get_value: Callable[[Any, str, Any], Any],
    normalize_suspension_row: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    quote_by_tdx_code = {
        str(get_value(quote, "full_code", "") or "").lower(): quote
        for quote in quotes
    }

    rows: list[dict[str, Any]] = []
    for stock_row in stock_rows:
        quote = quote_by_tdx_code.get(str(stock_row.get("tdx_code") or "").lower())
        if quote is None:
            continue
        trading_status_raw = int(get_value(quote, "trading_status_raw", 0) or 0)
        if not trading_status_raw & status_bit:
            continue
        rows.append(normalize_suspension_row(stock_row))
    return rows
