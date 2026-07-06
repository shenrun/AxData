"""Local cache for official exchange trading calendars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .source_request import request_interface

DEFAULT_PAST_DAYS = 180
DEFAULT_FUTURE_DAYS = 180
DEFAULT_RECHECK_PAST_DAYS = 30
DEFAULT_EXCHANGE = "SZSE"
CALENDAR_COLUMNS = ("exchange", "cal_date", "is_open", "pretrade_date", "next_trade_date")


class TradeCalendarCacheError(RuntimeError):
    """Raised when the trading calendar cache cannot be used."""


@dataclass(frozen=True)
class CalendarCoverage:
    start_date: str | None
    end_date: str | None
    row_count: int
    open_count: int

    @property
    def is_available(self) -> bool:
        return self.row_count > 0 and self.start_date is not None and self.end_date is not None


def trade_calendar_cache_path(data_root: str | Path) -> Path:
    """Return the default local calendar cache file path."""

    return Path(data_root).expanduser().resolve() / "cache" / "exchange" / "trade_calendar" / "trade_calendar.parquet"


def get_trade_calendar_cache_status(data_root: str | Path, *, today: date | None = None) -> dict[str, Any]:
    """Return local cache status without requesting upstream."""

    path = trade_calendar_cache_path(data_root)
    frame = _read_cache(path)
    coverage = _coverage(frame)
    today_text = _format_date(today or _local_today())
    today_row = _row_for_date(frame, today_text)
    return {
        "path": str(path),
        "exists": path.exists(),
        "row_count": coverage.row_count,
        "open_count": coverage.open_count,
        "start_date": coverage.start_date,
        "end_date": coverage.end_date,
        "today": today_text,
        "today_is_open": _bool_or_none(today_row.get("is_open") if today_row else None),
        "today_pretrade_date": today_row.get("pretrade_date") if today_row else None,
        "today_next_trade_date": today_row.get("next_trade_date") if today_row else None,
        "covers_today": today_row is not None,
        "updated_at": _file_updated_at(path),
    }


def refresh_trade_calendar_cache(
    data_root: str | Path,
    *,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
    past_days: int = DEFAULT_PAST_DAYS,
    future_days: int = DEFAULT_FUTURE_DAYS,
    recheck_past_days: int = DEFAULT_RECHECK_PAST_DAYS,
    today: date | None = None,
) -> dict[str, Any]:
    """Refresh local cache for the requested range and return status metadata."""

    today_value = today or _local_today()
    requested_start, requested_end = _resolve_refresh_range(
        start_date=start_date,
        end_date=end_date,
        past_days=past_days,
        future_days=future_days,
        today=today_value,
    )
    if requested_start > requested_end:
        raise TradeCalendarCacheError("start_date must be before or equal to end_date")

    cache_path = trade_calendar_cache_path(data_root)
    existing = _read_cache(cache_path)
    coverage = _coverage(existing)
    fetch_ranges = _missing_ranges(
        requested_start,
        requested_end,
        coverage,
        recheck_start=max(requested_start, today_value - timedelta(days=max(0, recheck_past_days))),
    )

    fetched_frames: list[pd.DataFrame] = []
    fetched_ranges: list[dict[str, str]] = []
    for fetch_start, fetch_end in fetch_ranges:
        records = request_interface(
            "stock_trade_calendar_exchange",
            params={"start_date": _format_date(fetch_start), "end_date": _format_date(fetch_end)},
            fields=list(CALENDAR_COLUMNS[1:]),
            persist=False,
        ).records
        fetched_ranges.append({"start_date": _format_date(fetch_start), "end_date": _format_date(fetch_end)})
        if records:
            fetched_frames.append(_records_to_frame(records, exchange=DEFAULT_EXCHANGE))

    merged = _merge_frames([existing, *fetched_frames])
    _write_cache(cache_path, merged)
    status = get_trade_calendar_cache_status(data_root, today=today_value)
    status.update(
        {
            "requested_start_date": _format_date(requested_start),
            "requested_end_date": _format_date(requested_end),
            "fetched_ranges": fetched_ranges,
            "fetched_row_count": int(sum(len(frame) for frame in fetched_frames)),
        }
    )
    return status


def ensure_trade_calendar_cache(
    data_root: str | Path,
    *,
    past_days: int = DEFAULT_PAST_DAYS,
    future_days: int = DEFAULT_FUTURE_DAYS,
    monthly_recheck_past_days: int = DEFAULT_RECHECK_PAST_DAYS,
    today: date | None = None,
) -> dict[str, Any]:
    """Ensure the default rolling range exists, with monthly recent rechecks."""

    today_value = today or _local_today()
    recheck_past_days = monthly_recheck_past_days if today_value.day == 1 else 0
    status = refresh_trade_calendar_cache(
        data_root,
        past_days=past_days,
        future_days=future_days,
        recheck_past_days=recheck_past_days,
        today=today_value,
    )
    status["maintenance_mode"] = "monthly_recheck" if today_value.day == 1 else "startup_gap_check"
    return status


def check_trade_calendar_cache(
    data_root: str | Path,
    *,
    start_date: str | date,
    end_date: str | date | None = None,
) -> dict[str, Any]:
    """Check whether local cache covers a requested date range."""

    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date if end_date is not None else start_date, "end_date")
    if start > end:
        raise TradeCalendarCacheError("start_date must be before or equal to end_date")

    path = trade_calendar_cache_path(data_root)
    frame = _read_cache(path)
    coverage = _coverage(frame)
    start_text = _format_date(start)
    end_text = _format_date(end)
    missing_dates = _missing_dates(frame, start, end)
    return {
        "path": str(path),
        "exists": path.exists(),
        "start_date": start_text,
        "end_date": end_text,
        "is_available": not missing_dates,
        "missing_count": len(missing_dates),
        "missing_dates": missing_dates[:20],
        "cache_start_date": coverage.start_date,
        "cache_end_date": coverage.end_date,
        "row_count": coverage.row_count,
    }


def update_trade_calendar_cache_from_records(
    data_root: str | Path,
    records: Iterable[dict[str, Any]],
    *,
    exchange: str = DEFAULT_EXCHANGE,
    today: date | None = None,
) -> dict[str, Any]:
    """Merge already-fetched trading calendar rows into the local cache."""

    cache_path = trade_calendar_cache_path(data_root)
    existing = _read_cache(cache_path)
    frame = _records_to_frame([dict(record) for record in records], exchange=exchange)
    merged = _merge_frames([existing, frame])
    _write_cache(cache_path, merged)
    status = get_trade_calendar_cache_status(data_root, today=today)
    status.update({"merged_row_count": int(len(frame))})
    return status


def _resolve_refresh_range(
    *,
    start_date: str | date | None,
    end_date: str | date | None,
    past_days: int,
    future_days: int,
    today: date,
) -> tuple[date, date]:
    if start_date is not None or end_date is not None:
        start = _parse_date(start_date if start_date is not None else end_date, "start_date")
        end = _parse_date(end_date if end_date is not None else start_date, "end_date")
        return start, end
    return today - timedelta(days=max(0, past_days)), today + timedelta(days=max(0, future_days))


def _missing_ranges(
    start: date,
    end: date,
    coverage: CalendarCoverage,
    *,
    recheck_start: date,
) -> list[tuple[date, date]]:
    if not coverage.is_available:
        return [(start, end)]

    ranges: list[tuple[date, date]] = []
    cache_start = _parse_date(coverage.start_date, "cache_start_date")
    cache_end = _parse_date(coverage.end_date, "cache_end_date")
    if start < cache_start:
        ranges.append((start, min(end, cache_start - timedelta(days=1))))
    if end > cache_end:
        ranges.append((max(start, cache_end + timedelta(days=1)), end))
    refresh_start = max(start, recheck_start)
    refresh_end = min(end, cache_end)
    if refresh_start <= refresh_end:
        ranges.append((refresh_start, refresh_end))
    return _merge_ranges(ranges)


def _merge_ranges(ranges: Iterable[tuple[date, date]]) -> list[tuple[date, date]]:
    normalized = sorted((start, end) for start, end in ranges if start <= end)
    merged: list[tuple[date, date]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1] + timedelta(days=1):
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _read_cache(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=CALENDAR_COLUMNS)
    frame = pd.read_parquet(path)
    return _normalize_frame(frame)


def _write_cache(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _normalize_frame(frame).to_parquet(path, engine="pyarrow", index=False)


def _records_to_frame(records: list[dict[str, Any]], *, exchange: str) -> pd.DataFrame:
    rows = []
    for record in records:
        rows.append(
            {
                "exchange": exchange,
                "cal_date": _normalize_date_text(record.get("cal_date")),
                "is_open": bool(record.get("is_open")),
                "pretrade_date": _normalize_date_text(record.get("pretrade_date")),
                "next_trade_date": _normalize_date_text(record.get("next_trade_date")),
            }
        )
    return _normalize_frame(pd.DataFrame.from_records(rows))


def _merge_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    non_empty = [_normalize_frame(frame) for frame in frames if frame is not None and not frame.empty]
    if not non_empty:
        return pd.DataFrame(columns=CALENDAR_COLUMNS)
    merged = pd.concat(non_empty, ignore_index=True)
    merged = _normalize_frame(merged)
    return merged.drop_duplicates(subset=["exchange", "cal_date"], keep="last").sort_values(["exchange", "cal_date"])


def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=CALENDAR_COLUMNS)
    normalized = frame.copy()
    for column in CALENDAR_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None
    normalized = normalized.loc[:, list(CALENDAR_COLUMNS)]
    normalized["exchange"] = normalized["exchange"].fillna(DEFAULT_EXCHANGE).astype(str)
    normalized["cal_date"] = normalized["cal_date"].map(_normalize_date_text)
    normalized["pretrade_date"] = normalized["pretrade_date"].map(_normalize_date_text)
    normalized["next_trade_date"] = normalized["next_trade_date"].map(_normalize_date_text)
    normalized["is_open"] = normalized["is_open"].map(_normalize_bool)
    normalized = normalized[normalized["cal_date"].notna()]
    return normalized


def _coverage(frame: pd.DataFrame) -> CalendarCoverage:
    if frame.empty:
        return CalendarCoverage(start_date=None, end_date=None, row_count=0, open_count=0)
    dates = sorted(str(item) for item in frame["cal_date"].dropna().unique())
    return CalendarCoverage(
        start_date=dates[0] if dates else None,
        end_date=dates[-1] if dates else None,
        row_count=len(frame),
        open_count=int(frame["is_open"].sum()) if "is_open" in frame.columns else 0,
    )


def _row_for_date(frame: pd.DataFrame, cal_date: str) -> dict[str, Any] | None:
    if frame.empty:
        return None
    matches = frame[frame["cal_date"] == cal_date]
    if matches.empty:
        return None
    return matches.iloc[-1].to_dict()


def _missing_dates(frame: pd.DataFrame, start: date, end: date) -> list[str]:
    available = set(str(item) for item in frame["cal_date"].dropna()) if not frame.empty else set()
    missing: list[str] = []
    current = start
    while current <= end:
        text = _format_date(current)
        if text not in available:
            missing.append(text)
        current += timedelta(days=1)
    return missing


def _covers(coverage: CalendarCoverage, start_date: str, end_date: str) -> bool:
    return bool(
        coverage.start_date
        and coverage.end_date
        and coverage.start_date <= start_date
        and coverage.end_date >= end_date
    )


def _parse_date(value: str | date | None, field_name: str) -> date:
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 8:
        raise TradeCalendarCacheError(f"{field_name} must be YYYYMMDD or YYYY-MM-DD")
    try:
        return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
    except ValueError as exc:
        raise TradeCalendarCacheError(f"{field_name} is not a valid date") from exc


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _normalize_date_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits[:8] if len(digits) >= 8 else None


def _local_today() -> date:
    return datetime.now().astimezone().date()


def _file_updated_at(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "open"}:
        return True
    if text in {"0", "false", "no", "n", "closed", ""}:
        return False
    return bool(value)
