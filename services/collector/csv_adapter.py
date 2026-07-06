"""CSV collector adapter for local development and dry-run jobs."""

from __future__ import annotations

import csv
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from services.collector.base import (
    ADJ_FACTOR,
    DAILY,
    STOCK_BASIC,
    TRADE_CAL,
    CollectorAdapter,
    FetchParams,
    Row,
    normalize_dataset,
)

DEFAULT_FILENAMES = {
    STOCK_BASIC: "stock_basic.csv",
    TRADE_CAL: "trade_cal.csv",
    DAILY: "daily.csv",
    ADJ_FACTOR: "adj_factor.csv",
}

CONTROL_PARAMS = {"path", "limit", "start_date", "end_date"}


class CsvCollectorAdapter(CollectorAdapter):
    """Read supported datasets from local CSV files.

    ``root`` can be a directory containing dataset files, or ``path`` can be
    passed per fetch call to point at a single CSV file or a dataset directory.
    """

    source = "csv"

    def __init__(
        self,
        root: str | Path | None = None,
        dataset_paths: Mapping[str, str | Path] | None = None,
        encoding: str = "utf-8-sig",
    ) -> None:
        self.root = Path(root) if root is not None else Path.cwd()
        self.dataset_paths = {
            normalize_dataset(dataset): Path(path)
            for dataset, path in (dataset_paths or {}).items()
        }
        self.encoding = encoding

    def fetch(self, dataset: str, params: FetchParams | None = None) -> list[Row]:
        dataset = normalize_dataset(dataset)
        params_dict = dict(params or {})
        csv_path = self._resolve_path(dataset, params_dict.get("path"))
        rows = self._read_csv(csv_path)
        rows = self._filter_rows(rows, params_dict)
        return self._limit_rows(rows, params_dict.get("limit"))

    def _resolve_path(self, dataset: str, override_path: Any = None) -> Path:
        candidate = Path(override_path) if override_path else self.dataset_paths.get(dataset)
        if candidate is None:
            candidate = self.root / DEFAULT_FILENAMES[dataset]

        if candidate.is_dir():
            candidate = candidate / DEFAULT_FILENAMES[dataset]

        if not candidate.exists():
            raise FileNotFoundError(f"CSV file for dataset '{dataset}' not found: {candidate}")
        if not candidate.is_file():
            raise ValueError(f"CSV path for dataset '{dataset}' is not a file: {candidate}")
        return candidate

    def _read_csv(self, path: Path) -> list[Row]:
        with path.open("r", encoding=self.encoding, newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            if reader.fieldnames is None:
                return []
            return [dict(row) for row in reader]

    def _filter_rows(self, rows: list[Row], params: dict[str, Any]) -> list[Row]:
        filters = {
            key: value
            for key, value in params.items()
            if key not in CONTROL_PARAMS and value is not None
        }
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if not filters and start_date is None and end_date is None:
            return rows

        filtered = []
        for row in rows:
            if filters and not self._matches_exact_filters(row, filters):
                continue
            if not self._matches_date_range(row, start_date, end_date):
                continue
            filtered.append(row)
        return filtered

    def _matches_exact_filters(self, row: Row, filters: dict[str, Any]) -> bool:
        return all(str(row.get(key, "")) == str(value) for key, value in filters.items())

    def _matches_date_range(self, row: Row, start_date: Any, end_date: Any) -> bool:
        if start_date is None and end_date is None:
            return True

        row_date = row.get("trade_date") or row.get("cal_date") or row.get("date")
        if row_date in (None, ""):
            return False

        row_date_text = str(row_date)
        if start_date is not None and row_date_text < str(start_date):
            return False
        if end_date is not None and row_date_text > str(end_date):
            return False
        return True

    def _limit_rows(self, rows: list[Row], limit: Any) -> list[Row]:
        if limit in (None, ""):
            return rows

        limit_int = int(limit)
        if limit_int < 0:
            raise ValueError("limit must be greater than or equal to 0")
        return rows[:limit_int]
