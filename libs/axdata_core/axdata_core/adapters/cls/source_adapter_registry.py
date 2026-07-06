"""CLS source adapter factory declarations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

SourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]

CLS_SOURCE_ADAPTER_PROVIDER_IDS: tuple[str, ...] = ("axdata.source.cls",)


def cls_provider_adapter_factories() -> dict[str, SourceAdapterFactory]:
    return {provider_id: _cls_adapter for provider_id in CLS_SOURCE_ADAPTER_PROVIDER_IDS}


def cls_legacy_source_adapter_factories() -> dict[str, SourceAdapterFactory]:
    return {"cls": _cls_adapter}


def cls_source_adapter_factory_declarations() -> tuple[
    dict[str, SourceAdapterFactory],
    dict[str, SourceAdapterFactory],
]:
    return cls_provider_adapter_factories(), cls_legacy_source_adapter_factories()


def _cls_adapter(options: Mapping[str, object] | None) -> Any:
    from .provider_bridge import create_cls_request_adapter

    return create_cls_request_adapter(options)
