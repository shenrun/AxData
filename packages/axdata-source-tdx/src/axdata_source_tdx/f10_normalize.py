"""TDX F10 value normalization helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .tdx_f10_models import F10FieldSpec


def f10_first_text(row: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = row.get(key)
        if is_empty_f10_value(value):
            continue
        return str(value)
    return None


def f10_first_value(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if is_empty_f10_value(value):
            continue
        return value
    return None


def f10_identifier_text(value: Any) -> str | None:
    if is_empty_f10_value(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def f10_market_from_market_code(value: Any) -> str | None:
    if is_empty_f10_value(value):
        return None
    text = str(value).strip()
    return {"0": "sz", "1": "sh", "2": "bj"}.get(text)


def scale_f10_hundred(value: Any) -> float | None:
    number = f10_number(value, integer=False)
    if number is None:
        return None
    return round(number / 100, 6)


def f10_field_value(
    field: F10FieldSpec,
    row: Mapping[str, Any],
    context: Mapping[str, Any],
    meta: Mapping[str, Any],
) -> Any:
    source = field.source
    if source is None:
        return None
    if isinstance(source, tuple):
        for item in source:
            value = f10_source_value(item, row, context, meta)
            if value not in (None, ""):
                return normalize_f10_value(value, field)
        return None
    value = f10_source_value(source, row, context, meta)
    return normalize_f10_value(value, field)


def f10_source_value(source: str, row: Mapping[str, Any], context: Mapping[str, Any], meta: Mapping[str, Any]) -> Any:
    if source.startswith("{") and source.endswith("}"):
        return context.get(source[1:-1])
    if source in row:
        return row.get(source)
    return meta.get(source)


def normalize_f10_value(value: Any, field: F10FieldSpec) -> Any:
    if is_empty_f10_value(value):
        return None
    if field.dtype.startswith("date") and value is not None:
        return f10_date_text(value)
    if field.dtype in {"number", "integer"}:
        return f10_number(value, integer=field.dtype == "integer")
    if field.dtype == "boolean":
        return bool(value)
    return value


def normalize_f10_plain_text(value: Any) -> str | None:
    if is_empty_f10_value(value):
        return None
    return str(value)


def is_empty_f10_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        return text in {"", "--", "-"} or text.lower() in {"none", "null"}
    return False


def f10_date_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    if len(digits) == 6:
        return digits
    if len(digits) == 4:
        return digits
    return text


def f10_number(value: Any, *, integer: bool) -> int | float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value) if integer else float(value)
    text = str(value).strip().replace(",", "")
    text = re.sub(r"[#].*$", "", text)
    text = text.replace("%", "")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if integer else number


def f10_page(cursor: Any) -> int:
    if cursor in (None, ""):
        return 1
    text = str(cursor).strip()
    if text.isdigit():
        return max(1, int(text))
    return 1


def f10_rating_code(value: Any) -> str:
    text = str(value or "all").strip().lower()
    return {
        "all": "0",
        "全部": "0",
        "buy": "5",
        "买入": "5",
        "overweight": "4",
        "增持": "4",
        "neutral": "3",
        "中性": "3",
        "underweight": "2",
        "减持": "2",
        "sell": "1",
        "卖出": "1",
    }.get(text, "0")


def date_dash(value: str | None) -> str:
    if not value:
        return ""
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return value
