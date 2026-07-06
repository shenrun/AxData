"""Historical price-limit base lookup helpers for TDX daily K-line requests."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable


@dataclass(frozen=True)
class PriceLimitBase:
    trade_date: str | None
    bar: Any | None
    page_count: int


@dataclass(frozen=True)
class PriceLimitRequestResult:
    tdx_code: str
    base: PriceLimitBase


def price_limit_base_from_daily_kline(
    client: Any,
    tdx_code: str,
    target_trade_date: Any,
    *,
    request_recent_daily_bars: Callable[..., tuple[list[Any], int]],
    bar_trade_date: Callable[[Any], str | None],
) -> PriceLimitBase:
    bars, page_count = request_recent_daily_bars(
        client,
        tdx_code,
        count=800,
        stats_date=target_trade_date,
    )
    target_text = str(target_trade_date or "")
    base_bar = None
    for bar in bars:
        trade_date = bar_trade_date(bar)
        if not trade_date:
            continue
        if target_text and trade_date >= target_text:
            continue
        base_bar = bar
        break
    if base_bar is None and bars:
        base_bar = bars[0]
    return PriceLimitBase(
        trade_date=bar_trade_date(base_bar) if base_bar is not None else None,
        bar=base_bar,
        page_count=page_count,
    )


def price_limit_bases_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    target_trade_date: Any,
    *,
    request_base: Callable[[Any, str, Any], PriceLimitBase],
    client_pool_size: Callable[[Any], int],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> list[PriceLimitRequestResult]:
    requested = list(tdx_codes)
    if not requested:
        return []
    total = len(requested)
    started_at = monotonic()
    worker_count = min(client_pool_size(client), len(requested))
    if worker_count <= 1 or len(requested) <= 1:
        results: list[PriceLimitRequestResult] = []
        for index, tdx_code in enumerate(requested, start=1):
            results.append(
                PriceLimitRequestResult(
                    tdx_code=tdx_code,
                    base=request_base(client, tdx_code, target_trade_date),
                )
            )
            emit_progress(progress_callback, completed=index, total=total, started_at=started_at)
        return results

    indexed_results: list[tuple[int, PriceLimitRequestResult]] = []
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="axdata-tdx-price-limit") as executor:
        futures = {
            executor.submit(request_base, client, tdx_code, target_trade_date): (index, tdx_code)
            for index, tdx_code in enumerate(requested)
        }
        completed = 0
        for future in as_completed(futures):
            index, tdx_code = futures[future]
            indexed_results.append((index, PriceLimitRequestResult(tdx_code=tdx_code, base=future.result())))
            completed += 1
            emit_progress(progress_callback, completed=completed, total=total, started_at=started_at)

    indexed_results.sort(key=lambda item: item[0])
    return [result for _index, result in indexed_results]
