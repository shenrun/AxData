"""TDX Ext source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

TDX_EXT_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.tdx_ext",
)


def tdx_ext_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by TDX Ext."""

    return {
        provider_id: _tdx_ext_adapter
        for provider_id in TDX_EXT_SOURCE_ADAPTER_PROVIDER_IDS
    }


def tdx_ext_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by TDX Ext."""

    return {"tdx_ext": _tdx_ext_adapter}


def tdx_ext_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by TDX Ext."""

    return tdx_ext_provider_adapter_factories(), tdx_ext_legacy_source_adapter_factories()


def _tdx_ext_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_tdx_ext_request_adapter

    return create_tdx_ext_request_adapter(options)
