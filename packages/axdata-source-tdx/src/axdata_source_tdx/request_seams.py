"""Request-module private helper seams owned by the TDX provider package."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date
from typing import Any

from axdata_core.source_errors import SourceUnavailableError


def request_legacy_quotes_parallel(
    client: Any,
    stock_rows: Sequence[Mapping[str, Any]],
    *,
    use_parallel_quote_clients: bool,
    quote_security: Callable[[Mapping[str, Any]], tuple[str, str]],
    chunked: Callable[[Sequence[Any], int], list[list[Any]]],
    batch_size: int,
    request_batches: Callable[..., list[Any]],
    request_batches_concurrent: Callable[..., list[Any]],
    request_on_host: Callable[..., list[Any]],
    client_pool_size: Callable[[Any], int],
    suspension_scan_hosts: Callable[[], list[str]],
    suspension_host_count: int,
    emit_progress: Callable[..., None],
    hosts: Sequence[str] | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> list[Any]:
    from .quote_fetch import request_legacy_quotes_parallel as impl

    return impl(
        client,
        stock_rows,
        use_parallel_quote_clients=use_parallel_quote_clients,
        quote_security=quote_security,
        chunked=chunked,
        batch_size=batch_size,
        request_batches=request_batches,
        request_batches_concurrent=request_batches_concurrent,
        request_on_host=request_on_host,
        client_pool_size=client_pool_size,
        suspension_scan_hosts=suspension_scan_hosts,
        suspension_host_count=suspension_host_count,
        emit_progress=emit_progress,
        hosts=hosts,
        progress_callback=progress_callback,
    )


def request_legacy_quote_batches_concurrent(
    client: Any,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    worker_count: int,
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[str, str]]], Any],
    as_list: Callable[[Any], list[Any]],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> list[Any]:
    from .quote_fetch import request_legacy_quote_batches_concurrent as impl

    return impl(
        client,
        batches,
        worker_count=worker_count,
        tdx_legacy_quotes=tdx_legacy_quotes,
        as_list=as_list,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
    )


def request_legacy_quotes_on_host(
    host: str,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    create_client: Callable[..., Any],
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[str, str]]], Any],
    pool_size: int,
    batch_progress: Callable[[], None] | None = None,
) -> list[Any]:
    from .quote_fetch import request_legacy_quotes_on_host as impl

    return impl(
        host,
        batches,
        create_client=create_client,
        tdx_legacy_quotes=tdx_legacy_quotes,
        pool_size=pool_size,
        batch_progress=batch_progress,
    )


def request_legacy_quote_batches(
    client: Any,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[str, str]]], Any],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> list[Any]:
    from .quote_fetch import request_legacy_quote_batches as impl

    return impl(
        client,
        batches,
        tdx_legacy_quotes=tdx_legacy_quotes,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
    )


def explicit_snapshot_rows_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    chunked: Callable[[Sequence[Any], int], list[list[Any]]],
    batch_size: int,
    client_pool_size: Callable[[Any], int],
    tdx_explicit_quotes: Callable[[Any, Sequence[tuple[str, str]]], Any],
    as_list: Callable[[Any], list[Any]],
    normalize_snapshot_row: Callable[[Any], dict[str, Any]],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
    progress_start: int = 30,
    progress_span: int = 38,
) -> tuple[dict[str, dict[str, Any]], int]:
    from .quote_fetch import explicit_snapshot_rows_by_tdx_code as impl

    return impl(
        client,
        tdx_codes,
        chunked=chunked,
        batch_size=batch_size,
        client_pool_size=client_pool_size,
        tdx_explicit_quotes=tdx_explicit_quotes,
        as_list=as_list,
        normalize_snapshot_row=normalize_snapshot_row,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def capital_change_rows_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    requested_categories: set[int] | None,
    tdx_capital_changes: Callable[[Any, str], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_capital_change_row: Callable[[str, Any], dict[str, Any]],
    category_matches: Callable[[Any, set[int] | None], bool],
    client_pool_size: Callable[[Any], int],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
    progress_start: int = 30,
    progress_span: int = 38,
) -> dict[str, dict[str, Any]]:
    from .finance_fetch import capital_change_rows_by_tdx_code as impl

    return impl(
        client,
        tdx_codes,
        requested_categories=requested_categories,
        tdx_capital_changes=tdx_capital_changes,
        as_list=as_list,
        get_value=get_value,
        normalize_capital_change_row=normalize_capital_change_row,
        category_matches=category_matches,
        client_pool_size=client_pool_size,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def finance_rows_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    chunked: Callable[[Sequence[Any], int], list[list[Any]]],
    tdx_finance_info: Callable[[Any, Sequence[str]], Sequence[Any]],
    finance_records: Callable[[Any], Sequence[Any]],
    normalize_finance_info_row: Callable[[Any], dict[str, Any]],
    get_value: Callable[[Any, str, Any], Any],
    client_pool_size: Callable[[Any], int],
    emit_progress: Callable[..., None],
    batch_size: int | None = None,
    progress_callback: Callable[..., None] | None = None,
    progress_start: int = 28,
    progress_span: int = 40,
) -> tuple[dict[str, dict[str, Any]], int]:
    from .finance_fetch import finance_rows_by_tdx_code as impl

    return impl(
        client,
        tdx_codes,
        chunked=chunked,
        tdx_finance_info=tdx_finance_info,
        finance_records=finance_records,
        normalize_finance_info_row=normalize_finance_info_row,
        get_value=get_value,
        client_pool_size=client_pool_size,
        emit_progress=emit_progress,
        unavailable_error=SourceUnavailableError,
        batch_size=batch_size,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def request_trade_series_history(
    client: Any,
    tdx_code: str,
    *,
    trade_date: str | None,
    page_size: int,
    max_start: int,
    price_decimal: Callable[[Any, str], int],
    today_trades: Callable[..., Any],
    historical_trades: Callable[..., Any],
    trade_records: Callable[[Any], Sequence[Any]],
    normalize_trade_row: Callable[..., dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    from .series_history import request_trade_series_history as impl

    return impl(
        client,
        tdx_code,
        trade_date=trade_date,
        page_size=page_size,
        max_start=max_start,
        price_decimal=price_decimal,
        today_trades=today_trades,
        historical_trades=historical_trades,
        trade_records=trade_records,
        normalize_trade_row=normalize_trade_row,
    )


def request_kline_series_history(
    client: Any,
    tdx_code: str,
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str,
    max_count: int,
    tdx_kline: Callable[..., Any],
    kline_bars: Callable[[Any], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
) -> tuple[Any, int]:
    from .series_history import request_kline_series_history as impl

    return impl(
        client,
        tdx_code,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        kind=kind,
        max_count=max_count,
        tdx_kline=tdx_kline,
        kline_bars=kline_bars,
        get_value=get_value,
    )


def request_kline_code_history(
    client: Any,
    index: int,
    tdx_code: str,
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str,
    request_series_history: Callable[..., tuple[Any, int]],
    normalize_kline_row: Callable[[Any, Any], dict[str, Any]],
    kline_bars: Callable[[Any], Sequence[Any]],
    row_sort_key: Callable[[dict[str, Any]], Any],
) -> Any:
    from .series_history import request_kline_code_history as impl

    return impl(
        client,
        index,
        tdx_code,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        kind=kind,
        request_series_history=request_series_history,
        normalize_kline_row=normalize_kline_row,
        kline_bars=kline_bars,
        row_sort_key=row_sort_key,
    )


def request_recent_daily_bars(
    client: Any,
    tdx_code: str,
    *,
    count: int,
    stats_date: Any,
    max_count: int,
    tdx_kline: Callable[..., Any],
    kline_bars: Callable[[Any], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
    bar_trade_date: Callable[[Any], str | None],
) -> tuple[list[Any], int]:
    from .series_history import request_recent_daily_bars as impl

    return impl(
        client,
        tdx_code,
        count=count,
        stats_date=stats_date,
        max_count=max_count,
        tdx_kline=tdx_kline,
        kline_bars=kline_bars,
        get_value=get_value,
        bar_trade_date=bar_trade_date,
    )


def request_kline_codes_on_host(
    host: str,
    indexed_codes: Sequence[tuple[int, str]],
    *,
    pool_size: int,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    create_client: Callable[..., Any],
    request_code_history: Callable[..., Any],
    client_meta: Callable[[Any], dict[str, Any]],
) -> Any:
    from .series_history import request_kline_codes_on_host as impl

    return impl(
        host,
        indexed_codes,
        pool_size=pool_size,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        create_client=create_client,
        request_code_history=request_code_history,
        client_meta=client_meta,
    )


def request_kline_codes_parallel(
    hosts: Sequence[str],
    tdx_codes: Sequence[str],
    *,
    pool_size: int,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    request_on_host: Callable[..., Any],
) -> Any:
    from .series_history import request_kline_codes_parallel as impl

    return impl(
        hosts,
        tdx_codes,
        pool_size=pool_size,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        request_on_host=request_on_host,
    )


def kline_meta(
    series: Any,
    *,
    page_size: int,
    page_count: int,
    requested_code_count: int,
    concurrency_limit: int,
    concurrency_capacity: int,
    get_value: Callable[[Any, str, Any], Any],
) -> dict[str, Any]:
    from .kline_helpers import kline_meta as impl

    return impl(
        series,
        page_size=page_size,
        page_count=page_count,
        requested_code_count=requested_code_count,
        concurrency_limit=concurrency_limit,
        concurrency_capacity=concurrency_capacity,
        get_value=get_value,
    )


def price_limit_base_from_daily_kline(
    client: Any,
    tdx_code: str,
    target_trade_date: Any,
    *,
    request_recent_daily_bars: Callable[..., tuple[list[Any], int]],
    bar_trade_date: Callable[[Any], str | None],
) -> Any:
    from .price_limit_history import price_limit_base_from_daily_kline as impl

    return impl(
        client,
        tdx_code,
        target_trade_date,
        request_recent_daily_bars=request_recent_daily_bars,
        bar_trade_date=bar_trade_date,
    )


def price_limit_bases_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    target_trade_date: Any,
    *,
    request_base: Callable[[Any, str, Any], Any],
    client_pool_size: Callable[[Any], int],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> list[Any]:
    from .price_limit_history import price_limit_bases_by_tdx_code as impl

    return impl(
        client,
        tdx_codes,
        target_trade_date,
        request_base=request_base,
        client_pool_size=client_pool_size,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
    )


def latest_daily_price_limit_calendar_dates(
    *,
    today: date | None = None,
    default_trade_date: Callable[[str], str | None],
    before_daily_close_buffer: Callable[[Any], bool],
    request_interface: Callable[..., Any] | None = None,
) -> Any:
    from .price_limit_calendar import latest_calendar_dates_from_source_request as impl

    return impl(
        today=today,
        request_interface=request_interface,
        default_trade_date=default_trade_date,
        before_daily_close_buffer=before_daily_close_buffer,
    )


def security_names_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    tdx_codes_all: Callable[[Sequence[str]], Sequence[str]],
    get_value: Callable[[Any, str, Any], Any],
) -> dict[str, str]:
    from .limit_ladder_fetch import security_names_by_tdx_code as impl

    return impl(
        client,
        tdx_codes,
        tdx_codes_all=tdx_codes_all,
        get_value=get_value,
    )


def request_limit_ladder_rank_rows(
    client: Any,
    *,
    include_touched: bool,
    category_quotes: Callable[..., Any],
    normalize_snapshot_row: Callable[[Any], dict[str, Any]],
    rank_page_below_threshold: Callable[[Sequence[Mapping[str, Any]], bool], bool],
    get_value: Callable[[Any, str, Any], Any],
    category: int,
    sort_type: int,
    page_size: int,
    max_start: int,
) -> tuple[list[dict[str, Any]], int]:
    from .limit_ladder_fetch import request_limit_ladder_rank_rows as impl

    return impl(
        client,
        include_touched=include_touched,
        category_quotes=category_quotes,
        normalize_snapshot_row=normalize_snapshot_row,
        rank_page_below_threshold=rank_page_below_threshold,
        get_value=get_value,
        category=category,
        sort_type=sort_type,
        page_size=page_size,
        max_start=max_start,
    )


def normalize_finance_info_row(
    record: Any,
    *,
    enrich_profile: bool = False,
    finance_maps: Any | None = None,
    profile_lookup: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    from .finance_normalize import normalize_finance_info_row as impl

    return impl(
        record,
        enrich_profile=enrich_profile,
        finance_maps=finance_maps,
        profile_lookup=profile_lookup,
    )
