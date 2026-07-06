"""AXP plugin archive preview and install helpers.

AXP is a second-stage Web-friendly envelope around ordinary Python wheels.  The
wheel + entry point + embedded manifest remain the real plugin format.
"""

from __future__ import annotations

import gc
import hashlib
import base64
from email.parser import Parser
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping
import re

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from .plugins import (
    DependencySpec,
    MANIFEST_FILE_NAME,
    ManifestError,
    PLUGIN_MANIFEST_FILE_NAME,
    ProviderManifest,
    validate_manifest,
)

AXP_MANIFEST_FILE_NAME = "manifest.json"
AXP_CHECKSUMS_FILE_NAME = "checksums.txt"
AXP_PLUGINS_DIR_NAME = "plugins"
AXP_SITE_PACKAGES_DIR_NAME = "site-packages"
AXP_SITE_PTH_NAME = "axdata_plugins.pth"
AXP_INSTALL_RECORDS_DIR_NAME = "installed"
AXP_INSTALL_RECORD_VERSION = 1
_BRIDGE_WHEEL_VERSION = "0.1.0"
_REPO_PACKAGE_EXPORTS: Mapping[str, tuple[str, ...]] = {
    "axdata.source.tdx_external": ("packages", "axdata-source-tdx"),
    "axdata.source.tdx_ext_external": ("packages", "axdata-source-tdx-ext"),
    "axdata.source.tencent_external": ("packages", "axdata-source-tencent"),
    "axdata.source.cninfo_external": ("packages", "axdata-source-cninfo"),
    "axdata.collector.tdx": ("packages", "axdata-source-tdx"),
}


class AxpError(ValueError):
    """Raised when an AXP archive cannot be previewed or installed."""


class AxpAlreadyInstalledError(AxpError):
    """Raised when an AXP Provider is already managed by AxData."""


class AxpUninstallError(AxpError):
    """Raised when an AxData-managed plugin cannot be uninstalled."""


@dataclass(frozen=True)
class AxpExportResult:
    """Result of exporting one discovered plugin capability to an AXP archive."""

    provider_id: str
    path: str
    file_name: str
    manifest: ProviderManifest
    wheels: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "path": self.path,
            "file_name": self.file_name,
            "manifest": self.manifest.to_dict(),
            "wheels": list(self.wheels),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class AxpWheelInfo:
    """Wheel entry discovered inside an AXP archive."""

    path: str
    file_name: str
    size: int
    sha256: str
    checksum_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "file_name": self.file_name,
            "size": self.size,
            "sha256": self.sha256,
            "checksum_status": self.checksum_status,
        }


@dataclass(frozen=True)
class AxpDependencyStatus:
    """Install-time dependency status for one required or optional package."""

    name: str
    version_spec: str | None = None
    optional: bool = False
    source: str | None = None
    declared_wheel: str | None = None
    status: str = "unknown"
    installed_version: str | None = None
    bundled_wheel: str | None = None
    bundled_version: str | None = None
    requirement: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version_spec": self.version_spec,
            "optional": self.optional,
            "source": self.source,
            "declared_wheel": self.declared_wheel,
            "status": self.status,
            "installed_version": self.installed_version,
            "bundled_wheel": self.bundled_wheel,
            "bundled_version": self.bundled_version,
            "requirement": self.requirement,
            "message": self.message,
            "blocking": self.is_blocking_offline,
        }

    @property
    def is_blocking_offline(self) -> bool:
        if self.optional and self.status in {"missing", "version_mismatch", "optional_missing"}:
            return False
        return self.status in {
            "invalid",
            "missing",
            "version_mismatch",
            "missing_bundled_wheel",
            "bundled_version_mismatch",
        }

    @property
    def can_be_installed_online(self) -> bool:
        return (not self.optional) and self.status in {"missing", "version_mismatch"}


@dataclass(frozen=True)
class AxpPreview:
    """Install-before-enable preview for one AXP archive."""

    path: str
    manifest: ProviderManifest
    manifest_source: str
    wheels: tuple[AxpWheelInfo, ...]
    readme: str | None = None
    license_text: str | None = None
    dependency_status: tuple[AxpDependencyStatus, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def provider_id(self) -> str:
        return self.manifest.identity

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "provider_id": self.provider_id,
            "source_code": _manifest_source_code(self.manifest),
            "source_name_zh": _manifest_name_zh(self.manifest),
            "version": _manifest_version(self.manifest),
            "declared_trust_level": _manifest_declared_trust(self.manifest),
            "effective_trust_level": "community",
            "status_after_install": "disabled",
            "manifest_source": self.manifest_source,
            "manifest": self.manifest.to_dict(),
            "interfaces": [interface.name for interface in self.manifest.interfaces],
            "downloaders": [profile.name for profile in self.manifest.downloaders],
            "collectors": [collector.name for collector in self.manifest.collectors],
            "dependencies": [dependency.to_dict() for dependency in self.manifest.dependencies],
            "dependency_status": [status.to_dict() for status in self.dependency_status],
            "interface_count": len(self.manifest.interfaces),
            "downloader_count": len(self.manifest.downloaders),
            "collector_count": len(self.manifest.collectors),
            "dependency_count": len(self.manifest.dependencies),
            "dependency_status_count": len(self.dependency_status),
            "missing_dependencies": [
                status.to_dict()
                for status in self.dependency_status
                if status.status in {"missing", "missing_bundled_wheel"}
                and not status.optional
            ],
            "unsatisfied_dependencies": [
                status.to_dict()
                for status in self.dependency_status
                if status.status in {"version_mismatch", "bundled_version_mismatch", "invalid"}
                and not status.optional
            ],
            "bundled_dependency_wheels": [
                status.bundled_wheel
                for status in self.dependency_status
                if status.bundled_wheel
            ],
            "can_install_offline": not any(
                status.is_blocking_offline for status in self.dependency_status
            ),
            "wheels": [wheel.to_dict() for wheel in self.wheels],
            "readme": self.readme,
            "license_text": self.license_text,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class AxpInstallResult:
    """Result of installing one AXP archive into AxData's plugin site."""

    preview: AxpPreview
    install_root: str
    site_packages: str
    installed_wheels: tuple[str, ...]
    enabled: bool = False
    replaced: bool = False
    installed_dependency_requirements: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.preview.provider_id,
            "install_root": self.install_root,
            "site_packages": self.site_packages,
            "installed_wheels": list(self.installed_wheels),
            "enabled": self.enabled,
            "replaced": self.replaced,
            "installed_dependency_requirements": list(self.installed_dependency_requirements),
            "status_after_install": "enabled" if self.enabled else "disabled",
            "preview": self.preview.to_dict(),
        }


