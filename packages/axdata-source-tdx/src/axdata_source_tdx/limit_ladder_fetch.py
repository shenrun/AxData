"""Source fetch helpers for TDX limit-ladder style interfaces."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class LimitLadderSourceRowsResult:
    stats: Any
    stats_refreshed: bool
    rank_rows: list[dict[str, Any]]
    page_count: int
    rows: list[dict[str, Any]]
    stats_ms: int
    rank_ms: int
    names_ms: int
    normalize_ms: int


@dataclass(frozen=True)
class LimitLadderTopicLookupResult:
    topic_rows: dict[str, list[dict[str, Any]]]
    lookup_performed: bool
    worker_count: Any
    lookup_meta: dict[str, Any]
    lookup_ms: int


@dataclass(frozen=True)
class LimitLadderRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


@dataclass(frozen=True)
class ThemeStrengthRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def limit_ladder_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    limit_count_param: Callable[[Any], int | None],
    requested_boards: Callable[[Any], set[str] | None],
    bool_param: Callable[..., bool],
    topic_type_param: Callable[[Any], str],
    prepare_source_rows: Callable[..., LimitLadderSourceRowsResult],
    lookup_topics: Callable[..., LimitLadderTopicLookupResult],
    request_rank_rows: Callable[..., tuple[list[dict[str, Any]], int]],
    security_names: Callable[[Any, Sequence[str]], Mapping[str, str]],
    needs_name_lookup: Callable[..., bool],
    normalize_row: Callable[..., dict[str, Any] | None],
    request_topics: Callable[..., dict[str, list[dict[str, Any]]]],
    topic_worker_count: Callable[[int], int],
    topic_refill_workers: Callable[[], int],
    topic_refill_rounds: Callable[[], int],
    set_initial_lookup_meta: Callable[[dict[str, Any]], None],
    get_lookup_meta: Callable[[], Mapping[str, Any]],
    attach_themes: Callable[[list[dict[str, Any]], Mapping[str, Sequence[Mapping[str, Any]]]], None],
    public_row: Callable[[Mapping[str, Any]], dict[str, Any]],
    topic_missing_stock_count: Callable[[Mapping[str, Sequence[Mapping[str, Any]]], Sequence[Mapping[str, Any]]], int],
    meta_func: Callable[..., dict[str, Any]],
    elapsed_ms: Callable[[float], int],
    emit_progress: Callable[..., None],
    progress_callback: Callable[..., None] | None = None,
) -> LimitLadderRequestResult:
    count = limit_count_param(params.get("count", "all"))
    boards = requested_boards(params.get("scope", "main"))
    include_touched = bool_param(params.get("include_touched", False), name="include_touched")
    topic_type = topic_type_param(params.get("topic_type", "theme"))
    timing_started = monotonic()
    source_rows = prepare_source_rows(
        client,
        stats_params=params,
        boards=boards,
        include_touched=include_touched,
        request_rank_rows=request_rank_rows,
        security_names=security_names,
        needs_name_lookup=needs_name_lookup,
        normalize_row=normalize_row,
        elapsed_ms=elapsed_ms,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
    )
    rows = source_rows.rows

    topic_lookup = lookup_topics(
        rows,
        topic_type=topic_type,
        request_topics=request_topics,
        topic_worker_count=topic_worker_count,
        topic_refill_workers=topic_refill_workers,
        topic_refill_rounds=topic_refill_rounds,
        set_initial_lookup_meta=set_initial_lookup_meta,
        get_lookup_meta=get_lookup_meta,
        elapsed_ms=elapsed_ms,
        emit_progress=emit_progress,
        progress_callback=progress_callback,
        progress_start=56,
        progress_span=10,
    )
    topic_rows = topic_lookup.topic_rows
    theme_attach_started = monotonic()
    attach_themes(rows, topic_rows)
    theme_attach_ms = elapsed_ms(theme_attach_started) if rows else 0

    sort_started = monotonic()
    rows.sort(
        key=lambda row: (
            -int(row.get("ladder_level") or 0),
            0 if row.get("limit_status") == "sealed" else 1,
            -float(row.get("same_theme_limit_up_count") or 0),
            -float(row.get("same_theme_highest_board") or 0),
            -float(row.get("same_theme_lianban_count") or 0),
            str(row.get("primary_theme") or "\uffff"),
            -float(row.get("seal_amount") or 0),
            int(row.get("rank") or 0),
        )
    )
    returned_rows = rows if count is None else rows[:count]
    public_rows = [public_row(row) for row in returned_rows]
    sort_ms = elapsed_ms(sort_started)
    total_ms = elapsed_ms(timing_started)
    return LimitLadderRequestResult(
        rows=public_rows,
        meta=meta_func(
            source_rows,
            public_rows,
            count=count,
            boards=boards,
            include_touched=include_touched,
            topic_type=topic_type,
            theme_lookup_performed=topic_lookup.lookup_performed,
            topic_worker_count=topic_lookup.worker_count,
            topic_lookup_meta=topic_lookup.lookup_meta,
            topic_missing_stock_count=topic_missing_stock_count(topic_rows, public_rows),
            theme_lookup_ms=topic_lookup.lookup_ms,
            theme_attach_ms=theme_attach_ms,
            sort_ms=sort_ms,
            total_ms=total_ms,
        ),
    )


def theme_strength_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    limit_count_param: Callable[[Any], int | None],
    requested_boards: Callable[[Any], set[str] | None],
    topic_type_param: Callable[[Any], str],
    prepare_source_rows: Callable[..., LimitLadderSourceRowsResult],
    lookup_topics: Callable[..., LimitLadderTopicLookupResult],
    request_rank_rows: Callable[..., tuple[list[dict[str, Any]], int]],
    security_names: Callable[[Any, Sequence[str]], Mapping[str, str]],
    needs_name_lookup: Callable[..., bool],
    normalize_row: Callable[..., dict[str, Any] | None],
    request_topics: Callable[..., dict[str, list[dict[str, Any]]]],
    topic_worker_count: Callable[[int], int],
    topic_refill_workers: Callable[[], int],
    topic_refill_rounds: Callable[[], int],
    set_initial_lookup_meta: Callable[[dict[str, Any]], None],
    get_lookup_meta: Callable[[], Mapping[str, Any]],
    theme_rank_rows: Callable[..., list[dict[str, Any]]],
    topic_missing_stock_count: Callable[[Mapping[str, Sequence[Mapping[str, Any]]], Sequence[Mapping[str, Any]]], int],
    meta_func: Callable[..., dict[str, Any]],
    elapsed_ms: Callable[[float], int],
) -> ThemeStrengthRequestResult:
    count = limit_count_param(params.get("count", "all"))
    boards = requested_boards(params.get("scope", "main"))
    topic_type = topic_type_param(params.get("topic_type", "theme"))
    timing_started = monotonic()
    source_rows = prepare_source_rows(
        client,
        stats_params=params,
        boards=boards,
        include_touched=False,
        request_rank_rows=request_rank_rows,
        security_names=security_names,
        needs_name_lookup=needs_name_lookup,
        normalize_row=normalize_row,
        elapsed_ms=elapsed_ms,
    )
    ladder_rows = source_rows.rows

    topic_lookup = lookup_topics(
        ladder_rows,
        topic_type=topic_type,
        request_topics=request_topics,
        topic_worker_count=topic_worker_count,
        topic_refill_workers=topic_refill_workers,
        topic_refill_rounds=topic_refill_rounds,
        set_initial_lookup_meta=set_initial_lookup_meta,
        get_lookup_meta=get_lookup_meta,
        elapsed_ms=elapsed_ms,
    )
    topic_rows = topic_lookup.topic_rows

    rank_build_started = monotonic()
    rank_rows_public = theme_rank_rows(
        ladder_rows,
        topic_rows,
        topic_type=topic_type,
    )
    returned_rows = rank_rows_public if count is None else rank_rows_public[:count]
    rank_build_ms = elapsed_ms(rank_build_started)
    total_ms = elapsed_ms(timing_started)
    return ThemeStrengthRequestResult(
        rows=returned_rows,
        meta=meta_func(
            source_rows,
            ladder_rows,
            returned_rows,
            count=count,
            boards=boards,
            topic_type=topic_type,
            theme_lookup_performed=topic_lookup.lookup_performed,
            topic_worker_count=topic_lookup.worker_count,
            topic_lookup_meta=topic_lookup.lookup_meta,
            topic_missing_stock_count=topic_missing_stock_count(topic_rows, ladder_rows),
            theme_lookup_ms=topic_lookup.lookup_ms,
            rank_build_ms=rank_build_ms,
            total_ms=total_ms,
        ),
    )


def limit_ladder_meta(
    source_rows: LimitLadderSourceRowsResult,
    returned_rows: Sequence[Mapping[str, Any]],
    *,
    count: int | None,
    boards: set[str] | None,
    include_touched: bool,
    topic_type: str,
    theme_lookup_performed: bool,
    topic_worker_count: Any,
    topic_lookup_meta: Mapping[str, Any],
    topic_missing_stock_count: int,
    theme_lookup_ms: int,
    theme_attach_ms: int,
    sort_ms: int,
    total_ms: int,
) -> dict[str, Any]:
    stats = source_rows.stats
    return {
        "tdx_protocol": "0x054b+tdxstat" + ("+7615" if theme_lookup_performed else ""),
        "tdx_f10_topic_workers": topic_worker_count,
        **dict(topic_lookup_meta),
        "tdx_stats_source_path": stats.source_path,
        "tdx_stats_date": stats.stats_date,
        "tdx_stats_cached": not source_rows.stats_refreshed,
        "tdx_stats_refreshed": source_rows.stats_refreshed,
        "tdx_rank_page_count": source_rows.page_count,
        "tdx_rank_scanned_count": len(source_rows.rank_rows),
        "tdx_returned_count": len(returned_rows),
        "tdx_topic_missing_stock_count": topic_missing_stock_count,
        "tdx_count": "all" if count is None else count,
        "tdx_scope": tuple(sorted(boards)) if boards else "all",
        "tdx_include_touched": include_touched,
        "tdx_topic_type": topic_type if theme_lookup_performed else None,
        "tdx_limit_ladder_timing_ms": {
            "stats": source_rows.stats_ms,
            "rank_scan": source_rows.rank_ms,
            "name_lookup": source_rows.names_ms,
            "normalize_filter": source_rows.normalize_ms,
            "theme_lookup": theme_lookup_ms,
            "theme_attach": theme_attach_ms,
            "sort_and_slice": sort_ms,
            "total": total_ms,
        },
    }


def theme_strength_meta(
    source_rows: LimitLadderSourceRowsResult,
    ladder_rows: Sequence[Mapping[str, Any]],
    returned_rows: Sequence[Mapping[str, Any]],
    *,
    count: int | None,
    boards: set[str] | None,
    topic_type: str,
    theme_lookup_performed: bool,
    topic_worker_count: Any,
    topic_lookup_meta: Mapping[str, Any],
    topic_missing_stock_count: int,
    theme_lookup_ms: int,
    rank_build_ms: int,
    total_ms: int,
) -> dict[str, Any]:
    stats = source_rows.stats
    return {
        "tdx_protocol": "0x054b+tdxstat" + ("+7615" if theme_lookup_performed else ""),
        "tdx_f10_topic_workers": topic_worker_count,
        **dict(topic_lookup_meta),
        "tdx_stats_source_path": stats.source_path,
        "tdx_stats_date": stats.stats_date,
        "tdx_stats_cached": not source_rows.stats_refreshed,
        "tdx_stats_refreshed": source_rows.stats_refreshed,
        "tdx_rank_page_count": source_rows.page_count,
        "tdx_rank_scanned_count": len(source_rows.rank_rows),
        "tdx_ladder_count": len(ladder_rows),
        "tdx_returned_count": len(returned_rows),
        "tdx_topic_missing_stock_count": topic_missing_stock_count,
        "tdx_count": "all" if count is None else count,
        "tdx_scope": tuple(sorted(boards)) if boards else "all",
        "tdx_topic_type": topic_type if theme_lookup_performed else None,
        "tdx_theme_strength_timing_ms": {
            "stats": source_rows.stats_ms,
            "rank_scan": source_rows.rank_ms,
            "name_lookup": source_rows.names_ms,
            "normalize_filter": source_rows.normalize_ms,
            "theme_lookup": theme_lookup_ms,
            "rank_build": rank_build_ms,
            "total": total_ms,
        },
    }


def prepare_limit_ladder_source_rows(
    client: Any,
    *,
    stats_params: Mapping[str, Any] | None = None,
    boards: set[str] | None,
    include_touched: bool,
    request_rank_rows: Callable[..., tuple[list[dict[str, Any]], int]],
    security_names: Callable[[Any, Sequence[str]], Mapping[str, str]],
    needs_name_lookup: Callable[..., bool],
    normalize_row: Callable[..., dict[str, Any] | None],
    elapsed_ms: Callable[[float], int],
    emit_progress: Callable[..., None] | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> LimitLadderSourceRowsResult:
    if emit_progress is not None:
        emit_progress(
            progress_callback,
            22,
            "读取盘前统计",
            progress_current=0,
            progress_total=1,
            progress_unit="步",
            progress_label="源端阶段",
        )
    stats_started = monotonic()
    stats, stats_refreshed = _ensure_tdx_stats_resource_for_params(client, stats_params)
    stats_ms = elapsed_ms(stats_started)

    if emit_progress is not None:
        emit_progress(
            progress_callback,
            28,
            "扫描涨停排行",
            progress_current=1,
            progress_total=4,
            progress_unit="步",
            progress_label="源端阶段",
        )
    rank_started = monotonic()
    rank_rows, page_count = request_rank_rows(
        client,
        include_touched=include_touched,
    )
    rank_ms = elapsed_ms(rank_started)
    candidate_codes = limit_ladder_candidate_tdx_codes(
        rank_rows,
        boards=boards,
        include_touched=include_touched,
        needs_name_lookup=needs_name_lookup,
    )

    if emit_progress is not None:
        emit_progress(
            progress_callback,
            44,
            "补全股票名称",
            progress_current=2,
            progress_total=4,
            progress_unit="步",
            progress_label="源端阶段",
        )
    names_started = monotonic()
    names_by_tdx_code = security_names(client, candidate_codes)
    names_ms = elapsed_ms(names_started)

    if emit_progress is not None:
        emit_progress(
            progress_callback,
            50,
            "整理候选股票",
            progress_current=3,
            progress_total=4,
            progress_unit="步",
            progress_label="源端阶段",
        )
    normalize_started = monotonic()
    rows = limit_ladder_rows_from_rank_rows(
        rank_rows,
        stats=stats,
        names_by_tdx_code=names_by_tdx_code,
        boards=boards,
        include_touched=include_touched,
        normalize_row=normalize_row,
    )
    normalize_ms = elapsed_ms(normalize_started)

    return LimitLadderSourceRowsResult(
        stats=stats,
        stats_refreshed=stats_refreshed,
        rank_rows=rank_rows,
        page_count=page_count,
        rows=rows,
        stats_ms=stats_ms,
        rank_ms=rank_ms,
        names_ms=names_ms,
        normalize_ms=normalize_ms,
    )


def lookup_limit_ladder_topics(
    rows: Sequence[Mapping[str, Any]],
    *,
    topic_type: str,
    request_topics: Callable[..., dict[str, list[dict[str, Any]]]],
    topic_worker_count: Callable[[int], int],
    topic_refill_workers: Callable[[], int],
    topic_refill_rounds: Callable[[], int],
    set_initial_lookup_meta: Callable[[dict[str, Any]], None],
    get_lookup_meta: Callable[[], Mapping[str, Any]],
    elapsed_ms: Callable[[float], int],
    emit_progress: Callable[..., None] | None = None,
    progress_callback: Callable[..., None] | None = None,
    progress_start: int | None = None,
    progress_span: int | None = None,
) -> LimitLadderTopicLookupResult:
    if not rows:
        return LimitLadderTopicLookupResult(
            topic_rows={},
            lookup_performed=False,
            worker_count=None,
            lookup_meta={},
            lookup_ms=0,
        )

    if emit_progress is not None:
        emit_progress(
            progress_callback,
            56,
            "查询题材",
            progress_current=0,
            progress_total=len(rows),
            progress_unit="只",
            progress_label="题材",
        )

    lookup_started = monotonic()
    worker_count = topic_worker_count(len(rows))
    set_initial_lookup_meta(
        {
            "tdx_f10_topic_workers": worker_count,
            "tdx_f10_topic_refill_workers": topic_refill_workers(),
            "tdx_f10_topic_refill_rounds": topic_refill_rounds(),
            "tdx_f10_topic_refill_requested_count": 0,
        }
    )
    request_kwargs: dict[str, Any] = {"topic_type": topic_type}
    if progress_start is not None or progress_span is not None:
        request_kwargs["progress_start"] = progress_start
        request_kwargs["progress_span"] = progress_span
    topic_rows = request_topics(
        [str(row.get("instrument_id") or "") for row in rows],
        **request_kwargs,
    )
    lookup_meta = dict(get_lookup_meta() or {})
    worker_count = lookup_meta.get("tdx_f10_topic_workers", worker_count)
    lookup_ms = elapsed_ms(lookup_started)

    if emit_progress is not None:
        emit_progress(
            progress_callback,
            67,
            "整理题材",
            progress_current=len(rows),
            progress_total=len(rows),
            progress_unit="只",
            progress_label="题材",
        )

    return LimitLadderTopicLookupResult(
        topic_rows=topic_rows,
        lookup_performed=True,
        worker_count=worker_count,
        lookup_meta=lookup_meta,
        lookup_ms=lookup_ms,
    )


def limit_ladder_candidate_tdx_codes(
    rank_rows: Sequence[Mapping[str, Any]],
    *,
    boards: set[str] | None,
    include_touched: bool,
    needs_name_lookup: Callable[..., bool],
) -> list[str]:
    return [
        str(row.get("tdx_code") or "")
        for row in rank_rows
        if needs_name_lookup(row, boards=boards, include_touched=include_touched)
    ]


def limit_ladder_rows_from_rank_rows(
    rank_rows: Sequence[Mapping[str, Any]],
    *,
    stats: Any,
    names_by_tdx_code: Mapping[str, str],
    boards: set[str] | None,
    include_touched: bool,
    normalize_row: Callable[..., dict[str, Any] | None],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in rank_rows:
        item = normalize_row(
            row,
            stats=stats,
            name=names_by_tdx_code.get(str(row.get("tdx_code") or "")),
            boards=boards,
            include_touched=include_touched,
        )
        if item is not None:
            rows.append(item)
    return rows


def security_names_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    tdx_codes_all: Callable[[Any, str], Sequence[Any]],
    get_value: Callable[[Any, str, Any], Any],
) -> dict[str, str]:
    names: dict[str, str] = {}
    requested = {str(tdx_code).lower() for tdx_code in tdx_codes if tdx_code}
    grouped: dict[str, set[str]] = {}
    for tdx_code in requested:
        grouped.setdefault(tdx_code[:2], set()).add(tdx_code[2:])
    for market, symbols in grouped.items():
        try:
            items = tdx_codes_all(client, market)
        except Exception:
            continue
        for item in items:
            full_code = str(get_value(item, "full_code", "") or "").lower()
            symbol = str(get_value(item, "code", "") or "")
            if full_code in tdx_codes or symbol in symbols:
                resolved = full_code if full_code else f"{market}{symbol}"
                name = str(get_value(item, "name", "") or "").strip()
                if name:
                    names[resolved] = name
    return names


def request_limit_ladder_rank_rows(
    client: Any,
    *,
    include_touched: bool,
    category_quotes: Callable[..., Any],
    normalize_snapshot_row: Callable[[Any], dict[str, Any]],
    rank_page_below_threshold: Callable[[Sequence[dict[str, Any]], float], bool],
    get_value: Callable[[Any, str, Any], Any],
    category: int,
    sort_type: int,
    page_size: int,
    max_start: int,
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    current_start = 0
    page_count = 0
    stop_threshold = None if include_touched else 8.5
    while True:
        page = category_quotes(
            client,
            category=category,
            sort_type=sort_type,
            start=current_start,
            count=page_size,
            ascending=False,
            filter_raw=0,
        )
        page_count += 1
        quotes = list(get_value(page, "records", ()) or ())
        for index, quote in enumerate(quotes, start=current_start + 1):
            row = {"rank": index}
            row.update(normalize_snapshot_row(quote))
            rows.append(row)
        if stop_threshold is not None and rank_page_below_threshold(rows[-len(quotes) :], stop_threshold):
            break
        if len(quotes) < page_size:
            break
        current_start += len(quotes)
        if current_start > max_start:
            break
    return rows, page_count


def _ensure_tdx_stats_resource_for_params(*args: Any, **kwargs: Any) -> tuple[Any, bool]:
    from .stats_resource import ensure_tdx_stats_resource_for_params

    return ensure_tdx_stats_resource_for_params(*args, **kwargs)
