"""Compatibility wrapper for TDX plugin downloader declarations."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

DownloaderAdapterFactory = Callable[..., Any]
RuntimeSourceServerMaxFactory = Callable[..., int]
DownloaderProfileDeclarations = Callable[[type[Any], type[Any]], dict[str, Any]]
TdxDownloaderDeclarations = tuple[
    DownloaderProfileDeclarations,
    dict[str, DownloaderAdapterFactory],
    dict[str, RuntimeSourceServerMaxFactory],
]
_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def tdx_downloader_profile_declarations(
    concurrency_profile_cls: type[Any],
    downloader_profile_cls: type[Any],
) -> dict[str, Any]:
    """Return downloader profile declarations owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_downloader_profile_declarations(
            concurrency_profile_cls,
            downloader_profile_cls,
        )
    return {}


def tdx_downloader_adapter_factories() -> dict[str, DownloaderAdapterFactory]:
    """Return downloader adapter factories owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_downloader_adapter_factories()
    return {}


def tdx_runtime_source_server_max_factories() -> dict[str, RuntimeSourceServerMaxFactory]:
    """Return runtime source-server cap factories owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_runtime_source_server_max_factories()
    return {}


def tdx_downloader_declarations() -> TdxDownloaderDeclarations:
    """Return all downloader declarations owned by TDX."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_downloader_declarations()
    return (
        tdx_downloader_profile_declarations,
        tdx_downloader_adapter_factories(),
        tdx_runtime_source_server_max_factories(),
    )


def _provider_package_registry() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.downloader_registry")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.downloader_registry"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_registry()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]


def _fallback_tdx_downloader_profile_declarations(
    concurrency_profile_cls: type[Any],
    downloader_profile_cls: type[Any],
) -> dict[str, Any]:
    return {}


def _fallback_tdx_download_adapter(
    *,
    interface_name: str,
    source_server_count: int,
    pool_size: int,
    data_root: str | Path | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> tuple[Any, Any]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_tdx_runtime_source_server_max(
    interface_name: str,
    *,
    configured_max: int,
    source_server_count_editable: bool,
    data_root: str | Path | None = None,
) -> int:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()