@dataclass(frozen=True)
class AxpInstalledPlugin:
    """One AxData-managed external plugin install record."""

    provider_id: str
    source_code: str
    source_name_zh: str
    version: str
    installed_path: str
    install_root: str
    site_packages: str
    installed_at: str
    installed_wheels: tuple[str, ...]
    wheel_files: tuple[str, ...]
    package_paths: tuple[str, ...]
    dist_info_paths: tuple[str, ...]
    manifest: ProviderManifest
    enabled: bool = False
    status: str = "disabled"
    effective_trust_level: str = "community"
    built_in: bool = False
    interfaces: tuple[str, ...] = ()
    downloaders: tuple[str, ...] = ()
    collectors: tuple[str, ...] = ()
    dependencies: tuple[Mapping[str, Any], ...] = ()
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        from .diagnostics import provider_guidance
        from .plugin_status import provider_management_fields

        guidance = provider_guidance(
            provider_id=self.provider_id,
            source_code=self.source_code,
            status=self.status,
            enabled=self.enabled,
            built_in=self.built_in,
            error=self.error,
        )
        return {
            "provider_id": self.provider_id,
            "source_code": self.source_code,
            "name": self.source_name_zh,
            "source_name_zh": self.source_name_zh,
            "version": self.version,
            "installed_path": self.installed_path,
            "install_root": self.install_root,
            "site_packages": self.site_packages,
            "installed_at": self.installed_at,
            "installed_wheels": list(self.installed_wheels),
            "enabled": self.enabled,
            "status": self.status,
            "effective_trust_level": self.effective_trust_level,
            "built_in": self.built_in,
            "interfaces": list(self.interfaces),
            "downloaders": list(self.downloaders),
            "collectors": list(self.collectors),
            "dependencies": [dict(dependency) for dependency in self.dependencies],
            "interface_count": len(self.interfaces),
            "downloader_count": len(self.downloaders),
            "collector_count": len(self.collectors),
            "dependency_count": len(self.dependencies),
            "error": self.error,
            "manifest": self.manifest.to_dict(),
            **provider_management_fields(self, managed_provider_ids={self.provider_id}),
            **guidance,
        }


@dataclass(frozen=True)
class AxpUninstallResult:
    """Result of uninstalling one AxData-managed plugin."""

    provider_id: str
    install_root: str
    removed_paths: tuple[str, ...]
    removed_record_path: str
    disabled: bool = False
    uninstall_mode: str = "physical_remove"
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "install_root": self.install_root,
            "removed_paths": list(self.removed_paths),
            "removed_record_path": self.removed_record_path,
            "disabled": self.disabled,
            "uninstall_mode": self.uninstall_mode,
            "message": self.message,
        }


def preview_axp(
    path: str | Path,
    *,
    data_root: str | Path | None = None,
    install_root: str | Path | None = None,
) -> AxpPreview:
    """Return a safe metadata preview without importing plugin code."""

    archive_path = Path(path).expanduser().resolve()
    if not archive_path.exists():
        raise AxpError(f"AXP archive does not exist: {archive_path}")
    warnings: list[str] = []
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            manifest, manifest_source = _read_axp_manifest(archive, names)
            validate_manifest(manifest)
            checksums = _read_checksums(archive, names)
            wheels = _wheel_infos(archive, checksums)
            if not wheels:
                raise AxpError("AXP archive must contain at least one wheel under wheels/.")
            missing_checksums = [wheel.path for wheel in wheels if wheel.checksum_status == "missing"]
            if missing_checksums:
                warnings.append(
                    "checksums.txt does not cover: " + ", ".join(missing_checksums)
                )
            bad_checksums = [wheel.path for wheel in wheels if wheel.checksum_status == "mismatch"]
            if bad_checksums:
                warnings.append(
                    "sha256 mismatch for: " + ", ".join(bad_checksums)
                )
            dependency_wheel_paths = _declared_dependency_wheel_paths(manifest.dependencies)
            plugin_wheels = tuple(
                wheel for wheel in wheels if wheel.path not in dependency_wheel_paths
            )
            dependencies = _merge_dependency_declarations(
                manifest.dependencies,
                _read_pyproject_dependencies(archive, names),
                _read_wheel_dependencies(archive, plugin_wheels),
            )
            dependency_status = _dependency_statuses(
                dependencies,
                wheels=wheels,
                archive=archive,
                site_packages=axp_plugin_site_packages(data_root=data_root)
                if install_root is None
                else Path(install_root).expanduser().resolve() / AXP_SITE_PACKAGES_DIR_NAME,
            )
            blocking_dependencies = [
                status
                for status in dependency_status
                if status.is_blocking_offline
            ]
            if blocking_dependencies:
                warnings.append(
                    "Some required dependencies are missing, unsatisfied, or lack bundled wheels: "
                    + ", ".join(status.name for status in blocking_dependencies)
                )
            optional_missing = [
                status.name
                for status in dependency_status
                if status.optional and status.status in {"missing", "optional_missing", "version_mismatch"}
            ]
            if optional_missing:
                warnings.append(
                    "Optional dependencies are not fully available: "
                    + ", ".join(optional_missing)
                )
            readme = _read_optional_text(archive, names, "README.md")
            license_text = _read_optional_text(archive, names, "LICENSE")
            warnings.append("Installing an AXP does not enable the Provider automatically.")
    except ManifestError as exc:
        raise AxpError(f"AXP manifest is invalid: {exc}") from exc
    except zipfile.BadZipFile as exc:
        raise AxpError(f"AXP archive is not a valid zip file: {archive_path}") from exc

    return AxpPreview(
        path=str(archive_path),
        manifest=manifest,
        manifest_source=manifest_source,
        wheels=wheels,
        readme=readme,
        license_text=license_text,
        dependency_status=tuple(dependency_status),
        warnings=tuple(warnings),
    )


def install_axp(
    path: str | Path,
    *,
    data_root: str | Path | None = None,
    install_root: str | Path | None = None,
    enable: bool = False,
    replace: bool = False,
    write_pth: bool = True,
    allow_online_deps: bool = False,
) -> AxpInstallResult:
    """Install wheels from an AXP archive into AxData's plugin directory.

    Installed Providers remain disabled unless ``enable=True`` is explicitly
    requested.  The MVP uses ``pip install --no-deps --target`` to avoid hidden
    online dependency resolution from Web upload flows.
    """

    root = _plugin_install_root(data_root=data_root, install_root=install_root)
    preview = preview_axp(path, data_root=data_root, install_root=root)
    _validate_installable_preview(preview, allow_online_deps=allow_online_deps)
    existing_record = _install_record_path(root, preview.provider_id)
    was_replaced = existing_record.exists()
    if was_replaced:
        if not replace:
            raise AxpAlreadyInstalledError(
                f"Provider {preview.provider_id!r} is already installed in AxData's plugin directory. "
                "Uninstall it first or pass replace=True."
            )
        _remove_installed_files_from_record(existing_record, root=root)
    site_packages = root / AXP_SITE_PACKAGES_DIR_NAME
    site_packages.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    distributions_before = _site_distributions(site_packages)
    try:
        with zipfile.ZipFile(Path(path).expanduser().resolve()) as archive:
            wheel_dir = root / "wheels"
            wheel_dir.mkdir(parents=True, exist_ok=True)
            dependency_requirements = tuple(
                status.requirement or _dependency_requirement_from_status(status)
                for status in preview.dependency_status
                if status.can_be_installed_online
            )
            if allow_online_deps and dependency_requirements:
                _pip_install_requirements_online(dependency_requirements, site_packages)
            for dependency_wheel in _dependency_wheels_to_install(preview):
                wheel_target = wheel_dir / dependency_wheel.file_name
                wheel_target.write_bytes(archive.read(dependency_wheel.path))
                _pip_install_wheel_no_deps(wheel_target, site_packages)
                installed.append(str(wheel_target))
            for wheel in _plugin_wheels_to_install(preview):
                wheel_target = wheel_dir / wheel.file_name
                wheel_target.write_bytes(archive.read(wheel.path))
                _pip_install_wheel_no_deps(wheel_target, site_packages)
                installed.append(str(wheel_target))
    except zipfile.BadZipFile as exc:
        raise AxpError(f"AXP archive is not a valid zip file: {path}") from exc
    distributions_after = _site_distributions(site_packages)
    installed_paths = _installed_site_paths(distributions_before, distributions_after, site_packages)
    _ensure_site_packages_on_path(site_packages, write_pth=write_pth)
    if enable:
        from .plugin_config import enable_provider

        enable_provider(preview.provider_id, data_root=data_root)
    else:
        from .plugin_config import disable_provider

        disable_provider(preview.provider_id, data_root=data_root)
    _write_install_record(
        root=root,
        preview=preview,
        installed_wheels=tuple(installed),
        installed_paths=installed_paths,
        enabled=enable,
    )
    return AxpInstallResult(
        preview=preview,
        install_root=str(root),
        site_packages=str(site_packages),
        installed_wheels=tuple(installed),
        enabled=enable,
        replaced=was_replaced,
        installed_dependency_requirements=tuple(
            status.requirement or _dependency_requirement_from_status(status)
            for status in preview.dependency_status
            if status.can_be_installed_online
        )
        if allow_online_deps
        else (),
    )


