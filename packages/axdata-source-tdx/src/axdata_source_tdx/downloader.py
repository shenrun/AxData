"""TDX downloader adapter factory owned by the provider package."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from .downloader_interface_sets import (
    DOWNLOADER_F10_TOPIC_PREFILL_INTERFACES,
    DOWNLOADER_PARALLEL_SUSPENSION_INTERFACES,
    DOWNLOADER_RUNTIME_SOURCE_SERVER_MAX_INTERFACES,
    DOWNLOADER_STATS_RESOURCE_INTERFACES,
)
from .server_cache import tdx_server_cache_root, tdx_stats_cache_root


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

    server_cache_root = tdx_server_cache_root(data_root)
    stats_cache_root = tdx_stats_cache_root(data_root)
    hosts = effective_host_strings("quote", cache_root=server_cache_root)[: max(1, source_server_count)]
    client = create_tdx_client(
        hosts=hosts or None,
        pool_size=max(1, pool_size),
        heartbeat_interval=None,
    )
    adapter_cls = _tdx_request_adapter_class()
    return (
        adapter_cls(
            client=client,
            progress_callback=progress_callback,
            use_parallel_suspension_quotes=interface_name in DOWNLOADER_PARALLEL_SUSPENSION_INTERFACES,
            options=tdx_adapter_options(
                interface_name=interface_name,
                pool_size=pool_size,
                server_cache_root=server_cache_root,
                stats_cache_root=stats_cache_root,
            ),
        ),
        client,
    )


def tdx_adapter_options(
    *,
    interface_name: str,
    pool_size: int,
    server_cache_root: str | None = None,
    stats_cache_root: str | None = None,
) -> dict[str, Any] | None:
    """Return request adapter options for a TDX downloader interface."""

    options: dict[str, Any] = {}
    if server_cache_root is not None:
        options["server_cache_root"] = server_cache_root
    if stats_cache_root is not None and interface_name in DOWNLOADER_STATS_RESOURCE_INTERFACES:
        options["stats_cache_root"] = stats_cache_root
    if interface_name in DOWNLOADER_F10_TOPIC_PREFILL_INTERFACES:
        options.update(
            {
                "f10_topic_workers": 6,
                "f10_topic_refill_workers": 6,
                "f10_topic_refill_rounds": 1,
            }
        )
    return options or None


def tdx_runtime_source_server_max(
    interface_name: str,
    *,
    configured_max: int,
    source_server_count_editable: bool,
    data_root: str | Path | None = None,
) -> int:
    """Return the runtime source-server cap for TDX downloader concurrency."""

    resolved_configured_max = max(1, int(configured_max))
    if (
        interface_name not in DOWNLOADER_RUNTIME_SOURCE_SERVER_MAX_INTERFACES
        or not source_server_count_editable
    ):
        return resolved_configured_max
    try:
        available_count = len(effective_host_strings("quote", cache_root=tdx_server_cache_root(data_root)))
    except Exception:
        available_count = 0
    if available_count <= 0:
        return resolved_configured_max
    return max(1, min(resolved_configured_max, available_count))


def _tdx_request_adapter_class() -> Any:
    adapter_cls = globals().get("TdxRequestAdapter")
    if adapter_cls is not None:
        return adapter_cls
    from .request_adapter import TdxRequestAdapter as loaded_adapter_cls

    globals()["TdxRequestAdapter"] = loaded_adapter_cls
    return loaded_adapter_cls


def __getattr__(name: str) -> Any:
    if name == "TdxRequestAdapter":
        return _tdx_request_adapter_class()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
