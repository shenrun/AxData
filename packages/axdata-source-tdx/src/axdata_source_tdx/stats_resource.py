"""TDX local statistics resource parser for auction-derived indicators."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from .stats_cache import (
    DEFAULT_TDX_STATS_META_PATH,
    DEFAULT_TDX_STATS_RESOURCE_PATH,
    SHANGHAI_TZ,
    build_stats_metadata as _cache_build_stats_metadata,
    default_tdx_stats_cache_root,
    default_tdx_stats_metadata_path,
    default_tdx_stats_resource_path,
    metadata_path_for_source as _cache_metadata_path_for_source,
    parse_datetime as _cache_parse_datetime,
    read_stats_metadata as _cache_read_stats_metadata,
    resolve_stats_source as _cache_resolve_stats_source,
    stats_cache_root as _cache_stats_cache_root,
    stats_cache_should_refresh as _cache_stats_cache_should_refresh,
    write_bytes_atomic as _cache_write_bytes_atomic,
    write_stats_metadata as _cache_write_stats_metadata,
    write_text_atomic as _cache_write_text_atomic,
)
from .stats_models import (
    TdxStat2Row,
    TdxStatRow,
    TdxStatsResource,
    decode_lines as _decode_lines,
    float_value as _float_value,
    int_value as _int_value,
    parse_stat2_rows as _parse_stat2_rows,
    parse_stat_rows as _parse_stat_rows,
    stats_resource_from_lines,
    text_value as _text_value,
)


DEFAULT_TDX_STATS_CHUNK_SIZE = 30000


def load_tdx_stats_resource(root: str | Path | None = None) -> TdxStatsResource:
    """Load tdxstat.cfg and tdxstat2.cfg from a directory or zhb.zip."""

    source = _resolve_stats_source(root)
    if source.is_file() and source.name.lower().endswith(".zip"):
        with ZipFile(source) as archive:
            stat_lines = _decode_lines(archive.read("tdxstat.cfg"))
            stat2_lines = _decode_lines(archive.read("tdxstat2.cfg"))
    else:
        stat_lines = (source / "tdxstat.cfg").read_text(encoding="gbk", errors="ignore").splitlines()
        stat2_lines = (source / "tdxstat2.cfg").read_text(encoding="gbk", errors="ignore").splitlines()
    return stats_resource_from_lines(
        stat_lines,
        stat2_lines,
        source_path=str(source),
        metadata=_read_stats_metadata(source),
    )


def _resolve_stats_source(root: str | Path | None) -> Path:
    return _cache_resolve_stats_source(root)


def refresh_tdx_stats_resource(
    client,
    *,
    cache_root: str | Path | None = None,
    source_path: str = DEFAULT_TDX_STATS_RESOURCE_PATH,
    chunk_size: int = DEFAULT_TDX_STATS_CHUNK_SIZE,
) -> TdxStatsResource:
    root = _cache_stats_cache_root(cache_root)
    root.mkdir(parents=True, exist_ok=True)
    payload = _download_tdx_file(client, source_path, chunk_size=chunk_size)
    target = root / Path(source_path).name
    _validate_stats_zip(payload)
    _write_bytes_atomic(target, payload)
    resource = load_tdx_stats_resource(target)
    metadata = _build_stats_metadata(
        resource,
        payload=payload,
        source_path=source_path,
        target=target,
    )
    _write_stats_metadata(_metadata_path_for_source(target), metadata)
    return load_tdx_stats_resource(target)


def request_tdx_stats_resource(
    client,
    *,
    source_path: str = DEFAULT_TDX_STATS_RESOURCE_PATH,
    chunk_size: int = DEFAULT_TDX_STATS_CHUNK_SIZE,
) -> TdxStatsResource:
    """Download and parse the TDX statistics resource without writing local cache."""

    payload = _download_tdx_file(client, source_path, chunk_size=chunk_size)
    _validate_stats_zip(payload)
    resource = _load_tdx_stats_resource_from_zip_payload(payload, source_path=source_path)
    metadata = {
        "downloaded_at": datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds"),
        "stats_date": resource.stats_date,
        "source_resource_path": source_path,
        "cache_path": None,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "stat_rows": len(resource.stat),
        "stat2_rows": len(resource.stat2),
    }
    return TdxStatsResource(
        stat=resource.stat,
        stat2=resource.stat2,
        source_path=f"tdx://{source_path}",
        metadata=metadata,
    )


def ensure_tdx_stats_resource(
    client,
    *,
    root: str | Path | None = None,
    cache_root: str | Path | None = None,
    refresh: bool = False,
) -> tuple[TdxStatsResource, bool]:
    if root not in (None, ""):
        return load_tdx_stats_resource(root), False
    if refresh:
        return refresh_tdx_stats_resource(client, cache_root=cache_root), True
    try:
        resource = load_tdx_stats_resource(cache_root)
        if _stats_cache_should_refresh(resource):
            return refresh_tdx_stats_resource(client, cache_root=cache_root), True
        return resource, False
    except (FileNotFoundError, OSError):
        return refresh_tdx_stats_resource(client, cache_root=cache_root), True


def ensure_tdx_stats_resource_for_params(
    client,
    params: Mapping[str, object] | None,
    *,
    validation_error: type[ValueError] = ValueError,
) -> tuple[TdxStatsResource, bool]:
    params = params or {}
    return ensure_tdx_stats_resource(
        client,
        root=params.get("stats_root"),
        cache_root=params.get("stats_cache_root"),
        refresh=_refresh_stats_param(
            params.get("refresh_stats", False),
            validation_error=validation_error,
        ),
    )


def _refresh_stats_param(
    value: object,
    *,
    validation_error: type[ValueError] = ValueError,
) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "升序"}:
        return True
    if text in {"0", "false", "no", "n", "off", "降序", ""}:
        return False
    raise validation_error("refresh_stats must be a boolean")


def _download_tdx_file(client, path: str, *, chunk_size: int) -> bytes:
    if hasattr(client, "download_file_resource"):
        return client.download_file_resource(path, chunk_size=chunk_size)
    if hasattr(client, "resources") and hasattr(client.resources, "download_file"):
        return client.resources.download_file(path, chunk_size=chunk_size)
    raise RuntimeError("TDX client does not expose 0x06b9 file resource requests.")


def _load_tdx_stats_resource_from_zip_payload(payload: bytes, *, source_path: str) -> TdxStatsResource:
    from io import BytesIO

    with ZipFile(BytesIO(payload)) as archive:
        stat_lines = _decode_lines(archive.read("tdxstat.cfg"))
        stat2_lines = _decode_lines(archive.read("tdxstat2.cfg"))
    return stats_resource_from_lines(
        stat_lines,
        stat2_lines,
        source_path=f"tdx://{source_path}",
        metadata=None,
    )


def _validate_stats_zip(payload: bytes) -> None:
    from io import BytesIO

    with ZipFile(BytesIO(payload)) as archive:
        names = set(archive.namelist())
        missing = {"tdxstat.cfg", "tdxstat2.cfg"} - names
        if missing:
            raise FileNotFoundError(f"TDX stats resource missing files: {', '.join(sorted(missing))}")


def _stats_cache_should_refresh(resource: TdxStatsResource) -> bool:
    return _cache_stats_cache_should_refresh(resource)


def _build_stats_metadata(
    resource: TdxStatsResource,
    *,
    payload: bytes,
    source_path: str,
    target: Path,
) -> dict[str, object]:
    return _cache_build_stats_metadata(resource, payload=payload, source_path=source_path, target=target)


def _read_stats_metadata(source: Path) -> dict[str, object] | None:
    return _cache_read_stats_metadata(source)


def _write_stats_metadata(path: Path, metadata: dict[str, object]) -> None:
    _cache_write_stats_metadata(path, metadata)


def _metadata_path_for_source(source: Path) -> Path:
    return _cache_metadata_path_for_source(source)


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    _cache_write_bytes_atomic(path, payload)


def _write_text_atomic(path: Path, text: str) -> None:
    _cache_write_text_atomic(path, text)


def _parse_datetime(value: object) -> datetime | None:
    return _cache_parse_datetime(value)
