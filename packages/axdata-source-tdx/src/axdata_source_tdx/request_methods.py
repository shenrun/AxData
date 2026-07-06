"""Provider-owned request method glue for the ordinary TDX adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from axdata_core.source_errors import SourceUnavailableError


def _loaded_core_request_attr(name: str) -> Any | None:
    import sys

    request_module = sys.modules.get("axdata_core.adapters.tdx.request")
    if request_module is None:
        return None
    return getattr(request_module, name, None)


def request_stock_codes(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
    *,
    progress_start: int = 20,
    progress_span: int = 40,
) -> list[dict[str, Any]]:
    from .code_fetch import (
        request_stock_codes as scan_stock_codes,
        stock_codes_request_result,
    )
    from .execution_utils import client_pool_size, emit_source_progress
    from .request_filters import (
        exchanges_for_boards,
        requested_boards,
        requested_codes,
        requested_exchanges,
        requested_names,
    )
    from .request_params import int_param

    result = stock_codes_request_result(
        client,
        params,
        requested_boards=requested_boards,
        requested_codes_func=requested_codes,
        requested_names_func=requested_names,
        requested_exchanges=requested_exchanges,
        exchanges_for_boards=exchanges_for_boards,
        int_param=int_param,
        scan_func=scan_stock_codes,
        client_pool_size=client_pool_size,
        request_exchange=adapter._request_stock_codes_exchange,
        emit_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )
    adapter.last_meta.update(result.meta)
    return result.rows


def request_stock_codes_exchange(
    client: Any,
    exchange: str,
    *,
    boards: set[str] | None,
    requested_codes: set[str] | None,
    requested_names: set[str] | None,
    start: int,
) -> tuple[list[dict[str, Any]], int]:
    from .code_fetch import request_stock_codes_exchange as request_exchange
    from .codes import exchange_to_market
    from .normalize_utils import as_list
    from .request_filters import board_matches, code_matches, name_matches
    from .request_limits import TDX_CODE_PAGE_SIZE
    from .security_codes import normalize_security
    from .snapshot_normalize import tdx_codes

    return request_exchange(
        client,
        exchange,
        start=start,
        page_size=TDX_CODE_PAGE_SIZE,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        board_matches=board_matches,
        code_matches=code_matches,
        name_matches=name_matches,
        boards=boards,
        requested_codes=requested_codes,
        requested_names=requested_names,
    )


def request_index_codes(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .code_fetch import index_codes_request_result, index_codes_result
    from .codes import exchange_to_market
    from .normalize_utils import as_list
    from .request_filters import (
        code_matches,
        name_matches,
        requested_codes,
        requested_exchanges,
        requested_names,
    )
    from .request_limits import TDX_CODE_PAGE_SIZE
    from .request_params import bool_param, int_param
    from .security_codes import index_type_from_tdx_code, normalize_index_code_row, normalize_security
    from .snapshot_normalize import tdx_codes

    result = index_codes_request_result(
        client,
        params,
        requested_codes_func=requested_codes,
        requested_names_func=requested_names,
        requested_exchanges_func=requested_exchanges,
        bool_param=bool_param,
        int_param=int_param,
        result_func=index_codes_result,
        page_size=TDX_CODE_PAGE_SIZE,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        index_type_from_tdx_code=index_type_from_tdx_code,
        normalize_index_code_row=normalize_index_code_row,
        code_matches=code_matches,
        name_matches=name_matches,
    )
    return adapter._finish_request_result(client, result)


def request_etf_codes(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .code_fetch import etf_codes_request_result, etf_codes_result
    from .codes import exchange_to_market
    from .normalize_utils import as_list
    from .request_filters import (
        code_matches,
        name_matches,
        requested_codes,
        requested_exchanges,
        requested_names,
    )
    from .request_limits import TDX_CODE_PAGE_SIZE
    from .request_params import int_param
    from .security_codes import etf_type_from_tdx_code, normalize_security
    from .snapshot_normalize import tdx_codes

    result = etf_codes_request_result(
        client,
        params,
        requested_codes_func=requested_codes,
        requested_names_func=requested_names,
        requested_exchanges_func=requested_exchanges,
        int_param=int_param,
        result_func=etf_codes_result,
        page_size=TDX_CODE_PAGE_SIZE,
        exchange_to_market=exchange_to_market,
        tdx_codes=tdx_codes,
        as_list=as_list,
        normalize_security=normalize_security,
        etf_type_from_tdx_code=etf_type_from_tdx_code,
        code_matches=code_matches,
        name_matches=name_matches,
    )
    return adapter._finish_request_result(client, result)


def request_stock_st_list(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .execution_utils import emit_source_progress
    from .price_limits import st_type_from_name
    from .quote_identity import normalize_st_row
    from .status_fetch import stock_st_list_request_result

    result = stock_st_list_request_result(
        params,
        request_stock_rows=lambda stock_params, start, span: adapter._request_stock_codes(
            client,
            stock_params,
            progress_start=start,
            progress_span=span,
        ),
        st_type_from_name=st_type_from_name,
        normalize_st_row=normalize_st_row,
        emit_source_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def request_stock_suspensions(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
    *,
    use_parallel_quote_clients: bool = False,
) -> list[dict[str, Any]]:
    from .execution_utils import emit_source_progress
    from .normalize_utils import get_value
    from .quote_identity import normalize_suspension_row
    from .request_limits import DEFAULT_QUOTE_BATCH_SIZE, TDX_SUSPENSION_STATUS_BIT
    from .status_fetch import stock_suspension_request_result

    result = stock_suspension_request_result(
        params,
        request_stock_rows=lambda stock_params, start, span: adapter._request_stock_codes(
            client,
            stock_params,
            progress_start=start,
            progress_span=span,
        ),
        request_quotes=lambda rows, **kwargs: _request_legacy_quotes_parallel(
            client,
            rows,
            use_parallel_quote_clients=use_parallel_quote_clients,
            hosts=adapter._configured_hosts(),
            **kwargs,
        ),
        status_bit=TDX_SUSPENSION_STATUS_BIT,
        quote_batch_size=DEFAULT_QUOTE_BATCH_SIZE,
        get_value=get_value,
        normalize_suspension_row=normalize_suspension_row,
        emit_source_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def request_stock_order_book(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .derived_rows import normalize_order_book_rows
    from .normalize_utils import as_list
    from .quote_fetch import order_book_request_result, order_book_rows, quote_rows_meta
    from .quote_identity import quote_security_from_tdx_code
    from .request_filters import requested_kline_codes
    from .wire_requests import tdx_legacy_quotes

    result = order_book_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=order_book_rows,
        meta_func=quote_rows_meta,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_legacy_quotes=tdx_legacy_quotes,
        as_list=as_list,
        normalize_order_book_rows=normalize_order_book_rows,
    )
    return adapter._finish_request_result(client, result)


def request_stock_realtime_snapshot(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .normalize_utils import as_list
    from .quote_fetch import explicit_quote_request_result, explicit_quote_rows, quote_rows_meta
    from .quote_identity import quote_security_from_tdx_code
    from .request_filters import requested_kline_codes
    from .snapshot_normalize import normalize_realtime_snapshot_row
    from .wire_requests import tdx_explicit_quotes

    result = explicit_quote_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=explicit_quote_rows,
        meta_func=quote_rows_meta,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_explicit_quotes=tdx_explicit_quotes,
        as_list=as_list,
        normalize_row=lambda quote: normalize_realtime_snapshot_row(quote, client=client),
    )
    return adapter._finish_request_result(client, result)


def request_index_realtime_snapshot(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .normalize_utils import as_list
    from .quote_fetch import explicit_quote_request_result, explicit_quote_rows, quote_rows_meta
    from .quote_identity import quote_security_from_tdx_code
    from .request_filters import requested_kline_codes
    from .snapshot_normalize import normalize_index_snapshot_row
    from .wire_requests import tdx_explicit_quotes

    result = explicit_quote_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=explicit_quote_rows,
        meta_func=quote_rows_meta,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_explicit_quotes=tdx_explicit_quotes,
        as_list=as_list,
        normalize_row=lambda quote: normalize_index_snapshot_row(quote, client=client),
    )
    return adapter._finish_request_result(client, result)


def request_stock_kline(
    adapter: Any,
    client: Any,
    interface_name: str,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .kline_helpers import sequential_kline_rows_and_meta, stock_kline_request_result
    from .normalize_utils import get_value
    from .request_filters import requested_kline_codes
    from .request_params import (
        adjust_param,
        anchor_date_param,
        kline_page_size,
        kline_period,
        validate_kline_anchor_date,
    )
    from .time_series_normalize import normalize_stock_kline_row

    result = stock_kline_request_result(
        client,
        interface_name,
        params,
        requested_codes=requested_kline_codes,
        kline_period=kline_period,
        kline_page_size=kline_page_size,
        adjust_param=adjust_param,
        anchor_date_param=anchor_date_param,
        validate_anchor_date=validate_kline_anchor_date,
        rows_meta_func=sequential_kline_rows_and_meta,
        normalize_row=normalize_stock_kline_row,
        request_code_history=_request_kline_code_history,
        get_value=get_value,
    )
    return adapter._finish_request_result(client, result)


def request_stock_kline_parallel(
    adapter: Any,
    interface_name: str,
    params: Mapping[str, Any],
    tdx_codes: Sequence[str],
) -> list[dict[str, Any]]:
    from .kline_helpers import kline_parallel_rows_and_meta, stock_kline_parallel_request_result
    from .normalize_utils import get_value
    from .options import (
        has_tdx_connection_options,
        tdx_request_option_connections_per_server,
        tdx_request_option_hosts,
    )
    from .request_host_config import configured_tdx_hosts_from_options, effective_host_strings
    from .request_limits import TDX_KLINE_HOST_COUNT, TDX_KLINE_POOL_SIZE
    from .request_params import (
        adjust_param,
        anchor_date_param,
        kline_page_size,
        kline_period,
        validate_kline_anchor_date,
    )
    from .series_history import kline_parallel_options
    from .time_series_normalize import normalize_stock_kline_row

    result = stock_kline_parallel_request_result(
        interface_name,
        params,
        tdx_codes,
        options=adapter._options,
        kline_period=kline_period,
        kline_page_size=kline_page_size,
        adjust_param=adjust_param,
        anchor_date_param=anchor_date_param,
        validate_anchor_date=validate_kline_anchor_date,
        parallel_options_func=kline_parallel_options,
        has_connection_options=has_tdx_connection_options,
        option_hosts=tdx_request_option_hosts,
        option_connections_per_server=tdx_request_option_connections_per_server,
        configured_hosts=adapter._configured_hosts,
        configured_hosts_from_options=lambda options: configured_tdx_hosts_from_options(
            options,
            effective_host_strings_func=effective_host_strings,
        ),
        env_int=_tdx_env_int,
        default_host_count=TDX_KLINE_HOST_COUNT,
        default_pool_size=TDX_KLINE_POOL_SIZE,
        request_parallel=_request_kline_codes_parallel,
        rows_meta_func=kline_parallel_rows_and_meta,
        normalize_row=normalize_stock_kline_row,
        get_value=get_value,
        unavailable_error=SourceUnavailableError,
    )
    adapter.last_meta = {**result.meta}
    return result.rows


def request_index_kline(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .kline_helpers import index_like_kline_request_result, sequential_kline_rows_and_meta
    from .normalize_utils import get_value
    from .request_filters import requested_kline_codes
    from .request_params import TDX_KLINE_MAX_COUNT, index_kline_period, int_param
    from .time_series_normalize import normalize_index_kline_row

    result = index_like_kline_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        index_kline_period=index_kline_period,
        int_param=int_param,
        max_count=TDX_KLINE_MAX_COUNT,
        rows_meta_func=sequential_kline_rows_and_meta,
        normalize_row=normalize_index_kline_row,
        request_code_history=_request_kline_code_history,
        get_value=get_value,
        request_kind="index",
        meta_kind="index",
    )
    return adapter._finish_request_result(client, result)


def _request_legacy_quotes_parallel(
    client: Any,
    stock_rows: Sequence[Mapping[str, Any]],
    *,
    use_parallel_quote_clients: bool,
    hosts: Sequence[str] | None = None,
    progress_callback: Any | None = None,
) -> list[Any]:
    from .execution_utils import chunked, client_pool_size, emit_batch_progress
    from .quote_identity import quote_security
    from .request_host_config import suspension_scan_hosts
    from .request_limits import DEFAULT_QUOTE_BATCH_SIZE, TDX_SUSPENSION_HOST_COUNT
    from .request_seams import request_legacy_quotes_parallel as request_parallel

    return request_parallel(
        client,
        stock_rows,
        use_parallel_quote_clients=use_parallel_quote_clients,
        quote_security=quote_security,
        chunked=chunked,
        batch_size=DEFAULT_QUOTE_BATCH_SIZE,
        request_batches=_request_legacy_quote_batches,
        request_batches_concurrent=_request_legacy_quote_batches_concurrent,
        request_on_host=_request_legacy_quotes_on_host,
        client_pool_size=client_pool_size,
        suspension_scan_hosts=suspension_scan_hosts,
        suspension_host_count=TDX_SUSPENSION_HOST_COUNT,
        emit_progress=emit_batch_progress,
        hosts=hosts,
        progress_callback=progress_callback,
    )


def _request_legacy_quote_batches_concurrent(
    client: Any,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    worker_count: int,
    progress_callback: Any | None = None,
) -> list[Any]:
    from .execution_utils import emit_batch_progress
    from .normalize_utils import as_list
    from .request_seams import request_legacy_quote_batches_concurrent
    from .wire_requests import tdx_legacy_quotes

    return request_legacy_quote_batches_concurrent(
        client,
        batches,
        worker_count=worker_count,
        tdx_legacy_quotes=tdx_legacy_quotes,
        as_list=as_list,
        emit_progress=emit_batch_progress,
        progress_callback=progress_callback,
    )


def _request_legacy_quotes_on_host(
    host: str,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    pool_size: int | None = None,
    batch_progress: Any | None = None,
) -> list[Any]:
    from .request_limits import TDX_SUSPENSION_POOL_SIZE
    from .request_seams import request_legacy_quotes_on_host
    from .wire_requests import tdx_legacy_quotes

    effective_pool_size = (
        _loaded_core_request_attr("TDX_SUSPENSION_POOL_SIZE")
        if pool_size is None
        else pool_size
    )
    return request_legacy_quotes_on_host(
        host,
        batches,
        create_client=create_tdx_client,
        tdx_legacy_quotes=tdx_legacy_quotes,
        pool_size=TDX_SUSPENSION_POOL_SIZE if effective_pool_size is None else effective_pool_size,
        batch_progress=batch_progress,
    )


def _request_legacy_quote_batches(
    client: Any,
    batches: Sequence[Sequence[tuple[str, str]]],
    *,
    progress_callback: Any | None = None,
) -> list[Any]:
    from .execution_utils import emit_batch_progress
    from .request_seams import request_legacy_quote_batches
    from .wire_requests import tdx_legacy_quotes

    return request_legacy_quote_batches(
        client,
        batches,
        tdx_legacy_quotes=tdx_legacy_quotes,
        emit_progress=emit_batch_progress,
        progress_callback=progress_callback,
    )


def _request_kline_series_history(
    client: Any,
    tdx_code: str,
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str = "stock",
) -> tuple[Any, int]:
    from .normalize_utils import get_value
    from .request_params import TDX_KLINE_MAX_COUNT
    from .request_seams import request_kline_series_history
    from .time_series_normalize import kline_bars
    from .wire_requests import tdx_kline

    return request_kline_series_history(
        client,
        tdx_code,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        kind=kind,
        max_count=TDX_KLINE_MAX_COUNT,
        tdx_kline=tdx_kline,
        kline_bars=kline_bars,
        get_value=get_value,
    )


def _request_kline_code_history(
    client: Any,
    index: int,
    tdx_code: str,
    *,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
    kind: str = "stock",
) -> Any:
    from .request_seams import request_kline_code_history
    from .time_series_normalize import kline_bars, kline_row_sort_key, normalize_kline_row

    return request_kline_code_history(
        client,
        index,
        tdx_code,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        kind=kind,
        request_series_history=_request_kline_series_history,
        normalize_kline_row=normalize_kline_row,
        kline_bars=kline_bars,
        row_sort_key=kline_row_sort_key,
    )


def _request_kline_codes_on_host(
    host: str,
    indexed_codes: Sequence[tuple[int, str]],
    *,
    pool_size: int,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
) -> Any:
    from .execution_utils import tdx_client_meta
    from .request_seams import request_kline_codes_on_host

    return request_kline_codes_on_host(
        host,
        indexed_codes,
        pool_size=pool_size,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        create_client=create_tdx_client,
        request_code_history=_request_kline_code_history,
        client_meta=tdx_client_meta,
    )


def _request_kline_codes_parallel(
    hosts: Sequence[str],
    tdx_codes: Sequence[str],
    *,
    pool_size: int,
    period: str,
    page_size: int,
    adjust: str,
    anchor_date: Any,
) -> Any:
    from .request_seams import request_kline_codes_parallel

    return request_kline_codes_parallel(
        hosts,
        tdx_codes,
        pool_size=pool_size,
        period=period,
        page_size=page_size,
        adjust=adjust,
        anchor_date=anchor_date,
        request_on_host=_request_kline_codes_on_host,
    )


def kline_meta(
    series: Any,
    *,
    page_size: int,
    page_count: int,
    requested_code_count: int,
    concurrency_limit: int,
    concurrency_capacity: int,
) -> dict[str, Any]:
    from .normalize_utils import get_value
    from .request_seams import kline_meta as build_kline_meta

    return build_kline_meta(
        series,
        page_size=page_size,
        page_count=page_count,
        requested_code_count=requested_code_count,
        concurrency_limit=concurrency_limit,
        concurrency_capacity=concurrency_capacity,
        get_value=get_value,
    )


def create_tdx_client(**kwargs: Any) -> Any:
    from .client_factory import create_tdx_client as create_client

    return create_client(**kwargs)


def _tdx_env_int(name: str, default: int, *, minimum: int) -> int:
    from .client_factory import tdx_env_int

    return tdx_env_int(name, default, minimum=minimum)


def request_stock_realtime_rank(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .normalize_utils import get_value
    from .rank_fetch import stock_realtime_rank_request_result, stock_realtime_rank_result
    from .rank_params import rank_category_param, rank_filter_param, rank_sort_param
    from .request_limits import TDX_RANK_DEFAULT_COUNT, TDX_RANK_MAX_COUNT, TDX_RANK_MAX_START
    from .request_params import bool_param, int_param
    from .snapshot_normalize import normalize_realtime_snapshot_row
    from .wire_requests import tdx_category_quotes

    result = stock_realtime_rank_request_result(
        client,
        params,
        category_param=rank_category_param,
        sort_param=rank_sort_param,
        filter_param=rank_filter_param,
        bool_param=bool_param,
        int_param=int_param,
        result_func=stock_realtime_rank_result,
        default_count=TDX_RANK_DEFAULT_COUNT,
        max_count=TDX_RANK_MAX_COUNT,
        max_start=TDX_RANK_MAX_START,
        category_quotes=tdx_category_quotes,
        get_value=get_value,
        normalize_quote=lambda quote: normalize_realtime_snapshot_row(quote, client=client),
    )
    return adapter._finish_request_result(client, result)


def request_index_realtime_rank(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .normalize_utils import get_value
    from .rank_fetch import index_realtime_rank_request_result, index_realtime_rank_result
    from .rank_params import TDX_RANK_CATEGORY_ALIASES, rank_sort_param
    from .request_limits import TDX_RANK_DEFAULT_COUNT, TDX_RANK_MAX_COUNT, TDX_RANK_MAX_START
    from .request_params import bool_param, int_param
    from .snapshot_normalize import normalize_index_snapshot_row
    from .wire_requests import tdx_category_quotes

    result = index_realtime_rank_request_result(
        client,
        params,
        category=TDX_RANK_CATEGORY_ALIASES["index"],
        sort_param=rank_sort_param,
        bool_param=bool_param,
        int_param=int_param,
        result_func=index_realtime_rank_result,
        default_count=TDX_RANK_DEFAULT_COUNT,
        max_count=TDX_RANK_MAX_COUNT,
        max_start=TDX_RANK_MAX_START,
        category_quotes=tdx_category_quotes,
        get_value=get_value,
        normalize_quote=lambda quote: normalize_index_snapshot_row(quote, client=client),
    )
    return adapter._finish_request_result(client, result)


def request_index_quote_refresh(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .normalize_utils import as_list, get_value
    from .quote_fetch import quote_rows_meta, refresh_quote_request_result, refresh_quote_rows
    from .quote_identity import quote_security_from_tdx_code
    from .request_filters import requested_kline_codes
    from .snapshot_normalize import normalize_index_snapshot_row
    from .wire_requests import tdx_refresh_quotes

    result = refresh_quote_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=refresh_quote_rows,
        meta_func=quote_rows_meta,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_refresh_quotes=tdx_refresh_quotes,
        as_list=as_list,
        get_value=get_value,
        normalize_row=lambda record: normalize_index_snapshot_row(record, client=client),
    )
    return adapter._finish_request_result(client, result)


def request_stock_limit_ladder(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .derived_rows import (
        limit_ladder_count_param,
        limit_ladder_needs_name_lookup,
        limit_ladder_public_row,
        limit_ladder_topic_type,
        normalize_limit_ladder_row,
    )
    from .execution_utils import elapsed_monotonic_ms, emit_source_progress
    from .limit_ladder_fetch import (
        limit_ladder_meta,
        limit_ladder_request_result,
        lookup_limit_ladder_topics,
        prepare_limit_ladder_source_rows,
    )
    from .limit_ladder_topics import attach_limit_ladder_themes, topic_missing_stock_count
    from .options import (
        tdx_request_option_f10_topic_refill_rounds,
        tdx_request_option_f10_topic_refill_workers,
        tdx_request_topic_worker_count,
    )
    from .request_filters import requested_boards
    from .request_params import bool_param

    result = limit_ladder_request_result(
        client,
        adapter._stats_resource_params(params),
        limit_count_param=limit_ladder_count_param,
        requested_boards=requested_boards,
        bool_param=bool_param,
        topic_type_param=limit_ladder_topic_type,
        prepare_source_rows=prepare_limit_ladder_source_rows,
        lookup_topics=lookup_limit_ladder_topics,
        request_rank_rows=_request_limit_ladder_rank_rows,
        security_names=_security_names_by_tdx_code,
        needs_name_lookup=limit_ladder_needs_name_lookup,
        normalize_row=normalize_limit_ladder_row,
        request_topics=adapter._topic_rows_by_instrument_id,
        topic_worker_count=lambda total: tdx_request_topic_worker_count(adapter._options, total),
        topic_refill_workers=lambda: tdx_request_option_f10_topic_refill_workers(adapter._options),
        topic_refill_rounds=lambda: tdx_request_option_f10_topic_refill_rounds(adapter._options),
        set_initial_lookup_meta=lambda meta: setattr(adapter, "_last_topic_lookup_meta", meta),
        get_lookup_meta=lambda: getattr(adapter, "_last_topic_lookup_meta", {}) or {},
        attach_themes=attach_limit_ladder_themes,
        public_row=limit_ladder_public_row,
        topic_missing_stock_count=topic_missing_stock_count,
        meta_func=limit_ladder_meta,
        elapsed_ms=elapsed_monotonic_ms,
        emit_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def request_stock_theme_strength_rank(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .derived_rows import (
        limit_ladder_count_param,
        limit_ladder_needs_name_lookup,
        limit_ladder_topic_type,
        normalize_limit_ladder_row,
    )
    from .execution_utils import elapsed_monotonic_ms
    from .limit_ladder_fetch import (
        lookup_limit_ladder_topics,
        prepare_limit_ladder_source_rows,
        theme_strength_meta,
        theme_strength_request_result,
    )
    from .limit_ladder_topics import limit_ladder_theme_rank_rows, topic_missing_stock_count
    from .options import (
        tdx_request_option_f10_topic_refill_rounds,
        tdx_request_option_f10_topic_refill_workers,
        tdx_request_topic_worker_count,
    )
    from .request_filters import requested_boards

    result = theme_strength_request_result(
        client,
        adapter._stats_resource_params(params),
        limit_count_param=limit_ladder_count_param,
        requested_boards=requested_boards,
        topic_type_param=limit_ladder_topic_type,
        prepare_source_rows=prepare_limit_ladder_source_rows,
        lookup_topics=lookup_limit_ladder_topics,
        request_rank_rows=_request_limit_ladder_rank_rows,
        security_names=_security_names_by_tdx_code,
        needs_name_lookup=limit_ladder_needs_name_lookup,
        normalize_row=normalize_limit_ladder_row,
        request_topics=adapter._topic_rows_by_instrument_id,
        topic_worker_count=lambda total: tdx_request_topic_worker_count(adapter._options, total),
        topic_refill_workers=lambda: tdx_request_option_f10_topic_refill_workers(adapter._options),
        topic_refill_rounds=lambda: tdx_request_option_f10_topic_refill_rounds(adapter._options),
        set_initial_lookup_meta=lambda meta: setattr(adapter, "_last_topic_lookup_meta", meta),
        get_lookup_meta=lambda: getattr(adapter, "_last_topic_lookup_meta", {}) or {},
        theme_rank_rows=limit_ladder_theme_rank_rows,
        topic_missing_stock_count=topic_missing_stock_count,
        meta_func=theme_strength_meta,
        elapsed_ms=elapsed_monotonic_ms,
    )
    return adapter._finish_request_result(client, result)


def topic_rows_by_instrument_id(
    adapter: Any,
    instrument_ids: Sequence[str],
    *,
    topic_type: str,
    progress_start: int | None = None,
    progress_span: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    from .f10_executor import request_topic_rows_lookup_result
    from .options import (
        tdx_request_option_f10_topic_refill_rounds,
        tdx_request_option_f10_topic_refill_workers,
        tdx_request_topic_worker_count,
    )
    from axdata_core.source_errors import SourceRequestError

    previous_meta = dict(adapter.last_meta)
    result = request_topic_rows_lookup_result(
        instrument_ids,
        topic_type=topic_type,
        request_f10=adapter._request_stock_f10,
        topic_worker_count=lambda total: tdx_request_topic_worker_count(adapter._options, total),
        refill_rounds=tdx_request_option_f10_topic_refill_rounds(adapter._options),
        refill_worker_count=tdx_request_option_f10_topic_refill_workers(adapter._options),
        request_error=SourceRequestError,
        progress_callback=adapter._progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )
    adapter._last_topic_lookup_meta = result.meta
    adapter.last_meta = previous_meta
    return result.rows


def request_stock_f10(
    adapter: Any,
    interface_name: str,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .f10_executor import default_stock_f10_request_result
    from .options import tdx_request_option_f10_workers
    from .request_filters import requested_f10_codes
    from .tdx_f10_specs import F10_INTERFACE_SPECS

    result = default_stock_f10_request_result(
        interface_name=interface_name,
        params=params,
        specs=F10_INTERFACE_SPECS,
        existing_client=adapter._client,
        requested_codes=requested_f10_codes,
        option_workers=tdx_request_option_f10_workers,
        options=adapter._options,
    )
    adapter.last_meta = result.meta
    return result.rows


def request_stock_f10_many(
    client: Any,
    spec: Any,
    params: Mapping[str, Any],
    requested_codes: Sequence[str],
    *,
    worker_count: int,
) -> list[dict[str, Any]]:
    from .f10_executor import request_f10_many_with_default_interface

    return request_f10_many_with_default_interface(
        client,
        spec,
        params,
        requested_codes,
        worker_count=worker_count,
    )


def stats_resource_params(adapter: Any, params: Mapping[str, Any]) -> dict[str, Any]:
    from .options import stats_resource_params as normalize_stats_resource_params

    return normalize_stats_resource_params(params, adapter._options)


def request_stock_auction_process(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import auction_process_request_result, point_rows_meta, request_auction_process_rows
    from .normalize_utils import as_list, get_value
    from .request_filters import requested_kline_codes
    from .time_series_normalize import normalize_auction_process_row
    from .wire_requests import tdx_auction_process

    result = auction_process_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=request_auction_process_rows,
        meta_func=point_rows_meta,
        auction_process=tdx_auction_process,
        as_list=as_list,
        get_value=get_value,
        normalize_row=normalize_auction_process_row,
    )
    return adapter._finish_request_result(client, result)


def request_stock_intraday_subchart(
    adapter: Any,
    client: Any,
    interface_name: str,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .interface_sets import INTRADAY_SUBCHART_INTERFACE_SPECS
    from .intraday_fetch import intraday_subchart_request_result, point_rows_meta, request_intraday_subchart_rows
    from .request_filters import requested_kline_codes
    from .time_series_normalize import normalize_intraday_subchart_row, subchart_points
    from .wire_requests import tdx_intraday_subchart

    result = intraday_subchart_request_result(
        client,
        interface_name,
        params,
        specs=INTRADAY_SUBCHART_INTERFACE_SPECS,
        requested_codes=requested_kline_codes,
        rows_func=request_intraday_subchart_rows,
        meta_func=point_rows_meta,
        intraday_subchart=tdx_intraday_subchart,
        subchart_points=subchart_points,
        normalize_row=normalize_intraday_subchart_row,
    )
    return adapter._finish_request_result(client, result)


def request_stock_intraday_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import intraday_history_request_result, point_rows_meta, request_intraday_history_rows
    from .request_filters import requested_kline_codes
    from .request_params import trade_date_param
    from .snapshot_normalize import price_decimal
    from .time_series_normalize import intraday_points, normalize_intraday_history_row
    from .wire_requests import tdx_historical_intraday

    result = intraday_history_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        trade_date_param=trade_date_param,
        rows_func=request_intraday_history_rows,
        meta_func=point_rows_meta,
        historical_intraday=tdx_historical_intraday,
        intraday_points=intraday_points,
        price_decimal=price_decimal,
        normalize_row=normalize_intraday_history_row,
    )
    return adapter._finish_request_result(client, result)


def request_index_intraday_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_intraday_history,
        asset_type="index",
    )


def request_stock_intraday_recent_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import (
        intraday_recent_history_request_result,
        point_rows_meta,
        request_intraday_recent_history_rows,
    )
    from .request_filters import requested_kline_codes
    from .request_params import trade_date_param
    from .snapshot_normalize import price_decimal
    from .time_series_normalize import intraday_points, normalize_intraday_recent_history_row
    from .wire_requests import tdx_recent_historical_intraday

    result = intraday_recent_history_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        trade_date_param=trade_date_param,
        rows_func=request_intraday_recent_history_rows,
        meta_func=point_rows_meta,
        recent_historical_intraday=tdx_recent_historical_intraday,
        intraday_points=intraday_points,
        price_decimal=price_decimal,
        normalize_row=normalize_intraday_recent_history_row,
    )
    return adapter._finish_request_result(client, result)


def request_stock_intraday_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import intraday_today_request_result, point_rows_meta, request_intraday_today_rows
    from .request_filters import requested_kline_codes
    from .snapshot_normalize import price_decimal
    from .time_series_normalize import intraday_points, normalize_intraday_today_row
    from .wire_requests import tdx_today_intraday

    result = intraday_today_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=request_intraday_today_rows,
        meta_func=point_rows_meta,
        today_intraday=tdx_today_intraday,
        intraday_points=intraday_points,
        price_decimal=price_decimal,
        normalize_row=normalize_intraday_today_row,
    )
    return adapter._finish_request_result(client, result)


def request_index_intraday_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_intraday_today,
        asset_type="index",
    )


def request_etf_realtime_snapshot(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_index_realtime_snapshot,
        asset_type="etf",
    )


def request_etf_realtime_rank(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .normalize_utils import get_value
    from .rank_fetch import etf_realtime_rank_request_result, etf_realtime_rank_result
    from .rank_params import rank_sort_param
    from .request_limits import TDX_RANK_DEFAULT_COUNT, TDX_RANK_MAX_COUNT, TDX_RANK_MAX_START
    from .request_params import bool_param, int_param
    from .snapshot_normalize import normalize_index_snapshot_row
    from .wire_requests import tdx_category_quotes

    result = etf_realtime_rank_request_result(
        client,
        params,
        category=0x2AFD,
        category_meta="0x2afd",
        category_name="etf",
        sort_param=rank_sort_param,
        bool_param=bool_param,
        int_param=int_param,
        result_func=etf_realtime_rank_result,
        default_count=TDX_RANK_DEFAULT_COUNT,
        max_count=TDX_RANK_MAX_COUNT,
        max_start=TDX_RANK_MAX_START,
        category_quotes=tdx_category_quotes,
        get_value=get_value,
        normalize_quote=lambda quote: normalize_index_snapshot_row(quote, client=client),
    )
    return adapter._finish_request_result(client, result)


def request_etf_kline(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .kline_helpers import index_like_kline_request_result, sequential_kline_rows_and_meta
    from .normalize_utils import get_value
    from .request_filters import requested_kline_codes
    from .request_params import TDX_KLINE_MAX_COUNT, index_kline_period, int_param
    from .time_series_normalize import normalize_index_kline_row

    result = index_like_kline_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        index_kline_period=index_kline_period,
        int_param=int_param,
        max_count=TDX_KLINE_MAX_COUNT,
        rows_meta_func=sequential_kline_rows_and_meta,
        normalize_row=normalize_index_kline_row,
        request_code_history=_request_kline_code_history,
        get_value=get_value,
        request_kind="stock",
        meta_kind="etf",
    )
    return adapter._finish_request_result(client, result)


def request_etf_intraday_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_intraday_today,
        asset_type="etf",
    )


def request_etf_intraday_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_intraday_history,
        asset_type="etf",
    )


def request_etf_trades_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_trades_today,
        asset_type="etf",
    )


def request_etf_trades_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_trades_history,
        asset_type="etf",
    )


def request_etf_auction_process(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_auction_process,
        asset_type="etf",
    )


def request_etf_auction_result_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return request_with_asset_type(
        adapter,
        client,
        params,
        adapter._request_stock_auction_result_today,
        asset_type="etf",
    )


def request_stock_trades_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import request_trade_rows, trade_rows_meta, trade_today_request_result
    from .request_filters import requested_kline_codes
    from .request_limits import TDX_TRADE_PAGE_SIZE
    from .time_series_normalize import trade_row_sort_key

    result = trade_today_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=request_trade_rows,
        meta_func=trade_rows_meta,
        page_size=TDX_TRADE_PAGE_SIZE,
        request_trade_series_history=_request_trade_series_history,
        row_sort_key=trade_row_sort_key,
    )
    return adapter._finish_request_result(client, result)


def request_stock_trades_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import request_trade_rows, trade_history_request_result, trade_rows_meta
    from .request_filters import requested_kline_codes
    from .request_limits import TDX_TRADE_PAGE_SIZE
    from .request_params import trade_date_param
    from .time_series_normalize import trade_row_sort_key

    result = trade_history_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        trade_date_param=trade_date_param,
        rows_func=request_trade_rows,
        meta_func=trade_rows_meta,
        page_size=TDX_TRADE_PAGE_SIZE,
        request_trade_series_history=_request_trade_series_history,
        row_sort_key=trade_row_sort_key,
    )
    return adapter._finish_request_result(client, result)


def request_stock_auction_result_today(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import auction_result_rows_meta, auction_result_today_request_result, request_auction_result_rows
    from .request_filters import requested_kline_codes
    from .request_limits import TDX_TRADE_PAGE_SIZE
    from .time_series_normalize import (
        auction_result_row_sort_key,
        is_opening_auction_result_trade,
        normalize_auction_result_row,
    )

    result = auction_result_today_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        rows_func=request_auction_result_rows,
        meta_func=auction_result_rows_meta,
        page_size=TDX_TRADE_PAGE_SIZE,
        request_trade_series_history=_request_trade_series_history,
        is_opening_auction_result_trade=is_opening_auction_result_trade,
        normalize_row=normalize_auction_result_row,
        row_sort_key=auction_result_row_sort_key,
    )
    return adapter._finish_request_result(client, result)


def request_stock_auction_result_history(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .intraday_fetch import auction_result_history_request_result, auction_result_rows_meta, request_auction_result_rows
    from .request_filters import requested_kline_codes
    from .request_limits import TDX_TRADE_PAGE_SIZE
    from .request_params import trade_date_param
    from .time_series_normalize import (
        auction_result_row_sort_key,
        is_opening_auction_result_trade,
        normalize_auction_result_row,
    )

    result = auction_result_history_request_result(
        client,
        params,
        requested_codes=requested_kline_codes,
        trade_date_param=trade_date_param,
        rows_func=request_auction_result_rows,
        meta_func=auction_result_rows_meta,
        page_size=TDX_TRADE_PAGE_SIZE,
        request_trade_series_history=_request_trade_series_history,
        is_opening_auction_result_trade=is_opening_auction_result_trade,
        normalize_row=normalize_auction_result_row,
        row_sort_key=auction_result_row_sort_key,
    )
    return adapter._finish_request_result(client, result)


def request_with_asset_type(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
    request_func: Any,
    *,
    asset_type: str,
) -> list[dict[str, Any]]:
    from .execution_utils import apply_asset_type_meta

    rows = request_func(client, params)
    rows, adapter.last_meta = apply_asset_type_meta(
        rows,
        adapter.last_meta,
        asset_type=asset_type,
    )
    return rows


def _request_trade_series_history(
    client: Any,
    tdx_code: str,
    *,
    trade_date: str | None,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    from .request_limits import TDX_TRADE_MAX_START
    from .request_seams import request_trade_series_history
    from .snapshot_normalize import price_decimal
    from .time_series_normalize import normalize_trade_row, trade_records
    from .wire_requests import tdx_historical_trades, tdx_today_trades

    return request_trade_series_history(
        client,
        tdx_code,
        trade_date=trade_date,
        page_size=page_size,
        max_start=TDX_TRADE_MAX_START,
        price_decimal=price_decimal,
        today_trades=tdx_today_trades,
        historical_trades=tdx_historical_trades,
        trade_records=trade_records,
        normalize_trade_row=normalize_trade_row,
    )


def request_stock_capital_changes(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .execution_utils import client_pool_size, emit_source_progress
    from .finance_fetch import capital_change_meta, capital_change_request_result, capital_change_result
    from .finance_normalize import requested_capital_change_categories

    result = capital_change_request_result(
        client,
        params,
        stock_code_pool=adapter._daily_share_tdx_codes,
        requested_categories=requested_capital_change_categories,
        capital_change_rows_by_tdx_code_func=_capital_change_rows_by_tdx_code,
        capital_change_result_func=capital_change_result,
        capital_change_meta_func=capital_change_meta,
        client_pool_size=client_pool_size,
        emit_source_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def request_stock_adj_factor(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .adjustment import build_adjustment_factors, selected_factor_value
    from .adjustment_fetch import adjustment_factor_meta, adjustment_factor_request_result, adjustment_factor_rows
    from .derived_rows import normalize_adj_factor_row
    from .normalize_utils import as_list, get_value
    from .request_filters import requested_kline_codes
    from .request_params import (
        KLINE_INTERFACE_SPECS,
        adj_factor_adjust_param,
        anchor_date_param,
        normalize_adj_factor_anchor_date,
    )
    from axdata_core.source_errors import SourceRequestValidationError
    from .wire_requests import tdx_capital_changes

    result = adjustment_factor_request_result(
        client,
        params,
        requested_kline_codes=requested_kline_codes,
        adjust_param=adj_factor_adjust_param,
        anchor_date_param=anchor_date_param,
        normalize_anchor_date=normalize_adj_factor_anchor_date,
        rows_func=adjustment_factor_rows,
        meta_func=adjustment_factor_meta,
        page_size=KLINE_INTERFACE_SPECS["stock_kline_daily_tdx"]["default_count"],
        request_kline_series_history=_request_kline_series_history,
        tdx_capital_changes=tdx_capital_changes,
        as_list=as_list,
        get_value=get_value,
        build_adjustment_factors=build_adjustment_factors,
        selected_factor_value=selected_factor_value,
        normalize_adj_factor_row=normalize_adj_factor_row,
        validation_error=SourceRequestValidationError,
    )
    return adapter._finish_request_result(client, result)


def request_stock_auction_indicators(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .auction_fetch import auction_indicator_meta, auction_indicator_request_result, auction_indicator_rows
    from .codes import MARKET_TO_ID
    from .derived_rows import normalize_auction_indicator_row
    from .execution_utils import emit_source_progress
    from .normalize_utils import as_list, get_value
    from .quote_identity import quote_security_from_tdx_code
    from .request_filters import requested_kline_codes
    from axdata_core.source_errors import SourceRequestValidationError
    from .wire_requests import tdx_explicit_quotes

    result = auction_indicator_request_result(
        client,
        adapter._stats_resource_params(params),
        requested_codes=requested_kline_codes,
        validation_error=SourceRequestValidationError,
        rows_func=auction_indicator_rows,
        meta_func=auction_indicator_meta,
        market_to_id=MARKET_TO_ID,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_explicit_quotes=tdx_explicit_quotes,
        as_list=as_list,
        get_value=get_value,
        finance_rows_by_tdx_code=_finance_rows_by_tdx_code,
        request_recent_daily_bars=_request_recent_daily_bars,
        normalize_auction_indicator_row=normalize_auction_indicator_row,
        emit_source_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def request_stock_daily_share(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .codes import MARKET_TO_ID
    from .derived_rows import normalize_daily_share_row
    from .execution_utils import client_pool_size, emit_source_progress
    from .finance_fetch import daily_share_meta, daily_share_request_result, daily_share_rows
    from .interface_sets import DAILY_SHARE_FINANCE_BATCH_SIZE
    from axdata_core.source_errors import SourceRequestValidationError

    result = daily_share_request_result(
        client,
        adapter._stats_resource_params(params),
        stock_code_pool=adapter._daily_share_tdx_codes,
        validation_error=SourceRequestValidationError,
        finance_rows_by_tdx_code=_finance_rows_by_tdx_code,
        daily_share_rows_func=daily_share_rows,
        daily_share_meta_func=daily_share_meta,
        market_to_id=MARKET_TO_ID,
        normalize_daily_share_row=normalize_daily_share_row,
        client_pool_size=client_pool_size,
        finance_batch_size=DAILY_SHARE_FINANCE_BATCH_SIZE,
        emit_source_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def daily_share_tdx_codes(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
    *,
    progress_start: int = 20,
    progress_span: int = 8,
) -> tuple[list[str], str | None, dict[str, str]]:
    from .code_fetch import stock_code_pool_from_params
    from .request_filters import is_all_codes_value, requested_kline_codes, scope_meta_value

    result = stock_code_pool_from_params(
        params,
        request_stock_rows=lambda stock_params, start, span: adapter._request_stock_codes(
            client,
            stock_params,
            progress_start=start,
            progress_span=span,
        ),
        is_all_codes_value=is_all_codes_value,
        requested_kline_codes=requested_kline_codes,
        scope_meta_value=scope_meta_value,
        progress_start=progress_start,
        progress_span=progress_span,
    )
    return result.tdx_codes, result.expanded_scope, result.names_by_tdx_code


def request_stock_daily_price_limit(
    adapter: Any,
    client: Any,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    from .derived_rows import normalize_daily_price_limit_row, normalize_daily_price_limit_snapshot_row
    from .execution_utils import client_pool_size, emit_source_progress
    from .price_limit_fetch import daily_price_limit_meta, daily_price_limit_request_result, daily_price_limit_result
    from .request_limits import DEFAULT_QUOTE_BATCH_SIZE
    from .request_params import normalize_optional_date_text

    result = daily_price_limit_request_result(
        client,
        params,
        stock_code_pool=adapter._daily_share_tdx_codes,
        normalize_optional_date_text=normalize_optional_date_text,
        security_names_by_tdx_code=_security_names_by_tdx_code,
        daily_price_limit_result_func=daily_price_limit_result,
        daily_price_limit_meta_func=daily_price_limit_meta,
        latest_calendar_dates=_latest_daily_price_limit_calendar_dates,
        request_snapshot_rows=lambda codes, **kwargs: _explicit_snapshot_rows_by_tdx_code(
            client,
            codes,
            **kwargs,
        ),
        request_price_limit_bases=lambda codes, target, **kwargs: _price_limit_bases_by_tdx_code(
            client,
            codes,
            target,
            **kwargs,
        ),
        normalize_snapshot_row=normalize_daily_price_limit_snapshot_row,
        normalize_history_row=normalize_daily_price_limit_row,
        client_pool_size=client_pool_size,
        default_quote_batch_size=DEFAULT_QUOTE_BATCH_SIZE,
        emit_source_progress=emit_source_progress,
        progress_callback=adapter._progress_callback,
    )
    return adapter._finish_request_result(client, result)


def _capital_change_rows_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    requested_categories: set[int] | None,
    progress_callback: Any | None = None,
    progress_start: int = 30,
    progress_span: int = 38,
) -> dict[str, dict[str, Any]]:
    from .execution_utils import client_pool_size, emit_batch_progress
    from .finance_normalize import capital_change_category_matches, normalize_capital_change_row
    from .normalize_utils import as_list, get_value
    from .request_seams import capital_change_rows_by_tdx_code
    from .wire_requests import tdx_capital_changes

    return capital_change_rows_by_tdx_code(
        client,
        tdx_codes,
        requested_categories=requested_categories,
        tdx_capital_changes=tdx_capital_changes,
        as_list=as_list,
        get_value=get_value,
        normalize_capital_change_row=normalize_capital_change_row,
        category_matches=capital_change_category_matches,
        client_pool_size=client_pool_size,
        emit_progress=emit_batch_progress,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def _finance_rows_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    batch_size: int | None = None,
    progress_callback: Any | None = None,
    progress_start: int = 28,
    progress_span: int = 40,
) -> tuple[dict[str, dict[str, Any]], int]:
    from .execution_utils import chunked, client_pool_size, emit_batch_progress
    from .finance_normalize import finance_records
    from .normalize_utils import get_value
    from .request_seams import finance_rows_by_tdx_code
    from .wire_requests import tdx_finance_info

    return finance_rows_by_tdx_code(
        client,
        tdx_codes,
        chunked=chunked,
        tdx_finance_info=tdx_finance_info,
        finance_records=finance_records,
        normalize_finance_info_row=_normalize_finance_info_row,
        get_value=get_value,
        client_pool_size=client_pool_size,
        emit_progress=emit_batch_progress,
        batch_size=batch_size,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def _request_recent_daily_bars(
    client: Any,
    tdx_code: str,
    *,
    count: int,
    stats_date: Any,
) -> tuple[list[Any], int]:
    from .normalize_utils import bar_trade_date, get_value
    from .request_params import TDX_KLINE_MAX_COUNT
    from .request_seams import request_recent_daily_bars
    from .time_series_normalize import kline_bars
    from .wire_requests import tdx_kline

    return request_recent_daily_bars(
        client,
        tdx_code,
        count=count,
        stats_date=stats_date,
        max_count=TDX_KLINE_MAX_COUNT,
        tdx_kline=tdx_kline,
        kline_bars=kline_bars,
        get_value=get_value,
        bar_trade_date=bar_trade_date,
    )


def _explicit_snapshot_rows_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    progress_callback: Any | None = None,
    progress_start: int = 30,
    progress_span: int = 38,
) -> tuple[dict[str, dict[str, Any]], int]:
    from .execution_utils import chunked, client_pool_size, emit_batch_progress
    from .normalize_utils import as_list
    from .request_limits import DEFAULT_QUOTE_BATCH_SIZE
    from .request_seams import explicit_snapshot_rows_by_tdx_code
    from .snapshot_normalize import normalize_realtime_snapshot_row
    from .wire_requests import tdx_explicit_quotes

    return explicit_snapshot_rows_by_tdx_code(
        client,
        tdx_codes,
        chunked=chunked,
        batch_size=DEFAULT_QUOTE_BATCH_SIZE,
        client_pool_size=client_pool_size,
        tdx_explicit_quotes=tdx_explicit_quotes,
        as_list=as_list,
        normalize_snapshot_row=normalize_realtime_snapshot_row,
        emit_progress=emit_batch_progress,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def _price_limit_bases_by_tdx_code(
    client: Any,
    tdx_codes: Sequence[str],
    target_trade_date: Any,
    *,
    progress_callback: Any | None = None,
) -> list[Any]:
    from .execution_utils import client_pool_size, emit_price_limit_progress
    from .request_seams import price_limit_bases_by_tdx_code

    return price_limit_bases_by_tdx_code(
        client,
        tdx_codes,
        target_trade_date,
        request_base=_price_limit_base_from_daily_kline,
        client_pool_size=client_pool_size,
        emit_progress=emit_price_limit_progress,
        progress_callback=progress_callback,
    )


def _price_limit_base_from_daily_kline(client: Any, tdx_code: str, target_trade_date: Any) -> Any:
    from .normalize_utils import bar_trade_date
    from .request_seams import price_limit_base_from_daily_kline

    return price_limit_base_from_daily_kline(
        client,
        tdx_code,
        target_trade_date,
        request_recent_daily_bars=_request_recent_daily_bars,
        bar_trade_date=bar_trade_date,
    )


def _latest_daily_price_limit_calendar_dates(
    *,
    today: Any | None = None,
    request_interface: Any | None = None,
) -> Any:
    from .derived_rows import before_daily_close_buffer, default_daily_price_limit_trade_date
    from .request_seams import latest_daily_price_limit_calendar_dates

    return latest_daily_price_limit_calendar_dates(
        today=today,
        default_trade_date=default_daily_price_limit_trade_date,
        before_daily_close_buffer=before_daily_close_buffer,
        request_interface=request_interface,
    )


def _security_names_by_tdx_code(client: Any, tdx_codes: Sequence[str]) -> dict[str, str]:
    from .normalize_utils import get_value
    from .request_seams import security_names_by_tdx_code
    from .snapshot_normalize import tdx_codes_all

    return security_names_by_tdx_code(
        client,
        tdx_codes,
        tdx_codes_all=tdx_codes_all,
        get_value=get_value,
    )


def _normalize_finance_info_row(
    record: Any,
    *,
    enrich_profile: bool = False,
    finance_maps: Any | None = None,
    profile_lookup: Any | None = None,
) -> dict[str, Any]:
    if profile_lookup is None:
        from .finance_maps import lookup_finance_profile_maps as profile_lookup
    from .request_seams import normalize_finance_info_row

    return normalize_finance_info_row(
        record,
        enrich_profile=enrich_profile,
        finance_maps=finance_maps,
        profile_lookup=profile_lookup,
    )


def request_stock_finance_info(
    adapter: Any,
    client: Any,
    interface_name: str,
    params: Mapping[str, Any],
    *,
    load_finance_maps: Any | None = None,
    lookup_finance_profile: Any | None = None,
) -> list[dict[str, Any]]:
    from .finance_fetch import finance_info_request_result, finance_info_result
    from .finance_normalize import finance_records
    from .interface_sets import FINANCE_INTERFACE_FIELDS
    from .normalize_utils import get_value
    from .request_filters import requested_kline_codes
    from .wire_requests import tdx_finance_info
    if load_finance_maps is None:
        from .finance_maps import load_finance_local_maps_from_root as load_finance_maps

    result = finance_info_request_result(
        client,
        interface_name,
        params,
        requested_kline_codes=requested_kline_codes,
        load_finance_maps=load_finance_maps,
        finance_info_result_func=finance_info_result,
        tdx_finance_info=tdx_finance_info,
        finance_records=finance_records,
        get_value=get_value,
        normalize_finance_info_row=lambda record, **kwargs: _normalize_finance_info_row(
            record,
            profile_lookup=lookup_finance_profile,
            **kwargs,
        ),
        fields_by_interface=FINANCE_INTERFACE_FIELDS,
    )
    return adapter._finish_request_result(client, result)


def _request_limit_ladder_rank_rows(client: Any, *, include_touched: bool) -> tuple[list[dict[str, Any]], int]:
    from .derived_rows import limit_ladder_rank_page_below_threshold
    from .normalize_utils import get_value
    from .rank_params import TDX_RANK_CATEGORY_ALIASES, TDX_RANK_SORT_ALIASES
    from .request_limits import TDX_LIMIT_LADDER_SCAN_PAGE_SIZE, TDX_RANK_MAX_START
    from .request_seams import request_limit_ladder_rank_rows
    from .snapshot_normalize import normalize_realtime_snapshot_row
    from .wire_requests import tdx_category_quotes

    return request_limit_ladder_rank_rows(
        client,
        include_touched=include_touched,
        category_quotes=tdx_category_quotes,
        normalize_snapshot_row=normalize_realtime_snapshot_row,
        rank_page_below_threshold=limit_ladder_rank_page_below_threshold,
        get_value=get_value,
        category=TDX_RANK_CATEGORY_ALIASES["a_share"],
        sort_type=TDX_RANK_SORT_ALIASES["change_pct"],
        page_size=TDX_LIMIT_LADDER_SCAN_PAGE_SIZE,
        max_start=TDX_RANK_MAX_START,
    )
