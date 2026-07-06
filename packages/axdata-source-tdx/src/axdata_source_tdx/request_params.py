"""TDX source request parameter normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError


KLINE_INTERFACE_SPECS: dict[str, dict[str, Any]] = {
    "stock_kline_second_tdx": {
        "param": "seconds",
        "unit": "s",
        "default": 5,
        "minimum": 1,
        "maximum": 60,
        "default_count": 800,
    },
    "stock_kline_minute_tdx": {
        "param": "period",
        "default": "1m",
        "allowed": {"1m", "5m", "15m", "30m", "60m"},
        "default_count": 800,
    },
    "stock_kline_nminute_tdx": {
        "param": "minutes",
        "unit": "m",
        "required": True,
        "minimum": 2,
        "maximum": 1440,
        "default_count": 800,
    },
    "stock_kline_daily_tdx": {"period": "day", "default_count": 800},
    "stock_kline_nday_tdx": {
        "param": "days",
        "unit": "d",
        "required": True,
        "minimum": 2,
        "maximum": 365,
        "default_count": 800,
    },
    "stock_kline_weekly_tdx": {"period": "week", "default_count": 300},
    "stock_kline_monthly_tdx": {"period": "month", "default_count": 240},
    "stock_kline_quarterly_tdx": {"period": "quarter", "default_count": 120},
    "stock_kline_yearly_tdx": {"period": "year", "default_count": 40},
}

INDEX_KLINE_INTERFACE = "index_kline_tdx"
INDEX_KLINE_PERIODS = {
    "day",
    "week",
    "month",
    "quarter",
    "year",
    "1m",
    "5m",
    "15m",
    "30m",
    "60m",
}

TDX_KLINE_MAX_COUNT = 65535


def bool_param(value: Any, *, name: str = "ascending") -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "升序"}:
        return True
    if text in {"0", "false", "no", "n", "off", "降序", ""}:
        return False
    raise SourceRequestValidationError(f"{name} must be a boolean")


def int_param(
    params: Mapping[str, Any],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int | None = None,
) -> int:
    value = params.get(name, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError(f"{name} must be an integer") from exc
    if parsed < minimum:
        raise SourceRequestValidationError(f"{name} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise SourceRequestValidationError(f"{name} must be <= {maximum}")
    return parsed


def adjust_param(value: Any) -> str:
    text = str(value or "none").strip().lower()
    allowed = {"none", "qfq", "hfq", "fixed_qfq"}
    if text not in allowed:
        raise SourceRequestValidationError(f"adjust must be one of: {', '.join(sorted(allowed))}")
    return text


def adj_factor_adjust_param(value: Any) -> str:
    text = str(value or "qfq").strip().lower()
    allowed = {"qfq", "hfq"}
    if text not in allowed:
        raise SourceRequestValidationError(f"adjust must be one of: {', '.join(sorted(allowed))}")
    return text


def anchor_date_param(params: Mapping[str, Any]) -> Any:
    if params.get("anchor_date") not in (None, ""):
        return params.get("anchor_date")
    return params.get("anchor_date_raw")


def validate_kline_anchor_date(adjust: str, anchor_date: Any) -> None:
    has_anchor_date = anchor_date not in (None, "", 0, "0")
    if adjust == "fixed_qfq" and not has_anchor_date:
        raise SourceRequestValidationError("anchor_date is required when adjust=fixed_qfq")
    if adjust != "fixed_qfq" and has_anchor_date:
        raise SourceRequestValidationError("anchor_date is only supported when adjust=fixed_qfq")


def normalize_adj_factor_anchor_date(adjust: str, anchor_date: Any) -> str | None:
    has_anchor_date = anchor_date not in (None, "", 0, "0")
    if adjust == "hfq" and has_anchor_date:
        raise SourceRequestValidationError("anchor_date is only supported when adjust=qfq")
    if not has_anchor_date:
        return None
    return normalize_optional_date_text(anchor_date, name="anchor_date")


def trade_date_param(value: Any) -> str:
    if value in (None, "", 0, "0"):
        raise SourceRequestValidationError("trade_date is required")
    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise SourceRequestValidationError("trade_date must be YYYYMMDD or YYYY-MM-DD")
    try:
        datetime.strptime(text, "%Y%m%d")
    except ValueError as exc:
        raise SourceRequestValidationError("trade_date must be a valid date") from exc
    return text


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


def kline_page_size(interface_name: str, params: Mapping[str, Any]) -> int:
    default_count = int(KLINE_INTERFACE_SPECS[interface_name].get("default_count", 800))
    return int_param(
        params,
        "count",
        default_count,
        minimum=1,
        maximum=TDX_KLINE_MAX_COUNT,
    )


def kline_period(interface_name: str, params: Mapping[str, Any]) -> str:
    spec = KLINE_INTERFACE_SPECS[interface_name]
    if spec.get("period"):
        return str(spec["period"])

    param = str(spec["param"])
    if param == "period":
        period = str(params.get(param, spec.get("default", "1m"))).strip().lower()
        allowed_periods = set(spec.get("allowed", ()))
        if period not in allowed_periods:
            allowed = ", ".join(sorted(allowed_periods))
            raise SourceRequestValidationError(f"period must be one of: {allowed}")
        return period

    if spec.get("required") and params.get(param) in (None, ""):
        raise SourceRequestValidationError(f"{param} is required")
    value = int_param(
        params,
        param,
        int(spec.get("default", 0)),
        minimum=int(spec.get("minimum", 1)),
        maximum=int(spec["maximum"]) if spec.get("maximum") is not None else None,
    )
    allowed_values = spec.get("allowed")
    if allowed_values and value not in allowed_values:
        allowed = ", ".join(str(item) for item in sorted(allowed_values))
        raise SourceRequestValidationError(f"{param} must be one of: {allowed}")
    return f"{value}{spec['unit']}"


def index_kline_period(value: Any) -> str:
    if value in (None, ""):
        return "day"
    period = str(value).strip().lower()
    aliases = {
        "daily": "day",
        "d": "day",
        "weekly": "week",
        "w": "week",
        "monthly": "month",
        "m": "month",
        "quarterly": "quarter",
        "q": "quarter",
        "yearly": "year",
        "y": "year",
        "minute": "1m",
    }
    period = aliases.get(period, period)
    if period not in INDEX_KLINE_PERIODS:
        allowed = ", ".join(sorted(INDEX_KLINE_PERIODS))
        raise SourceRequestValidationError(f"period must be one of: {allowed}")
    return period
