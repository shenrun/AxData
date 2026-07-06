"""TDX downloader adapter factory."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from .downloader_interface_sets import (
    DOWNLOADER_F10_TOPIC_PREFILL_INTERFACES,
    DOWNLOADER_PARALLEL_SUSPENSION_INTERFACES,
    DOWNLOADER_RUNTIME_SOURCE_SERVER_MAX_INTERFACES,
    DOWNLOADER_STATS_RESOURCE_INTERFACES,
)
from .server_cache import tdx_server_cache_root, tdx_stats_cache_root


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


class _SourceRequestAdapterLike(Protocol):
    source: str

    def supports(self, interface_name: str) -> bool: ...

    def request(self, interface_name: str, params: dict[str, Any]) -> list[dict[str, Any]]: ...


def create_tdx_client(**kwargs: Any) -> Any:
    """Create a TDX client through the regular factory lazily."""

    from .client_factory import create_tdx_client as create_client

    return create_client(**kwargs)


def effective_host_strings(kind: str, *, cache_root: str | None = None) -> list[str]:
    """Resolve configured TDX quote hosts lazily."""

    from .host_config import effective_host_strings as resolve_hosts

    return list(resolve_hosts(kind, cache_root=cache_root))


def create_tdx_download_adapter(
    *,
    interface_name: str,
    source_server_count: int,
    pool_size: int,
    data_root: str | Path | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> tuple[_SourceRequestAdapterLike, Any]:
    """Create the long-connection adapter used by TDX downloader runs."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.create_tdx_download_adapter(
            interface_name=interface_name,
            source_server_count=source_server_count,
            pool_size=pool_size,
            data_root=data_root,
            progress_callback=progress_callback,
        )
    return _fallback_create_tdx_download_adapter(
        interface_name=interface_name,
        source_server_count=source_server_count,
        pool_size=pool_size,
        data_root=data_root,
        progress_callback=progress_callback,
    )


def _fallback_create_tdx_download_adapter(
    *,
    interface_name: str,
    source_server_count: int,
    pool_size: int,
    data_root: str | Path | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> tuple[_SourceRequestAdapterLike, Any]:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def tdx_adapter_options(
    *,
    interface_name: str,
    pool_size: int,
    server_cache_root: str | None = None,
    stats_cache_root: str | None = None,
) -> dict[str, Any] | None:
    """Return request adapter options for a TDX downloader interface."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_adapter_options(
            interface_name=interface_name,
            pool_size=pool_size,
            server_cache_root=server_cache_root,
            stats_cache_root=stats_cache_root,
        )
    return _fallback_tdx_adapter_options(
        interface_name=interface_name,
        pool_size=pool_size,
        server_cache_root=server_cache_root,
        stats_cache_root=stats_cache_root,
    )


def _fallback_tdx_adapter_options(
    *,
    interface_name: str,
    pool_size: int,
    server_cache_root: str | None = None,
    stats_cache_root: str | None = None,
) -> dict[str, Any] | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def tdx_runtime_source_server_max(
    interface_name: str,
    *,
    configured_max: int,
    source_server_count_editable: bool,
    data_root: str | Path | None = None,
) -> int:
    """Return the runtime source-server cap for TDX downloader concurrency."""

    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_runtime_source_server_max(
            interface_name,
            configured_max=configured_max,
            source_server_count_editable=source_server_count_editable,
            data_root=data_root,
        )
    return _fallback_tdx_runtime_source_server_max(
        interface_name,
        configured_max=configured_max,
        source_server_count_editable=source_server_count_editable,
        data_root=data_root,
    )


def _fallback_tdx_runtime_source_server_max(
    interface_name: str,
    *,
    configured_max: int,
    source_server_count_editable: bool,
    data_root: str | Path | None = None,
) -> int:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_downloader() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.downloader")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.downloader"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_downloader()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]


def _tdx_request_adapter_class() -> Any:
    adapter_cls = globals().get("TdxRequestAdapter")
    if adapter_cls is not None:
        return adapter_cls
    from .request import TdxRequestAdapter as loaded_adapter_cls

    globals()["TdxRequestAdapter"] = loaded_adapter_cls
    return loaded_adapter_cls


def __getattr__(name: str) -> Any:
    if name == "TdxRequestAdapter":
        return _tdx_request_adapter_class()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
