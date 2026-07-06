"""Registry-backed catalog helpers."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from .plugin_config import PluginConfig
    from .plugins import CollectorSpec, InterfaceSpec
    from .provider_registry import InterfaceRegistration, ProviderRegistry
    from .collector_registry import CollectorRegistration


def build_builtin_provider_registry(
    *,
    plugin_config: PluginConfig | None = None,
    data_root: str | Path | None = None,
    discover_entry_points: bool = True,
) -> ProviderRegistry:
    """Build a registry containing the current built-in providers."""

    from .plugin_config import load_plugin_config
    from .provider_registry import ProviderRegistry

    config = plugin_config or load_plugin_config(data_root=data_root)
    registry = ProviderRegistry(
        enabled_provider_ids=set(config.enabled_provider_ids),
        disabled_provider_ids=set(config.disabled_provider_ids) | set(getattr(config, "removed_provider_ids", ())),
        provider_overrides=config.provider_overrides,
    )
    from .builtin_providers import list_builtin_providers

    for provider in list_builtin_providers():
        registry.register_builtin_provider(provider)
    if discover_entry_points:
        _ensure_axdata_managed_plugin_path(data_root=data_root)
        registry.discover_entry_points()
        _register_repo_preinstalled_source_plugins(registry, config=config)
    return registry


def list_registry_interface_dicts(
    *,
    plugin_config: PluginConfig | None = None,
    data_root: str | Path | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return current source request catalog entries enriched with registry metadata.

    The old catalog fields are preserved so existing API and frontend callers
    remain compatible while the registry becomes the catalog authority.
    """

    from .sources import list_request_interface_dicts

    legacy_entries = {
        str(entry["name"]): dict(entry)
        for entry in list_request_interface_dicts()
    }
    from .plugin_config import load_plugin_config

    config = plugin_config or load_plugin_config(data_root=data_root)
    removed_provider_ids = set(getattr(config, "removed_provider_ids", ()))
    registry = build_builtin_provider_registry(plugin_config=plugin_config, data_root=data_root)
    snapshot = registry.snapshot()
    enriched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for interface_name in sorted(snapshot.interfaces):
        route = snapshot.interfaces.get(interface_name)
        entry = _merge_interface_catalog_entry(
            legacy_entries.get(interface_name),
            route.interface,
        )
        if route is not None:
            entry.update(_route_metadata(route, snapshot.providers.get(route.provider_id)))
            entry["source_code"] = route.interface.source_code
            entry["source_name_zh"] = route.interface.source_name_zh
        enriched.append(entry)
        seen.add(interface_name)

    for provider in sorted(snapshot.providers.values(), key=lambda item: item.provider_id):
        if provider.provider_id in removed_provider_ids:
            continue
        if _hide_unavailable_provider_interfaces(provider):
            continue
        if provider.status == "enabled" and provider.enabled:
            continue
        for interface in sorted(provider.manifest.interfaces, key=lambda item: item.name):
            if interface.name in seen:
                continue
            entry = _merge_interface_catalog_entry(
                legacy_entries.get(interface.name),
                interface,
            )
            entry.update(_unavailable_interface_metadata(interface, provider))
            entry["source_code"] = interface.source_code
            entry["source_name_zh"] = interface.source_name_zh
            enriched.append(entry)
            seen.add(interface.name)
    return tuple(enriched)


