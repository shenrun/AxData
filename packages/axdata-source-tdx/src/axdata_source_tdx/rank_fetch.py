"""Realtime rank fetch helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class RealtimeRankResult:
    rows: list[dict[str, Any]]
    page_count: int
    sort_reverse: Any


@dataclass(frozen=True)
class RealtimeRankRowsResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def stock_realtime_rank_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    category_param: Callable[[Any], Any],
    sort_param: Callable[[Any], int],
    filter_param: Callable[[Any], int],
    bool_param: Callable[..., bool],
    int_param: Callable[..., int],
    result_func: Callable[..., RealtimeRankRowsResult],
    default_count: int,
    max_count: int,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankRowsResult:
    category = category_param(params.get("category", "a_share"))
    sort_type = sort_param(params.get("sort", "change_pct"))
    start = int_param(params, "start", 0, minimum=0, maximum=max_start)
    count_value = params.get("count", default_count)
    full_rank = isinstance(count_value, str) and count_value.strip().lower() == "all"
    page_size = (
        max_count
        if full_rank
        else int_param(params, "count", default_count, minimum=1, maximum=max_count)
    )
    ascending = bool_param(params.get("ascending", False))
    filter_raw = filter_param(params.get("filters"))
    return result_func(
        client,
        category=category,
        sort_type=sort_type,
        start=start,
        page_size=page_size,
        full_rank=full_rank,
        ascending=ascending,
        filter_raw=filter_raw,
        max_start=max_start,
        category_quotes=category_quotes,
        get_value=get_value,
        normalize_quote=normalize_quote,
    )


def index_realtime_rank_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    category: Any,
    sort_param: Callable[[Any], int],
    bool_param: Callable[..., bool],
    int_param: Callable[..., int],
    result_func: Callable[..., RealtimeRankRowsResult],
    default_count: int,
    max_count: int,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankRowsResult:
    sort_type = sort_param(params.get("sort", "change_pct"))
    start = int_param(params, "start", 0, minimum=0, maximum=max_start)
    count = int_param(params, "count", default_count, minimum=1, maximum=max_count)
    ascending = bool_param(params.get("ascending", False))
    return result_func(
        client,
        category=category,
        sort_type=sort_type,
        start=start,
        count=count,
        ascending=ascending,
        max_start=max_start,
        category_quotes=category_quotes,
        get_value=get_value,
        normalize_quote=normalize_quote,
    )


def etf_realtime_rank_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    category: Any,
    category_meta: str,
    category_name: str,
    sort_param: Callable[[Any], int],
    bool_param: Callable[..., bool],
    int_param: Callable[..., int],
    result_func: Callable[..., RealtimeRankRowsResult],
    default_count: int,
    max_count: int,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankRowsResult:
    sort_type = sort_param(params.get("sort", "change_pct"))
    start = int_param(params, "start", 0, minimum=0, maximum=max_start)
    count = int_param(params, "count", default_count, minimum=1, maximum=max_count)
    ascending = bool_param(params.get("ascending", False))
    return result_func(
        client,
        category=category,
        category_meta=category_meta,
        category_name=category_name,
        sort_type=sort_type,
        start=start,
        count=count,
        ascending=ascending,
        max_start=max_start,
        category_quotes=category_quotes,
        get_value=get_value,
        normalize_quote=normalize_quote,
    )


def stock_realtime_rank_result(
    client: Any,
    *,
    category: Any,
    sort_type: int,
    start: int,
    page_size: int,
    full_rank: bool,
    ascending: bool,
    filter_raw: int,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankRowsResult:
    result = request_realtime_rank_pages(
        client,
        category=category,
        sort_type=sort_type,
        start=start,
        page_size=page_size,
        full_rank=full_rank,
        ascending=ascending,
        filter_raw=filter_raw,
        max_start=max_start,
        category_quotes=category_quotes,
        get_value=get_value,
        normalize_quote=normalize_quote,
    )
    return RealtimeRankRowsResult(
        rows=result.rows,
        meta={
            "tdx_protocol": "0x054b",
            "tdx_category": category,
            "tdx_sort_type": sort_type,
            "tdx_start": start,
            "tdx_requested_count": page_size,
            "tdx_returned_count": len(result.rows),
            "tdx_page_count": result.page_count,
            "tdx_full_rank": full_rank,
            "tdx_sort_reverse": result.sort_reverse,
            "tdx_filter_raw": filter_raw,
        },
    )


def index_realtime_rank_result(
    client: Any,
    *,
    category: Any,
    sort_type: int,
    start: int,
    count: int,
    ascending: bool,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankRowsResult:
    result = request_realtime_rank_pages(
        client,
        category=category,
        sort_type=sort_type,
        start=start,
        page_size=count,
        full_rank=False,
        ascending=ascending,
        filter_raw=0,
        max_start=max_start,
        category_quotes=category_quotes,
        get_value=get_value,
        normalize_quote=normalize_quote,
    )
    return RealtimeRankRowsResult(
        rows=result.rows,
        meta={
            "tdx_protocol": "0x054b",
            "tdx_category": category,
            "tdx_sort_type": sort_type,
            "tdx_start": start,
            "tdx_requested_count": count,
            "tdx_returned_count": len(result.rows),
            "tdx_sort_reverse": result.sort_reverse,
        },
    )


def etf_realtime_rank_result(
    client: Any,
    *,
    category: Any,
    category_meta: str,
    category_name: str,
    sort_type: int,
    start: int,
    count: int,
    ascending: bool,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankRowsResult:
    result = request_realtime_rank_pages(
        client,
        category=category,
        sort_type=sort_type,
        start=start,
        page_size=count,
        full_rank=False,
        ascending=ascending,
        filter_raw=0,
        max_start=max_start,
        category_quotes=category_quotes,
        get_value=get_value,
        normalize_quote=normalize_quote,
    )
    return RealtimeRankRowsResult(
        rows=result.rows,
        meta={
            "tdx_protocol": "0x054b",
            "tdx_category": category_meta,
            "tdx_category_name": category_name,
            "tdx_sort_type": sort_type,
            "tdx_start": start,
            "tdx_requested_count": count,
            "tdx_returned_count": len(result.rows),
            "tdx_sort_reverse": result.sort_reverse,
        },
    )


def request_realtime_rank_pages(
    client: Any,
    *,
    category: Any,
    sort_type: int,
    start: int,
    page_size: int,
    full_rank: bool,
    ascending: bool,
    filter_raw: int,
    max_start: int,
    category_quotes: Callable[..., Any],
    get_value: Callable[[Any, str, Any], Any],
    normalize_quote: Callable[[Any], dict[str, Any]],
) -> RealtimeRankResult:
    rows: list[dict[str, Any]] = []
    pages = []
    current_start = start
    while True:
        page = category_quotes(
            client,
            category=category,
            sort_type=sort_type,
            start=current_start,
            count=page_size,
            ascending=ascending,
            filter_raw=filter_raw,
        )
        pages.append(page)
        quotes = list(get_value(page, "records", ()) or ())
        for index, quote in enumerate(quotes, start=current_start + 1):
            row = {"rank": index}
            row.update(normalize_quote(quote))
            rows.append(row)
        if not full_rank or len(quotes) < page_size:
            break
        current_start += len(quotes)
        if current_start > max_start:
            break

    last_page = pages[-1] if pages else None
    return RealtimeRankResult(
        rows=rows,
        page_count=len(pages),
        sort_reverse=get_value(last_page, "sort_reverse", None),
    )
