"""TDX source adapter factory declarations owned by the provider package."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

TDX_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tdx",
)


def tdx_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by TDX."""

    return {
        provider_id: _tdx_adapter
        for provider_id in TDX_SOURCE_ADAPTER_PROVIDER_IDS
    }


def tdx_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by TDX."""

    return {"tdx": _tdx_adapter}


def tdx_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by TDX."""

    return tdx_provider_adapter_factories(), tdx_legacy_source_adapter_factories()


def _tdx_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_tdx_request_adapter

    return create_tdx_request_adapter(options)
