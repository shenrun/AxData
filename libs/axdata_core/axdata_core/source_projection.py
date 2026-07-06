"""Lightweight helpers for projecting source request records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def select_fields(
    records: Sequence[Mapping[str, Any]],
    fields: Sequence[str] | None,
) -> list[dict[str, Any]]:
    """Return plain dict records, optionally projected to selected fields."""

    selected: list[dict[str, Any]] = []
    for record in records:
        row = dict(record)
        if fields:
            row = {field: row.get(field) for field in fields}
        selected.append(row)
    return selected
