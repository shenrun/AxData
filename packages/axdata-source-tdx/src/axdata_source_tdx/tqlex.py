"""TDX 7615 TQLEX HTTP helpers.

This module is intentionally small and source-facing. Product interfaces map
the parsed tables to AxData fields in the request adapter.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_TQLEX_URL = "http://static.tdx.com.cn:7615/TQLEX"


@dataclass(frozen=True)
class TqlexTable:
    """One table parsed from a 7615 JSON response."""

    key: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]


class TdxTqlexClient:
    """Minimal request-level client for TDX 7615 data pages."""

    def __init__(self, *, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or os.getenv("AXDATA_TDX_TQLEX_URL") or DEFAULT_TQLEX_URL).rstrip("?")
        self.timeout = timeout if timeout is not None else _env_float("AXDATA_TDX_TQLEX_TIMEOUT", 10.0)

    def request(self, entry: str, body: Any) -> dict[str, Any]:
        """POST one request and return decoded JSON."""

        entry_text = str(entry or "").strip()
        if not entry_text:
            raise ValueError("entry is required")
        separator = "&" if "?" in self.base_url else "?"
        url = f"{self.base_url}{separator}{urlencode({'Entry': entry_text})}"
        payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "User-Agent": "Mozilla/5.0 AxData/0.1",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            raw = response.read()
        text = raw.decode("utf-8-sig")
        decoded = json.loads(text)
        if not isinstance(decoded, dict):
            raise ValueError("TQLEX response must be a JSON object")
        return decoded


def parse_tqlex_tables(payload: dict[str, Any]) -> tuple[TqlexTable, ...]:
    """Parse TQLEX ResultSets into row dictionaries.

    Duplicate source column names are preserved by suffixing later occurrences
    with ``__{index}``, while the first occurrence keeps the original name.
    """

    error_code = payload.get("ErrorCode", 0)
    if error_code not in (0, "0", None):
        raise ValueError(f"TQLEX response ErrorCode={error_code}")

    result_sets = payload.get("ResultSets") or []
    if not isinstance(result_sets, list):
        raise ValueError("TQLEX ResultSets must be a list")

    tables: list[TqlexTable] = []
    for table_index, result_set in enumerate(result_sets):
        if not isinstance(result_set, dict):
            continue
        columns = _result_set_columns(result_set)
        unique_columns = _unique_columns(columns)
        content = result_set.get("Content") or []
        rows: list[dict[str, Any]] = []
        if isinstance(content, list):
            for raw_row in content:
                if isinstance(raw_row, dict):
                    rows.append(dict(raw_row))
                    continue
                if not isinstance(raw_row, list):
                    continue
                row = {
                    unique_columns[index]: raw_row[index] if index < len(raw_row) else None
                    for index in range(len(unique_columns))
                }
                rows.append(row)
        key = str(result_set.get("ResultSetKey") or f"table{table_index}")
        tables.append(TqlexTable(key=key, columns=tuple(unique_columns), rows=tuple(rows)))
    return tuple(tables)


def _result_set_columns(result_set: dict[str, Any]) -> list[str]:
    col_name = result_set.get("ColName")
    if isinstance(col_name, list):
        return [str(name) for name in col_name]
    col_des = result_set.get("ColDes")
    if isinstance(col_des, list):
        names: list[str] = []
        for item in col_des:
            if isinstance(item, dict):
                names.append(str(item.get("Name") or item.get("name") or ""))
            else:
                names.append(str(item))
        return names
    return []


def _unique_columns(columns: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique: list[str] = []
    for index, column in enumerate(columns):
        name = column or f"column_{index}"
        count = seen.get(name, 0)
        seen[name] = count + 1
        unique.append(name if count == 0 else f"{name}__{index}")
    return unique


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default
