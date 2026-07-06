"""Sina source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

SINA_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.sina",
)


def sina_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by Sina."""

    return {
        provider_id: _sina_adapter
        for provider_id in SINA_SOURCE_ADAPTER_PROVIDER_IDS
    }


def sina_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by Sina."""

    return {"sina": _sina_adapter}


def sina_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by Sina."""

    return sina_provider_adapter_factories(), sina_legacy_source_adapter_factories()


def _sina_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_sina_request_adapter

    return create_sina_request_adapter(options)
