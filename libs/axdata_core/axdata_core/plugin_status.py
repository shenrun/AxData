"""Shared Provider status projection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .plugins import (
    ConfigSchema,
    PluginStatus,
    PluginTrustLevel,
    ProviderInfo,
    ProviderManifest,
)

TDX_PROVIDER_ID = "axdata.source.tdx_external"
TDX_EXT_PROVIDER_ID = "axdata.source.tdx_ext_external"
PREINSTALLED_UNINSTALL_MODE = "managed_disable"


@dataclass(frozen=True)
class ExpectedProvider:
    provider_id: str
    source_code: str
    source_name_zh: str
    package_hint: str
    install_hint: str
    interface_count: int = 0
    status_message: str = ""
    next_action: str = ""


EXPECTED_OPTIONAL_PROVIDERS: tuple[ExpectedProvider, ...] = (
    ExpectedProvider(
        provider_id=TDX_PROVIDER_ID,
        source_code="tdx",
        source_name_zh="通达信",
        package_hint="axdata-source-tdx",
        install_hint="请安装/启用 TDX 插件。",
        interface_count=90,
        status_message="TDX 插件未安装或当前 Python 环境不可发现；普通 TDX 接口不会出现在运行目录。",
        next_action="需要股票、指数、ETF、K 线、F10、短线等普通 TDX 接口时，请安装/启用 TDX 插件。",
    ),
    ExpectedProvider(
        provider_id=TDX_EXT_PROVIDER_ID,
        source_code="tdx_ext",
        source_name_zh="通达信扩展行情",
        package_hint="axdata-source-tdx-ext",
        install_hint="请安装/启用 TDX Ext 扩展行情插件。",
        interface_count=31,
        status_message="TDX Ext 扩展行情插件未安装或当前 Python 环境不可发现；扩展行情接口不会出现在运行目录。",
        next_action="需要期货、期权、基金、债券、外汇、宏观等扩展行情接口时，请安装/启用 TDX Ext 扩展行情插件。",
    ),
)


def expected_provider_statuses(existing_provider_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Return missing optional Provider rows that should be visible to users."""

    existing = set(existing_provider_ids)
    return [
        _expected_provider_row(expected)
        for expected in EXPECTED_OPTIONAL_PROVIDERS
        if expected.provider_id not in existing
    ]


