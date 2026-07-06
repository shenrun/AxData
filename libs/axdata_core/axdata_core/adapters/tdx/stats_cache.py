"""Compatibility wrapper for TDX statistics resource cache helpers."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from axdata_core.adapters.tdx.stats_models import TdxStatsResource


DEFAULT_TDX_STATS_RESOURCE_PATH = "zhb.zip"
DEFAULT_TDX_STATS_META_PATH = "zhb.meta.json"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def default_tdx_stats_cache_root() -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation.default_tdx_stats_cache_root()
    return _fallback_default_tdx_stats_cache_root()


def _fallback_default_tdx_stats_cache_root() -> Path:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def default_tdx_stats_resource_path() -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation.default_tdx_stats_resource_path()
    return _fallback_default_tdx_stats_cache_root() / DEFAULT_TDX_STATS_RESOURCE_PATH


def default_tdx_stats_metadata_path() -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation.default_tdx_stats_metadata_path()
    return _fallback_default_tdx_stats_cache_root() / DEFAULT_TDX_STATS_META_PATH


def resolve_stats_source(root: str | Path | None) -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation.resolve_stats_source(root)
    return _fallback_resolve_stats_source(root)


def _fallback_resolve_stats_source(root: str | Path | None) -> Path:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def stats_cache_root(cache_root: str | Path | None) -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation.stats_cache_root(cache_root)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def stats_cache_should_refresh(resource: "TdxStatsResource") -> bool:
    implementation = _implementation()
    if implementation is not None:
        return implementation.stats_cache_should_refresh(resource)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def build_stats_metadata(
    resource: "TdxStatsResource",
    *,
    payload: bytes,
    source_path: str,
    target: Path,
) -> dict[str, object]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.build_stats_metadata(resource, payload=payload, source_path=source_path, target=target)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def read_stats_metadata(source: Path) -> dict[str, object] | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.read_stats_metadata(source)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def write_stats_metadata(path: Path, metadata: dict[str, object]) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.write_stats_metadata(path, metadata)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def metadata_path_for_source(source: Path) -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation.metadata_path_for_source(source)
    return _fallback_metadata_path_for_source(source)


def _fallback_metadata_path_for_source(source: Path) -> Path:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.write_bytes_atomic(path, payload)
    _fallback_write_bytes_atomic(path, payload)


def _fallback_write_bytes_atomic(path: Path, payload: bytes) -> None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def write_text_atomic(path: Path, text: str) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.write_text_atomic(path, text)
    _fallback_write_text_atomic(path, text)


def _fallback_write_text_atomic(path: Path, text: str) -> None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def parse_datetime(value: object) -> datetime | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.parse_datetime(value)
    return _fallback_parse_datetime(value)


def _fallback_parse_datetime(value: object) -> datetime | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_stats_cache() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.stats_cache")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.stats_cache"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_stats_cache()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]
