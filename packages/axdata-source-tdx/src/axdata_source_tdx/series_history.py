"""Historical K-line and trade pagination helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, is_dataclass, replace
from types import SimpleNamespace
from typing import Any, Callable


@dataclass(frozen=True)
class KlineParallelOptions:
    hosts: list[str]
    pool_size: int


@dataclass(frozen=True)
class KlineRequestResult:
    index: int
    rows: list[dict[str, Any]]
    series: Any
    page_count: int


@dataclass(frozen=True)
class KlineHostResult:
    results: list[KlineRequestResult]
    meta: dict[str, Any]


@dataclass(frozen=True)
class KlineParallelResult:
    results: list[KlineRequestResult]
    host_metas: list[dict[str, Any]]
    host_count: int
    pool_size_per_host: int
    concurrency_capacity: int
    concurrency_limit: int


def kline_parallel_options(
    options: Any,
    *,
    has_connection_options: Callable[[Any], bool],
    option_hosts: Callable[..., list[str] | None],
    option_connections_per_server: Callable[[Any], int],
    configured_hosts: Callable[[], list[str]],
    configured_hosts_from_options: Callable[..., list[str]],
    env_int: Callable[..., int],
    default_host_count: int,
    default_pool_size: int,
) -> KlineParallelOptions:
    if has_connection_options(options):
        hosts = option_hosts(
            options,
            configured_hosts=configured_hosts_from_options,
        ) or configured_hosts()
        pool_size = option_connections_per_server(options)
    else:
        host_count = env_int("AXDATA_TDX_KLINE_HOST_COUNT", default_host_count, minimum=1)
        pool_size = env_int("AXDATA_TDX_KLINE_POOL_SIZE", default_pool_size, minimum=1)
        hosts = list(configured_hosts()[:host_count])
    return KlineParallelOptions(hosts=list(hosts), pool_size=pool_size)


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
    current_start = 0
    page_count = 0
    rows: list[dict[str, Any]] = []
    decimal = price_decimal(client, tdx_code)

    while current_start <= max_start:
        if trade_date is None:
            series = today_trades(
                client,
                tdx_code,
                start=current_start,
                count=page_size,
            )
        else:
            series = historical_trades(
                client,
                tdx_code,
                trade_date=trade_date,
                start=current_start,
                count=page_size,
            )
        page_count += 1
        records = trade_records(series)
        if not records:
            break

        rows.extend(normalize_trade_row(series, record, decimal=decimal) for record in records)
        if len(records) < page_size:
            break
        current_start += len(records)

    return rows, page_count


def request_kline_series_history(
    client: Any,
    tdx_code: str,
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str = "stock",
    max_count: int,
    tdx_kline: Callable[..., Any],
    kline_bars: Callable[[Any], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
) -> tuple[Any, int]:
    current_start = 0
    page_count = 0
    first_series: Any | None = None
    bars_by_time: dict[Any, Any] = {}

    while current_start <= max_count:
        series = tdx_kline(
            client,
            tdx_code,
            period=period,
            start=current_start,
            count=page_size,
            adjust=adjust,
            anchor_date=anchor_date,
            kind=kind,
        )
        if first_series is None:
            first_series = series
        page_count += 1
        bars = kline_bars(series)
        if not bars:
            break

        new_bar_count = 0
        for bar in bars:
            key = get_value(bar, "time", None)
            if key in bars_by_time:
                continue
            bars_by_time[key] = bar
            new_bar_count += 1

        if len(bars) < page_size or new_bar_count == 0:
            break
        current_start += len(bars)

    assert first_series is not None
    bars = tuple(sorted(bars_by_time.values(), key=lambda item: get_value(item, "time", None)))
    if is_dataclass(first_series):
        return replace(first_series, bars=bars), page_count
    series_dict = {
        key: value
        for key, value in vars(first_series).items()
        if not key.startswith("_")
    }
    series_dict["bars"] = bars
    return SimpleNamespace(**series_dict), page_count


def request_kline_code_history(
    client: Any,
    index: int,
    tdx_code: str,
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str = "stock",
    request_series_history: Callable[..., tuple[Any, int]],
    normalize_kline_row: Callable[[Any, Any], dict[str, Any]],
    kline_bars: Callable[[Any], Sequence[Any]],
    row_sort_key: Callable[[dict[str, Any]], Any],
) -> KlineRequestResult:
    series, page_count = request_series_history(
        client,
        tdx_code,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        kind=kind,
    )
    rows = sorted((normalize_kline_row(series, bar) for bar in kline_bars(series)), key=row_sort_key)
    return KlineRequestResult(index=index, rows=rows, series=series, page_count=page_count)


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
    stats_date_text = str(stats_date or "")
    page_size = max(1, int(count))
    current_start = 0
    page_count = 0

    while current_start <= max_count:
        series = tdx_kline(
            client,
            tdx_code,
            period="day",
            start=current_start,
            count=page_size,
            adjust="none",
            anchor_date=None,
        )
        page_count += 1
        bars = sorted(kline_bars(series), key=lambda item: get_value(item, "time", None), reverse=True)
        if not bars:
            break

        filtered: list[Any] = []
        has_base_bar = False
        for bar in bars:
            trade_date = bar_trade_date(bar)
            if stats_date_text and trade_date and trade_date > stats_date_text:
                continue
            filtered.append(bar)
            if stats_date_text and trade_date and trade_date < stats_date_text:
                has_base_bar = True
            if len(filtered) >= 5:
                return filtered, page_count

        oldest_date = bar_trade_date(bars[-1])
        if filtered and (not stats_date_text or has_base_bar):
            return filtered, page_count
        if stats_date_text and oldest_date and oldest_date < stats_date_text:
            break
        if len(bars) < page_size:
            break
        current_start += len(bars)

    return [], page_count


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
    request_code_history: Callable[..., KlineRequestResult],
    client_meta: Callable[[Any], dict[str, Any]],
) -> KlineHostResult:
    client = create_client(
        hosts=[host],
        pool_size=pool_size,
        heartbeat_interval=None,
    )
    try:
        if hasattr(client, "connect"):
            client.connect()
        worker_count = min(pool_size, max(1, len(indexed_codes)))
        results: list[KlineRequestResult] = []
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-kline-host") as executor:
            futures = [
                executor.submit(
                    request_code_history,
                    client,
                    index,
                    tdx_code,
                    period=period,
                    page_size=page_size,
                    adjust=adjust,
                    anchor_date=anchor_date,
                )
                for index, tdx_code in indexed_codes
            ]
            for future in as_completed(futures):
                results.append(future.result())
        return KlineHostResult(results=results, meta=client_meta(client))
    finally:
        if hasattr(client, "close"):
            client.close()


def request_kline_codes_parallel(
    hosts: Sequence[str],
    tdx_codes: Sequence[str],
    *,
    pool_size: int,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    request_on_host: Callable[..., KlineHostResult],
) -> KlineParallelResult:
    capacity = len(hosts) * pool_size
    concurrency_limit = min(len(tdx_codes), capacity)

    indexed_codes = list(enumerate(tdx_codes))
    worker_count = min(len(hosts), len(indexed_codes))
    grouped_codes = [indexed_codes[index::worker_count] for index in range(worker_count)]
    host_results: list[KlineHostResult] = []
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-kline") as executor:
        futures = [
            executor.submit(
                request_on_host,
                hosts[index],
                grouped_codes[index],
                pool_size=pool_size,
                period=period,
                page_size=page_size,
                adjust=adjust,
                anchor_date=anchor_date,
            )
            for index in range(worker_count)
            if grouped_codes[index]
        ]
        for future in as_completed(futures):
            host_results.append(future.result())

    return KlineParallelResult(
        results=[result for host_result in host_results for result in host_result.results],
        host_metas=[host_result.meta for host_result in host_results],
        host_count=len(hosts),
        pool_size_per_host=pool_size,
        concurrency_capacity=capacity,
        concurrency_limit=concurrency_limit,
    )