def provider_management_fields(
    provider: Any,
    *,
    managed_provider_ids: Iterable[str] = (),
    removed_provider_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Return install/action fields shared by CLI, API, diagnostics, and Web."""

    provider_id = str(getattr(provider, "provider_id", "") or "")
    status = str(getattr(provider, "status", "") or "")
    enabled = bool(getattr(provider, "enabled", False))
    built_in = bool(getattr(provider, "built_in", False))
    entry_point = getattr(provider, "entry_point", None)
    install_source = install_source_for_provider(
        provider,
        managed_provider_ids=set(managed_provider_ids),
    )
    is_removed = provider_id in set(removed_provider_ids)
    can_enable = status not in {
        PluginStatus.ENABLED.value,
        PluginStatus.FAILED.value,
        PluginStatus.INCOMPATIBLE.value,
        PluginStatus.CONFLICT.value,
        "missing",
    } or is_removed
    can_disable = enabled
    provider_kind = provider_kind_for_provider(provider)
    uninstall_mode = uninstall_mode_for_source(install_source=install_source)
    can_uninstall = install_source in {"preinstalled", "axp_managed"}
    uninstall_block_reason = None
    if not can_uninstall:
        uninstall_block_reason = uninstall_block_reason_for_source(
            install_source=install_source,
            built_in=built_in,
            provider_id=provider_id,
        )
    return {
        "install_source": install_source,
        "provider_kind": provider_kind,
        "lifecycle_status": "uninstalled" if is_removed else status,
        "can_enable": can_enable,
        "can_disable": can_disable,
        "can_uninstall": can_uninstall,
        "uninstall_mode": uninstall_mode,
        "uninstall_block_reason": uninstall_block_reason,
    }


def install_source_for_provider(
    provider: Any,
    *,
    managed_provider_ids: set[str] | None = None,
) -> str:
    provider_id = str(getattr(provider, "provider_id", "") or "")
    if bool(getattr(provider, "built_in", False)):
        return "preinstalled"
    if _repo_preinstalled_provider_exists(provider_id):
        return "preinstalled"
    if managed_provider_ids and provider_id in managed_provider_ids:
        return "axp_managed"
    entry_point = getattr(provider, "entry_point", None)
    if entry_point is not None:
        dist = getattr(entry_point, "dist", None)
        if _distribution_is_editable(dist):
            return "editable/development"
        return "python_environment"
    if getattr(provider, "provider", None) is not None:
        return "editable/development"
    return "unknown"


def provider_kind_for_provider(provider: Any) -> str:
    """Return the high-level plugin kind for API/CLI/Web display."""

    provider_id = str(getattr(provider, "provider_id", "") or "")
    source_code = str(getattr(provider, "source_code", "") or "")
    if provider_id == "axdata.core" or source_code == "core":
        return "core"
    manifest = getattr(provider, "manifest", None)
    has_interfaces = bool(getattr(manifest, "interfaces", ()) or ())
    has_collectors = bool(getattr(manifest, "collectors", ()) or ())
    if has_interfaces:
        return "source_plugin"
    if has_collectors:
        return "collector_plugin"
    return "tool_plugin"


def uninstall_mode_for_source(*, install_source: str) -> str | None:
    if install_source == "axp_managed":
        return "physical_remove"
    if install_source == "preinstalled":
        return PREINSTALLED_UNINSTALL_MODE
    return None


def uninstall_block_reason_for_source(
    *,
    install_source: str,
    built_in: bool,
    provider_id: str,
) -> str | None:
    if install_source == "axp_managed":
        return None
    if built_in or install_source == "preinstalled":
        return None
    if install_source == "core":
        return "AxData Core 是数据库、插件协议、任务平台和 API/Web/CLI 宿主，不能卸载。"
    if install_source in {"python_environment", "editable/development"}:
        return "该插件不是通过 AxData AXP 管理安装，请使用 pip uninstall 或移除开发路径。"
    if install_source == "missing":
        return "当前环境未发现该插件，AxData 无可卸载的插件文件。"
    return f"Provider {provider_id} 不是 AxData AXP 管理安装，不能在 AxData 内卸载。"


def managed_provider_ids(*, data_root: str | Path | None = None) -> set[str]:
    try:
        from .axp import list_installed_axp_plugins

        return {
            plugin.provider_id
            for plugin in list_installed_axp_plugins(data_root=data_root)
        }
    except Exception:
        return set()


def provider_status_row(
    provider: Any,
    *,
    provider_overrides: Mapping[str, str] | None = None,
    snapshot: Any | None = None,
    managed_provider_ids: Iterable[str] = (),
    removed_provider_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Serialize one registry Provider with management/action fields."""

    from .diagnostics import provider_guidance

    manifest = provider.manifest
    provider_info = manifest.provider
    plugin_info = manifest.plugin
    interfaces = [interface.name for interface in manifest.interfaces]
    downloaders = [profile.name for profile in manifest.downloaders]
    collectors = [collector.name for collector in manifest.collectors]
    dependencies = [dependency.to_dict() for dependency in manifest.dependencies]
    removed_ids = set(removed_provider_ids)
    is_removed = provider.provider_id in removed_ids
    display_status = "uninstalled" if is_removed else provider.status
    display_enabled = False if is_removed else provider.enabled
    guidance = provider_guidance(
        provider_id=provider.provider_id,
        source_code=provider.source_code,
        status=display_status,
        enabled=display_enabled,
        built_in=provider.built_in,
        error=provider.error,
    )
    return {
        "provider_id": provider.provider_id,
        "source_code": provider.source_code,
        "source_name_zh": _manifest_display_name(manifest),
        "version": _manifest_version(manifest),
        "plugin": plugin_info.to_dict() if plugin_info is not None else None,
        "status": display_status,
        "enabled": display_enabled,
        "built_in": provider.built_in,
        "declared_trust_level": provider_info.declared_trust_level if provider_info is not None else "community",
        "effective_trust_level": provider.effective_trust_level,
        "interface_count": len(interfaces),
        "downloader_count": len(downloaders),
        "collector_count": len(collectors),
        "dependency_count": len(dependencies),
        "required_config": [config.to_dict() for config in manifest.required_config],
        "config_schema": manifest.config_schema.to_dict(),
        "dependencies": dependencies,
        "description": provider_info.description if provider_info is not None else (plugin_info.description if plugin_info is not None else ""),
        "homepage": provider_info.homepage if provider_info is not None else None,
        "license": provider_info.license if provider_info is not None else None,
        "interfaces": interfaces,
        "downloaders": downloaders,
        "collectors": collectors,
        "overridden_interfaces": _overridden_interfaces(provider.provider_id, provider_overrides),
        "conflicting_interfaces": _conflicting_interfaces(provider, snapshot, provider_overrides),
        "error": provider.error,
        **provider_management_fields(
            provider,
            managed_provider_ids=managed_provider_ids,
            removed_provider_ids=removed_ids,
        ),
        **guidance,
    }


def _expected_provider_row(expected: ExpectedProvider) -> dict[str, Any]:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id=expected.provider_id,
            source_code=expected.source_code,
            source_name_zh=expected.source_name_zh,
            version="unknown",
            declared_trust_level=PluginTrustLevel.COMMUNITY.value,
            description=expected.install_hint,
        ),
        interfaces=(),
        config_schema=ConfigSchema(),
    )
    provider_like = _ProviderLike(
        provider_id=expected.provider_id,
        source_code=expected.source_code,
        source_name_zh=expected.source_name_zh,
        version="unknown",
        status="missing",
        enabled=False,
        built_in=False,
        effective_trust_level=PluginTrustLevel.COMMUNITY.value,
        error=expected.status_message,
        manifest=manifest,
    )
    row = provider_status_row(provider_like, managed_provider_ids=())
    row.update(
        {
            "interface_count": expected.interface_count,
            "status_message": expected.status_message,
            "next_action": expected.next_action,
            "action_command": f"pip install {expected.package_hint}",
            "install_source": "missing",
            "can_enable": False,
            "can_disable": False,
            "can_uninstall": False,
            "provider_kind": "source_plugin",
            "uninstall_mode": None,
            "uninstall_block_reason": uninstall_block_reason_for_source(
                install_source="missing",
                built_in=False,
                provider_id=expected.provider_id,
            ),
            "expected_package": expected.package_hint,
        }
    )
    return row


