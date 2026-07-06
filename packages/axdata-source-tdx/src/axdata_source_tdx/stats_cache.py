"""TDX statistics resource cache paths and metadata helpers."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from .stats_models import TdxStatsResource


DEFAULT_TDX_STATS_RESOURCE_PATH = "zhb.zip"
DEFAULT_TDX_STATS_META_PATH = "zhb.meta.json"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def default_tdx_stats_cache_root() -> Path:
    raw = os.getenv("AXDATA_TDX_STATS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.cwd() / "cache" / "tdx" / "stats").resolve()


def default_tdx_stats_resource_path() -> Path:
    return default_tdx_stats_cache_root() / DEFAULT_TDX_STATS_RESOURCE_PATH


def default_tdx_stats_metadata_path() -> Path:
    return default_tdx_stats_cache_root() / DEFAULT_TDX_STATS_META_PATH


def resolve_stats_source(root: str | Path | None) -> Path:
    if root not in (None, ""):
        source = Path(str(root)).expanduser()
        if source.is_file():
            return source
        if (source / "tdxstat.cfg").exists() and (source / "tdxstat2.cfg").exists():
            return source
        if (source / DEFAULT_TDX_STATS_RESOURCE_PATH).exists():
            return source / DEFAULT_TDX_STATS_RESOURCE_PATH
        raise FileNotFoundError(f"TDX stats resource not found under {source}")

    source = default_tdx_stats_resource_path()
    if source.exists():
        return source
    raise FileNotFoundError(
        "TDX stats resource not found in AxData cache. Refresh stats resource from TDX source first."
    )


def stats_cache_root(cache_root: str | Path | None) -> Path:
    if cache_root in (None, ""):
        return default_tdx_stats_cache_root()
    return Path(str(cache_root)).expanduser().resolve()


def stats_cache_should_refresh(resource: TdxStatsResource) -> bool:
    metadata = resource.metadata or {}
    downloaded_at = parse_datetime(metadata.get("downloaded_at"))
    if downloaded_at is None:
        return True
    return downloaded_at.astimezone(SHANGHAI_TZ).date() != datetime.now(SHANGHAI_TZ).date()


def build_stats_metadata(
    resource: TdxStatsResource,
    *,
    payload: bytes,
    source_path: str,
    target: Path,
) -> dict[str, object]:
    return {
        "downloaded_at": datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds"),
        "stats_date": resource.stats_date,
        "source_resource_path": source_path,
        "cache_path": str(target),
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "stat_rows": len(resource.stat),
        "stat2_rows": len(resource.stat2),
    }


def read_stats_metadata(source: Path) -> dict[str, object] | None:
    meta_path = metadata_path_for_source(source)
    if not meta_path.exists():
        return None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_stats_metadata(path: Path, metadata: dict[str, object]) -> None:
    write_text_atomic(path, json.dumps(metadata, ensure_ascii=False, indent=2))


def metadata_path_for_source(source: Path) -> Path:
    if source.is_file():
        return source.with_name(DEFAULT_TDX_STATS_META_PATH)
    return source / DEFAULT_TDX_STATS_META_PATH


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        os.replace(tmp_path, path)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def parse_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=SHANGHAI_TZ)
    return parsed