def axp_plugin_site_packages(*, data_root: str | Path | None = None) -> Path:
    """Return the default AxData-managed plugin site-packages path."""

    return _plugin_install_root(data_root=data_root) / AXP_SITE_PACKAGES_DIR_NAME


def list_installed_axp_plugins(
    *,
    data_root: str | Path | None = None,
    install_root: str | Path | None = None,
) -> tuple[AxpInstalledPlugin, ...]:
    """List external plugins installed into AxData's managed plugin directory."""

    root = _plugin_install_root(data_root=data_root, install_root=install_root)
    records_dir = _install_records_dir(root)
    if not records_dir.exists():
        return ()
    registry_providers = _registry_providers_by_id(data_root=data_root)
    plugins: list[AxpInstalledPlugin] = []
    for record_path in sorted(records_dir.glob("*.json")):
        try:
            plugins.append(_installed_plugin_from_record(record_path, root=root, registry_providers=registry_providers))
        except Exception as exc:
            plugins.append(
                AxpInstalledPlugin(
                    provider_id=record_path.stem,
                    source_code="unknown",
                    source_name_zh="未知插件",
                    version="0.0.0",
                    installed_path=str(record_path),
                    install_root=str(root),
                    site_packages=str(root / AXP_SITE_PACKAGES_DIR_NAME),
                    installed_at=_path_mtime_iso(record_path),
                    installed_wheels=(),
                    wheel_files=(),
                    package_paths=(),
                    dist_info_paths=(),
                    manifest=_failed_manifest(record_path.stem),
                    status="failed",
                    error=f"Install record cannot be read: {exc}",
                )
            )
    return tuple(plugins)


def uninstall_axp_plugin(
    provider_id: str,
    *,
    data_root: str | Path | None = None,
    install_root: str | Path | None = None,
    disable_first: bool = False,
) -> AxpUninstallResult:
    """Uninstall one plugin from AxData's managed AXP install directory.

    The conservative MVP refuses to uninstall an enabled Provider unless
    ``disable_first=True`` is explicitly requested by an admin surface.
    """

    provider_id = str(provider_id or "").strip()
    if not provider_id:
        raise AxpUninstallError("provider_id is required.")
    root = _plugin_install_root(data_root=data_root, install_root=install_root)
    registry_providers = _registry_providers_by_id(data_root=data_root)
    provider = registry_providers.get(provider_id)
    if provider is not None:
        from .plugin_status import install_source_for_provider

        install_source = install_source_for_provider(provider)
    else:
        install_source = ""
    if provider is not None and (getattr(provider, "built_in", False) or install_source == "preinstalled"):
        from .plugin_config import remove_provider

        remove_provider(provider_id, data_root=data_root)
        _clear_provider_config_references(provider_id, data_root=data_root, keep_removed=True)
        return AxpUninstallResult(
            provider_id=provider_id,
            install_root=str(root),
            removed_paths=(),
            removed_record_path="",
            disabled=True,
            uninstall_mode="managed_disable",
            message="预装插件已从当前 AxData 管理状态移除并隐藏能力；不会物理删除随包代码，也不会删除已采集数据、metadata 或 run history。",
        )
    record_path = _install_record_path(root, provider_id)
    if not record_path.exists():
        if provider is not None:
            raise AxpUninstallError(
                "该插件不是通过 AxData AXP 管理安装，请使用 pip uninstall 或移除开发路径。"
            )
        raise AxpUninstallError(f"Provider {provider_id!r} is not installed in AxData's managed plugin directory.")
    if _provider_is_enabled(provider_id, provider=provider, data_root=data_root):
        if not disable_first:
            raise AxpUninstallError(
                f"Provider {provider_id!r} is enabled. Disable it before uninstalling."
            )
        from .plugin_config import disable_provider

        disable_provider(provider_id, data_root=data_root)

    removed_paths = _remove_installed_files_from_record(record_path, root=root)
    record_path.unlink(missing_ok=True)
    _clear_provider_config_references(provider_id, data_root=data_root)
    return AxpUninstallResult(
        provider_id=provider_id,
        install_root=str(root),
        removed_paths=tuple(str(path) for path in removed_paths),
        removed_record_path=str(record_path),
        disabled=disable_first,
        message="AXP 管理插件文件已移除；已采集数据、metadata 和 run history 未删除。",
    )


