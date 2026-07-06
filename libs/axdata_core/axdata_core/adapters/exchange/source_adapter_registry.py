"""Exchange source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

EXCHANGE_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.exchange",
)


def exchange_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by Exchange."""

    return {
        provider_id: _exchange_adapter
        for provider_id in EXCHANGE_SOURCE_ADAPTER_PROVIDER_IDS
    }


def exchange_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by Exchange."""

    return {"exchange": _exchange_adapter}


def exchange_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by Exchange."""

    return exchange_provider_adapter_factories(), exchange_legacy_source_adapter_factories()


def _exchange_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_exchange_request_adapter

    return create_exchange_request_adapter(options)
