"""TDX downloader factory declarations owned by the provider package."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

DownloaderAdapterFactory = Callable[..., Any]
RuntimeSourceServerMaxFactory = Callable[..., int]
DownloaderProfileDeclarations = Callable[[type[Any], type[Any]], dict[str, Any]]
TdxDownloaderDeclarations = tuple[
    DownloaderProfileDeclarations,
    dict[str, DownloaderAdapterFactory],
    dict[str, RuntimeSourceServerMaxFactory],
]


def tdx_downloader_profile_declarations(
    concurrency_profile_cls: type[Any],
    downloader_profile_cls: type[Any],
) -> dict[str, Any]:
    """Return downloader profile declarations owned by TDX."""

    from .downloader_profiles import tdx_downloader_profiles

    return tdx_downloader_profiles(concurrency_profile_cls, downloader_profile_cls)


def tdx_downloader_adapter_factories() -> dict[str, DownloaderAdapterFactory]:
    """Return downloader adapter factories owned by TDX."""

    return {"tdx": _tdx_download_adapter}


def tdx_runtime_source_server_max_factories() -> dict[str, RuntimeSourceServerMaxFactory]:
    """Return runtime source-server cap factories owned by TDX."""

    return {"tdx": _tdx_runtime_source_server_max}


def tdx_downloader_declarations() -> TdxDownloaderDeclarations:
    """Return all downloader declarations owned by TDX."""

    return (
        tdx_downloader_profile_declarations,
        tdx_downloader_adapter_factories(),
        tdx_runtime_source_server_max_factories(),
    )


def _tdx_download_adapter(
    *,
    interface_name: str,
    source_server_count: int,
    pool_size: int,
    data_root: str | Path | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> tuple[Any, Any]:
    from .downloader import create_tdx_download_adapter

    return create_tdx_download_adapter(
        interface_name=interface_name,
        source_server_count=source_server_count,
        pool_size=pool_size,
        data_root=data_root,
        progress_callback=progress_callback,
    )


def _tdx_runtime_source_server_max(
    interface_name: str,
    *,
    configured_max: int,
    source_server_count_editable: bool,
    data_root: str | Path | None = None,
) -> int:
    from .downloader import tdx_runtime_source_server_max

    return tdx_runtime_source_server_max(
        interface_name,
        configured_max=configured_max,
        source_server_count_editable=source_server_count_editable,
        data_root=data_root,
    )
