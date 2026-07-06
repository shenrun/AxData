"""Tencent source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

TENCENT_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tencent",
)


def tencent_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by Tencent."""

    return {
        provider_id: _tencent_adapter
        for provider_id in TENCENT_SOURCE_ADAPTER_PROVIDER_IDS
    }


def tencent_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by Tencent."""

    return {"tencent": _tencent_adapter}


def tencent_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by Tencent."""

    return tencent_provider_adapter_factories(), tencent_legacy_source_adapter_factories()


def _tencent_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_tencent_request_adapter

    return create_tencent_request_adapter(options)
