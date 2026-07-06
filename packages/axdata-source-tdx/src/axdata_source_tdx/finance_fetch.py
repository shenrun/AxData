"""Finance and capital-change fetch execution helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable


@dataclass(frozen=True)
class CapitalChangeResult:
    rows: list[dict[str, Any]]
    event_count: int
    returned_event_count: int
    concurrency: int


@dataclass(frozen=True)
class CapitalChangeRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


@dataclass(frozen=True)
class FinanceInfoResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def finance_info_request_result(
    client: Any,
    interface_name: str,
    params: Mapping[str, Any],
    *,
    requested_kline_codes: Callable[[Any], Sequence[str]],
    load_finance_maps: Callable[[str], Any],
    finance_info_result_func: Callable[..., FinanceInfoResult],
    tdx_finance_info: Callable[[Any, Sequence[str]], Sequence[Any]],
    finance_records: Callable[[Any], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_finance_info_row: Callable[..., dict[str, Any]],
    fields_by_interface: Mapping[str, Sequence[str]],
) -> FinanceInfoResult:
    tdx_codes = requested_kline_codes(params.get("code"))
    finance_maps = (
        load_finance_maps(str(params.get("map_root")))
        if interface_name == "stock_finance_profile_tdx" and params.get("map_root")
        else None
    )
    finance_map_source = None
    if interface_name == "stock_finance_profile_tdx":
        finance_map_source = "map_root" if params.get("map_root") else "builtin"
    return finance_info_result_func(
        client,
        tdx_codes,
        interface_name=interface_name,
        tdx_finance_info=tdx_finance_info,
        finance_records=finance_records,
        get_value=get_value,
        normalize_finance_info_row=normalize_finance_info_row,
        fields=fields_by_interface[interface_name],
        enrich_profile=interface_name == "stock_finance_profile_tdx",
        finance_maps=finance_maps,
        finance_map_source=finance_map_source,
    )


def capital_change_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    stock_code_pool: Callable[..., tuple[list[str], str | None, dict[str, str]]],
    requested_categories: Callable[[Any], set[int] | None],
    capital_change_rows_by_tdx_code_func: Callable[..., dict[str, dict[str, Any]]],
    capital_change_result_func: Callable[..., CapitalChangeResult],
    capital_change_meta_func: Callable[..., dict[str, Any]],
    client_pool_size: Callable[[Any], int],
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> CapitalChangeRequestResult:
    tdx_codes, expanded_scope, _names_by_tdx_code = stock_code_pool(
        client,
        params,
        progress_start=20,
        progress_span=8,
    )
    categories = requested_categories(params.get("category"))

    emit_source_progress(
        progress_callback,
        29,
        f"已准备股票池，共 {len(tdx_codes)} 只",
        progress_current=0,
        progress_total=len(tdx_codes),
        progress_unit="只",
        eta_ms=None,
    )
    code_results = capital_change_rows_by_tdx_code_func(
        client,
        tdx_codes,
        requested_categories=categories,
        progress_callback=progress_callback,
        progress_start=30,
        progress_span=38,
    )
    result = capital_change_result_func(
        tdx_codes,
        code_results,
        pool_size=client_pool_size(client),
    )
    return CapitalChangeRequestResult(
        rows=result.rows,
        meta=capital_change_meta_func(
            result,
            tdx_codes,
            expanded_scope=expanded_scope,
            requested_categories=categories,
        ),
    )


@dataclass(frozen=True)
class DailyShareRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def daily_share_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    stock_code_pool: Callable[..., tuple[list[str], str | None, dict[str, str]]],
    validation_error: type[ValueError],
    finance_rows_by_tdx_code: Callable[..., tuple[dict[str, dict[str, Any]], int]],
    daily_share_rows_func: Callable[..., list[dict[str, Any]]],
    daily_share_meta_func: Callable[..., dict[str, Any]],
    market_to_id: Mapping[str, int],
    normalize_daily_share_row: Callable[..., dict[str, Any]],
    client_pool_size: Callable[[Any], int],
    finance_batch_size: int,
    emit_source_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> DailyShareRequestResult:
    tdx_codes, expanded_scope, _names_by_tdx_code = stock_code_pool(
        client,
        params,
        progress_start=20,
        progress_span=8,
    )
    stats, stats_refreshed = _ensure_tdx_stats_resource_for_params(
        client,
        params,
        validation_error=validation_error,
    )
    finance_by_tdx_code, finance_batch_count = finance_rows_by_tdx_code(
        client,
        tdx_codes,
        batch_size=finance_batch_size,
        progress_callback=progress_callback,
        progress_start=32,
        progress_span=36,
    )

    rows = daily_share_rows_func(
        tdx_codes,
        stats=stats,
        finance_by_tdx_code=finance_by_tdx_code,
        market_to_id=market_to_id,
        normalize_daily_share_row=normalize_daily_share_row,
    )
    emit_source_progress(
        progress_callback,
        68,
        f"每日股本整理完成 {len(rows)}/{len(tdx_codes)} 只",
        progress_current=len(tdx_codes),
        progress_total=len(tdx_codes),
        progress_unit="只",
        eta_ms=None,
    )
    return DailyShareRequestResult(
        rows=rows,
        meta=daily_share_meta_func(
            rows,
            tdx_codes,
            stats=stats,
            stats_refreshed=stats_refreshed,
            expanded_scope=expanded_scope,
            finance_batch_count=finance_batch_count,
            finance_batch_size=finance_batch_size,
            finance_concurrency=client_pool_size(client),
        ),
    )


def capital_change_meta(
    result: CapitalChangeResult,
    tdx_codes: Sequence[str],
    *,
    expanded_scope: str | None,
    requested_categories: set[int] | None,
) -> dict[str, Any]:
    return {
        "tdx_protocol": "0x000f",
        "tdx_event_count": result.event_count,
        "tdx_returned_event_count": result.returned_event_count,
        "tdx_stock_scope": expanded_scope,
        "tdx_code_expansion_source": "stock_codes_tdx" if expanded_scope is not None else None,
        "tdx_requested_code_count": len(tdx_codes),
        "tdx_capital_change_concurrency": result.concurrency,
        "tdx_category_filter": tuple(sorted(requested_categories)) if requested_categories else None,
    }


def finance_info_result(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    interface_name: str,
    tdx_finance_info: Callable[[Any, Sequence[str]], Sequence[Any]],
    finance_records: Callable[[Any], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_finance_info_row: Callable[..., dict[str, Any]],
    fields: Sequence[str],
    enrich_profile: bool,
    finance_maps: Any = None,
    finance_map_source: str | None = None,
) -> FinanceInfoResult:
    rows, record_count, skipped_empty_count = finance_info_rows(
        client,
        tdx_codes,
        tdx_finance_info=tdx_finance_info,
        finance_records=finance_records,
        get_value=get_value,
        normalize_finance_info_row=normalize_finance_info_row,
        fields=fields,
        enrich_profile=enrich_profile,
        finance_maps=finance_maps,
    )
    meta = {
        "tdx_protocol": "0x0010",
        "tdx_requested_code_count": len(tdx_codes),
        "tdx_finance_record_count": record_count,
        "tdx_skipped_empty_record_count": skipped_empty_count,
        "tdx_finance_view": interface_name,
    }
    if finance_map_source is not None:
        meta["tdx_finance_map_source"] = finance_map_source
        if finance_maps is not None:
            meta["tdx_finance_map_loaded"] = finance_maps.loaded
    return FinanceInfoResult(rows=rows, meta=meta)


def finance_info_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    tdx_finance_info: Callable[[Any, Sequence[str]], Sequence[Any]],
    finance_records: Callable[[Any], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_finance_info_row: Callable[..., dict[str, Any]],
    fields: Sequence[str],
    enrich_profile: bool,
    finance_maps: Any = None,
) -> tuple[list[dict[str, Any]], int, int]:
    rows: list[dict[str, Any]] = []
    record_count = 0
    skipped_empty_count = 0
    for block in tdx_finance_info(client, tdx_codes):
        records = finance_records(block)
        record_count += len(records)
        for record in records:
            if bool(get_value(record, "is_empty", False)):
                skipped_empty_count += 1
                continue
            row = normalize_finance_info_row(
                record,
                enrich_profile=enrich_profile,
                finance_maps=finance_maps,
            )
            rows.append({field: row.get(field) for field in fields})

    rows.sort(key=lambda row: str(row.get("instrument_id") or ""))
    return rows, record_count, skipped_empty_count


def daily_share_rows(
    tdx_codes: Sequence[str],
    *,
    stats: Any,
    finance_by_tdx_code: dict[str, dict[str, Any]],
    market_to_id: Mapping[str, int],
    normalize_daily_share_row: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tdx_code in tdx_codes:
        market_id = market_to_id.get(tdx_code[:2], 0)
        stat_row, _stat2_row = stats.row(market_id, tdx_code[2:])
        finance_row = finance_by_tdx_code.get(tdx_code)
        rows.append(
            normalize_daily_share_row(
                tdx_code,
                stats_date=stats.stats_date,
                stat_row=stat_row,
                finance_row=finance_row,
            )
        )

    rows.sort(key=lambda row: str(row.get("instrument_id") or ""))
    return rows


def daily_share_meta(
    rows: Sequence[Mapping[str, Any]],
    tdx_codes: Sequence[str],
    *,
    stats: Any,
    stats_refreshed: bool,
    expanded_scope: str | None,
    finance_batch_count: int,
    finance_batch_size: int,
    finance_concurrency: int,
) -> dict[str, Any]:
    return {
        "tdx_protocol": "0x0010+tdxstat",
        "tdx_stats_source_path": stats.source_path,
        "tdx_stats_refreshed": stats_refreshed,
        "tdx_stats_date": stats.stats_date,
        "tdx_stock_scope": expanded_scope,
        "tdx_code_expansion_source": "stock_codes_tdx" if expanded_scope is not None else None,
        "tdx_requested_code_count": len(tdx_codes),
        "tdx_returned_count": len(rows),
        "tdx_finance_batch_count": finance_batch_count,
        "tdx_finance_batch_size": finance_batch_size,
        "tdx_finance_concurrency": finance_concurrency,
    }


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
    requested = list(tdx_codes)
    results: dict[str, dict[str, Any]] = {}
    started_at = monotonic()

    def request_one(tdx_code: str) -> tuple[str, dict[str, Any]]:
        capital_changes = tdx_capital_changes(client, tdx_code)
        records = as_list(get_value(capital_changes, "records", ()))
        rows = [
            normalize_capital_change_row(tdx_code, record)
            for record in records
            if category_matches(record, requested_categories)
        ]
        return tdx_code, {"event_count": len(records), "rows": rows}

    if not requested:
        return results

    worker_count = min(client_pool_size(client), len(requested))
    if worker_count <= 1 or len(requested) <= 1:
        for index, tdx_code in enumerate(requested, start=1):
            result_code, result = request_one(tdx_code)
            results[result_code] = result
            emit_progress(
                progress_callback,
                completed=index,
                total=len(requested),
                unit="只",
                started_at=started_at,
                percent_start=progress_start,
                percent_span=progress_span,
                label="请求股本变迁",
            )
        return results

    with ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix="axdata-tdx-capital-changes",
    ) as executor:
        futures = [executor.submit(request_one, tdx_code) for tdx_code in requested]
        completed = 0
        for future in as_completed(futures):
            result_code, result = future.result()
            results[result_code] = result
            completed += 1
            emit_progress(
                progress_callback,
                completed=completed,
                total=len(requested),
                unit="只",
                started_at=started_at,
                percent_start=progress_start,
                percent_span=progress_span,
                label="请求股本变迁",
            )
    return results


def capital_change_result(
    tdx_codes: Sequence[str],
    code_results: Mapping[str, Mapping[str, Any]],
    *,
    pool_size: int,
) -> CapitalChangeResult:
    rows: list[dict[str, Any]] = []
    event_count = 0
    for tdx_code in tdx_codes:
        code_result = code_results.get(tdx_code, {})
        event_count += int(code_result.get("event_count") or 0)
        rows.extend(code_result.get("rows") or [])

    rows.sort(
        key=lambda row: (
            row["tdx_code"],
            row["event_date"] or "",
            int(row["category_raw"] or 0),
        )
    )
    return CapitalChangeResult(
        rows=rows,
        event_count=event_count,
        returned_event_count=len(rows),
        concurrency=min(pool_size, max(len(tdx_codes), 1)),
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
    unavailable_error: type[BaseException],
    batch_size: int | None = None,
    progress_callback: Callable[..., None] | None = None,
    progress_start: int = 28,
    progress_span: int = 40,
) -> tuple[dict[str, dict[str, Any]], int]:
    rows: dict[str, dict[str, Any]] = {}
    batches = chunked(list(tdx_codes), batch_size or max(len(tdx_codes), 1))
    worker_count = client_pool_size(client)
    started_at = monotonic()
    try:
        if worker_count <= 1 or len(batches) <= 1:
            blocks = []
            for index, batch in enumerate(batches, start=1):
                blocks.extend(tdx_finance_info(client, batch))
                emit_progress(
                    progress_callback,
                    completed=index,
                    total=len(batches),
                    unit="批",
                    started_at=started_at,
                    percent_start=progress_start,
                    percent_span=progress_span,
                    label="请求财务快照",
                )
        else:
            blocks = []
            with ThreadPoolExecutor(
                max_workers=min(worker_count, len(batches)),
                thread_name_prefix="axdata-tdx-finance",
            ) as executor:
                futures = [executor.submit(tdx_finance_info, client, batch) for batch in batches]
                completed = 0
                for future in as_completed(futures):
                    blocks.extend(future.result())
                    completed += 1
                    emit_progress(
                        progress_callback,
                        completed=completed,
                        total=len(batches),
                        unit="批",
                        started_at=started_at,
                        percent_start=progress_start,
                        percent_span=progress_span,
                        label="请求财务快照",
                    )
    except unavailable_error:
        return rows, len(batches)
    for block in blocks:
        for record in finance_records(block):
            if bool(get_value(record, "is_empty", False)):
                continue
            row = normalize_finance_info_row(record)
            tdx_code = str(row.get("tdx_code") or "").lower()
            if tdx_code:
                rows[tdx_code] = row
    return rows, len(batches)


def _ensure_tdx_stats_resource_for_params(*args: Any, **kwargs: Any) -> tuple[Any, bool]:
    from .stats_resource import ensure_tdx_stats_resource_for_params

    return ensure_tdx_stats_resource_for_params(*args, **kwargs)
