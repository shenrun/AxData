"""Legacy source adapter factory keyed by catalog source code."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

LegacySourceAdapterFactory = Callable[[Mapping[str, object] | None], Any]
SourceAdapterFactoryDeclarations = tuple[
    dict[str, LegacySourceAdapterFactory],
    dict[str, LegacySourceAdapterFactory],
]


def adapter_for_source_identity(
    *,
    provider_id: str | None = None,
    source_code: str | None = None,
    options: Mapping[str, object] | None = None,
    provider_factories: Mapping[str, LegacySourceAdapterFactory] | None = None,
    source_factories: Mapping[str, LegacySourceAdapterFactory] | None = None,
) -> Any:
    """Create a built-in adapter by Provider identity, with legacy source fallback."""

    normalized_provider_id = str(provider_id or "").strip()
    normalized_source_code = str(source_code or "").strip()
    if normalized_provider_id:
        return adapter_for_provider_id(
            normalized_provider_id,
            options=options,
            factories=provider_factories,
        )
    if normalized_source_code:
        return adapter_for_source_code(
            normalized_source_code,
            options=options,
            factories=source_factories,
        )
    raise KeyError("No provider_id or source_code was provided for source adapter resolution.")


def adapter_for_provider_id(
    provider_id: str,
    *,
    options: Mapping[str, object] | None = None,
    factories: Mapping[str, LegacySourceAdapterFactory] | None = None,
) -> Any:
    """Create the adapter for one known built-in Provider ID."""

    normalized = str(provider_id or "").strip()
    resolved_factories = builtin_provider_adapter_factories() if factories is None else factories
    factory = resolved_factories.get(normalized)
    if factory is not None:
        return factory(options)
    raise KeyError(f"No built-in source adapter is registered for provider {provider_id!r}.")


def adapter_for_source_code(
    source_code: str,
    *,
    options: Mapping[str, object] | None = None,
    factories: Mapping[str, LegacySourceAdapterFactory] | None = None,
) -> Any:
    """Create the legacy adapter for one known built-in source code."""

    normalized = str(source_code or "").strip()
    resolved_factories = legacy_source_adapter_factories() if factories is None else factories
    factory = resolved_factories.get(normalized)
    if factory is not None:
        return factory(options)
    raise KeyError(f"No legacy source adapter is registered for source {source_code!r}.")


def builtin_provider_adapter_factories() -> dict[str, LegacySourceAdapterFactory]:
    """Return lazy factories for built-in Provider IDs."""

    factories: dict[str, LegacySourceAdapterFactory] = {}
    for provider_factories, _ in _source_adapter_factory_declarations():
        factories.update(provider_factories)
    return factories


def legacy_source_adapter_factories() -> dict[str, LegacySourceAdapterFactory]:
    """Return lazy factories for known built-in legacy source adapters."""

    factories: dict[str, LegacySourceAdapterFactory] = {}
    for _, source_factories in _source_adapter_factory_declarations():
        factories.update(source_factories)
    return factories


def _source_adapter_factory_declarations() -> tuple[SourceAdapterFactoryDeclarations, ...]:
    from .builtin_source_declarations import builtin_source_adapter_factory_declarations

    return builtin_source_adapter_factory_declarations()
