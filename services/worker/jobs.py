"""Collection worker job definitions."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from services.collector import (
    ADJ_FACTOR,
    DAILY,
    STOCK_BASIC,
    TRADE_CAL,
    CollectorAdapter,
    CsvCollectorAdapter,
    OfficialExchangeStockBasicAdapter,
    Row,
    normalize_dataset,
)
from services.worker.models import TaskState


@dataclass(frozen=True)
class JobDefinition:
    name: str
    dataset: str


@dataclass
class JobResult:
    state: TaskState
    rows: list[Row]
    dry_run: bool = True


JOB_DEFINITIONS = {
    "update_stock_basic": JobDefinition("update_stock_basic", STOCK_BASIC),
    "update_stock_basic_exchange": JobDefinition("update_stock_basic_exchange", STOCK_BASIC),
    "update_trade_cal": JobDefinition("update_trade_cal", TRADE_CAL),
    "update_daily": JobDefinition("update_daily", DAILY),
    "update_adj_factor": JobDefinition("update_adj_factor", ADJ_FACTOR),
}

OFFICIAL_EXCHANGE_SOURCES = {"official_exchange", "official", "exchange"}

STOCK_BASIC_EXCHANGE_SUFFIXES = {
    "SSE": ".SH",
    "SZSE": ".SZ",
    "BSE": ".BJ",
}

STOCK_BASIC_EXCHANGE_ALIASES = {
    "SH": "SSE",
    "SSE": "SSE",
    "上海": "SSE",
    "上交所": "SSE",
    "SZ": "SZSE",
    "SZSE": "SZSE",
    "深圳": "SZSE",
    "深交所": "SZSE",
    "BJ": "BSE",
    "BSE": "BSE",
    "北京": "BSE",
    "北交所": "BSE",
}

STOCK_BASIC_MIN_ROWS_BY_EXCHANGE = {
    "SSE": 1000,
    "SZSE": 1500,
    "BSE": 200,
}

STOCK_BASIC_MIN_EXISTING_RATIO = 0.9


def create_adapter(source: str, path: str | Path | None = None) -> CollectorAdapter:
    source_name = source.strip().lower()
    if source_name == "csv":
        return CsvCollectorAdapter(root=path)
    if source_name in OFFICIAL_EXCHANGE_SOURCES:
        return OfficialExchangeStockBasicAdapter()
    raise ValueError(
        f"Unsupported source '{source}'. Expected one of: csv, official_exchange"
    )


def run_update_job(
    dataset: str,
    *,
    source: str = "csv",
    path: str | Path | None = None,
    data_root: str | Path | None = None,
    dry_run: bool = True,
    batch_id: str | None = None,
    params: dict[str, Any] | None = None,
    adapter: CollectorAdapter | None = None,
) -> JobResult:
    dataset_name = normalize_dataset(dataset)
    task_state = TaskState(
        batch_id=batch_id or str(uuid4()),
        source=source,
        dataset=dataset_name,
    )
    task_state.mark_running()

    try:
        fetch_params = dict(params or {})
        if path is not None:
            fetch_params["path"] = path
        fetch_params.setdefault("batch_id", task_state.batch_id)

        collector = adapter or create_adapter(source, path)
        rows = collector.fetch(dataset_name, fetch_params)
        if not dry_run:
            persist_rows(
                dataset_name,
                rows,
                data_root=data_root,
                source=source,
                params=fetch_params,
            )
        task_state.mark_finished(len(rows), status="dry_run" if dry_run else "success")
        return JobResult(state=task_state, rows=rows, dry_run=dry_run)
    except Exception as exc:
        task_state.mark_failed(exc)
        return JobResult(state=task_state, rows=[], dry_run=dry_run)


def persist_rows(
    dataset: str,
    rows: list[Row],
    *,
    data_root: str | Path | None = None,
    source: str | None = None,
    params: dict[str, Any] | None = None,
) -> Path:
    """Persist fetched rows into the canonical core Parquet table."""

    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError("Worker persistence requires pandas. Install it with `pip install pandas`.") from exc

    from axdata_core import get_schema, read_core_table, validate_table, write_core_table

    root = Path(data_root or os.getenv("AXDATA_DATA_DIR", "data"))
    df = pd.DataFrame.from_records(rows)
    schema = get_schema(dataset)
    for field in schema.fields:
        if field.name not in df.columns:
            continue
        if field.dtype in {"float64", "float", "double"}:
            df[field.name] = pd.to_numeric(df[field.name], errors="coerce")
        elif field.dtype in {"int64", "int", "integer"}:
            df[field.name] = pd.to_numeric(df[field.name], errors="coerce").astype("Int64")
    schema_columns = [field for field in schema.field_names if field in df.columns]
    df = df[schema_columns]

    if _is_official_stock_basic(dataset, source):
        _validate_official_stock_basic_fetch(df, params=params or {})

    if _is_official_stock_basic(dataset, source):
        df = _merge_stock_basic_snapshot(df, root=root, read_core_table=read_core_table)

    issues = validate_table(dataset, df)
    if issues:
        messages = "; ".join(issue.message for issue in issues)
        raise ValueError(f"Quality checks failed for {dataset}: {messages}")
    return write_core_table(dataset, df, root=root)


def _is_official_stock_basic(dataset: str, source: str | None) -> bool:
    return dataset == STOCK_BASIC and (source or "").strip().lower() in OFFICIAL_EXCHANGE_SOURCES


def _validate_official_stock_basic_fetch(df: "pd.DataFrame", *, params: dict[str, Any]) -> None:
    if params.get("limit") not in (None, ""):
        raise ValueError(
            "Refusing to persist limited official stock_basic_exchange data. "
            "Use dry-run for previews, or run without --limit to collect a complete exchange list."
        )

    if df.empty:
        raise ValueError("Refusing to persist empty official stock_basic_exchange data.")

    if "exchange" not in df.columns or "instrument_id" not in df.columns:
        raise ValueError("Official stock_basic_exchange data must include exchange and instrument_id.")

    expected_exchanges = _parse_expected_stock_basic_exchanges(params)
    actual_exchanges = set(df["exchange"].dropna().astype(str))
    missing_exchanges = expected_exchanges - actual_exchanges
    if missing_exchanges:
        missing = ", ".join(sorted(missing_exchanges))
        raise ValueError(f"Official stock_basic_exchange data is missing expected exchange(s): {missing}.")

    unexpected_exchanges = actual_exchanges - set(STOCK_BASIC_EXCHANGE_SUFFIXES)
    if unexpected_exchanges:
        unexpected = ", ".join(sorted(unexpected_exchanges))
        raise ValueError(f"Official stock_basic_exchange data contains unsupported exchange(s): {unexpected}.")

    for exchange in sorted(actual_exchanges):
        suffix = STOCK_BASIC_EXCHANGE_SUFFIXES[exchange]
        exchange_rows = df[df["exchange"] == exchange]
        bad_suffix_rows = ~exchange_rows["instrument_id"].astype(str).str.endswith(suffix)
        bad_count = int(bad_suffix_rows.sum())
        if bad_count:
            raise ValueError(
                f"Official stock_basic_exchange data has {bad_count} {exchange} row(s) "
                f"without instrument_id suffix {suffix}."
            )

        min_rows = STOCK_BASIC_MIN_ROWS_BY_EXCHANGE[exchange]
        row_count = len(exchange_rows)
        if row_count < min_rows:
            raise ValueError(
                f"Official stock_basic_exchange data for {exchange} has only {row_count} row(s); "
                f"expected at least {min_rows}. Refusing to overwrite core data."
            )

    if "asset_type" in df.columns:
        non_stock_rows = int((df["asset_type"].dropna().astype(str) != "stock").sum())
        if non_stock_rows:
            raise ValueError(
                f"Official stock_basic_exchange data has {non_stock_rows} row(s) whose asset_type is not stock."
            )


def _parse_expected_stock_basic_exchanges(params: dict[str, Any]) -> set[str]:
    value = params.get("exchanges", params.get("exchange"))
    if value in (None, ""):
        parts = ("SSE", "SZSE", "BSE")
    elif isinstance(value, str):
        parts = re.split(r"[,，\s]+", value)
    elif isinstance(value, (list, tuple, set)):
        parts = value
    else:
        parts = (value,)

    exchanges: set[str] = set()
    for part in parts:
        text = str(part).strip()
        if not text:
            continue
        normalized = STOCK_BASIC_EXCHANGE_ALIASES.get(
            text.upper(),
            STOCK_BASIC_EXCHANGE_ALIASES.get(text),
        )
        if normalized is None:
            raise ValueError(
                f"Unsupported exchange {text!r}. Expected one of: SSE, SZSE, BSE."
            )
        exchanges.add(normalized)
    return exchanges or {"SSE", "SZSE", "BSE"}


def _merge_stock_basic_snapshot(
    df: "pd.DataFrame",
    *,
    root: Path,
    read_core_table: Any,
) -> "pd.DataFrame":
    import pandas as pd

    if df.empty or "exchange" not in df.columns:
        return df

    exchanges = set(df["exchange"].dropna().astype(str))
    try:
        existing = read_core_table(STOCK_BASIC, root=root)
    except FileNotFoundError:
        return df

    if existing.empty or "exchange" not in existing.columns:
        return df

    _check_stock_basic_existing_counts(df, existing, exchanges=exchanges)
    remaining = existing[~existing["exchange"].astype(str).isin(exchanges)]
    if remaining.empty:
        return df

    combined = pd.concat([remaining, df], ignore_index=True)
    return combined


def _check_stock_basic_existing_counts(
    df: "pd.DataFrame",
    existing: "pd.DataFrame",
    *,
    exchanges: set[str],
) -> None:
    for exchange in sorted(exchanges):
        old_count = int((existing["exchange"].astype(str) == exchange).sum())
        if old_count == 0:
            continue
        new_count = int((df["exchange"].astype(str) == exchange).sum())
        min_allowed = int(old_count * STOCK_BASIC_MIN_EXISTING_RATIO)
        if new_count < min_allowed:
            raise ValueError(
                f"Official stock_basic_exchange data for {exchange} dropped from {old_count} "
                f"to {new_count} row(s). Refusing to overwrite existing core data."
            )


def update_stock_basic(**kwargs: Any) -> JobResult:
    return run_update_job(STOCK_BASIC, **kwargs)


def update_stock_basic_exchange(**kwargs: Any) -> JobResult:
    return run_update_job(STOCK_BASIC, **kwargs)


def update_trade_cal(**kwargs: Any) -> JobResult:
    return run_update_job(TRADE_CAL, **kwargs)


def update_daily(**kwargs: Any) -> JobResult:
    return run_update_job(DAILY, **kwargs)


def update_adj_factor(**kwargs: Any) -> JobResult:
    return run_update_job(ADJ_FACTOR, **kwargs)
