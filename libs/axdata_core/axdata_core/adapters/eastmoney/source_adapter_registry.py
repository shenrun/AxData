"""Eastmoney source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

EASTMONEY_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.eastmoney",
)


def eastmoney_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by Eastmoney."""

    return {
        provider_id: _eastmoney_adapter
        for provider_id in EASTMONEY_SOURCE_ADAPTER_PROVIDER_IDS
    }


def eastmoney_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by Eastmoney."""

    return {"eastmoney": _eastmoney_adapter}


def eastmoney_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by Eastmoney."""

    return eastmoney_provider_adapter_factories(), eastmoney_legacy_source_adapter_factories()


def _eastmoney_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_eastmoney_request_adapter

    return create_eastmoney_request_adapter(options)