def export_axp_plugin(
    provider_id: str,
    *,
    data_root: str | Path | None = None,
    install_root: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> AxpExportResult:
    """Export one discovered plugin capability as a Web-shareable AXP archive.

    The archive intentionally contains only plugin metadata and wheels. It does
    not include local data, metadata databases, cache, logs, task history, or
    tokens.
    """

    provider_id = str(provider_id or "").strip()
    if not provider_id:
        raise AxpError("provider_id is required.")

    root = _plugin_install_root(data_root=data_root, install_root=install_root)
    work_dir = Path(output_dir).expanduser().resolve() if output_dir is not None else Path(tempfile.mkdtemp(prefix="axdata-axp-export-"))
    work_dir.mkdir(parents=True, exist_ok=True)

    manifest, wheel_paths, warnings = _export_manifest_and_wheels(
        provider_id,
        data_root=data_root,
        install_root=root,
        work_dir=work_dir,
    )
    try:
        validate_manifest(manifest)
    except ManifestError as exc:
        raise AxpError(f"Cannot export invalid plugin manifest for {provider_id!r}: {exc}") from exc
    if not wheel_paths:
        raise AxpError(f"Plugin {provider_id!r} has no exportable wheel.")

    file_name = _axp_export_file_name(manifest)
    axp_path = work_dir / file_name
    _write_axp_archive(
        axp_path,
        manifest=manifest,
        wheel_paths=wheel_paths,
        readme=_export_readme(manifest, warnings=warnings),
    )
    # Reuse the existing preview parser as the final archive smoke check.
    preview_axp(axp_path, data_root=data_root, install_root=root)
    return AxpExportResult(
        provider_id=manifest.identity,
        path=str(axp_path),
        file_name=file_name,
        manifest=manifest,
        wheels=tuple(str(path) for path in wheel_paths),
        warnings=tuple(warnings),
    )


def _export_manifest_and_wheels(
    provider_id: str,
    *,
    data_root: str | Path | None,
    install_root: Path,
    work_dir: Path,
) -> tuple[ProviderManifest, tuple[Path, ...], list[str]]:
    managed = _managed_export_manifest_and_wheels(provider_id, install_root=install_root)
    if managed is not None:
        return managed

    manifest = _registry_manifest_for_export(provider_id, data_root=data_root)
    if manifest is None:
        raise AxpError(f"Plugin {provider_id!r} is not installed or discoverable.")

    wheels: list[Path] = []
    warnings: list[str] = []
    repo_root = _repo_export_package_root(manifest.identity)
    if repo_root is not None:
        wheels.append(_build_local_package_wheel(repo_root, work_dir=work_dir))
        if manifest.provider is None:
            wheels.append(_build_bridge_wheel(manifest, work_dir=work_dir, source_code=None))
    else:
        if manifest.provider is None:
            raise AxpError(
                f"Collector plugin {manifest.identity!r} cannot be exported because its runner package wheel is not available."
            )
        source_code = manifest.provider.source_code
        wheels.append(_build_bridge_wheel(manifest, work_dir=work_dir, source_code=source_code))
        warnings.append(
            "该预装源当前仍由 axdata-core 投影；导出的 bridge wheel 依赖目标环境的 axdata-core 提供运行实现。"
        )
    return manifest, tuple(wheels), warnings


def _managed_export_manifest_and_wheels(
    provider_id: str,
    *,
    install_root: Path,
) -> tuple[ProviderManifest, tuple[Path, ...], list[str]] | None:
    record_path = _install_record_path(install_root, provider_id)
    if not record_path.exists():
        return None
    record = _read_install_record(record_path)
    manifest_payload = record.get("manifest")
    if not isinstance(manifest_payload, Mapping):
        raise AxpError(f"Install record for {provider_id!r} has no manifest object.")
    manifest = ProviderManifest.from_dict(manifest_payload)
    wheel_paths = tuple(
        Path(str(item)).expanduser().resolve()
        for item in record.get("wheel_files", ())
        if str(item).strip()
    )
    missing = [path for path in wheel_paths if not path.is_file()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise AxpError(f"Cannot export {provider_id!r}; installed wheel file is missing: {missing_text}")
    if not wheel_paths:
        raise AxpError(f"Cannot export {provider_id!r}; install record does not list wheel files.")
    return manifest, wheel_paths, []


def _registry_manifest_for_export(
    provider_id: str,
    *,
    data_root: str | Path | None,
) -> ProviderManifest | None:
    try:
        from .provider_catalog import build_builtin_provider_registry

        provider_registry = build_builtin_provider_registry(data_root=data_root)
        provider = provider_registry.snapshot().providers.get(provider_id)
        if provider is not None:
            return provider.manifest
    except Exception:
        provider_registry = None

    try:
        from .collector_registry import build_collector_registry

        collector_registry = build_collector_registry(provider_registry=provider_registry, data_root=data_root)
        plugin = collector_registry.snapshot().plugins.get(provider_id)
        if plugin is not None:
            return plugin.manifest
    except Exception:
        return None
    return None


def _repo_export_package_root(provider_id: str) -> Path | None:
    parts = _REPO_PACKAGE_EXPORTS.get(provider_id)
    if parts is None:
        return None
    root = Path(__file__).resolve().parents[3].joinpath(*parts)
    return root if root.joinpath("pyproject.toml").is_file() else None


def _build_local_package_wheel(package_root: Path, *, work_dir: Path) -> Path:
    wheel_dir = work_dir / "wheelhouse"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in wheel_dir.glob("*.whl")}
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "-w",
                str(wheel_dir),
                str(package_root),
            ],
            check=True,
            cwd=Path(__file__).resolve().parents[3],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise AxpError(f"pip failed while building export wheel for {package_root.name}: {detail}") from exc
    created = [path for path in wheel_dir.glob("*.whl") if path.name not in before]
    if not created:
        created = sorted(wheel_dir.glob("*.whl"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not created:
        raise AxpError(f"pip did not produce a wheel for {package_root}.")
    return created[0].resolve()


def _build_bridge_wheel(
    manifest: ProviderManifest,
    *,
    work_dir: Path,
    source_code: str | None,
) -> Path:
    slug = _safe_slug(manifest.identity)
    module_name = f"axdata_export_{slug.replace('-', '_')}"
    dist_name = f"axdata-export-{slug}"
    dist_info = f"{dist_name.replace('-', '_')}-{_BRIDGE_WHEEL_VERSION}.dist-info"
    wheel_name = f"{dist_name.replace('-', '_')}-{_BRIDGE_WHEEL_VERSION}-py3-none-any.whl"
    wheel_path = (work_dir / "bridge-wheels" / wheel_name).resolve()
    wheel_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_file_name = MANIFEST_FILE_NAME if manifest.provider is not None else PLUGIN_MANIFEST_FILE_NAME
    entry_group = "axdata.providers" if manifest.provider is not None else "axdata.plugins"
    entry_target = f"{module_name}.provider:provider" if manifest.provider is not None else f"{module_name}.plugin:plugin"
    package_files: dict[str, bytes] = {
        f"{module_name}/__init__.py": b'"""AxData exported plugin bridge."""\n',
        f"{module_name}/{manifest_file_name}": (
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8"),
        f"{dist_info}/METADATA": _bridge_metadata(dist_name, manifest).encode("utf-8"),
        f"{dist_info}/WHEEL": (
            "Wheel-Version: 1.0\n"
            "Generator: axdata\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ).encode("utf-8"),
        f"{dist_info}/entry_points.txt": (
            f"[{entry_group}]\n"
            f"{slug.replace('-', '_')} = {entry_target}\n"
        ).encode("utf-8"),
    }
    if manifest.provider is not None:
        if source_code is None:
            raise AxpError(f"Provider bridge for {manifest.identity!r} requires source_code.")
        package_files[f"{module_name}/provider.py"] = (
            "from axdata_core.builtin_providers import get_builtin_provider\n\n"
            f"provider = get_builtin_provider({source_code!r})\n"
        ).encode("utf-8")
    else:
        package_files[f"{module_name}/plugin.py"] = (
            "# The collector manifest is read from axdata-plugin.json during discovery.\n"
            "plugin = object()\n"
        ).encode("utf-8")
    _write_wheel(wheel_path, package_files, dist_info=dist_info)
    return wheel_path


def _bridge_metadata(dist_name: str, manifest: ProviderManifest) -> str:
    description = ""
    if manifest.provider is not None:
        description = manifest.provider.description
    elif manifest.plugin is not None:
        description = manifest.plugin.description
    return (
        "Metadata-Version: 2.1\n"
        f"Name: {dist_name}\n"
        f"Version: {_BRIDGE_WHEEL_VERSION}\n"
        "Summary: AxData exported plugin bridge wheel\n"
        "Requires-Python: >=3.11\n"
        "Requires-Dist: axdata-core>=0.1.0\n"
        f"Description-Content-Type: text/plain\n\n{description}\n"
    )


def _write_wheel(wheel_path: Path, files: Mapping[str, bytes], *, dist_info: str) -> None:
    record_rows: list[str] = []
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            data = files[name]
            archive.writestr(name, data)
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
            record_rows.append(f"{name},sha256={digest},{len(data)}")
        record_name = f"{dist_info}/RECORD"
        record_rows.append(f"{record_name},,")
        archive.writestr(record_name, "\n".join(record_rows) + "\n")


def _write_axp_archive(
    axp_path: Path,
    *,
    manifest: ProviderManifest,
    wheel_paths: tuple[Path, ...],
    readme: str,
) -> None:
    seen_names: set[str] = set()
    checksum_rows: list[str] = []
    with zipfile.ZipFile(axp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n")
        archive.writestr("README.md", readme)
        for wheel_path in wheel_paths:
            wheel_name = _unique_wheel_archive_name(wheel_path.name, seen_names)
            archive_name = f"wheels/{wheel_name}"
            data = wheel_path.read_bytes()
            archive.writestr(archive_name, data)
            checksum_rows.append(f"{hashlib.sha256(data).hexdigest()}  {archive_name}")
        archive.writestr(AXP_CHECKSUMS_FILE_NAME, "\n".join(checksum_rows) + "\n")


def _unique_wheel_archive_name(file_name: str, seen_names: set[str]) -> str:
    if file_name not in seen_names:
        seen_names.add(file_name)
        return file_name
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    index = 2
    while True:
        candidate = f"{stem}-{index}{suffix}"
        if candidate not in seen_names:
            seen_names.add(candidate)
            return candidate
        index += 1


def _export_readme(manifest: ProviderManifest, *, warnings: list[str]) -> str:
    return (
        f"# { _manifest_name_zh(manifest) } AXP Export\n\n"
        f"- Plugin identity: `{manifest.identity}`\n"
        f"- Source code: `{_manifest_source_code(manifest)}`\n"
        f"- Version: `{_manifest_version(manifest)}`\n"
        f"- Interfaces: {len(manifest.interfaces)}\n"
        f"- Collectors: {len(manifest.collectors)}\n"
        f"- Exported at: {_now_iso()}\n\n"
        "This archive contains plugin manifests and wheel files only. It does not include local data, metadata databases, task history, logs, cache, API tokens, or third-party credentials.\n"
        + (("\nWarnings:\n" + "\n".join(f"- {warning}" for warning in warnings) + "\n") if warnings else "")
    )


def _axp_export_file_name(manifest: ProviderManifest) -> str:
    return f"{_safe_slug(manifest.identity)}-{_safe_slug(_manifest_version(manifest) or '0.0.0')}.axp"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip()).strip(".-").lower()
    slug = slug.replace(".", "-").replace("_", "-")
    if not slug:
        slug = "plugin"
    if not slug[0].isalpha():
        slug = f"plugin-{slug}"
    return slug


def _validate_installable_preview(preview: AxpPreview, *, allow_online_deps: bool = False) -> None:
    bad_wheels = [
        f"{wheel.path} ({wheel.checksum_status})"
        for wheel in preview.wheels
        if wheel.checksum_status != "ok"
    ]
    if bad_wheels:
        raise AxpError(
            "AXP install requires every wheel to have a matching sha256 checksum: "
            + ", ".join(bad_wheels)
        )
    blocking = [
        status
        for status in preview.dependency_status
        if status.is_blocking_offline
        and not (allow_online_deps and status.can_be_installed_online)
    ]
    if blocking:
        details = ", ".join(
            f"{status.name} ({status.status})"
            for status in blocking
        )
        raise AxpError(
            "AXP install cannot continue offline because required dependencies are "
            f"missing or unsatisfied: {details}. Bundle matching dependency wheels "
            "inside the AXP or pass allow_online_deps=True / --allow-online-deps."
        )


def _read_axp_manifest(
    archive: zipfile.ZipFile,
    names: set[str],
) -> tuple[ProviderManifest, str]:
    if AXP_MANIFEST_FILE_NAME in names:
        raw = archive.read(AXP_MANIFEST_FILE_NAME).decode("utf-8")
        return _manifest_from_json(raw, AXP_MANIFEST_FILE_NAME), AXP_MANIFEST_FILE_NAME
    provider_manifest_names = [
        name
        for name in names
        if name.replace("\\", "/").endswith("/" + MANIFEST_FILE_NAME)
        or name == MANIFEST_FILE_NAME
    ]
    if not provider_manifest_names:
        raise AxpError(f"AXP archive must include {AXP_MANIFEST_FILE_NAME} or embedded {MANIFEST_FILE_NAME}.")
    manifest_name = sorted(provider_manifest_names)[0]
    raw = archive.read(manifest_name).decode("utf-8")
    return _manifest_from_json(raw, manifest_name), manifest_name


def _manifest_from_json(raw: str, source_name: str) -> ProviderManifest:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AxpError(f"{source_name} is not valid JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise AxpError(f"{source_name} must contain a JSON object.")
    return ProviderManifest.from_dict(payload)


def _read_checksums(
    archive: zipfile.ZipFile,
    names: set[str],
) -> dict[str, str]:
    if AXP_CHECKSUMS_FILE_NAME not in names:
        return {}
    rows = archive.read(AXP_CHECKSUMS_FILE_NAME).decode("utf-8").splitlines()
    checksums: dict[str, str] = {}
    for row in rows:
        row = row.strip()
        if not row or row.startswith("#"):
            continue
        parts = row.split()
        if len(parts) < 2:
            continue
        digest = parts[0].removeprefix("sha256:")
        target = parts[-1].lstrip("*")
        checksums[target] = digest.lower()
    return checksums


def _wheel_infos(
    archive: zipfile.ZipFile,
    checksums: Mapping[str, str],
) -> tuple[AxpWheelInfo, ...]:
    wheels: list[AxpWheelInfo] = []
    for info in archive.infolist():
        normalized = info.filename.replace("\\", "/")
        if not normalized.startswith("wheels/") or not normalized.endswith(".whl"):
            continue
        digest = hashlib.sha256(archive.read(info.filename)).hexdigest()
        expected = checksums.get(normalized) or checksums.get(Path(normalized).name)
        if expected is None:
            status = "missing"
        elif expected.lower() == digest:
            status = "ok"
        else:
            status = "mismatch"
        wheels.append(
            AxpWheelInfo(
                path=normalized,
                file_name=Path(normalized).name,
                size=info.file_size,
                sha256=digest,
                checksum_status=status,
            )
        )
    return tuple(sorted(wheels, key=lambda item: item.path))


def _read_optional_text(archive: zipfile.ZipFile, names: set[str], name: str) -> str | None:
    if name not in names:
        return None
    raw = archive.read(name)
    return raw.decode("utf-8", errors="replace")


def _merge_dependency_declarations(
    manifest_dependencies: tuple[DependencySpec, ...],
    pyproject_dependencies: tuple[DependencySpec, ...],
    wheel_dependencies: tuple[DependencySpec, ...],
) -> tuple[DependencySpec, ...]:
    """Merge dependency declarations by package name.

    Manifest declarations are the most explicit source because they can point to
    bundled wheels and mark optional dependencies. Wheel / pyproject metadata is
    used as install-time safety net when the manifest is sparse.
    """

    merged: dict[str, DependencySpec] = {}
    for dependency in (*wheel_dependencies, *pyproject_dependencies, *manifest_dependencies):
        key = canonicalize_name(dependency.name)
        previous = merged.get(key)
        if previous is None:
            merged[key] = dependency
            continue
        merged[key] = DependencySpec(
            name=previous.name,
            version_spec=dependency.version_spec or previous.version_spec,
            optional=dependency.optional if dependency.optional != previous.optional else previous.optional,
            source=dependency.source or previous.source,
            wheel=dependency.wheel or previous.wheel,
            description=dependency.description or previous.description,
        )
    return tuple(merged[key] for key in sorted(merged))


def _read_pyproject_dependencies(
    archive: zipfile.ZipFile,
    names: set[str],
) -> tuple[DependencySpec, ...]:
    candidates = sorted(name for name in names if name.replace("\\", "/").endswith("pyproject.toml"))
    dependencies: list[DependencySpec] = []
    for name in candidates:
        try:
            payload = tomllib.loads(archive.read(name).decode("utf-8"))
        except Exception:
            continue
        project = payload.get("project", {})
        if not isinstance(project, Mapping):
            continue
        for raw in project.get("dependencies", ()) or ():
            spec = _dependency_from_requirement_string(str(raw), source=f"{name}:project.dependencies")
            if spec is not None:
                dependencies.append(spec)
    return tuple(dependencies)


def _read_wheel_dependencies(
    archive: zipfile.ZipFile,
    wheels: tuple[AxpWheelInfo, ...],
) -> tuple[DependencySpec, ...]:
    dependencies: list[DependencySpec] = []
    for wheel in wheels:
        metadata_payload = _read_wheel_metadata(archive, wheel.path)
        if metadata_payload is None:
            continue
        for raw in metadata_payload.get_all("Requires-Dist") or ():
            spec = _dependency_from_requirement_string(str(raw), source=f"{wheel.path}:METADATA")
            if spec is not None:
                dependencies.append(spec)
    return tuple(dependencies)


def _read_wheel_metadata(archive: zipfile.ZipFile, wheel_path: str) -> Any | None:
    try:
        wheel_bytes = archive.read(wheel_path)
        with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as wheel_archive:
            metadata_names = [
                name
                for name in wheel_archive.namelist()
                if name.replace("\\", "/").endswith(".dist-info/METADATA")
            ]
            if not metadata_names:
                return None
            return Parser().parsestr(
                wheel_archive.read(sorted(metadata_names)[0]).decode("utf-8", errors="replace")
            )
    except (KeyError, zipfile.BadZipFile):
        return None


def _dependency_from_requirement_string(raw: str, *, source: str) -> DependencySpec | None:
    try:
        requirement = Requirement(raw)
    except InvalidRequirement:
        return DependencySpec(
            name=_safe_dependency_name(raw),
            version_spec=None,
            optional=False,
            source=source,
            description=f"Invalid requirement string: {raw}",
        )
    if requirement.marker is not None and not requirement.marker.evaluate(default_environment()):
        return None
    version_spec = str(requirement.specifier) or None
    return DependencySpec(
        name=canonicalize_name(requirement.name),
        version_spec=version_spec,
        optional=False,
        source=source,
        description=raw,
    )


def _safe_dependency_name(raw: str) -> str:
    name = str(raw or "").strip().split(";", 1)[0].split("[", 1)[0].split(" ", 1)[0]
    name = name.replace("-", "_").replace(".", "_").lower()
    return name if name and name[0].isalpha() else "invalid_dependency"


def _dependency_statuses(
    dependencies: tuple[DependencySpec, ...],
    *,
    wheels: tuple[AxpWheelInfo, ...],
    archive: zipfile.ZipFile,
    site_packages: Path,
) -> tuple[AxpDependencyStatus, ...]:
    wheel_by_name = _bundled_wheels_by_distribution_name(archive, wheels)
    statuses: list[AxpDependencyStatus] = []
    for dependency in dependencies:
        statuses.append(_dependency_status(dependency, wheels=wheel_by_name, site_packages=site_packages))
    return tuple(statuses)


def _dependency_status(
    dependency: DependencySpec,
    *,
    wheels: Mapping[str, AxpWheelInfo],
    site_packages: Path,
) -> AxpDependencyStatus:
    installed_version = _installed_dependency_version(dependency.name, site_packages=site_packages)
    declared_wheel = dependency.wheel
    bundled_wheel = _matching_bundled_wheel(dependency, wheels)
    bundled_version = (
        _wheel_distribution_version(bundled_wheel.file_name)
        if bundled_wheel is not None
        else None
    )
    requirement = _dependency_requirement(dependency)

    try:
        specifier = SpecifierSet(dependency.version_spec or "")
    except InvalidSpecifier:
        return AxpDependencyStatus(
            name=dependency.name,
            version_spec=dependency.version_spec,
            optional=dependency.optional,
            source=dependency.source,
            declared_wheel=declared_wheel,
            status="invalid",
            installed_version=installed_version,
            bundled_wheel=bundled_wheel.path if bundled_wheel else None,
            bundled_version=bundled_version,
            requirement=requirement,
            message=f"Invalid version specifier: {dependency.version_spec}",
        )

    if installed_version is not None and _version_satisfies(installed_version, specifier):
        return AxpDependencyStatus(
            name=dependency.name,
            version_spec=dependency.version_spec,
            optional=dependency.optional,
            source=dependency.source,
            declared_wheel=declared_wheel,
            status="satisfied",
            installed_version=installed_version,
            bundled_wheel=bundled_wheel.path if bundled_wheel else None,
            bundled_version=bundled_version,
            requirement=requirement,
            message="Dependency is already installed and satisfies the requirement.",
        )

    if bundled_wheel is not None:
        if bundled_version is None or not _version_satisfies(bundled_version, specifier):
            return AxpDependencyStatus(
                name=dependency.name,
                version_spec=dependency.version_spec,
                optional=dependency.optional,
                source=dependency.source,
                declared_wheel=declared_wheel,
                status="bundled_version_mismatch",
                installed_version=installed_version,
                bundled_wheel=bundled_wheel.path,
                bundled_version=bundled_version,
                requirement=requirement,
                message="Bundled dependency wheel does not satisfy the declared version.",
            )
        return AxpDependencyStatus(
            name=dependency.name,
            version_spec=dependency.version_spec,
            optional=dependency.optional,
            source=dependency.source,
            declared_wheel=declared_wheel,
            status="bundled",
            installed_version=installed_version,
            bundled_wheel=bundled_wheel.path,
            bundled_version=bundled_version,
            requirement=requirement,
            message="Dependency can be installed offline from the bundled wheel.",
        )

    if declared_wheel:
        return AxpDependencyStatus(
            name=dependency.name,
            version_spec=dependency.version_spec,
            optional=dependency.optional,
            source=dependency.source,
            declared_wheel=declared_wheel,
            status="missing_bundled_wheel",
            installed_version=installed_version,
            requirement=requirement,
            message=f"Declared dependency wheel is not present in the AXP: {declared_wheel}",
        )

    if installed_version is not None:
        return AxpDependencyStatus(
            name=dependency.name,
            version_spec=dependency.version_spec,
            optional=dependency.optional,
            source=dependency.source,
            declared_wheel=declared_wheel,
            status="version_mismatch",
            installed_version=installed_version,
            requirement=requirement,
            message="Installed dependency version does not satisfy the requirement.",
        )

    return AxpDependencyStatus(
        name=dependency.name,
        version_spec=dependency.version_spec,
        optional=dependency.optional,
        source=dependency.source,
        declared_wheel=declared_wheel,
        status="optional_missing" if dependency.optional else "missing",
        requirement=requirement,
        message=(
            "Optional dependency is not installed and no bundled wheel was found."
            if dependency.optional
            else "Required dependency is not installed and no bundled wheel was found."
        ),
    )


def _bundled_wheels_by_distribution_name(
    archive: zipfile.ZipFile,
    wheels: tuple[AxpWheelInfo, ...],
) -> dict[str, AxpWheelInfo]:
    result: dict[str, AxpWheelInfo] = {}
    for wheel in wheels:
        name = _wheel_distribution_name_from_metadata(archive, wheel.path) or _wheel_distribution_name(wheel.file_name)
        if name:
            result.setdefault(canonicalize_name(name), wheel)
    return result


def _wheel_distribution_name_from_metadata(archive: zipfile.ZipFile, wheel_path: str) -> str | None:
    payload = _read_wheel_metadata(archive, wheel_path)
    if payload is None:
        return None
    name = payload.get("Name")
    return str(name).strip() if name else None


def _wheel_distribution_name(file_name: str) -> str | None:
    stem = file_name[:-4] if file_name.endswith(".whl") else file_name
    parts = stem.split("-")
    if len(parts) < 2:
        return None
    return parts[0].replace("_", "-")


def _wheel_distribution_version(file_name: str) -> str | None:
    stem = file_name[:-4] if file_name.endswith(".whl") else file_name
    parts = stem.split("-")
    if len(parts) < 2:
        return None
    return parts[1]


def _matching_bundled_wheel(
    dependency: DependencySpec,
    wheels: Mapping[str, AxpWheelInfo],
) -> AxpWheelInfo | None:
    if dependency.wheel:
        normalized = dependency.wheel.replace("\\", "/")
        for wheel in wheels.values():
            if wheel.path == normalized or wheel.file_name == Path(normalized).name:
                return wheel
        return None
    return wheels.get(canonicalize_name(dependency.name))


def _installed_dependency_version(name: str, *, site_packages: Path) -> str | None:
    normalized = canonicalize_name(name)
    if normalized in {"axdata-core", "axdata"}:
        return _host_axdata_version(normalized)
    managed_version = _managed_dependency_version(name, site_packages=site_packages)
    if managed_version is not None:
        return managed_version
    return None


def _managed_dependency_version(name: str, *, site_packages: Path) -> str | None:
    if not site_packages.exists():
        return None
    normalized = canonicalize_name(name)
    try:
        for distribution in metadata.distributions(path=[str(site_packages)]):
            dist_name = _dist_name(distribution)
            if dist_name and canonicalize_name(dist_name) == normalized:
                version = distribution.version
                return str(version).strip() if version else None
    except Exception:
        return None
    return None


def _host_axdata_version(normalized_name: str) -> str | None:
    try:
        if normalized_name == "axdata-core":
            import axdata_core  # noqa: F401

            return "0.1.0"
        if normalized_name == "axdata":
            import axdata

            return getattr(axdata, "__version__", "0.1.0")
    except Exception:
        return None
    return None


def _version_satisfies(version: str | None, specifier: SpecifierSet) -> bool:
    if version is None:
        return not str(specifier)
    if not str(specifier):
        return True
    try:
        return Version(version) in specifier
    except InvalidVersion:
        return False


def _dependency_requirement(dependency: DependencySpec) -> str:
    return f"{dependency.name}{dependency.version_spec or ''}"


def _dependency_requirement_from_status(status: AxpDependencyStatus) -> str:
    return status.requirement or f"{status.name}{status.version_spec or ''}"


def _dependency_wheels_to_install(preview: AxpPreview) -> tuple[AxpWheelInfo, ...]:
    dependency_paths = {
        status.bundled_wheel
        for status in preview.dependency_status
        if status.bundled_wheel
    }
    return tuple(wheel for wheel in preview.wheels if wheel.path in dependency_paths)


def _plugin_wheels_to_install(preview: AxpPreview) -> tuple[AxpWheelInfo, ...]:
    dependency_paths = {wheel.path for wheel in _dependency_wheels_to_install(preview)}
    return tuple(wheel for wheel in preview.wheels if wheel.path not in dependency_paths)


def _declared_dependency_wheel_paths(dependencies: tuple[DependencySpec, ...]) -> set[str]:
    paths: set[str] = set()
    for dependency in dependencies:
        if not dependency.wheel:
            continue
        normalized = dependency.wheel.replace("\\", "/")
        paths.add(normalized)
        paths.add(f"wheels/{Path(normalized).name}")
    return paths


def _plugin_install_root(
    *,
    data_root: str | Path | None = None,
    install_root: str | Path | None = None,
) -> Path:
    if install_root is not None:
        return Path(install_root).expanduser().resolve()
    env_root = os.getenv("AXDATA_PLUGIN_INSTALL_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()
    root = Path(data_root or os.getenv("AXDATA_DATA_DIR", "data")).expanduser().resolve()
    return root.parent / AXP_PLUGINS_DIR_NAME


def _install_records_dir(root: Path) -> Path:
    return root / AXP_INSTALL_RECORDS_DIR_NAME


def _install_record_path(root: Path, provider_id: str) -> Path:
    safe_name = provider_id.replace("/", "_").replace("\\", "_")
    return _install_records_dir(root) / f"{safe_name}.json"


def _pip_install_wheel_no_deps(wheel_path: Path, site_packages: Path) -> None:
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                str(site_packages),
                str(wheel_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise AxpError(f"pip failed while installing {wheel_path.name}: {detail}") from exc


def _pip_install_requirements_online(requirements: tuple[str, ...], site_packages: Path) -> None:
    if not requirements:
        return
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--target",
                str(site_packages),
                *requirements,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise AxpError(
            "pip failed while installing online dependencies "
            f"{', '.join(requirements)}: {detail}"
        ) from exc


def _ensure_site_packages_on_path(site_packages: Path, *, write_pth: bool) -> None:
    site_packages = site_packages.resolve()
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    if not write_pth:
        return
    pth_path = _user_site_pth_path()
    if pth_path is None:
        return
    pth_path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if pth_path.exists():
        existing = {line.strip() for line in pth_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    if str(site_packages) in existing:
        return
    with pth_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(str(site_packages) + "\n")


def _user_site_pth_path() -> Path | None:
    try:
        import site

        user_site = site.getusersitepackages()
    except Exception:
        return None
    if not user_site:
        return None
    return Path(user_site) / AXP_SITE_PTH_NAME


def _site_distributions(site_packages: Path) -> dict[str, set[str]]:
    if not site_packages.exists():
        return {}
    result: dict[str, set[str]] = {}
    for dist in metadata.distributions(path=[str(site_packages)]):
        name = _dist_name(dist)
        if not name:
            continue
        result[name] = {str(path) for path in (dist.files or ())}
    return result


def _installed_site_paths(
    before: Mapping[str, set[str]],
    after: Mapping[str, set[str]],
    site_packages: Path,
) -> tuple[Path, ...]:
    paths: set[Path] = set()
    for dist in metadata.distributions(path=[str(site_packages)]):
        name = _dist_name(dist)
        if not name:
            continue
        before_files = before.get(name, set())
        after_files = {str(path) for path in (dist.files or ())}
        if name not in before or after_files != before_files:
            dist_path = Path(str(getattr(dist, "_path", "")))
            if dist_path:
                paths.add(dist_path.resolve())
            for file_name in after_files:
                top = Path(file_name).parts[0] if Path(file_name).parts else ""
                if top:
                    paths.add((site_packages / top).resolve())
    return tuple(sorted(paths, key=lambda path: str(path).lower()))


def _dist_name(distribution: Any) -> str:
    try:
        return str(distribution.metadata.get("Name", "")).strip().lower()
    except Exception:
        return ""


def _write_install_record(
    *,
    root: Path,
    preview: AxpPreview,
    installed_wheels: tuple[str, ...],
    installed_paths: tuple[Path, ...],
    enabled: bool,
) -> None:
    record_path = _install_record_path(root, preview.provider_id)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    site_packages = root / AXP_SITE_PACKAGES_DIR_NAME
    payload = {
        "version": AXP_INSTALL_RECORD_VERSION,
        "installed_at": _now_iso(),
        "enabled_at_install": enabled,
        "install_root": str(root),
        "site_packages": str(site_packages),
        "provider_id": preview.provider_id,
        "source_code": _manifest_source_code(preview.manifest),
        "source_name_zh": _manifest_name_zh(preview.manifest),
        "provider_version": _manifest_version(preview.manifest),
        "manifest_source": preview.manifest_source,
        "manifest": preview.manifest.to_dict(),
        "installed_wheels": list(installed_wheels),
        "wheel_files": [str((root / "wheels" / wheel.file_name).resolve()) for wheel in preview.wheels],
        "site_paths": [str(path) for path in installed_paths],
    }
    temp_path = record_path.with_name(f".{record_path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(record_path)


def _read_install_record(record_path: Path) -> dict[str, Any]:
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise AxpError(f"Install record {record_path} must contain a JSON object.")
    version = payload.get("version", AXP_INSTALL_RECORD_VERSION)
    if version != AXP_INSTALL_RECORD_VERSION:
        raise AxpError(f"Unsupported install record version {version!r}.")
    return dict(payload)


def _installed_plugin_from_record(
    record_path: Path,
    *,
    root: Path,
    registry_providers: Mapping[str, Any],
) -> AxpInstalledPlugin:
    record = _read_install_record(record_path)
    manifest_payload = record.get("manifest")
    if not isinstance(manifest_payload, Mapping):
        raise AxpError("Install record has no manifest object.")
    manifest = ProviderManifest.from_dict(manifest_payload)
    provider_id = str(record.get("provider_id") or manifest.identity)
    provider = registry_providers.get(provider_id)
    interfaces = tuple(interface.name for interface in manifest.interfaces)
    downloaders = tuple(profile.name for profile in manifest.downloaders)
    collectors = tuple(collector.name for collector in manifest.collectors)
    dependencies = tuple(dependency.to_dict() for dependency in manifest.dependencies)
    installed_wheels = tuple(str(item) for item in record.get("installed_wheels", ()) if str(item))
    wheel_files = tuple(str(item) for item in record.get("wheel_files", ()) if str(item))
    site_paths = tuple(str(item) for item in record.get("site_paths", ()) if str(item))
    return AxpInstalledPlugin(
        provider_id=provider_id,
        source_code=_manifest_source_code(manifest),
        source_name_zh=_manifest_name_zh(manifest),
        version=_manifest_version(manifest),
        installed_path=str(record_path),
        install_root=str(root),
        site_packages=str(root / AXP_SITE_PACKAGES_DIR_NAME),
        installed_at=str(record.get("installed_at") or _path_mtime_iso(record_path)),
        installed_wheels=installed_wheels,
        wheel_files=wheel_files,
        package_paths=site_paths,
        dist_info_paths=tuple(path for path in site_paths if path.endswith(".dist-info")),
        manifest=manifest,
        enabled=bool(getattr(provider, "enabled", False)) if provider is not None else False,
        status=str(getattr(provider, "status", "installed")) if provider is not None else "installed",
        effective_trust_level=str(getattr(provider, "effective_trust_level", "community")) if provider is not None else "community",
        built_in=bool(getattr(provider, "built_in", False)) if provider is not None else False,
        interfaces=interfaces,
        downloaders=downloaders,
        collectors=collectors,
        dependencies=dependencies,
        error=str(getattr(provider, "error", "")) if provider is not None else "",
    )


def _remove_installed_files_from_record(record_path: Path, *, root: Path) -> tuple[Path, ...]:
    record = _read_install_record(record_path)
    candidates = [
        Path(str(item)).expanduser().resolve()
        for item in [*record.get("site_paths", ()), *record.get("wheel_files", ())]
        if str(item).strip()
    ]
    removed: list[Path] = []
    for path in sorted(set(candidates), key=lambda item: len(item.parts), reverse=True):
        if not _is_relative_to(path, root):
            continue
        if not path.exists():
            continue
        _remove_installed_path(path)
        removed.append(path)
    return tuple(removed)


def _remove_installed_path(path: Path) -> None:
    for attempt in range(6):
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if attempt == 5:
                raise
            gc.collect()
            time.sleep(0.1 * (attempt + 1))


def _registry_providers_by_id(*, data_root: str | Path | None = None) -> dict[str, Any]:
    try:
        from .provider_catalog import build_builtin_provider_registry

        return dict(build_builtin_provider_registry(data_root=data_root).snapshot().providers)
    except Exception:
        return {}


def _provider_is_enabled(provider_id: str, *, provider: Any | None, data_root: str | Path | None) -> bool:
    if provider is not None and bool(getattr(provider, "enabled", False)):
        return True
    try:
        from .plugin_config import load_plugin_config

        return provider_id in load_plugin_config(data_root=data_root).enabled_provider_ids
    except Exception:
        return False


def _clear_provider_config_references(
    provider_id: str,
    *,
    data_root: str | Path | None = None,
    keep_removed: bool = False,
) -> None:
    from .plugin_config import load_plugin_config, save_plugin_config

    config = load_plugin_config(data_root=data_root)
    overrides = {
        interface_name: override_provider_id
        for interface_name, override_provider_id in config.provider_overrides.items()
        if override_provider_id != provider_id
    }
    from .plugin_config import PluginConfig

    save_plugin_config(
        PluginConfig(
            enabled_provider_ids=tuple(item for item in config.enabled_provider_ids if item != provider_id),
            disabled_provider_ids=tuple(item for item in config.disabled_provider_ids if item != provider_id),
            removed_provider_ids=(
                tuple(config.removed_provider_ids)
                if keep_removed
                else tuple(item for item in config.removed_provider_ids if item != provider_id)
            ),
            provider_overrides=overrides,
            version=config.version,
        ),
        data_root=data_root,
    )


def _failed_manifest(provider_id: str) -> ProviderManifest:
    from .plugins import ProviderInfo, PluginTrustLevel

    return ProviderManifest(
        provider=ProviderInfo(
            provider_id=provider_id,
            source_code="unknown",
            source_name_zh="未知插件",
            version="0.0.0",
            declared_trust_level=PluginTrustLevel.COMMUNITY.value,
        ),
        interfaces=(),
    )


def _manifest_source_code(manifest: ProviderManifest) -> str:
    if manifest.provider is not None:
        return manifest.provider.source_code
    return "plugin"


def _manifest_name_zh(manifest: ProviderManifest) -> str:
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


def _manifest_declared_trust(manifest: ProviderManifest) -> str:
    if manifest.provider is not None:
        return manifest.provider.declared_trust_level
    return "community"


def _path_mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat().replace("+00:00", "Z")


def _now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
