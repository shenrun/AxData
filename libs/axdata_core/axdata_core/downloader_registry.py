"""Built-in downloader profile registration.

This module is a small transition seam while downloader profiles move from
core-owned declarations toward Provider-owned declarations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

DownloaderAdapterFactory = Callable[..., Any]
RuntimeSourceServerMaxFactory = Callable[..., int]
DownloaderProfileDeclarations = Callable[[type[Any], type[Any]], dict[str, Any]]
DownloaderDeclarations = tuple[
    DownloaderProfileDeclarations,
    dict[str, DownloaderAdapterFactory],
    dict[str, RuntimeSourceServerMaxFactory],
]


def load_builtin_downloader_profiles(
    concurrency_profile_cls: type[Any],
    downloader_profile_cls: type[Any],
) -> dict[str, Any]:
    """Return downloader profiles bundled with the current AxData package."""

    profiles: dict[str, Any] = {}
    for profile_declarations, _, _ in _downloader_declarations():
        profiles.update(
            profile_declarations(
                concurrency_profile_cls,
                downloader_profile_cls,
            )
        )
    return profiles


def load_builtin_downloader_adapter_factories(
) -> dict[str, DownloaderAdapterFactory]:
    """Return adapter factories bundled with current downloader profiles."""

    factories: dict[str, DownloaderAdapterFactory] = {}
    for _, adapter_factories, _ in _downloader_declarations():
        factories.update(adapter_factories)
    return factories


def load_builtin_runtime_source_server_max_factories(
) -> dict[str, RuntimeSourceServerMaxFactory]:
    """Return runtime concurrency cap factories bundled with current profiles."""

    factories: dict[str, RuntimeSourceServerMaxFactory] = {}
    for _, _, runtime_source_server_max_factories in _downloader_declarations():
        factories.update(runtime_source_server_max_factories)
    return factories


def _downloader_declarations() -> tuple[DownloaderDeclarations, ...]:
    from .builtin_source_declarations import builtin_downloader_declarations

    return builtin_downloader_declarations()
