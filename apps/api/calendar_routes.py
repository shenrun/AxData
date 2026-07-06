from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import data_root, load_trade_calendar_maintenance_config, save_trade_calendar_maintenance_config
from .models import TradeCalendarMaintenanceUpdateRequest
from .serialization import error_payload, response_payload, to_jsonable


router = APIRouter()


class CalendarRefreshRequest(BaseModel):
    start_date: str | None = Field(default=None, description="Start date, YYYYMMDD or YYYY-MM-DD.")
    end_date: str | None = Field(default=None, description="End date, YYYYMMDD or YYYY-MM-DD.")
    past_days: int = Field(default=180, ge=0, le=3650, description="Default days before today to cover.")
    future_days: int = Field(default=180, ge=0, le=3650, description="Default days after today to cover.")
    recheck_past_days: int = Field(default=30, ge=0, le=3650, description="Recent days to refresh again.")


class CalendarCheckRequest(BaseModel):
    start_date: str = Field(description="Start date, YYYYMMDD or YYYY-MM-DD.")
    end_date: str | None = Field(default=None, description="End date, YYYYMMDD or YYYY-MM-DD.")


@router.get("/v1/trade-calendar/cache")
def get_trade_calendar_cache() -> JSONResponse:
    try:
        from axdata_core import get_trade_calendar_cache_status

        status_data = get_trade_calendar_cache_status(data_root())
    except Exception as exc:  # pragma: no cover - defensive API boundary
        return _calendar_error("TRADE_CALENDAR_CACHE_ERROR", exc)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(status_data)))


@router.post("/v1/trade-calendar/cache/refresh")
def refresh_calendar_cache(request: CalendarRefreshRequest) -> JSONResponse:
    try:
        from axdata_core import refresh_trade_calendar_cache

        status_data = refresh_trade_calendar_cache(
            data_root(),
            start_date=request.start_date,
            end_date=request.end_date,
            past_days=request.past_days,
            future_days=request.future_days,
            recheck_past_days=request.recheck_past_days,
        )
    except Exception as exc:
        return _calendar_error("TRADE_CALENDAR_REFRESH_FAILED", exc)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(status_data)))


@router.post("/v1/trade-calendar/cache/check")
def check_calendar_cache(request: CalendarCheckRequest) -> JSONResponse:
    try:
        from axdata_core import check_trade_calendar_cache

        status_data = check_trade_calendar_cache(data_root(), start_date=request.start_date, end_date=request.end_date)
    except Exception as exc:
        return _calendar_error("TRADE_CALENDAR_CHECK_FAILED", exc)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(status_data)))


@router.get("/v1/trade-calendar/maintenance")
def get_trade_calendar_maintenance() -> JSONResponse:
    try:
        config = load_trade_calendar_maintenance_config()
    except Exception as exc:  # pragma: no cover - defensive API boundary
        return _calendar_error("TRADE_CALENDAR_MAINTENANCE_ERROR", exc)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(config)))


@router.put("/v1/trade-calendar/maintenance")
def update_trade_calendar_maintenance(request: TradeCalendarMaintenanceUpdateRequest) -> JSONResponse:
    try:
        payload = request.model_dump()
        _validate_maintenance_time(payload["time"])
        path = save_trade_calendar_maintenance_config(payload)
        config = load_trade_calendar_maintenance_config()
        config["path"] = str(path)
    except Exception as exc:
        return _calendar_error("TRADE_CALENDAR_MAINTENANCE_SAVE_FAILED", exc)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(config)))


def _validate_maintenance_time(value: str) -> None:
    hour_text, minute_text = value.split(":", 1)
    hour = int(hour_text)
    minute = int(minute_text)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("time must be a valid HH:MM value.")


def _calendar_error(code: str, exc: Exception) -> JSONResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    if type(exc).__name__ in {"SourceUnavailableError", "SourceAdapterError"}:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    payload = error_payload(code, str(exc), error_type=type(exc).__name__)
    return JSONResponse(status_code=status_code, content=to_jsonable(payload))
