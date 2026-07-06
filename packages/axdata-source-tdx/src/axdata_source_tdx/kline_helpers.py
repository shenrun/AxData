"""K-line result and metadata helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol


class KlineResultLike(Protocol):
    index: int
    rows: list[dict[str, Any]]
    series: Any
    page_count: int


class KlineParallelResultLike(Protocol):
    results: Sequence[KlineResultLike]
    host_metas: Sequence[Mapping[str, Any]]
    host_count: int
    pool_size_per_host: int
    concurrency_capacity: int
    concurrency_limit: int


@dataclass(frozen=True)
class KlineRequestRowsResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def stock_kline_request_result(
    client: Any,
    interface_name: str,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    kline_period: Callable[[str, Mapping[str, Any]], str],
    kline_page_size: Callable[[str, Mapping[str, Any]], int],
    adjust_param: Callable[[Any], str],
    anchor_date_param: Callable[[Mapping[str, Any]], Any],
    validate_anchor_date: Callable[[str, Any], None],
    rows_meta_func: Callable[..., tuple[list[dict[str, Any]], dict[str, Any]]],
    normalize_row: Callable[[Any], dict[str, Any]],
    request_code_history: Callable[..., KlineResultLike],
    get_value: Any,
) -> KlineRequestRowsResult:
    tdx_codes = requested_codes(params.get("code"))
    period = kline_period(interface_name, params)
    page_size = kline_page_size(interface_name, params)
    adjust = adjust_param(params.get("adjust"))
    anchor_date = anchor_date_param(params)
    validate_anchor_date(adjust, anchor_date)

    rows, meta = rows_meta_func(
        client,
        tdx_codes,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        kind="stock",
        normalize_row=normalize_row,
        request_code_history=request_code_history,
        get_value=get_value,
    )
    return KlineRequestRowsResult(rows=rows, meta=meta)


def stock_kline_parallel_request_result(
    interface_name: str,
    params: Mapping[str, Any],
    tdx_codes: Sequence[str],
    *,
    options: Any,
    kline_period: Callable[[str, Mapping[str, Any]], str],
    kline_page_size: Callable[[str, Mapping[str, Any]], int],
    adjust_param: Callable[[Any], str],
    anchor_date_param: Callable[[Mapping[str, Any]], Any],
    validate_anchor_date: Callable[[str, Any], None],
    parallel_options_func: Callable[..., Any],
    has_connection_options: Callable[[Any], bool],
    option_hosts: Callable[..., list[str] | None],
    option_connections_per_server: Callable[[Any], int],
    configured_hosts: Callable[[], list[str]],
    configured_hosts_from_options: Callable[..., list[str]],
    env_int: Callable[..., int],
    default_host_count: int,
    default_pool_size: int,
    request_parallel: Callable[..., KlineParallelResultLike],
    rows_meta_func: Callable[..., tuple[list[dict[str, Any]], dict[str, Any]]],
    normalize_row: Callable[[Any], dict[str, Any]],
    get_value: Any,
    unavailable_error: type[Exception],
) -> KlineRequestRowsResult:
    period = kline_period(interface_name, params)
    page_size = kline_page_size(interface_name, params)
    adjust = adjust_param(params.get("adjust"))
    anchor_date = anchor_date_param(params)
    validate_anchor_date(adjust, anchor_date)
    parallel_options = parallel_options_func(
        options,
        has_connection_options=has_connection_options,
        option_hosts=option_hosts,
        option_connections_per_server=option_connections_per_server,
        configured_hosts=configured_hosts,
        configured_hosts_from_options=configured_hosts_from_options,
        env_int=env_int,
        default_host_count=default_host_count,
        default_pool_size=default_pool_size,
    )
    hosts = parallel_options.hosts
    pool_size = parallel_options.pool_size
    if not hosts:
        raise unavailable_error("No TDX 7709 hosts are configured for kline requests.")

    result = request_parallel(
        hosts,
        tdx_codes,
        pool_size=pool_size,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
    )
    rows, meta = rows_meta_func(
        result,
        hosts=hosts,
        page_size=page_size,
        requested_code_count=len(tdx_codes),
        normalize_row=normalize_row,
        get_value=get_value,
    )
    return KlineRequestRowsResult(rows=rows, meta=meta)


def index_like_kline_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    index_kline_period: Callable[[Any], str],
    int_param: Callable[..., int],
    max_count: int,
    rows_meta_func: Callable[..., tuple[list[dict[str, Any]], dict[str, Any]]],
    normalize_row: Callable[[Any], dict[str, Any]],
    request_code_history: Callable[..., KlineResultLike],
    get_value: Any,
    request_kind: str,
    meta_kind: str,
) -> KlineRequestRowsResult:
    tdx_codes = requested_codes(params.get("code"))
    period = index_kline_period(params.get("period", "day"))
    page_size = int_param(params, "count", 120, minimum=1, maximum=max_count)

    rows, meta = rows_meta_func(
        client,
        tdx_codes,
        period=period,
        page_size=page_size,
        adjust="none",
        anchor_date=None,
        kind=request_kind,
        normalize_row=normalize_row,
        request_code_history=request_code_history,
        get_value=get_value,
        tail_count_per_code=page_size,
        extra_meta={"tdx_kline_kind": meta_kind},
    )
    return KlineRequestRowsResult(rows=rows, meta=meta)


def sequential_kline_rows_and_meta(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str,
    normalize_row: Callable[[Any], dict[str, Any]],
    request_code_history: Callable[..., KlineResultLike],
    get_value: Any,
    extra_meta: Mapping[str, Any] | None = None,
    tail_count_per_code: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = [
        request_code_history(
            client,
            index,
            tdx_code,
            period=period,
            page_size=page_size,
            adjust=adjust,
            anchor_date=anchor_date,
            kind=kind,
        )
        for index, tdx_code in enumerate(tdx_codes)
    ]
    return kline_rows_and_meta(
        results,
        page_size=page_size,
        requested_code_count=len(tdx_codes),
        concurrency_limit=1,
        concurrency_capacity=1,
        normalize_row=normalize_row,
        get_value=get_value,
        extra_meta=extra_meta,
        tail_count_per_code=tail_count_per_code,
    )


def flatten_kline_results(results: Sequence[KlineResultLike]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in sorted(results, key=lambda item: item.index):
        rows.extend(result.rows)
    return rows


def kline_rows_and_meta(
    results: Sequence[KlineResultLike],
    *,
    page_size: int,
    requested_code_count: int,
    concurrency_limit: int,
    concurrency_capacity: int,
    normalize_row: Callable[[Any], dict[str, Any]],
    get_value: Any,
    extra_meta: Mapping[str, Any] | None = None,
    tail_count_per_code: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sorted_results = sorted(results, key=lambda item: item.index)
    if tail_count_per_code is None:
        source_rows = flatten_kline_results(sorted_results)
    else:
        source_rows = [
            row
            for result in sorted_results
            for row in result.rows[-tail_count_per_code:]
        ]
    rows = [normalize_row(row) for row in source_rows]
    series = sorted_results[0].series
    meta = kline_meta(
        series,
        page_size=page_size,
        page_count=sum(result.page_count for result in sorted_results),
        requested_code_count=requested_code_count,
        concurrency_limit=concurrency_limit,
        concurrency_capacity=concurrency_capacity,
        get_value=get_value,
    )
    if extra_meta:
        meta.update(dict(extra_meta))
    return rows, meta


def kline_parallel_rows_and_meta(
    result: KlineParallelResultLike,
    *,
    hosts: Sequence[str],
    page_size: int,
    requested_code_count: int,
    normalize_row: Callable[[Any], dict[str, Any]],
    get_value: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, meta = kline_rows_and_meta(
        result.results,
        page_size=page_size,
        requested_code_count=requested_code_count,
        concurrency_limit=result.concurrency_limit,
        concurrency_capacity=result.concurrency_capacity,
        normalize_row=normalize_row,
        get_value=get_value,
    )
    return rows, {
        **tdx_parallel_client_meta(result.host_metas, hosts),
        **meta,
        "tdx_kline_host_count": result.host_count,
        "tdx_kline_pool_size_per_host": result.pool_size_per_host,
    }


def kline_meta(
    series: Any,
    *,
    page_size: int,
    page_count: int,
    requested_code_count: int,
    concurrency_limit: int,
    concurrency_capacity: int,
    get_value: Any,
) -> dict[str, Any]:
    return {
        "tdx_protocol": "0x052d",
        "tdx_period_raw": get_value(series, "period_raw", 13),
        "tdx_period_param_raw": get_value(series, "period_param_raw", None),
        "tdx_full_history": True,
        "tdx_page_size": page_size,
        "tdx_page_count": page_count,
        "tdx_start": 0,
        "tdx_request_count": page_size,
        "tdx_adjust_mode": get_value(series, "adjust_mode", None),
        "tdx_adjust_mode_raw": get_value(series, "adjust_mode_raw", None),
        "tdx_anchor_date_raw": get_value(series, "anchor_date_raw", None),
        "tdx_requested_code_count": requested_code_count,
        "tdx_concurrency_limit": concurrency_limit,
        "tdx_concurrency_capacity": concurrency_capacity,
    }


def tdx_parallel_client_meta(
    host_metas: Sequence[Mapping[str, Any]],
    configured_hosts: Sequence[str],
) -> dict[str, Any]:
    connected_hosts: list[Any] = []
    for meta in host_metas:
        values = meta.get("tdx_connected_hosts")
        if values:
            connected_hosts.extend(values)
            continue
        connected_host = meta.get("tdx_connected_host")
        if connected_host:
            connected_hosts.append(connected_host)

    return {
        "tdx_connected_host": connected_hosts[0] if connected_hosts else None,
        "tdx_connected_hosts": tuple(connected_hosts) if connected_hosts else None,
        "tdx_configured_host_count": len(configured_hosts),
        "tdx_configured_hosts_sample": tuple(configured_hosts[:5]),
        "tdx_pool_size": sum(int(meta.get("tdx_pool_size") or 0) for meta in host_metas),
        "tdx_heartbeat_interval": None,
    }
