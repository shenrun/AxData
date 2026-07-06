"""Intraday, trade, and auction fetch helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class PointRowsResult:
    rows: list[dict[str, Any]]
    point_count: int


@dataclass(frozen=True)
class TradeRowsResult:
    rows: list[dict[str, Any]]
    trade_count: int
    page_count: int


@dataclass(frozen=True)
class IntradayRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def auction_process_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., PointRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    auction_process: Callable[[Any, str], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_row: Callable[[Any, Any], dict[str, Any]],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        auction_process=auction_process,
        as_list=as_list,
        get_value=get_value,
        normalize_row=normalize_row,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x056a",
            requested_code_count=len(tdx_codes),
        ),
    )


def intraday_subchart_request_result(
    client: Any,
    interface_name: str,
    params: Mapping[str, Any],
    *,
    specs: Mapping[str, Mapping[str, Any]],
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., PointRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    intraday_subchart: Callable[..., Any],
    subchart_points: Callable[[Any], Sequence[Any]],
    normalize_row: Callable[[Any, Any], Mapping[str, Any]],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    spec = specs[interface_name]
    selector = int(spec["selector"])
    result = rows_func(
        client,
        tdx_codes,
        selector=selector,
        fields=spec["fields"],
        intraday_subchart=intraday_subchart,
        subchart_points=subchart_points,
        normalize_row=normalize_row,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol=spec["protocol"],
            requested_code_count=len(tdx_codes),
            selector_raw=selector,
            selector_name="buy_sell_strength" if selector == 0 else "volume_comparison",
        ),
    )


def intraday_history_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    trade_date_param: Callable[[Any], str],
    rows_func: Callable[..., PointRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    historical_intraday: Callable[..., Any],
    intraday_points: Callable[[Any], Sequence[Any]],
    price_decimal: Callable[[Any, str], int],
    normalize_row: Callable[..., dict[str, Any]],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    trade_date = trade_date_param(params.get("trade_date"))
    result = rows_func(
        client,
        tdx_codes,
        trade_date=trade_date,
        historical_intraday=historical_intraday,
        intraday_points=intraday_points,
        price_decimal=price_decimal,
        normalize_row=normalize_row,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0fb4",
            trade_date=trade_date,
            requested_code_count=len(tdx_codes),
        ),
    )


def intraday_recent_history_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    trade_date_param: Callable[[Any], str],
    rows_func: Callable[..., PointRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    recent_historical_intraday: Callable[..., Any],
    intraday_points: Callable[[Any], Sequence[Any]],
    price_decimal: Callable[[Any, str], int],
    normalize_row: Callable[..., dict[str, Any]],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    trade_date = trade_date_param(params.get("trade_date"))
    result = rows_func(
        client,
        tdx_codes,
        trade_date=trade_date,
        recent_historical_intraday=recent_historical_intraday,
        intraday_points=intraday_points,
        price_decimal=price_decimal,
        normalize_row=normalize_row,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0feb",
            trade_date=trade_date,
            requested_code_count=len(tdx_codes),
        ),
    )


def intraday_today_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., PointRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    today_intraday: Callable[[Any, str], Any],
    intraday_points: Callable[[Any], Sequence[Any]],
    price_decimal: Callable[[Any, str], int],
    normalize_row: Callable[..., dict[str, Any]],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        today_intraday=today_intraday,
        intraday_points=intraday_points,
        price_decimal=price_decimal,
        normalize_row=normalize_row,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0537",
            requested_code_count=len(tdx_codes),
        ),
    )


def trade_today_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., TradeRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    page_size: int,
    request_trade_series_history: Callable[..., tuple[list[dict[str, Any]], int]],
    row_sort_key: Callable[[Mapping[str, Any]], Any],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        trade_date=None,
        page_size=page_size,
        request_trade_series_history=request_trade_series_history,
        row_sort_key=row_sort_key,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0fc5",
            trade_date=None,
            page_size=page_size,
            requested_code_count=len(tdx_codes),
        ),
    )


def trade_history_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    trade_date_param: Callable[[Any], str],
    rows_func: Callable[..., TradeRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    page_size: int,
    request_trade_series_history: Callable[..., tuple[list[dict[str, Any]], int]],
    row_sort_key: Callable[[Mapping[str, Any]], Any],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    trade_date = trade_date_param(params.get("trade_date"))
    result = rows_func(
        client,
        tdx_codes,
        trade_date=trade_date,
        page_size=page_size,
        request_trade_series_history=request_trade_series_history,
        row_sort_key=row_sort_key,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0fc6",
            trade_date=trade_date,
            page_size=page_size,
            requested_code_count=len(tdx_codes),
        ),
    )


def auction_result_today_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    rows_func: Callable[..., TradeRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    page_size: int,
    request_trade_series_history: Callable[..., tuple[list[dict[str, Any]], int]],
    is_opening_auction_result_trade: Callable[[Mapping[str, Any]], bool],
    normalize_row: Callable[..., dict[str, Any]],
    row_sort_key: Callable[[Mapping[str, Any]], Any],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    result = rows_func(
        client,
        tdx_codes,
        trade_date=None,
        page_size=page_size,
        include_datetime=False,
        request_trade_series_history=request_trade_series_history,
        is_opening_auction_result_trade=is_opening_auction_result_trade,
        normalize_row=normalize_row,
        row_sort_key=row_sort_key,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0fc5",
            trade_date=None,
            page_size=page_size,
            requested_code_count=len(tdx_codes),
        ),
    )


def auction_result_history_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_codes: Callable[[Any], Sequence[str]],
    trade_date_param: Callable[[Any], str],
    rows_func: Callable[..., TradeRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    page_size: int,
    request_trade_series_history: Callable[..., tuple[list[dict[str, Any]], int]],
    is_opening_auction_result_trade: Callable[[Mapping[str, Any]], bool],
    normalize_row: Callable[..., dict[str, Any]],
    row_sort_key: Callable[[Mapping[str, Any]], Any],
) -> IntradayRequestResult:
    tdx_codes = requested_codes(params.get("code"))
    trade_date = trade_date_param(params.get("trade_date"))
    result = rows_func(
        client,
        tdx_codes,
        trade_date=trade_date,
        page_size=page_size,
        include_datetime=True,
        request_trade_series_history=request_trade_series_history,
        is_opening_auction_result_trade=is_opening_auction_result_trade,
        normalize_row=normalize_row,
        row_sort_key=row_sort_key,
    )
    return IntradayRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            protocol="0x0fc6",
            trade_date=trade_date,
            page_size=page_size,
            requested_code_count=len(tdx_codes),
        ),
    )


def point_rows_meta(
    result: PointRowsResult,
    *,
    protocol: str,
    requested_code_count: int,
    trade_date: str | None = None,
    selector_raw: int | None = None,
    selector_name: str | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "tdx_protocol": protocol,
        "tdx_requested_code_count": requested_code_count,
        "tdx_point_count": result.point_count,
    }
    if trade_date is not None:
        meta["tdx_trade_date"] = trade_date
    if selector_raw is not None:
        meta["tdx_selector_raw"] = selector_raw
    if selector_name is not None:
        meta["tdx_selector_name"] = selector_name
    return meta


def trade_rows_meta(
    result: TradeRowsResult,
    *,
    protocol: str,
    trade_date: str | None,
    page_size: int,
    requested_code_count: int,
) -> dict[str, Any]:
    return {
        "tdx_protocol": protocol,
        "tdx_trade_date": trade_date,
        "tdx_full_history": True,
        "tdx_page_size": page_size,
        "tdx_page_count": result.page_count,
        "tdx_requested_code_count": requested_code_count,
        "tdx_trade_count": result.trade_count,
    }


def auction_result_rows_meta(
    result: TradeRowsResult,
    *,
    protocol: str,
    trade_date: str | None,
    page_size: int,
    requested_code_count: int,
) -> dict[str, Any]:
    return {
        **trade_rows_meta(
            result,
            protocol=protocol,
            trade_date=trade_date,
            page_size=page_size,
            requested_code_count=requested_code_count,
        ),
        "tdx_result_time": "09:25",
        "tdx_result_count": len(result.rows),
    }


def request_auction_process_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    auction_process: Callable[[Any, str], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    normalize_row: Callable[[Any, Any], dict[str, Any]],
) -> PointRowsResult:
    rows: list[dict[str, Any]] = []
    point_count = 0
    for tdx_code in tdx_codes:
        series = auction_process(client, tdx_code)
        records = as_list(get_value(series, "records", ()))
        point_count += len(records)
        rows.extend(normalize_row(series, record) for record in records)

    rows.sort(
        key=lambda row: (
            str(row.get("instrument_id") or ""),
            int(row.pop("_sort_time_seconds", 0) or 0),
            int(row.get("auction_index") or 0),
        )
    )
    return PointRowsResult(rows=rows, point_count=point_count)


def request_intraday_subchart_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    selector: int,
    fields: Sequence[str],
    intraday_subchart: Callable[..., Any],
    subchart_points: Callable[[Any], Sequence[Any]],
    normalize_row: Callable[[Any, Any], Mapping[str, Any]],
) -> PointRowsResult:
    rows: list[dict[str, Any]] = []
    point_count = 0
    for tdx_code in tdx_codes:
        series = intraday_subchart(client, tdx_code, selector=selector)
        points = subchart_points(series)
        point_count += len(points)
        for point in points:
            row = normalize_row(series, point)
            rows.append({field: row.get(field) for field in fields})

    rows.sort(
        key=lambda row: (
            str(row.get("instrument_id") or ""),
            int(row.get("minute_index") or 0),
        )
    )
    return PointRowsResult(rows=rows, point_count=point_count)


def request_intraday_history_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    trade_date: str,
    historical_intraday: Callable[..., Any],
    intraday_points: Callable[[Any], Sequence[Any]],
    price_decimal: Callable[[Any, str], int],
    normalize_row: Callable[..., dict[str, Any]],
) -> PointRowsResult:
    rows: list[dict[str, Any]] = []
    point_count = 0
    for tdx_code in tdx_codes:
        series = historical_intraday(client, tdx_code, trade_date=trade_date)
        points = intraday_points(series)
        point_count += len(points)
        decimal = price_decimal(client, tdx_code)
        rows.extend(normalize_row(series, point, decimal=decimal) for point in points)

    rows.sort(
        key=lambda row: (
            str(row.get("instrument_id") or ""),
            str(row.get("trade_time") or ""),
        )
    )
    return PointRowsResult(rows=rows, point_count=point_count)


def request_intraday_recent_history_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    trade_date: str,
    recent_historical_intraday: Callable[..., Any],
    intraday_points: Callable[[Any], Sequence[Any]],
    price_decimal: Callable[[Any, str], int],
    normalize_row: Callable[..., dict[str, Any]],
) -> PointRowsResult:
    rows: list[dict[str, Any]] = []
    point_count = 0
    for tdx_code in tdx_codes:
        series = recent_historical_intraday(client, tdx_code, trade_date=trade_date)
        points = intraday_points(series)
        point_count += len(points)
        decimal = price_decimal(client, tdx_code)
        rows.extend(normalize_row(series, point, decimal=decimal) for point in points)

    rows.sort(
        key=lambda row: (
            str(row.get("instrument_id") or ""),
            str(row.get("trade_time") or ""),
        )
    )
    return PointRowsResult(rows=rows, point_count=point_count)


def request_intraday_today_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    today_intraday: Callable[[Any, str], Any],
    intraday_points: Callable[[Any], Sequence[Any]],
    price_decimal: Callable[[Any, str], int],
    normalize_row: Callable[..., dict[str, Any]],
) -> PointRowsResult:
    rows: list[dict[str, Any]] = []
    point_count = 0
    for tdx_code in tdx_codes:
        series = today_intraday(client, tdx_code)
        points = intraday_points(series)
        point_count += len(points)
        decimal = price_decimal(client, tdx_code)
        rows.extend(normalize_row(series, point, decimal=decimal) for point in points)

    rows.sort(
        key=lambda row: (
            str(row.get("instrument_id") or ""),
            str(row.get("time_label") or ""),
        )
    )
    return PointRowsResult(rows=rows, point_count=point_count)


def request_trade_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    trade_date: str | None,
    page_size: int,
    request_trade_series_history: Callable[..., tuple[list[dict[str, Any]], int]],
    row_sort_key: Callable[[Mapping[str, Any]], Any],
) -> TradeRowsResult:
    rows: list[dict[str, Any]] = []
    trade_count = 0
    page_count = 0
    for tdx_code in tdx_codes:
        code_rows, current_page_count = request_trade_series_history(
            client,
            tdx_code,
            trade_date=trade_date,
            page_size=page_size,
        )
        page_count += current_page_count
        trade_count += len(code_rows)
        rows.extend(code_rows)

    rows.sort(key=row_sort_key)
    return TradeRowsResult(rows=rows, trade_count=trade_count, page_count=page_count)


def request_auction_result_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    trade_date: str | None,
    page_size: int,
    include_datetime: bool,
    request_trade_series_history: Callable[..., tuple[list[dict[str, Any]], int]],
    is_opening_auction_result_trade: Callable[[Mapping[str, Any]], bool],
    normalize_row: Callable[..., dict[str, Any]],
    row_sort_key: Callable[[Mapping[str, Any]], Any],
) -> TradeRowsResult:
    rows: list[dict[str, Any]] = []
    trade_count = 0
    page_count = 0
    for tdx_code in tdx_codes:
        code_rows, current_page_count = request_trade_series_history(
            client,
            tdx_code,
            trade_date=trade_date,
            page_size=page_size,
        )
        page_count += current_page_count
        trade_count += len(code_rows)
        rows.extend(
            normalize_row(row, include_datetime=include_datetime)
            for row in code_rows
            if is_opening_auction_result_trade(row)
        )

    rows.sort(key=row_sort_key)
    return TradeRowsResult(rows=rows, trade_count=trade_count, page_count=page_count)
