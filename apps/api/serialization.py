from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def parse_fields(fields: str | list[str] | tuple[str, ...] | None) -> list[str] | None:
    if fields in (None, ""):
        return None
    if isinstance(fields, str):
        return [field.strip() for field in fields.split(",") if field.strip()]
    return [str(field).strip() for field in fields if str(field).strip()]


def normalize_date_text(value: Any) -> Any:
    if isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-":
        return value.replace("-", "")
    return value


def normalize_param_value(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_date_text(value)
    if isinstance(value, tuple):
        return tuple(normalize_param_value(item) for item in value)
    if isinstance(value, list):
        return [normalize_param_value(item) for item in value]
    if isinstance(value, set | frozenset):
        return [normalize_param_value(item) for item in value]
    return value


def pop_date_params(params: dict[str, Any]) -> tuple[str | None, str | None]:
    start_date = params.pop("start_date", None) or params.pop("start", None)
    end_date = params.pop("end_date", None) or params.pop("end", None)
    return normalize_date_text(start_date), normalize_date_text(end_date)


def normalize_filters(params: dict[str, Any], filters: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = {
        str(key): normalize_param_value(value)
        for key, value in (filters or {}).items()
        if value is not None
    }
    for key, value in params.items():
        if value is not None:
            normalized[str(key)] = normalize_param_value(value)
    return normalized


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, str | bool):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, int):
        return value

    if isinstance(value, Decimal):
        return float(value) if value.is_finite() else None

    if isinstance(value, datetime | date):
        return value.isoformat()

    if hasattr(value, "item") and callable(value.item):
        try:
            return to_jsonable(value.item())
        except (TypeError, ValueError):
            pass

    if hasattr(value, "to_dict"):
        try:
            return to_jsonable(value.to_dict(orient="records"))
        except TypeError:
            return to_jsonable(value.to_dict())

    if is_dataclass(value):
        return to_jsonable(asdict(value))

    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}

    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]

    if isinstance(value, list):
        return [to_jsonable(item) for item in value]

    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())

    return value


def response_payload(data: Any, **metadata: Any) -> dict[str, Any]:
    json_data = to_jsonable(data)
    payload = {"success": True, "data": json_data}
    meta = {key: value for key, value in metadata.items() if value is not None}
    if meta:
        payload["meta"] = meta
    return payload


def error_payload(code: str, message: str, **metadata: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "error": {"code": code, "message": message},
        "data": None,
    }
    meta = {key: value for key, value in metadata.items() if value is not None}
    if meta:
        payload["meta"] = meta
    return payload