@dataclass(frozen=True)
class _ProviderLike:
    provider_id: str
    source_code: str
    source_name_zh: str
    version: str
    status: str
    enabled: bool
    built_in: bool
    effective_trust_level: str
    error: str
    manifest: ProviderManifest
    entry_point: Any | None = None


def _distribution_is_editable(distribution: Any | None) -> bool:
    if distribution is None:
        return False
    try:
        raw = distribution.read_text("direct_url.json")
    except Exception:
        return False
    if not raw:
        return False
    try:
        import json

        payload = json.loads(raw)
    except Exception:
        return False
    dir_info = payload.get("dir_info") if isinstance(payload, Mapping) else None
    return isinstance(dir_info, Mapping) and dir_info.get("editable") is True


def _repo_preinstalled_provider_exists(provider_id: str) -> bool:
    package_paths = {
        TDX_PROVIDER_ID: ("packages", "axdata-source-tdx", "src", "axdata_source_tdx", "axdata-provider.json"),
        TDX_EXT_PROVIDER_ID: (
            "packages",
            "axdata-source-tdx-ext",
            "src",
            "axdata_source_tdx_ext",
            "axdata-provider.json",
        ),
    }
    parts = package_paths.get(provider_id)
    if parts is None:
        return False
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root.joinpath(*parts).is_file()


def _manifest_display_name(manifest: ProviderManifest) -> str:
    if manifest.provider is not None:
        return manifest.provider.source_name_zh
    if manifest.plugin is not None:
        return manifest.plugin.name_zh
    return "未知插件"


def _manifest_version(manifest: ProviderManifest) -> str:
    if manifest.provider is not None:
        return manifest.provider.version
    if manifest.plugin is not None:
        return manifest.plugin.version
    return "0.0.0"


def _overridden_interfaces(provider_id: str, provider_overrides: Any | None = None) -> list[str]:
    overrides = dict(provider_overrides or {})
    return [
        interface_name
        for interface_name, override_provider_id in sorted(overrides.items())
        if override_provider_id == provider_id
    ]


def _conflicting_interfaces(
    provider: Any,
    snapshot: Any | None,
    provider_overrides: Any | None = None,
) -> list[dict[str, Any]]:
    if snapshot is None:
        return []

    overrides = dict(provider_overrides or {})
    provider_interfaces = {interface.name for interface in provider.manifest.interfaces}
    conflicts: list[dict[str, Any]] = []
    for interface_name in sorted(provider_interfaces):
        contenders = [
            candidate
            for candidate in snapshot.providers.values()
            if candidate.enabled
            and candidate.status not in {"disabled", "failed", "incompatible"}
            and interface_name in {interface.name for interface in candidate.manifest.interfaces}
        ]
        if len(contenders) <= 1:
            continue
        route = snapshot.interfaces.get(interface_name)
        conflicts.append(
            {
                "interface_name": interface_name,
                "providers": sorted(candidate.provider_id for candidate in contenders),
                "resolved_provider_id": route.provider_id if route is not None else None,
                "override_provider_id": overrides.get(interface_name),
            }
        )
    return conflicts
