"""Cninfo source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

CNINFO_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = (
    "axdata.source.cninfo",
)


def cninfo_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return Provider ID keyed adapter factories owned by Cninfo."""

    return {
        provider_id: _cninfo_adapter
        for provider_id in CNINFO_SOURCE_ADAPTER_PROVIDER_IDS
    }


def cninfo_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    """Return legacy source-code adapter factories owned by Cninfo."""

    return {"cninfo": _cninfo_adapter}


def cninfo_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    """Return Provider and legacy adapter factory declarations owned by Cninfo."""

    return cninfo_provider_adapter_factories(), cninfo_legacy_source_adapter_factories()


def _cninfo_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_cninfo_request_adapter

    return create_cninfo_request_adapter(options)
