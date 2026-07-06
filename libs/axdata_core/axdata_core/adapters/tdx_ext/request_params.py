"""Parameter parsing helpers for TDX extended market requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from axdata_core.source_errors import SourceRequestValidationError


EXT_KLINE_PERIODS = {
    "5m": 0,
    "15m": 1,
    "30m": 2,
    "60m": 3,
    "day": 4,
    "week": 5,
    "month": 6,
    "1m": 7,
    "quarter": 10,
    "year": 11,
}


def asset_types_param(value: Any) -> set[str] | None:
    if value in (None, ""):
        return None
    allowed = {"futures", "option", "fund", "bond", "fx", "macro", "other"}
    aliases = {
        "期货": "futures",
        "期权": "option",
        "基金": "fund",
        "债券": "bond",
        "外汇": "fx",
        "宏观": "macro",
        "其它": "other",
    }
    result: set[str] = set()
    for raw in string_values(value):
        key = raw.strip()
        normalized = aliases.get(key, key.lower())
        if normalized not in allowed:
            raise SourceRequestValidationError(
                f"asset_type must be one of: {', '.join(sorted(allowed))}"
            )
        result.add(normalized)
    return result or None


def code_filter(value: Any) -> set[str] | None:
    if value in (None, ""):
        return None
    return {normalize_code(value) for value in string_values(value) if str(value).strip()}


def exchange_filter(value: Any) -> set[str] | None:
    if value in (None, "", "all", "ALL", "全部"):
        return None
    return {str(item).strip().upper() for item in string_values(value) if str(item).strip()}


def contains_filter(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    return tuple(str(item).strip().lower() for item in string_values(value) if str(item).strip())


def normalize_code(value: Any) -> str:
    return str(value or "").strip().upper()


def optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def limit_param(params: Mapping[str, Any], *, default: int, maximum: int) -> int:
    raw = params.get("limit", default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError("limit must be an integer") from exc
    if value <= 0:
        raise SourceRequestValidationError("limit must be > 0")
    if value > maximum:
        raise SourceRequestValidationError(f"limit must be <= {maximum}")
    return value


def period_param(value: Any, *, default: str) -> str:
    if value in (None, ""):
        return default
    key = str(value).strip().lower()
    aliases = {
        "1min": "1m",
        "5min": "5m",
        "15min": "15m",
        "30min": "30m",
        "60min": "60m",
        "1d": "day",
        "daily": "day",
        "d": "day",
        "1w": "week",
        "w": "week",
        "1mo": "month",
        "mo": "month",
        "1q": "quarter",
        "q": "quarter",
        "1y": "year",
        "y": "year",
    }
    normalized = aliases.get(key, key)
    if normalized not in EXT_KLINE_PERIODS:
        raise SourceRequestValidationError(
            "period must be one of: 1m, 5m, 15m, 30m, 60m, day, week, month, quarter, year"
        )
    return normalized


def bool_param(value: Any, *, default: bool) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    key = str(value).strip().lower()
    if key in {"1", "true", "yes", "y"}:
        return True
    if key in {"0", "false", "no", "n"}:
        return False
    raise SourceRequestValidationError("boolean param must be true or false")


def float_param(value: Any, *, default: float) -> float:
    if value in (None, ""):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError("timeout must be a number") from exc
    if result <= 0:
        raise SourceRequestValidationError("timeout must be > 0")
    return result


def required_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SourceRequestValidationError(f"{name} is required")
    return text.replace("-", "")


def string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Sequence):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]
