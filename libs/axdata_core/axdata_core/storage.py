"""Parquet storage helpers for AxData core tables."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .paths import AxDataPaths
from .schema import get_schema, normalize_table_name

if TYPE_CHECKING:
    import pandas as pd


def _require_pyarrow() -> None:
    try:
        import pyarrow  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Parquet support requires pyarrow. Install it with "
            "`pip install pyarrow` or `pip install axdata-core[parquet]`."
        ) from exc


def core_table_path(table: str, root: str | Path) -> Path:
    table_name = normalize_table_name(table)
    get_schema(table_name)
    return AxDataPaths(root).table_path("core", table_name)


def core_table_partition_path(table: str, root: str | Path) -> Path:
    table_name = normalize_table_name(table)
    get_schema(table_name)
    return AxDataPaths(root).core / f"table={table_name}"


def core_table_parquet_roots(table: str, root: str | Path) -> tuple[Path, ...]:
    table_name = normalize_table_name(table)
    get_schema(table_name)
    partition_path = AxDataPaths(root).core / f"table={table_name}"
    return (partition_path, partition_path / "parquet")


def core_table_files(table: str, root: str | Path) -> tuple[Path, ...]:
    """Return parquet files for a core table.

    The current implementation writes compact tables to `core/{table}.parquet`.
    The architecture also reserves date-sharded layouts such as
    `core/table=daily/parquet/YYYYMMDD.parquet`. Older partition directories
    such as `core/table=daily/parquet/trade_date=YYYYMMDD/*.parquet` are still
    readable so local data survives storage layout evolution.
    """

    file_path = core_table_path(table, root)
    if file_path.exists():
        return (file_path,)

    first_existing_root: Path | None = None
    for partition_path in core_table_parquet_roots(table, root):
        if not partition_path.exists():
            continue
        first_existing_root = first_existing_root or partition_path
        files = tuple(sorted(path for path in partition_path.rglob("*.parquet") if path.is_file()))
        if files:
            return files
    if first_existing_root is not None:
        raise FileNotFoundError(f"Core table partition directory has no parquet files: {first_existing_root}")

    partition_path = core_table_partition_path(table, root)
    raise FileNotFoundError(
        f"Core table parquet does not exist: {file_path} or {partition_path}"
    )


def core_table_read_path(table: str, root: str | Path) -> str:
    """Return the best pandas/pyarrow readable root path for a core table."""

    files = core_table_files(table, root)
    single_file_path = core_table_path(table, root)
    if len(files) == 1 and files[0] == single_file_path:
        return str(single_file_path)
    return str(_partition_root_for_files(table, root, files))


def core_table_duckdb_path(table: str, root: str | Path) -> str:
    """Return the best DuckDB read_parquet path for a core table."""

    file_path = core_table_path(table, root)
    if file_path.exists():
        return str(file_path)

    for partition_path in core_table_parquet_roots(table, root):
        if partition_path.exists():
            return str(partition_path / "**" / "*.parquet")

    raise FileNotFoundError(
        f"Core table parquet does not exist: {file_path} or {core_table_partition_path(table, root)}"
    )


def _partition_values(file_path: Path, partition_root: Path) -> dict[str, str]:
    try:
        relative_parts = file_path.relative_to(partition_root).parts[:-1]
    except ValueError:
        return {}

    values: dict[str, str] = {}
    for part in relative_parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key:
            values[key] = value
    return values


def _normalize_partition_value(table: str, field: str, value: str) -> str:
    schema = get_schema(table)
    if field == schema.date_field:
        return value.replace("-", "")
    return value


def read_core_table(table: str, root: str | Path, **kwargs: object) -> "pd.DataFrame":
    """Read a core table parquet file or partition directory into a pandas DataFrame."""

    _require_pyarrow()
    import pandas as pd

    files = core_table_files(table, root)
    single_file_path = core_table_path(table, root)
    if len(files) == 1 and files[0] == single_file_path:
        return pd.read_parquet(single_file_path, engine="pyarrow", **kwargs)

    schema = get_schema(table)
    partition_path = _partition_root_for_files(table, root, files)
    frames = []
    for file_path in files:
        frame = pd.read_parquet(file_path, engine="pyarrow", **kwargs)
        partition_values = _partition_values(file_path, partition_path)
        for field, value in partition_values.items():
            if field in schema.field_names and field not in frame.columns:
                frame[field] = _normalize_partition_value(table, field, value)
        frames.append(frame)

    result = pd.concat(frames, ignore_index=True)
    schema_columns = [field for field in schema.field_names if field in result.columns]
    extra_columns = [field for field in result.columns if field not in schema_columns]
    return result[schema_columns + extra_columns]


def _partition_root_for_files(table: str, root: str | Path, files: tuple[Path, ...]) -> Path:
    for candidate in core_table_parquet_roots(table, root):
        try:
            if all(file_path.is_relative_to(candidate) for file_path in files):
                return candidate
        except AttributeError:  # pragma: no cover - Python < 3.9 compatibility
            try:
                if all(file_path.relative_to(candidate) for file_path in files):
                    return candidate
            except ValueError:
                continue
            return candidate
    return core_table_partition_path(table, root)


def write_core_table(
    table: str,
    df: "pd.DataFrame",
    root: str | Path,
    *,
    index: bool = False,
    create_dirs: bool = True,
    **kwargs: object,
) -> Path:
    """Write a pandas DataFrame to the canonical core parquet path."""

    _require_pyarrow()
    schema = get_schema(table)
    schema_columns = [field for field in schema.field_names if field in df.columns]
    df = df[schema_columns]
    path = core_table_path(table, root)
    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", index=index, **kwargs)
    return path
