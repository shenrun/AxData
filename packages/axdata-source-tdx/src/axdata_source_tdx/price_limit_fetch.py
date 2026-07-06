"""Daily price-limit row construction helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class DailyPriceLimitResult:
    rows: list[dict[str, Any]]
    mode: str
    target_trade_date: str
    pre_close_trade_date: str | None
    calendar_source: str | None
    snapshot_base_field: str | None
    kline_page_count: int
    quote_count: int
    quote_batch_count: int
    quote_concurrency: int | None


@dataclass(frozen=True)
class DailyPriceLimitRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def daily_price_limit_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    stock_code_pool: Callable[..., tuple[list[str], str | None, dict[str, str]]],
    normalize_optional_date_text: Callable[..., str | None],
    security_names_by_tdx_code: Callable[[Any, Sequence[str]], Mapping[str, str]],
    daily_price_limit_result_func: Callable[..., DailyPriceLimitResult],
    daily_price_limit_meta_func: Callable[..., dict[str, Any]],
    latest_calendar_dates: Callable[[], Any],
    request_snapshot_rows: Callable[..., tuple[dict[str, dict[str, Any]], int]],
    request_price_limit_bases: Callable[..., Sequence[Any]],
    normalize_snapshot_row: Callable[..., dict[str, Any]],
    normalize_history_row: Callable[..., dict[str, Any]],
    client_pool_size: Callable[[Any], int],
    default_quote_batch_size: int,
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> DailyPriceLimitRequestResult:
    tdx_codes, expanded_scope, names_by_tdx_code = stock_code_pool(
        client,
        params,
        progress_start=20,
        progress_span=8,
    )
    trade_date = normalize_optional_date_text(params.get("trade_date"), name="trade_date")
    emit_source_progress(
        progress_callback,
        29,
        f"已准备股票池，共 {len(tdx_codes)} 只",
        progress_current=0,
        progress_total=len(tdx_codes),
        progress_unit="只",
        eta_ms=None,
    )
    missing_name_codes = [tdx_code for tdx_code in tdx_codes if tdx_code not in names_by_tdx_code]
    if missing_name_codes:
        names_by_tdx_code.update(security_names_by_tdx_code(client, missing_name_codes))
    result = daily_price_limit_result_func(
        tdx_codes,
        trade_date=trade_date,
        names_by_tdx_code=names_by_tdx_code,
        latest_calendar_dates=latest_calendar_dates,
        request_snapshot_rows=request_snapshot_rows,
        request_price_limit_bases=request_price_limit_bases,
        normalize_snapshot_row=normalize_snapshot_row,
        normalize_history_row=normalize_history_row,
        client_pool_size=client_pool_size(client),
        emit_source_progress=emit_source_progress,
        progress_callback=progress_callback,
    )
    return DailyPriceLimitRequestResult(
        rows=result.rows,
        meta=daily_price_limit_meta_func(
            result,
            trade_date=trade_date,
            expanded_scope=expanded_scope,
            requested_code_count=len(tdx_codes),
            client_pool_size=client_pool_size(client),
            default_quote_batch_size=default_quote_batch_size,
        ),
    )


def daily_price_limit_meta(
    result: DailyPriceLimitResult,
    *,
    trade_date: str | None,
    expanded_scope: str | None,
    requested_code_count: int,
    client_pool_size: int,
    default_quote_batch_size: int,
) -> dict[str, Any]:
    return {
        "tdx_protocol": "0x052d" if trade_date else "0x054c+exchange_calendar",
        "tdx_price_limit_mode": result.mode,
        "tdx_target_trade_date": result.target_trade_date,
        "tdx_pre_close_trade_date": result.pre_close_trade_date,
        "tdx_trade_calendar_source": result.calendar_source,
        "tdx_snapshot_base_field": result.snapshot_base_field,
        "snapshot_date": result.target_trade_date,
        "tdx_stock_scope": expanded_scope,
        "tdx_code_expansion_source": "stock_codes_tdx" if expanded_scope is not None else None,
        "tdx_requested_code_count": requested_code_count,
        "tdx_kline_page_count": result.kline_page_count,
        "tdx_kline_concurrency": (
            min(client_pool_size, max(requested_code_count, 1)) if trade_date else None
        ),
        "tdx_quote_count": result.quote_count,
        "tdx_quote_batch_count": result.quote_batch_count,
        "tdx_quote_batch_size": default_quote_batch_size if trade_date is None else None,
        "tdx_quote_concurrency": result.quote_concurrency,
        "tdx_returned_count": len(result.rows),
    }


def daily_price_limit_result(
    tdx_codes: Sequence[str],
    *,
    trade_date: str | None,
    names_by_tdx_code: Mapping[str, str],
    latest_calendar_dates: Callable[[], Any],
    request_snapshot_rows: Callable[..., tuple[dict[str, dict[str, Any]], int]],
    request_price_limit_bases: Callable[..., Sequence[Any]],
    normalize_snapshot_row: Callable[..., dict[str, Any]],
    normalize_history_row: Callable[..., dict[str, Any]],
    client_pool_size: int,
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> DailyPriceLimitResult:
    if trade_date is None:
        calendar_dates = latest_calendar_dates()
        target_trade_date = calendar_dates.target_trade_date
        emit_source_progress(
            progress_callback,
            30,
            "已读取股票名称，开始请求快照昨收价",
            progress_current=0,
            progress_total=len(tdx_codes),
            progress_unit="只",
            eta_ms=None,
        )
        quote_rows, quote_batch_count = request_snapshot_rows(
            tdx_codes,
            progress_callback=progress_callback,
            progress_start=30,
            progress_span=38,
        )
        rows = daily_price_limit_snapshot_rows(
            tdx_codes,
            target_trade_date=target_trade_date,
            pre_close_trade_date=calendar_dates.pre_close_trade_date,
            snapshot_base_field=calendar_dates.snapshot_base_field,
            quote_rows=quote_rows,
            names_by_tdx_code=names_by_tdx_code,
            normalize_row=normalize_snapshot_row,
        )
        return DailyPriceLimitResult(
            rows=rows,
            mode="latest_snapshot",
            target_trade_date=target_trade_date,
            pre_close_trade_date=calendar_dates.pre_close_trade_date,
            calendar_source=calendar_dates.source,
            snapshot_base_field=calendar_dates.snapshot_base_field,
            kline_page_count=0,
            quote_count=len(quote_rows),
            quote_batch_count=quote_batch_count,
            quote_concurrency=min(client_pool_size, max(quote_batch_count, 1)),
        )

    target_trade_date = trade_date
    emit_source_progress(
        progress_callback,
        30,
        "已读取股票名称，开始请求日 K",
        progress_current=0,
        progress_total=len(tdx_codes),
        progress_unit="只",
        eta_ms=None,
    )
    price_limit_results = request_price_limit_bases(
        tdx_codes,
        target_trade_date,
        progress_callback=progress_callback,
    )
    rows = daily_price_limit_history_rows(
        price_limit_results,
        target_trade_date=target_trade_date,
        names_by_tdx_code=names_by_tdx_code,
        normalize_row=normalize_history_row,
    )
    pre_close_dates = sorted(
        {
            str(row.get("pre_close_trade_date"))
            for row in rows
            if row.get("pre_close_trade_date") not in (None, "")
        }
    )
    return DailyPriceLimitResult(
        rows=rows,
        mode="historical_kline",
        target_trade_date=target_trade_date,
        pre_close_trade_date=pre_close_dates[0] if len(pre_close_dates) == 1 else None,
        calendar_source=None,
        snapshot_base_field=None,
        kline_page_count=sum(result.base.page_count for result in price_limit_results),
        quote_count=0,
        quote_batch_count=0,
        quote_concurrency=None,
    )


def daily_price_limit_snapshot_rows(
    tdx_codes: Sequence[str],
    *,
    target_trade_date: str,
    pre_close_trade_date: str | None,
    snapshot_base_field: str,
    quote_rows: Mapping[str, Any],
    names_by_tdx_code: Mapping[str, str],
    normalize_row: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        normalize_row(
            tdx_code,
            target_trade_date=target_trade_date,
            pre_close_trade_date=pre_close_trade_date,
            snapshot=quote_rows.get(tdx_code),
            snapshot_base_field=snapshot_base_field,
            name=names_by_tdx_code.get(tdx_code),
        )
        for tdx_code in tdx_codes
    ]
    rows.sort(key=lambda row: str(row.get("instrument_id") or ""))
    return rows


def daily_price_limit_history_rows(
    price_limit_results: Sequence[Any],
    *,
    target_trade_date: str,
    names_by_tdx_code: Mapping[str, str],
    normalize_row: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        normalize_row(
            result.tdx_code,
            target_trade_date=target_trade_date,
            base=result.base,
            name=names_by_tdx_code.get(result.tdx_code),
        )
        for result in price_limit_results
    ]
    rows.sort(key=lambda row: str(row.get("instrument_id") or ""))
    return rows