def list_registry_collector_dicts(
    *,
    plugin_config: PluginConfig | None = None,
    data_root: str | Path | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return enabled collector capabilities enriched with registry metadata.

    The public helper name stays stable for CLI/API compatibility. The catalog
    rows now come from CollectorRegistry, with Provider manifest collectors
    imported as legacy entries.
    """

    from .plugin_config import load_plugin_config

    config = plugin_config or load_plugin_config(data_root=data_root)
    provider_registry = build_builtin_provider_registry(plugin_config=config, data_root=data_root)
    from .collector_registry import build_collector_registry

    registry = build_collector_registry(
        provider_registry=provider_registry,
        plugin_config=config,
        data_root=data_root,
    )
    snapshot = registry.snapshot()
    rows: list[dict[str, Any]] = []
    for collector_id in sorted(snapshot.collectors):
        route = snapshot.collectors[collector_id]
        rows.append(_collector_to_catalog_entry(route))
    return tuple(rows)


def _interface_to_catalog_entry(interface: InterfaceSpec) -> dict[str, Any]:
    """Convert a registry-only interface into the legacy catalog wire shape."""

    return {
        "name": interface.name,
        "interface_name": interface.name,
        "display_name_zh": interface.display_name_zh,
        "source_code": interface.source_code,
        "source_name_zh": interface.source_name_zh,
        "category": interface.category or "/".join(interface.menu_path),
        "request_mode": interface.request_mode,
        "first_stage_strategy": "provider_registry",
        "source_ability": "provider_registry",
        "description": interface.notes,
        "summary_zh": interface.summary_zh,
        "description_zh": interface.description_zh,
        "params_note_zh": interface.params_note_zh,
        "params_example_zh": interface.params_example_zh,
        "persisted": False,
        "parameters": [
            {
                "name": parameter.name,
                "dtype": parameter.type,
                "required": parameter.required,
                "description": parameter.description,
                "description_zh": parameter.display_name_zh,
                **({"default": parameter.default} if parameter.default is not None else {}),
            }
            for parameter in interface.parameters
        ],
        "fields": [
            {
                "name": field.name,
                "dtype": field.type,
                "description": field.description,
                "description_zh": field.display_name_zh,
            }
            for field in interface.fields
        ],
        "example": _example_to_catalog_entry(interface),
        "reference_sections": [section.to_dict() for section in interface.reference_sections],
    }


def _merge_interface_catalog_entry(
    legacy_entry: Mapping[str, Any] | None,
    interface: InterfaceSpec,
) -> dict[str, Any]:
    """Keep legacy-only fields, but use the plugin InterfaceSpec for docs content."""

    entry = dict(legacy_entry or {})
    interface_entry = _interface_to_catalog_entry(interface)
    for key in (
        "name",
        "interface_name",
        "display_name_zh",
        "source_code",
        "source_name_zh",
        "category",
        "request_mode",
        "parameters",
        "fields",
        "example",
        "reference_sections",
        "summary_zh",
        "description_zh",
        "params_note_zh",
        "params_example_zh",
    ):
        entry[key] = interface_entry[key]
    if interface_entry["description_zh"]:
        entry["description"] = interface_entry["description_zh"]
    elif interface_entry["description"]:
        entry["description"] = interface_entry["description"]
    return entry


def _collector_to_catalog_entry(
    route: CollectorRegistration,
) -> dict[str, Any]:
    collector = route.collector
    plugin = route.plugin
    plugin_manifest = plugin.manifest if plugin is not None else None
    return {
        **_collector_spec_to_dict(collector),
        "collector_plugin_id": route.collector_plugin_id,
        "legacy_source": route.legacy_source,
        "is_legacy": route.is_legacy,
        "provider_id": route.provider_id or route.collector_plugin_id,
        "legacy_provider_id": route.provider_id if route.is_legacy else None,
        "collector_plugin_status": plugin.status,
        "source_code": plugin.source_code if plugin is not None else "plugin",
        "source_name_zh": _manifest_display_name(plugin_manifest),
        "declared_trust_level": _manifest_declared_trust_level(plugin_manifest),
        "effective_trust_level": route.effective_trust_level,
        "built_in": route.built_in,
        "plugin_status": plugin.status if plugin is not None else "enabled",
        "enabled": plugin.enabled if plugin is not None else True,
        "required_config": (
            [config.to_dict() for config in plugin_manifest.required_config]
            if plugin_manifest is not None
            else []
        ),
        "config_schema": (
            plugin_manifest.config_schema.to_dict()
            if plugin_manifest is not None
            else {"required_config": []}
        ),
    }


def _collector_spec_to_dict(collector: CollectorSpec) -> dict[str, Any]:
    return {
        "name": collector.name,
        "collector_id": collector.collector_id,
        "collector_name": collector.name,
        "display_name_zh": collector.display_name_zh,
        "description": collector.description,
        "collector_plugin_id": collector.collector_plugin_id,
        "dataset_id": collector.dataset_id,
        "asset_class": collector.asset_class,
        "category": collector.category,
        "collector_config_schema": dict(collector.config_schema),
        "quality": dict(collector.quality),
        "runner_entry": collector.runner_entry,
        "lifecycle_status": collector.lifecycle_status,
        "legacy_source": collector.legacy_source or (
            "provider_manifest" if collector.is_legacy else None
        ),
        "is_legacy": collector.is_legacy,
        "interfaces": list(collector.interfaces),
        "downloader_profile": collector.downloader_profile,
        "resource_group": collector.resource_group,
        "default_schedule": dict(collector.default_schedule),
        "default_params": dict(collector.default_params),
        "required_interfaces": list(collector.required_interfaces),
        "required_datasets": list(collector.required_datasets),
        "output": dict(collector.output),
    }


def _ensure_axdata_managed_plugin_path(*, data_root: str | Path | None = None) -> None:
    """Make AxData-managed AXP installs discoverable in this process."""

    try:
        from .axp import axp_plugin_site_packages

        site_packages = axp_plugin_site_packages(data_root=data_root)
    except Exception:
        return
    if not site_packages.exists():
        return
    import sys

    path = str(site_packages)
    if path not in sys.path:
        sys.path.insert(0, path)


def _register_repo_preinstalled_source_plugins(registry: ProviderRegistry, *, config: PluginConfig) -> None:
    """Expose repository-shipped source packages as preinstalled plugins in dev.

    Editable installs and wheels are still discovered through entry points. This
    fallback is only for the local workspace shape where a shipped source package
    exists under ``packages/`` but has not been installed into the current
    virtualenv yet.
    """

    from .provider_registry import DEFAULT_ENABLED_ENTRY_POINT_DISTS

    existing = set(registry.snapshot().providers)
    disabled = set(config.disabled_provider_ids) | set(getattr(config, "removed_provider_ids", ()))
    for spec in _repo_preinstalled_source_specs():
        if spec["provider_id"] in existing:
            continue
        manifest_path = _repo_root() / spec["package_dir"] / "src" / spec["module_name"] / "axdata-provider.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = _manifest_from_file(manifest_path)
        except Exception:
            continue
        enabled = spec["provider_id"] in set(config.enabled_provider_ids) or (
            spec["provider_id"] in DEFAULT_ENABLED_ENTRY_POINT_DISTS
            and spec["provider_id"] not in disabled
        )
        provider = _load_repo_provider(spec) if enabled else None
        registry.register_manifest(
            manifest,
            provider=provider,
            built_in=True,
            enabled=enabled,
        )


def _repo_preinstalled_source_specs() -> tuple[dict[str, str], ...]:
    return (
        {
            "provider_id": "axdata.source.tdx_external",
            "package_dir": "packages/axdata-source-tdx",
            "module_name": "axdata_source_tdx",
            "provider_module": "axdata_source_tdx.provider",
        },
        {
            "provider_id": "axdata.source.tdx_ext_external",
            "package_dir": "packages/axdata-source-tdx-ext",
            "module_name": "axdata_source_tdx_ext",
            "provider_module": "axdata_source_tdx_ext.provider",
        },
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _manifest_from_file(path: Path):
    from .plugins import ProviderManifest

    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProviderManifest.from_dict(payload)


def _load_repo_provider(spec: Mapping[str, str]) -> Any | None:
    src_path = _repo_root() / spec["package_dir"] / "src"
    if src_path.is_dir():
        src_text = str(src_path)
        if src_text not in sys.path:
            sys.path.insert(0, src_text)
    module = importlib.import_module(spec["provider_module"])
    return getattr(module, "provider", None)


def _hide_unavailable_provider_interfaces(provider: Any) -> bool:
    """Keep disabled TDX Ext out of the runtime interface tree until enabled."""

    provider_id = str(getattr(provider, "provider_id", "") or "")
    source_code = str(getattr(provider, "source_code", "") or "")
    if provider_id == "axdata.source.tdx_ext_external" or source_code == "tdx_ext":
        return True
    return False


def _example_to_catalog_entry(interface: InterfaceSpec) -> dict[str, Any]:
    if not interface.examples:
        return {"request": {}, "response": []}
    example = interface.examples[0]
    request = example.request.get("params", example.request)
    response = example.response.get("data", example.response)
    return {
        "request": dict(request) if isinstance(request, dict) else {},
        "response": list(response) if isinstance(response, list) else [],
    }


def _route_metadata(route: InterfaceRegistration, provider: Any | None = None) -> dict[str, Any]:
    declared_trust_level = (
        provider.manifest.provider.declared_trust_level
        if provider is not None and provider.manifest.provider is not None
        else ("official" if route.built_in else "community")
    )
    required_config = (
        [config.to_dict() for config in provider.manifest.required_config]
        if provider is not None
        else []
    )
    return {
        "provider_id": route.provider_id,
        "asset_class": route.interface.asset_class,
        "menu_path": list(route.interface.menu_path),
        "collection": route.interface.collection.to_dict(),
        "declared_trust_level": declared_trust_level,
        "effective_trust_level": route.effective_trust_level,
        "plugin_status": "enabled",
        "enabled": provider.enabled if provider is not None else True,
        "built_in": route.built_in,
        "required_config": required_config,
        "config_schema": provider.manifest.config_schema.to_dict() if provider is not None else {"required_config": []},
        "collector_count": len(provider.manifest.collectors) if provider is not None else 0,
        "dependency_count": len(provider.manifest.dependencies) if provider is not None else 0,
    }


def _unavailable_interface_metadata(interface: InterfaceSpec, provider: Any) -> dict[str, Any]:
    from .diagnostics import provider_guidance

    guidance = provider_guidance(
        provider_id=provider.provider_id,
        source_code=provider.source_code,
        status=provider.status,
        enabled=provider.enabled,
        built_in=provider.built_in,
        error=provider.error,
    )
    return {
        "provider_id": provider.provider_id,
        "asset_class": interface.asset_class,
        "menu_path": list(interface.menu_path),
        "collection": interface.collection.to_dict(),
        "declared_trust_level": _manifest_declared_trust_level(provider.manifest),
        "effective_trust_level": provider.effective_trust_level,
        "plugin_status": provider.status,
        "enabled": provider.enabled,
        "built_in": provider.built_in,
        "required_config": [config.to_dict() for config in provider.manifest.required_config],
        "config_schema": provider.manifest.config_schema.to_dict(),
        "collector_count": len(provider.manifest.collectors),
        "dependency_count": len(provider.manifest.dependencies),
        **guidance,
    }


def _manifest_display_name(manifest: Any | None) -> str:
    if manifest is None:
        return "未知插件"
    if manifest.provider is not None:
        return manifest.provider.source_name_zh
    if manifest.plugin is not None:
        return manifest.plugin.name_zh
    return "未知插件"


def _manifest_declared_trust_level(manifest: Any | None) -> str:
    if manifest is None or manifest.provider is None:
        return "community"
    return manifest.provider.declared_trust_level
