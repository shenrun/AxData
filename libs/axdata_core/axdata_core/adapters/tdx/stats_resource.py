"""Compatibility wrapper for TDX local statistics resource helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, TYPE_CHECKING
from zipfile import ZipFile

if TYPE_CHECKING:
    from axdata_core.adapters.tdx.stats_models import TdxStatsResource


DEFAULT_TDX_STATS_CHUNK_SIZE = 30000
DEFAULT_TDX_STATS_RESOURCE_PATH = "zhb.zip"
DEFAULT_TDX_STATS_META_PATH = "zhb.meta.json"
_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None
_CACHE_IMPLEMENTATION = None
_MODELS_IMPLEMENTATION = None


def load_tdx_stats_resource(root: str | Path | None = None) -> TdxStatsResource:
    implementation = _implementation()
    if implementation is not None:
        return implementation.load_tdx_stats_resource(root)
    return _fallback_load_tdx_stats_resource(root)


def _fallback_load_tdx_stats_resource(root: str | Path | None = None) -> TdxStatsResource:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _resolve_stats_source(root: str | Path | None) -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation._resolve_stats_source(root)
    return _stats_cache().resolve_stats_source(root)


def refresh_tdx_stats_resource(
    client,
    *,
    cache_root: str | Path | None = None,
    source_path: str = DEFAULT_TDX_STATS_RESOURCE_PATH,
    chunk_size: int = DEFAULT_TDX_STATS_CHUNK_SIZE,
) -> TdxStatsResource:
    implementation = _implementation()
    if implementation is not None:
        return implementation.refresh_tdx_stats_resource(
            client,
            cache_root=cache_root,
            source_path=source_path,
            chunk_size=chunk_size,
        )
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def request_tdx_stats_resource(
    client,
    *,
    source_path: str = DEFAULT_TDX_STATS_RESOURCE_PATH,
    chunk_size: int = DEFAULT_TDX_STATS_CHUNK_SIZE,
) -> TdxStatsResource:
    implementation = _implementation()
    if implementation is not None:
        return implementation.request_tdx_stats_resource(
            client,
            source_path=source_path,
            chunk_size=chunk_size,
        )
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def ensure_tdx_stats_resource(
    client,
    *,
    root: str | Path | None = None,
    cache_root: str | Path | None = None,
    refresh: bool = False,
) -> tuple[TdxStatsResource, bool]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.ensure_tdx_stats_resource(
            client,
            root=root,
            cache_root=cache_root,
            refresh=refresh,
        )
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def ensure_tdx_stats_resource_for_params(
    client,
    params: Mapping[str, object] | None,
    *,
    validation_error: type[ValueError] = ValueError,
) -> tuple[TdxStatsResource, bool]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.ensure_tdx_stats_resource_for_params(
            client,
            params,
            validation_error=validation_error,
        )
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _refresh_stats_param(
    value: object,
    *,
    validation_error: type[ValueError] = ValueError,
) -> bool:
    implementation = _implementation()
    if implementation is not None:
        return implementation._refresh_stats_param(value, validation_error=validation_error)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _download_tdx_file(client, path: str, *, chunk_size: int) -> bytes:
    implementation = _implementation()
    if implementation is not None:
        return implementation._download_tdx_file(client, path, chunk_size=chunk_size)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _load_tdx_stats_resource_from_zip_payload(payload: bytes, *, source_path: str) -> TdxStatsResource:
    implementation = _implementation()
    if implementation is not None:
        return implementation._load_tdx_stats_resource_from_zip_payload(payload, source_path=source_path)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _validate_stats_zip(payload: bytes) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation._validate_stats_zip(payload)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _stats_cache_should_refresh(resource: TdxStatsResource) -> bool:
    implementation = _implementation()
    if implementation is not None:
        return implementation._stats_cache_should_refresh(resource)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _build_stats_metadata(
    resource: TdxStatsResource,
    *,
    payload: bytes,
    source_path: str,
    target: Path,
) -> dict[str, object]:
    implementation = _implementation()
    if implementation is not None:
        return implementation._build_stats_metadata(resource, payload=payload, source_path=source_path, target=target)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _read_stats_metadata(source: Path) -> dict[str, object] | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation._read_stats_metadata(source)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _write_stats_metadata(path: Path, metadata: dict[str, object]) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation._write_stats_metadata(path, metadata)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _metadata_path_for_source(source: Path) -> Path:
    implementation = _implementation()
    if implementation is not None:
        return implementation._metadata_path_for_source(source)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation._write_bytes_atomic(path, payload)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _write_text_atomic(path: Path, text: str) -> None:
    implementation = _implementation()
    if implementation is not None:
        return implementation._write_text_atomic(path, text)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _parse_datetime(value: object) -> datetime | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation._parse_datetime(value)
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _stats_cache() -> ModuleType:
    global _CACHE_IMPLEMENTATION
    if _CACHE_IMPLEMENTATION is None:
        _CACHE_IMPLEMENTATION = import_module("axdata_core.adapters.tdx.stats_cache")
    return _CACHE_IMPLEMENTATION


def _stats_models() -> ModuleType:
    global _MODELS_IMPLEMENTATION
    if _MODELS_IMPLEMENTATION is None:
        _MODELS_IMPLEMENTATION = import_module("axdata_core.adapters.tdx.stats_models")
    return _MODELS_IMPLEMENTATION


def _provider_package_stats_resource() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.stats_resource")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.stats_resource"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_stats_resource()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]


def __getattr__(name: str) -> Any:
    if name in {
        "SHANGHAI_TZ",
        "default_tdx_stats_cache_root",
        "default_tdx_stats_metadata_path",
        "default_tdx_stats_resource_path",
    }:
        value = getattr(_stats_cache(), name)
    elif name in {
        "TdxStat2Row",
        "TdxStatRow",
        "TdxStatsResource",
        "_decode_lines",
        "_float_value",
        "_int_value",
        "_parse_stat2_rows",
        "_parse_stat_rows",
        "stats_resource_from_lines",
        "_text_value",
    }:
        alias = {
            "_decode_lines": "decode_lines",
            "_float_value": "float_value",
            "_int_value": "int_value",
            "_parse_stat2_rows": "parse_stat2_rows",
            "_parse_stat_rows": "parse_stat_rows",
            "_text_value": "text_value",
        }.get(name, name)
        value = getattr(_stats_models(), alias)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value
