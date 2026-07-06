"""Bundled Provider declaration entry points.

This module is a lightweight transition seam.  It centralizes the list of
source-owned declaration registries while built-in sources move toward fully
Provider-owned manifests.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

LegacySourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]
SourceAdapterFactoryDeclarations = tuple[
    dict[str, LegacySourceAdapterFactory],
    dict[str, LegacySourceAdapterFactory],
]

SourceExecutionEnricherFactory = Callable[[str | Path | None], Callable[[dict[str, Any]], None]]

DownloaderAdapterFactory = Callable[..., Any]
RuntimeSourceServerMaxFactory = Callable[..., int]
DownloaderProfileDeclarations = Callable[[type[Any], type[Any]], dict[str, Any]]
DownloaderDeclarations = tuple[
    DownloaderProfileDeclarations,
    dict[str, DownloaderAdapterFactory],
    dict[str, RuntimeSourceServerMaxFactory],
]


def builtin_source_adapter_factory_declarations() -> tuple[SourceAdapterFactoryDeclarations, ...]:
    """Return source-owned adapter factory declarations for bundled Providers."""

    return (
        _tdx_source_adapter_factory_declarations(),
        _tdx_ext_source_adapter_factory_declarations(),
        _exchange_source_adapter_factory_declarations(),
        _cninfo_source_adapter_factory_declarations(),
        _tencent_source_adapter_factory_declarations(),
        _eastmoney_source_adapter_factory_declarations(),
        _cls_source_adapter_factory_declarations(),
        _kph_source_adapter_factory_declarations(),
        _sina_source_adapter_factory_declarations(),
    )


def builtin_source_execution_enricher_declarations() -> tuple[
    dict[str, SourceExecutionEnricherFactory],
    ...,
]:
    """Return source-owned execution option enrichers for bundled Providers."""

    return (
        _tdx_source_execution_enricher_declarations(),
        _tdx_ext_source_execution_enricher_declarations(),
    )


def builtin_downloader_declarations() -> tuple[DownloaderDeclarations, ...]:
    """Return source-owned downloader declarations for bundled Providers."""

    return (_tdx_downloader_declarations(),)


def _tdx_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    try:
        from axdata_source_tdx.source_adapter_registry import (
            tdx_source_adapter_factory_declarations,
        )
    except ModuleNotFoundError as exc:
        if exc.name not in {"axdata_source_tdx", "axdata_source_tdx.source_adapter_registry"}:
            raise
    else:
        return tdx_source_adapter_factory_declarations()
    return {}, {}


def _tdx_ext_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.tdx_ext.source_adapter_registry import tdx_ext_source_adapter_factory_declarations

    return tdx_ext_source_adapter_factory_declarations()


def _exchange_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.exchange.source_adapter_registry import exchange_source_adapter_factory_declarations

    return exchange_source_adapter_factory_declarations()


def _cninfo_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.cninfo.source_adapter_registry import cninfo_source_adapter_factory_declarations

    return cninfo_source_adapter_factory_declarations()


def _tencent_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.tencent.source_adapter_registry import tencent_source_adapter_factory_declarations

    return tencent_source_adapter_factory_declarations()


def _eastmoney_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.eastmoney.source_adapter_registry import eastmoney_source_adapter_factory_declarations

    return eastmoney_source_adapter_factory_declarations()


def _cls_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.cls.source_adapter_registry import cls_source_adapter_factory_declarations

    return cls_source_adapter_factory_declarations()


def _kph_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.kph.source_adapter_registry import kph_source_adapter_factory_declarations

    return kph_source_adapter_factory_declarations()


def _sina_source_adapter_factory_declarations() -> SourceAdapterFactoryDeclarations:
    from .adapters.sina.source_adapter_registry import sina_source_adapter_factory_declarations

    return sina_source_adapter_factory_declarations()


def _tdx_source_execution_enricher_declarations() -> dict[str, SourceExecutionEnricherFactory]:
    try:
        from axdata_source_tdx.source_execution_registry import (
            tdx_source_execution_enricher_declarations,
        )
    except ModuleNotFoundError as exc:
        if exc.name not in {"axdata_source_tdx", "axdata_source_tdx.source_execution_registry"}:
            raise
    else:
        return tdx_source_execution_enricher_declarations()
    return {}


def _tdx_ext_source_execution_enricher_declarations() -> dict[str, SourceExecutionEnricherFactory]:
    from .adapters.tdx_ext.source_execution_registry import tdx_ext_source_execution_enricher_declarations

    return tdx_ext_source_execution_enricher_declarations()


def _tdx_downloader_declarations() -> DownloaderDeclarations:
    try:
        from axdata_source_tdx.downloader_registry import tdx_downloader_declarations
    except ModuleNotFoundError as exc:
        if exc.name not in {"axdata_source_tdx", "axdata_source_tdx.downloader_registry"}:
            raise
    else:
        return tdx_downloader_declarations()
    from .tdx_plugin_required import empty_downloader_profile_declarations

    return empty_downloader_profile_declarations, {}, {}
