"""Quote fetch execution helpers for TDX request adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any, Callable


@dataclass(frozen=True)
class QuoteRowsResult:
    rows: list[dict[str, Any]]
    quote_count: int


@dataclass(frozen=True)
class QuoteRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def order_book_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., QuoteRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[Any, Any]]], Any],
    as_list: Callable[[Any], list[Any]],
    normalize_order_book_rows: Callable[[Any], Sequence[dict[str, Any]]],
) -> QuoteRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_legacy_quotes=tdx_legacy_quotes,
        as_list=as_list,
        normalize_order_book_rows=normalize_order_book_rows,
    )
    return QuoteRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x053e",
            requested_code_count=len(tdx_codes),
        ),
    )


def explicit_quote_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., QuoteRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_explicit_quotes: Callable[[Any, Sequence[tuple[Any, Any]]], Any],
    as_list: Callable[[Any], list[Any]],
    normalize_row: Callable[[Any], dict[str, Any]],
) -> QuoteRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_explicit_quotes=tdx_explicit_quotes,
        as_list=as_list,
        normalize_row=normalize_row,
    )
    return QuoteRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x054c",
            requested_code_count=len(tdx_codes),
        ),
    )


def refresh_quote_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., QuoteRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_refresh_quotes: Callable[[Any, Sequence[tuple[Any, Any, int]]], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_row: Callable[[Any], dict[str, Any]],
) -> QuoteRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_refresh_quotes=tdx_refresh_quotes,
        as_list=as_list,
        get_value=get_value,
        normalize_row=normalize_row,
    )
    return QuoteRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0547",
            requested_code_count=len(tdx_codes),
        ),
    )


def quote_rows_meta(
    result: QuoteRowsResult,
    *,
    protocol: str,
    requested_code_count: int,
) -> dict[str, Any]:
    return {
        "tdx_protocol": protocol,
        "tdx_requested_code_count": requested_code_count,
        "tdx_quote_count": result.quote_count,
    }


def order_book_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[Any, Any]]], Any],
    as_list: Callable[[Any], list[Any]],
    normalize_order_book_rows: Callable[[Any], Sequence[dict[str, Any]]],
) -> QuoteRowsResult:
    securities = [quote_security_from_tdx_code(tdx_code) for tdx_code in tdx_codes]
    quotes = as_list(tdx_legacy_quotes(client, securities))

    rows: list[dict[str, Any]] = []
    for quote in quotes:
        rows.extend(normalize_order_book_rows(quote))

    rows.sort(
        key=lambda row: (
            str(row.get("instrument_id") or ""),
            int(row.get("level") or 0),
        )
    )
    return QuoteRowsResult(rows=rows, quote_count=len(quotes))


def explicit_quote_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_explicit_quotes: Callable[[Any, Sequence[tuple[Any, Any]]], Any],
    as_list: Callable[[Any], list[Any]],
    normalize_row: Callable[[Any], dict[str, Any]],
) -> QuoteRowsResult:
    securities = [quote_security_from_tdx_code(tdx_code) for tdx_code in tdx_codes]
    quotes = as_list(tdx_explicit_quotes(client, securities))
    rows = [normalize_row(quote) for quote in quotes]
    return QuoteRowsResult(rows=rows, quote_count=len(quotes))


def refresh_quote_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_refresh_quotes: Callable[[Any, Sequence[tuple[Any, Any, int]]], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_row: Callable[[Any], dict[str, Any]],
) -> QuoteRowsResult:
    cursors = []
    for tdx_code in tdx_codes:
        market, symbol = quote_security_from_tdx_code(tdx_code)
        cursors.append((market, symbol, 0))
    batch = tdx_refresh_quotes(client, cursors)
    records = as_list(get_value(batch, "records", ()))
    rows = [normalize_row(record) for record in records]
    rows.sort(key=lambda row: str(row.get("instrument_id") or ""))
    return QuoteRowsResult(rows=rows, quote_count=len(rows))


def request_realtime_refresh_rows(
    *,
    code: Any,
    fields: Sequence[str] | None = None,
    cursors: Mapping[str, int] | None = None,
    include_internal: bool = False,
    client: Any | None = None,
    requested_codes: Callable[[Any], Sequence[str]],
    quote_security_from_tdx_code: Callable[[str], tuple[Any, Any]],
    tdx_code_to_instrument_id: Callable[[str], str],
    create_client: Callable[..., Any],
    tdx_refresh_quotes: Callable[[Any, Sequence[tuple[Any, Any, int]]], Any],
    normalize_snapshot_row: Callable[[Any], dict[str, Any]],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    optional_int: Callable[[Any], int | None],
) -> list[dict[str, Any]]:
    tdx_codes = requested_codes(code)
    cursor_map = {str(key).upper(): int(value) for key, value in dict(cursors or {}).items()}
    refresh_cursors = []
    for tdx_code in tdx_codes:
        market, symbol = quote_security_from_tdx_code(tdx_code)
        instrument_id = tdx_code_to_instrument_id(tdx_code)
        refresh_cursors.append((market, symbol, cursor_map.get(instrument_id, 0)))

    current_client = client or create_client()
    should_close = client is None
    try:
        if hasattr(current_client, "connect"):
            current_client.connect()
        batch = tdx_refresh_quotes(current_client, refresh_cursors)
    finally:
        if should_close and hasattr(current_client, "close"):
            current_client.close()

    rows = []
    for record in as_list(get_value(batch, "records", ())):
        row = normalize_snapshot_row(record)
        if include_internal:
            row["_tdx_instrument_id"] = row.get("instrument_id")
            row["_tdx_update_time_raw"] = optional_int(get_value(record, "update_time_raw", None))
        rows.append(row)
    rows.sort(key=lambda row: str(row.get("instrument_id") or ""))
    if fields:
        requested_fields = [str(field).strip() for field in fields if str(field).strip()]
        if include_internal:
            requested_fields.extend(["_tdx_instrument_id", "_tdx_update_time_raw"])
        return [{field: row.get(field) for field in requested_fields} for row in rows]
    return rows


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
    securities = [quote_security(row) for row in stock_rows]
    batches = list(chunked(securities, batch_size))
    if not batches:
        return []

    if not use_parallel_quote_clients:
        return request_batches(client, batches, progress_callback=progress_callback)

    pool_size = client_pool_size(client)
    if pool_size > 1:
        return request_batches_concurrent(
            client,
            batches,
            worker_count=min(pool_size, len(batches)),
            progress_callback=progress_callback,
        )

    resolved_hosts = list(hosts or suspension_scan_hosts())
    if len(resolved_hosts) <= 1:
        return request_batches(client, batches, progress_callback=progress_callback)

    worker_count = min(len(resolved_hosts), suspension_host_count)
    grouped_batches = [batches[index::worker_count] for index in range(worker_count)]
    quotes: list[Any] = []
    started_at = monotonic()
    completed_batches = 0
    total_batches = len(batches)
    progress_lock = Lock()

    def mark_batch_done() -> None:
        nonlocal completed_batches
        with progress_lock:
            completed_batches += 1
            current = completed_batches
        emit_progress(
            progress_callback,
            completed=current,
            total=total_batches,
            unit="批",
            started_at=started_at,
            percent_start=28,
            percent_span=40,
            label="请求停牌状态",
        )

    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-suspensions") as executor:
        futures = []
        for index in range(worker_count):
            if not grouped_batches[index]:
                continue
            futures.append(
                executor.submit(
                    request_on_host,
                    resolved_hosts[index],
                    grouped_batches[index],
                    batch_progress=mark_batch_done,
                )
            )
        for future in as_completed(futures):
            quotes.extend(future.result())
    return quotes


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
    quotes: list[Any] = []
    started_at = monotonic()
    total = len(batches)
    completed = 0
    with ThreadPoolExecutor(
        max_workers=max(1, worker_count),
        thread_name_prefix="axdata-tdx-suspensions-pool",
    ) as executor:
        futures = [executor.submit(tdx_legacy_quotes, client, batch) for batch in batches]
        for future in as_completed(futures):
            quotes.extend(as_list(future.result()))
            completed += 1
            emit_progress(
                progress_callback,
                completed=completed,
                total=total,
                unit="批",
                started_at=started_at,
                percent_start=28,
                percent_span=40,
                label="请求停牌状态",
            )
    return quotes


def request_legacy_quotes_on_host(
    host: str,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    create_client: Callable[..., Any],
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[str, str]]], Any],
    pool_size: int,
    batch_progress: Callable[[], None] | None = None,
) -> list[Any]:
    client = create_client(
        hosts=[host],
        pool_size=pool_size,
        heartbeat_interval=None,
    )
    try:
        if hasattr(client, "connect"):
            client.connect()
        quotes: list[Any] = []
        worker_count = min(pool_size, max(1, len(batches)))
        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="axdata-tdx-suspensions-host",
        ) as executor:
            futures = [executor.submit(tdx_legacy_quotes, client, batch) for batch in batches]
            for future in as_completed(futures):
                quotes.extend(future.result())
                if batch_progress is not None:
                    batch_progress()
        return quotes
    finally:
        if hasattr(client, "close"):
            client.close()


def request_legacy_quote_batches(
    client: Any,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    tdx_legacy_quotes: Callable[[Any, Sequence[tuple[str, str]]], Any],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> list[Any]:
    quotes: list[Any] = []
    started_at = monotonic()
    total = len(batches)
    for index, batch in enumerate(batches, start=1):
        quotes.extend(tdx_legacy_quotes(client, batch))
        emit_progress(
            progress_callback,
            completed=index,
            total=total,
            unit="批",
            started_at=started_at,
            percent_start=28,
            percent_span=40,
            label="请求停牌状态",
        )
    return quotes


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
    requested = [str(tdx_code).lower() for tdx_code in tdx_codes if tdx_code]
    securities = [(tdx_code[:2], tdx_code[2:]) for tdx_code in requested]
    batches = chunked(securities, batch_size)
    if not batches:
        return {}, 0

    quotes: list[Any] = []
    worker_count = min(client_pool_size(client), len(batches))
    started_at = monotonic()
    if worker_count <= 1 or len(batches) <= 1:
        for index, batch in enumerate(batches, start=1):
            quotes.extend(as_list(tdx_explicit_quotes(client, batch)))
            emit_progress(
                progress_callback,
                completed=index,
                total=len(batches),
                unit="批",
                started_at=started_at,
                percent_start=progress_start,
                percent_span=progress_span,
                label="请求快照昨收价",
            )
    else:
        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="axdata-tdx-price-limit-snapshot",
        ) as executor:
            futures = [executor.submit(tdx_explicit_quotes, client, batch) for batch in batches]
            completed = 0
            for future in as_completed(futures):
                quotes.extend(as_list(future.result()))
                completed += 1
                emit_progress(
                    progress_callback,
                    completed=completed,
                    total=len(batches),
                    unit="批",
                    started_at=started_at,
                    percent_start=progress_start,
                    percent_span=progress_span,
                    label="请求快照昨收价",
                )

    rows: dict[str, dict[str, Any]] = {}
    for quote in quotes:
        row = normalize_snapshot_row(quote)
        tdx_code = str(row.get("tdx_code") or "").lower()
        if tdx_code:
            rows[tdx_code] = row
    return rows, len(batches)
