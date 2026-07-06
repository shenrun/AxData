"""Collector registry for AxData collector capability catalogs."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

from .plugins import CollectorSpec, PluginStatus, validate_manifest
from .provider_registry import ProviderRegistry, ProviderRegistrySnapshot, RegisteredProvider


@dataclass(frozen=True)
class RegisteredCollectorPlugin:
    """A plugin that contributes collector capabilities."""

    plugin_id: str
    manifest: Any
    status: str
    effective_trust_level: str
    enabled: bool = False
    built_in: bool = False
    error: str = ""
    legacy_source: str | None = None
    source_provider_id: str | None = None

    @property
    def source_code(self) -> str:
        if self.manifest.provider is not None:
            return self.manifest.provider.source_code
        return "plugin"


@dataclass(frozen=True)
class CollectorRegistration:
    """Resolved collector catalog entry."""

    collector: CollectorSpec
    collector_id: str
    collector_plugin_id: str
    plugin: RegisteredCollectorPlugin
    effective_trust_level: str
    built_in: bool
    is_legacy: bool = False
    legacy_source: str | None = None
    provider_id: str | None = None


@dataclass(frozen=True)
class CollectorRegistrySnapshot:
    """Immutable view of collector registry state."""

    plugins: Mapping[str, RegisteredCollectorPlugin]
    collectors: Mapping[str, CollectorRegistration] = field(default_factory=dict)


@dataclass
class CollectorRegistry:
    """Build collector capability catalogs independent of source interface routes."""

    _plugins: dict[str, RegisteredCollectorPlugin] = field(default_factory=dict)
    _collectors: dict[str, CollectorRegistration] = field(default_factory=dict)

    @classmethod
    def from_provider_registry(
        cls,
        registry: ProviderRegistry,
        *,
        disabled_collector_plugin_ids: set[str] | None = None,
    ) -> "CollectorRegistry":
        return cls.from_provider_snapshot(
            registry.snapshot(),
            disabled_collector_plugin_ids=disabled_collector_plugin_ids,
        )

    @classmethod
    def from_provider_snapshot(
        cls,
        snapshot: ProviderRegistrySnapshot,
        *,
        disabled_collector_plugin_ids: set[str] | None = None,
    ) -> "CollectorRegistry":
        registry = cls()
        if _should_register_preinstalled_tdx_collectors(snapshot):
            registry.register_preinstalled_tdx_collector_plugin(
                disabled_collector_plugin_ids=disabled_collector_plugin_ids,
            )
        for provider_id in sorted(snapshot.providers):
            provider = snapshot.providers[provider_id]
            registry.register_provider_plugin(provider)
        return registry

    def register_preinstalled_tdx_collector_plugin(
        self,
        *,
        disabled_collector_plugin_ids: set[str] | None = None,
    ) -> None:
        """Register the preinstalled TDX collector-only plugin."""

        try:
            from axdata_source_tdx.collectors import TDX_COLLECTOR_PLUGIN_ID, tdx_collector_manifest
        except Exception:
            return

        manifest = tdx_collector_manifest()
        validate_manifest(manifest)
        disabled = TDX_COLLECTOR_PLUGIN_ID in set(disabled_collector_plugin_ids or ())
        plugin = RegisteredCollectorPlugin(
            plugin_id=TDX_COLLECTOR_PLUGIN_ID,
            manifest=manifest,
            status=PluginStatus.DISABLED.value if disabled else PluginStatus.ENABLED.value,
            effective_trust_level="official",
            enabled=not disabled,
            built_in=True,
            source_provider_id=None,
        )
        self._plugins[TDX_COLLECTOR_PLUGIN_ID] = plugin
        if disabled:
            return
        for collector in manifest.collectors:
            self.register_collector(collector, plugin=plugin)

    def register_provider_plugin(self, provider: RegisteredProvider) -> None:
        """Import enabled collectors from a ProviderRegistry plugin snapshot."""

        if provider.status != PluginStatus.ENABLED.value or not provider.enabled:
            return
        if not provider.manifest.collectors:
            return

        plugin_id = provider.manifest.identity
        is_legacy_provider_manifest = provider.manifest.provider is not None
        legacy_source = "provider_manifest" if is_legacy_provider_manifest else None
        plugin = RegisteredCollectorPlugin(
            plugin_id=plugin_id,
            manifest=provider.manifest,
            status=provider.status,
            effective_trust_level=provider.effective_trust_level,
            enabled=provider.enabled,
            built_in=provider.built_in,
            error=provider.error,
            legacy_source=legacy_source,
            source_provider_id=provider.provider_id if is_legacy_provider_manifest else None,
        )
        self._plugins[plugin_id] = plugin
        for collector in provider.manifest.collectors:
            collector_legacy_source = (
                legacy_source if is_legacy_provider_manifest and collector.is_legacy else None
            )
            self.register_collector(
                collector,
                plugin=plugin,
                provider_id=provider.provider_id if collector_legacy_source else None,
                legacy_source=collector_legacy_source,
            )

    def register_collector(
        self,
        collector: CollectorSpec,
        *,
        plugin: RegisteredCollectorPlugin,
        provider_id: str | None = None,
        legacy_source: str | None = None,
    ) -> None:
        collector_id = collector.collector_id
        effective_legacy_source = collector.legacy_source or legacy_source
        effective_collector = collector
        if effective_legacy_source and collector.legacy_source != effective_legacy_source:
            effective_collector = replace(collector, legacy_source=effective_legacy_source)
        registration = CollectorRegistration(
            collector=effective_collector,
            collector_id=collector_id,
            collector_plugin_id=effective_collector.collector_plugin_id or plugin.plugin_id,
            plugin=plugin,
            effective_trust_level=plugin.effective_trust_level,
            built_in=plugin.built_in,
            is_legacy=effective_collector.is_legacy or effective_legacy_source is not None,
            legacy_source=effective_legacy_source,
            provider_id=provider_id,
        )
        existing = self._collectors.get(collector_id)
        if existing is not None:
            return
        self._collectors[collector_id] = registration

    def snapshot(self) -> CollectorRegistrySnapshot:
        return CollectorRegistrySnapshot(
            plugins=dict(self._plugins),
            collectors=dict(self._collectors),
        )

    def list_collectors(self) -> tuple[CollectorRegistration, ...]:
        return tuple(self._collectors.values())


def build_collector_registry(
    *,
    provider_registry: ProviderRegistry | None = None,
    plugin_config: Any | None = None,
    data_root: str | Path | None = None,
    discover_entry_points: bool = True,
) -> CollectorRegistry:
    """Build the collector registry from discovered plugin manifests."""

    from .plugin_config import load_plugin_config

    config = plugin_config or load_plugin_config(data_root=data_root)
    if provider_registry is None:
        from .provider_catalog import build_builtin_provider_registry

        provider_registry = build_builtin_provider_registry(
            plugin_config=config,
            data_root=data_root,
            discover_entry_points=discover_entry_points,
        )
    disabled_collector_plugin_ids: set[str] = set()
    disabled_collector_plugin_ids.update(getattr(config, "disabled_provider_ids", ()) or ())
    disabled_collector_plugin_ids.update(getattr(config, "removed_provider_ids", ()) or ())
    return CollectorRegistry.from_provider_registry(
        provider_registry,
        disabled_collector_plugin_ids=disabled_collector_plugin_ids,
    )


def _should_register_preinstalled_tdx_collectors(snapshot: ProviderRegistrySnapshot) -> bool:
    provider = snapshot.providers.get("axdata.source.tdx_external")
    return provider is not None
