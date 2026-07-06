"""TDX F10 parameter and context helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError

from .codes import MARKET_TO_ID, instrument_id_to_tdx_code, tdx_code_to_instrument_id
from .f10_normalize import date_dash, f10_date_text, f10_first_value, f10_page, f10_rating_code
from .tdx_f10_models import F10InterfaceSpec


def analyst_target_stats(tables: Sequence[Any]) -> Mapping[str, Any]:
    for table in tables[1:]:
        for row in table.rows:
            if "N004" in row and "N005" in row:
                return row
    return {}


def control_ranking_item(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return {
            "rank": f10_first_value(value, ("pm", "rank", "N001")),
            "market_code": f10_first_value(value, ("sc", "market_code", "N002")),
            "symbol": f10_first_value(value, ("code", "symbol", "zqdm", "N003")),
            "name": f10_first_value(value, ("name", "zqjc", "N004")),
            "control_ratio_pct": f10_first_value(value, ("zlkp", "control_ratio_pct", "N005")),
        }
    if isinstance(value, (list, tuple)) and len(value) >= 5:
        return {
            "rank": value[0],
            "market_code": value[1],
            "symbol": value[2],
            "name": value[3],
            "control_ratio_pct": value[4],
        }
    return None


def f10_unfiltered_page_params(spec: F10InterfaceSpec, params: Mapping[str, Any]) -> dict[str, Any]:
    page_params = dict(params)
    if spec.name == "stock_shareholder_change_plans_tdx":
        page_params.pop("direction", None)
    if spec.name == "stock_northbound_holding_tdx":
        page_params.pop("start_date", None)
        page_params.pop("end_date", None)
    return page_params


def f10_business_period_candidates(row: Mapping[str, Any]) -> list[str]:
    preferred = ("T002", "rq", "bgq", "report_period", "period")
    periods = [f10_business_period_value(row.get(key)) for key in preferred]
    periods = [period for period in periods if period]
    if periods:
        return periods
    return [period for period in (f10_business_period_value(value) for value in row.values()) if period]


def f10_business_period_value(value: Any) -> str | None:
    text = f10_date_text(value)
    if text and len(text) == 8 and text.isdigit():
        return text
    return None


def f10_context(spec: F10InterfaceSpec, params: Mapping[str, Any]) -> dict[str, Any]:
    code_value = params.get("code")
    tdx_code = instrument_id_to_tdx_code(str(code_value)) if code_value not in (None, "") else ""
    market = tdx_code[:2] if len(tdx_code) == 8 else ""
    symbol = tdx_code[2:] if len(tdx_code) == 8 else str(code_value or "").strip()
    market_id = MARKET_TO_ID.get(market, 0)
    function = f10_function(spec, params)
    count = (
        int_param(params, "count", 20, minimum=1, maximum=500)
        if any(parameter.name == "count" for parameter in spec.params) or params.get("count") not in (None, "")
        else 20
    )
    cursor = params.get("cursor")
    page = f10_page(cursor)
    start_date_text = normalize_optional_date_text(params.get("start_date"), name="start_date")
    end_date_text = normalize_optional_date_text(params.get("end_date"), name="end_date")
    event_date = normalize_optional_date_text(params.get("event_date"))
    return {
        "code": symbol,
        "tdx_code": tdx_code,
        "instrument_id": tdx_code_to_instrument_id(tdx_code) if tdx_code else None,
        "market": market,
        "market_id": market_id,
        "function": function,
        "count": count,
        "page": page,
        "keyword": params.get("keyword", "") or "",
        "rating_code": f10_rating_code(params.get("rating")),
        "period": normalize_optional_date_text(params.get("period")) or "",
        "event_date": event_date or "",
        "event_date_dash": date_dash(event_date),
        "begin_date": start_date_text or "0",
        "end_date_for_request": end_date_text or "0",
        "start_date_for_request": start_date_text or "",
        "end_date_text": end_date_text or "",
        "concept_code": params.get("concept_code", "") or "",
        "sort_by": params.get("sort_by", "zdf") or "zdf",
        "metric": params.get("metric", spec.function_default or "") or "",
        "category": params.get("category", spec.function_default or "") or "",
        "detail_id": params.get("detail_id", "") or "",
        "detail_type": params.get("detail_type", spec.function_default or "") or "",
    }


def f10_function(spec: F10InterfaceSpec, params: Mapping[str, Any]) -> str:
    if spec.name == "stock_dividend_metrics_tdx":
        return f10_dividend_metrics_function(params)
    if not spec.function_param:
        return spec.function_default or ""
    value = str(params.get(spec.function_param, spec.function_default or "") or "").strip()
    key = value.lower()
    if key in spec.function_aliases:
        return spec.function_aliases[key]
    if value in spec.function_aliases.values() and spec.name != "stock_valuation_series_tdx":
        return value
    allowed = ", ".join(sorted(spec.function_aliases))
    raise SourceRequestValidationError(f"{spec.function_param} must be one of: {allowed}")


def f10_dividend_metrics_function(params: Mapping[str, Any]) -> str:
    metric = str(params.get("metric") or "dividend_yield").strip().lower()
    view_raw = params.get("view")
    view = str(view_raw).strip().lower() if view_raw not in (None, "") else ""
    metric_aliases = {
        "dividend_yield": "dividend_yield",
        "股息率": "dividend_yield",
        "payout_ratio": "payout_ratio",
        "股利支付率": "payout_ratio",
        "cash_financing": "cash_financing",
        "派现融资": "cash_financing",
    }
    view_aliases = {
        "": "",
        "trend": "trend",
        "走势": "trend",
        "ranking": "ranking",
        "rank": "ranking",
        "排名": "ranking",
        "summary": "summary",
        "总览": "summary",
    }
    if metric not in metric_aliases:
        raise SourceRequestValidationError("metric must be one of: dividend_yield, payout_ratio, cash_financing")
    if view not in view_aliases:
        raise SourceRequestValidationError("view must be one of: trend, ranking, summary")
    metric_key = metric_aliases[metric]
    view_key = view_aliases[view]
    if not view_key:
        view_key = "summary" if metric_key == "cash_financing" else "trend"
    function_map = {
        ("dividend_yield", "trend"): "fhlszs_gxl",
        ("dividend_yield", "ranking"): "fhpm_gxl",
        ("payout_ratio", "trend"): "fhlszs_glzfl",
        ("payout_ratio", "ranking"): "fhpm_glzfl",
        ("cash_financing", "summary"): "pxmz",
        ("cash_financing", "ranking"): "fhpm_pxrzb",
    }
    try:
        return function_map[(metric_key, view_key)]
    except KeyError as exc:
        raise SourceRequestValidationError(
            "Unsupported metric/view combination. Use dividend_yield or payout_ratio with trend/ranking; "
            "use cash_financing with summary/ranking."
        ) from exc


def int_param(
    params: Mapping[str, Any],
    name: str,
    default: int,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    value = params.get(name, default)
    if value in (None, ""):
        value = default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError(f"{name} must be an integer") from exc
    if minimum is not None and parsed < minimum:
        raise SourceRequestValidationError(f"{name} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise SourceRequestValidationError(f"{name} must be <= {maximum}")
    return parsed


def bool_param(value: Any, *, name: str = "ascending") -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise SourceRequestValidationError(f"{name} must be a boolean")


def normalize_optional_date_text(value: Any, *, name: str = "anchor_date") -> str | None:
    if value in (None, "", 0, "0"):
        return None
    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise SourceRequestValidationError(f"{name} must be YYYYMMDD or YYYY-MM-DD")
    try:
        datetime.strptime(text, "%Y%m%d")
    except ValueError as exc:
        raise SourceRequestValidationError(f"{name} must be a valid date") from exc
    return text
