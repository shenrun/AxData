"""Basic quality checks for AxData tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pandas as pd

from .schema import get_schema


@dataclass(frozen=True)
class QualityIssue:
    check: str
    table: str
    message: str
    rows: int = 0


def check_primary_key_duplicates(table: str, df: "pd.DataFrame") -> List[QualityIssue]:
    schema = get_schema(table)
    pk = list(schema.primary_key)
    missing_pk = [field for field in pk if field not in df.columns]
    if missing_pk:
        fields = ", ".join(missing_pk)
        return [
            QualityIssue(
                check="primary_key_duplicates",
                table=table,
                message=f"Cannot check duplicate primary keys because field(s) are missing: {fields}.",
            )
        ]

    duplicate_mask = df.duplicated(subset=pk, keep=False)
    duplicate_rows = int(duplicate_mask.sum())
    if duplicate_rows == 0:
        return []
    pk_text = ", ".join(pk)
    return [
        QualityIssue(
            check="primary_key_duplicates",
            table=table,
            message=f"Found {duplicate_rows} row(s) with duplicate primary key ({pk_text}).",
            rows=duplicate_rows,
        )
    ]


def check_missing_required(table: str, df: "pd.DataFrame") -> List[QualityIssue]:
    schema = get_schema(table)
    issues: List[QualityIssue] = []

    for field in schema.required_fields:
        if field not in df.columns:
            issues.append(
                QualityIssue(
                    check="missing_required",
                    table=table,
                    message=f"Required field {field!r} is missing from DataFrame.",
                )
            )
            continue

        missing_rows = int(df[field].isna().sum())
        if missing_rows:
            issues.append(
                QualityIssue(
                    check="missing_required",
                    table=table,
                    message=f"Required field {field!r} has {missing_rows} missing row(s).",
                    rows=missing_rows,
                )
            )

    return issues


def validate_table(table: str, df: "pd.DataFrame") -> List[QualityIssue]:
    """Run the built-in quality checks for a table."""

    return [
        *check_missing_required(table, df),
        *check_primary_key_duplicates(table, df),
    ]
