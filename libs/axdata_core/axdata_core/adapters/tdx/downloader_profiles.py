"""Compatibility wrapper for TDX downloader profile declarations."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def tdx_downloader_profiles(
    concurrency_profile_cls: type[Any],
    downloader_profile_cls: type[Any],
) -> dict[str, Any]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.tdx_downloader_profiles(
            concurrency_profile_cls,
            downloader_profile_cls,
        )
    from axdata_core.tdx_plugin_required import empty_downloader_profile_declarations

    return empty_downloader_profile_declarations(concurrency_profile_cls, downloader_profile_cls)


def _provider_package_profiles() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.downloader_profiles")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.downloader_profiles"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_profiles()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]
