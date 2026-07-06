"""Stock code table scan helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class StockCodeScanResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


@dataclass(frozen=True)
class StockCodePoolResult:
    tdx_codes: list[str]
    expanded_scope: str | None
    names_by_tdx_code: dict[str, str]


@dataclass(frozen=True)
class CodeRowsResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def index_codes_result(
    client: Any,
    *,
    exchanges: Sequence[str],
    start: int,
    limit: int,
    include_tdx_block_index: bool,
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    index_type_from_tdx_code: Callable[[str], str],
    normalize_index_code_row: Callable[[Mapping[str, Any], str], dict[str, Any]],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    requested_codes: set[str] | None,
    requested_names: set[str] | None,
) -> CodeRowsResult:
    rows = request_index_codes(
        client,
        exchanges=exchanges,
        start=start,
        limit=limit,
        include_tdx_block_index=include_tdx_block_index,
        page_size=page_size,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        index_type_from_tdx_code=index_type_from_tdx_code,
        normalize_index_code_row=normalize_index_code_row,
        code_matches=code_matches,
        name_matches=name_matches,
        requested_codes=requested_codes,
        requested_names=requested_names,
    )
    return CodeRowsResult(
        rows=rows,
        meta={
            "tdx_protocol": "0x044d",
            "tdx_requested_exchange_count": len(exchanges),
            "tdx_include_tdx_block_index": include_tdx_block_index,
            "tdx_returned_count": len(rows),
        },
    )


def index_codes_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes_func: Callable[[Any], set[str] | None],
    requested_names_func: Callable[[Any], set[str] | None],
    requested_exchanges_func: Callable[[Any], list[str]],
    bool_param: Callable[..., bool],
    int_param: Callable[..., int],
    result_func: Callable[..., CodeRowsResult],
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    index_type_from_tdx_code: Callable[[str], str],
    normalize_index_code_row: Callable[[Mapping[str, Any], str], dict[str, Any]],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
) -> CodeRowsResult:
    requested_codes = requested_codes_func(params.get("code"))
    requested_names = requested_names_func(params.get("name"))
    exchanges = requested_exchanges_func(params.get("exchange") or "all")
    include_tdx_block_index = bool_param(
        params.get("include_tdx_block_index", False),
        name="include_tdx_block_index",
    )
    start = int_param(params, "start", 0, minimum=0)
    limit = int_param(params, "limit", 0, minimum=0)
    return result_func(
        client,
        exchanges=exchanges,
        start=start,
        limit=limit,
        include_tdx_block_index=include_tdx_block_index,
        page_size=page_size,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        index_type_from_tdx_code=index_type_from_tdx_code,
        normalize_index_code_row=normalize_index_code_row,
        code_matches=code_matches,
        name_matches=name_matches,
        requested_codes=requested_codes,
        requested_names=requested_names,
    )


def etf_codes_result(
    client: Any,
    *,
    exchanges: Sequence[str],
    start: int,
    limit: int,
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    etf_type_from_tdx_code: Callable[[str], str | None],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    requested_codes: set[str] | None,
    requested_names: set[str] | None,
) -> CodeRowsResult:
    rows = request_etf_codes(
        client,
        exchanges=exchanges,
        start=start,
        limit=limit,
        page_size=page_size,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        etf_type_from_tdx_code=etf_type_from_tdx_code,
        code_matches=code_matches,
        name_matches=name_matches,
        requested_codes=requested_codes,
        requested_names=requested_names,
    )
    return CodeRowsResult(
        rows=rows,
        meta={
            "tdx_protocol": "0x044d",
            "tdx_requested_exchange_count": len(exchanges),
            "tdx_returned_count": len(rows),
        },
    )


def etf_codes_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes_func: Callable[[Any], set[str] | None],
    requested_names_func: Callable[[Any], set[str] | None],
    requested_exchanges_func: Callable[[Any], list[str]],
    int_param: Callable[..., int],
    result_func: Callable[..., CodeRowsResult],
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    etf_type_from_tdx_code: Callable[[str], str | None],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
) -> CodeRowsResult:
    requested_codes = requested_codes_func(params.get("code"))
    requested_names = requested_names_func(params.get("name"))
    exchanges = requested_exchanges_func(params.get("exchange") or "all")
    start = int_param(params, "start", 0, minimum=0)
    limit = int_param(params, "limit", 0, minimum=0)
    return result_func(
        client,
        exchanges=exchanges,
        start=start,
        limit=limit,
        page_size=page_size,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        etf_type_from_tdx_code=etf_type_from_tdx_code,
        code_matches=code_matches,
        name_matches=name_matches,
        requested_codes=requested_codes,
        requested_names=requested_names,
    )


def stock_rows_to_tdx_code_pool(
    stock_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[str], dict[str, str]]:
    tdx_codes: list[str] = []
    names_by_tdx_code: dict[str, str] = {}
    seen: set[str] = set()
    for row in stock_rows:
        tdx_code = str(row.get("tdx_code") or "").lower()
        if not tdx_code or tdx_code in seen:
            continue
        seen.add(tdx_code)
        tdx_codes.append(tdx_code)
        name = str(row.get("name") or "").strip()
        if name:
            names_by_tdx_code[tdx_code] = name
    return tdx_codes, names_by_tdx_code


def stock_code_pool_from_params(
    params: Mapping[str, Any],
    *,
    request_stock_rows: Callable[[Mapping[str, Any], int, int], Sequence[Mapping[str, Any]]],
    is_all_codes_value: Callable[[Any], bool],
    requested_kline_codes: Callable[[Any], list[str]],
    scope_meta_value: Callable[[Any], str],
    progress_start: int = 20,
    progress_span: int = 8,
) -> StockCodePoolResult:
    code = params.get("code")
    if is_all_codes_value(code):
        scope = params.get("scope", "all")
        stock_rows = request_stock_rows({"scope": scope}, progress_start, progress_span)
        tdx_codes, names_by_tdx_code = stock_rows_to_tdx_code_pool(stock_rows)
        return StockCodePoolResult(
            tdx_codes=tdx_codes,
            expanded_scope=scope_meta_value(scope),
            names_by_tdx_code=names_by_tdx_code,
        )
    return StockCodePoolResult(
        tdx_codes=requested_kline_codes(code),
        expanded_scope=None,
        names_by_tdx_code={},
    )


def should_parallelize_stock_code_request(
    params: Mapping[str, Any],
    *,
    pool_size_env_set: bool,
    int_param: Callable[..., int],
    requested_boards: Callable[[Any], set[str] | None],
    requested_exchanges: Callable[[Any], list[str]],
    exchanges_for_boards: Callable[[set[str] | None], str],
) -> bool:
    if pool_size_env_set:
        return False
    if int_param(params, "limit", 0, minimum=0) != 0:
        return False
    boards = requested_boards(params.get("scope"))
    exchanges = requested_exchanges(params.get("exchange") or exchanges_for_boards(boards))
    return len(exchanges) > 1


def stock_code_request_pool_size(
    params: Mapping[str, Any],
    *,
    requested_boards: Callable[[Any], set[str] | None],
    requested_exchanges: Callable[[Any], list[str]],
    exchanges_for_boards: Callable[[set[str] | None], str],
) -> int:
    boards = requested_boards(params.get("scope"))
    exchanges = requested_exchanges(params.get("exchange") or exchanges_for_boards(boards))
    return max(1, min(len(exchanges), 3))


def stock_codes_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_boards: Callable[[Any], set[str] | None],
    requested_codes_func: Callable[[Any], set[str] | None],
    requested_names_func: Callable[[Any], set[str] | None],
    requested_exchanges: Callable[[Any], list[str]],
    exchanges_for_boards: Callable[[set[str] | None], str],
    int_param: Callable[..., int],
    scan_func: Callable[..., StockCodeScanResult],
    client_pool_size: Callable[[Any], int],
    request_exchange: Callable[..., tuple[list[dict[str, Any]], int]],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
    progress_start: int = 20,
    progress_span: int = 40,
) -> StockCodeScanResult:
    boards = requested_boards(params.get("scope"))
    requested_codes_set = requested_codes_func(params.get("code"))
    requested_names = requested_names_func(params.get("name"))
    exchanges = requested_exchanges(params.get("exchange") or exchanges_for_boards(boards))
    start = int_param(params, "start", 0, minimum=0)
    limit = int_param(params, "limit", 0, minimum=0)
    return scan_func(
        client,
        exchanges=exchanges,
        limit=limit,
        start=start,
        client_pool_size=client_pool_size,
        request_exchange=lambda current_client, exchange, current_start: request_exchange(
            current_client,
            exchange,
            boards=boards,
            requested_codes=requested_codes_set,
            requested_names=requested_names,
            start=current_start,
        ),
        emit_progress=emit_progress,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def request_stock_codes(
    client: Any,
    *,
    exchanges: Sequence[str],
    limit: int,
    start: int,
    client_pool_size: Callable[[Any], int],
    request_exchange: Callable[[Any, str, int], tuple[list[dict[str, Any]], int]],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
    progress_start: int = 20,
    progress_span: int = 40,
) -> StockCodeScanResult:
    rows: list[dict[str, Any]] = []
    seen_instrument_ids: set[str] = set()
    scanned_pages = 0
    exchange_count = max(len(exchanges), 1)

    if limit == 0 and len(exchanges) > 1 and client_pool_size(client) > 1:
        exchange_results: dict[int, tuple[list[dict[str, Any]], int]] = {}
        worker_count = min(len(exchanges), client_pool_size(client))
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-stock-codes") as executor:
            futures = {
                executor.submit(request_exchange, client, exchange, start): exchange_index
                for exchange_index, exchange in enumerate(exchanges)
            }
            completed = 0
            for future in as_completed(futures):
                exchange_index = futures[future]
                exchange_rows, exchange_pages = future.result()
                exchange_results[exchange_index] = (exchange_rows, exchange_pages)
                completed += 1
                emit_progress(
                    progress_callback,
                    min(progress_start + progress_span - 1, progress_start + int((completed / exchange_count) * progress_span)),
                    f"完成 {exchanges[exchange_index]} 股票列表扫描，已返回 {sum(len(value[0]) for value in exchange_results.values())} 条",
                    progress_current=sum(len(value[0]) for value in exchange_results.values()),
                    progress_total=None,
                    progress_unit="条",
                    eta_ms=None,
                )
        for exchange_index in range(len(exchanges)):
            exchange_rows, exchange_pages = exchange_results.get(exchange_index, ([], 0))
            scanned_pages += exchange_pages
            for row in exchange_rows:
                instrument_id = str(row.get("instrument_id") or "")
                if instrument_id in seen_instrument_ids:
                    continue
                seen_instrument_ids.add(instrument_id)
                rows.append(row)
        return StockCodeScanResult(
            rows=rows,
            meta={
                "tdx_code_market_scan_mode": "parallel",
                "tdx_code_market_worker_count": worker_count,
                "tdx_code_scanned_pages": scanned_pages,
            },
        )

    for exchange_index, exchange in enumerate(exchanges):
        exchange_rows, exchange_pages = request_exchange(client, exchange, start)
        scanned_pages += exchange_pages
        for row in exchange_rows:
            instrument_id = str(row.get("instrument_id") or "")
            if instrument_id in seen_instrument_ids:
                continue
            seen_instrument_ids.add(instrument_id)
            rows.append(row)
            if limit and len(rows) >= limit:
                emit_progress(
                    progress_callback,
                    progress_start + progress_span,
                    f"股票列表达到 {len(rows)} 条",
                    progress_current=len(rows),
                    progress_total=limit,
                    progress_unit="条",
                    eta_ms=None,
                )
                return StockCodeScanResult(rows=rows, meta={})
        emit_progress(
            progress_callback,
            min(
                progress_start + progress_span,
                progress_start + int(((exchange_index + 1) / exchange_count) * progress_span),
            ),
            f"完成 {exchange} 股票列表扫描，已返回 {len(rows)} 条",
            progress_current=len(rows),
            progress_total=None,
            progress_unit="条",
            eta_ms=None,
        )
    return StockCodeScanResult(
        rows=rows,
        meta={
            "tdx_code_market_scan_mode": "sequential",
            "tdx_code_market_worker_count": 1,
            "tdx_code_scanned_pages": scanned_pages,
        },
    )


def request_stock_codes_exchange(
    client: Any,
    exchange: str,
    *,
    start: int,
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    board_matches: Callable[[Any, set[str] | None], bool],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    boards: set[str] | None,
    requested_codes: set[str] | None,
    requested_names: set[str] | None,
) -> tuple[list[dict[str, Any]], int]:
    market = exchange_to_market(exchange)
    current_start = start
    rows: list[dict[str, Any]] = []
    scanned_pages = 0
    while True:
        items = as_list(tdx_codes(client, market, start=current_start, limit=page_size))
        if not items:
            break
        scanned_pages += 1
        for item in items:
            row = normalize_security(item)
            if (
                row["tdx_category"] in {"a_share", "cdr"}
                and board_matches(row["market_code"], boards)
                and code_matches(row, requested_codes)
                and name_matches(row, requested_names)
            ):
                rows.append(row)
        if len(items) < page_size:
            break
        current_start += len(items)
    return rows, scanned_pages


def request_index_codes(
    client: Any,
    *,
    exchanges: Sequence[str],
    start: int,
    limit: int,
    include_tdx_block_index: bool,
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    index_type_from_tdx_code: Callable[[str], str],
    normalize_index_code_row: Callable[[Mapping[str, Any], str], dict[str, Any]],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    requested_codes: set[str] | None,
    requested_names: set[str] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_instrument_ids: set[str] = set()

    for exchange in exchanges:
        market = exchange_to_market(exchange)
        current_start = start
        while True:
            items = as_list(tdx_codes(client, market, start=current_start, limit=page_size))
            if not items:
                break
            for item in items:
                row = normalize_security(item)
                if row.get("tdx_category") != "index":
                    continue
                index_type = index_type_from_tdx_code(str(row.get("tdx_code") or ""))
                if index_type == "tdx_block_index" and not include_tdx_block_index:
                    continue
                if not code_matches(row, requested_codes) or not name_matches(row, requested_names):
                    continue
                instrument_id = str(row.get("instrument_id") or "")
                if instrument_id in seen_instrument_ids:
                    continue
                seen_instrument_ids.add(instrument_id)
                rows.append(normalize_index_code_row(row, index_type))
                if limit and len(rows) >= limit:
                    return rows
            if len(items) < page_size:
                break
            current_start += len(items)

    return rows


def request_etf_codes(
    client: Any,
    *,
    exchanges: Sequence[str],
    start: int,
    limit: int,
    page_size: int,
    exchange_to_market: Callable[[str], str],
    tdx_codes: Callable[..., Any],
    as_list: Callable[[Any], list[Any]],
    normalize_security: Callable[[Any], dict[str, Any]],
    etf_type_from_tdx_code: Callable[[str], str | None],
    code_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    name_matches: Callable[[Mapping[str, Any], set[str] | None], bool],
    requested_codes: set[str] | None,
    requested_names: set[str] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_instrument_ids: set[str] = set()

    for exchange in exchanges:
        market = exchange_to_market(exchange)
        current_start = start
        while True:
            items = as_list(tdx_codes(client, market, start=current_start, limit=page_size))
            if not items:
                break
            for item in items:
                row = normalize_security(item)
                tdx_code = str(row.get("tdx_code") or "")
                if etf_type_from_tdx_code(tdx_code) is None:
                    continue
                if not code_matches(row, requested_codes) or not name_matches(row, requested_names):
                    continue
                instrument_id = str(row.get("instrument_id") or "")
                if instrument_id in seen_instrument_ids:
                    continue
                seen_instrument_ids.add(instrument_id)
                rows.append(
                    {
                        "instrument_id": row.get("instrument_id"),
                        "symbol": row.get("symbol"),
                        "tdx_code": row.get("tdx_code"),
                        "exchange": row.get("exchange"),
                        "name": row.get("name"),
                        "previous_close": row.get("tdx_previous_close_price"),
                    }
                )
                if limit and len(rows) >= limit:
                    return rows
            if len(items) < page_size:
                break
            current_start += len(items)

    return rows
