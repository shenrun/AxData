"""Adjustment-factor fetch helpers for TDX requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class AdjustmentFactorRowsResult:
    rows: list[dict[str, Any]]
    page_count: int
    event_count: int
    xdxr_event_count: int


@dataclass(frozen=True)
class AdjustmentFactorRequestResult:
    rows: list[dict[str, Any]]
    meta: dict[str, Any]


def adjustment_factor_request_result(
    client: Any,
    params: Mapping[str, Any],
    *,
    requested_kline_codes: Callable[[Any], Sequence[str]],
    adjust_param: Callable[[Any], str],
    anchor_date_param: Callable[[Mapping[str, Any]], Any],
    normalize_anchor_date: Callable[[str, Any], Any],
    rows_func: Callable[..., AdjustmentFactorRowsResult],
    meta_func: Callable[..., dict[str, Any]],
    page_size: int,
    request_kline_series_history: Callable[..., tuple[Any, int]],
    tdx_capital_changes: Callable[[Any, str], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    build_adjustment_factors: Callable[..., Sequence[Any]],
    selected_factor_value: Callable[[Any, str], float],
    normalize_adj_factor_row: Callable[[str, str, float], dict[str, Any]],
    validation_error: type[BaseException],
) -> AdjustmentFactorRequestResult:
    tdx_codes = requested_kline_codes(params.get("code"))
    adjust = adjust_param(params.get("adjust"))
    anchor_date = normalize_anchor_date(adjust, anchor_date_param(params))

    try:
        result = rows_func(
            client,
            tdx_codes,
            adjust=adjust,
            anchor_date=anchor_date,
            page_size=page_size,
            request_kline_series_history=request_kline_series_history,
            tdx_capital_changes=tdx_capital_changes,
            as_list=as_list,
            get_value=get_value,
            build_adjustment_factors=build_adjustment_factors,
            selected_factor_value=selected_factor_value,
            normalize_adj_factor_row=normalize_adj_factor_row,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc

    return AdjustmentFactorRequestResult(
        rows=result.rows,
        meta=meta_func(
            result,
            adjust=adjust,
            anchor_date=anchor_date,
            requested_code_count=len(tdx_codes),
        ),
    )


def adjustment_factor_meta(
    result: AdjustmentFactorRowsResult,
    *,
    adjust: str,
    anchor_date: Any,
    requested_code_count: int,
) -> dict[str, Any]:
    return {
        "tdx_protocol": "0x000f+0x052d",
        "tdx_adjust_method": adjust,
        "tdx_anchor_date": anchor_date,
        "tdx_event_count": result.event_count,
        "tdx_xdxr_event_count": result.xdxr_event_count,
        "tdx_kline_page_count": result.page_count,
        "tdx_requested_code_count": requested_code_count,
    }


def adjustment_factor_rows(
    client: Any,
    tdx_codes: Sequence[str],
    *,
    adjust: str,
    anchor_date: Any,
    page_size: int,
    request_kline_series_history: Callable[..., tuple[Any, int]],
    tdx_capital_changes: Callable[[Any, str], Any],
    as_list: Callable[[Any], list[Any]],
    get_value: Callable[[Any, str, Any], Any],
    build_adjustment_factors: Callable[..., Sequence[Any]],
    selected_factor_value: Callable[[Any, str], float],
    normalize_adj_factor_row: Callable[[str, str, float], dict[str, Any]],
) -> AdjustmentFactorRowsResult:
    rows: list[dict[str, Any]] = []
    page_count = 0
    event_count = 0
    xdxr_event_count = 0
    for tdx_code in tdx_codes:
        day_kline, current_page_count = request_kline_series_history(
            client,
            tdx_code,
            period="day",
            page_size=page_size,
            adjust="none",
            anchor_date=None,
        )
        page_count += current_page_count
        capital_changes = tdx_capital_changes(client, tdx_code)
        capital_records = as_list(get_value(capital_changes, "records", ()))
        event_count += len(capital_records)
        xdxr_event_count += sum(1 for record in capital_records if get_value(record, "category_raw", 0) == 1)
        factors = build_adjustment_factors(
            day_kline,
            capital_changes,
            adjust=adjust,
            anchor_date=anchor_date,
        )
        for factor in factors:
            rows.append(
                normalize_adj_factor_row(
                    tdx_code,
                    factor.trade_date.strftime("%Y%m%d"),
                    selected_factor_value(factor, adjust),
                )
            )

    return AdjustmentFactorRowsResult(
        rows=rows,
        page_count=page_count,
        event_count=event_count,
        xdxr_event_count=xdxr_event_count,
    )
