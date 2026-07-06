from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from axdata_core.axp import (
    AxpAlreadyInstalledError,
    AxpError,
    AxpUninstallError,
    export_axp_plugin,
    install_axp,
    list_installed_axp_plugins,
    preview_axp,
    uninstall_axp_plugin,
)
from axdata_core.plugin_config import enable_provider, load_plugin_config, set_provider_override
from axdata_core.provider_catalog import build_builtin_provider_registry

from tests.test_tencent_provider_package import (
    BUILTIN_TENCENT_PROVIDER_ID,
    TENCENT_INTERFACE_NAME,
    TENCENT_PACKAGE_ROOT,
    TENCENT_PROVIDER_ID,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def restore_sys_path() -> None:
    original = list(sys.path)
    try:
        yield
    finally:
        sys.path[:] = original


def test_axp_preview_reads_manifest_wheel_and_checksums(tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)

    preview = preview_axp(axp_path)
    payload = preview.to_dict()

    assert payload["provider_id"] == TENCENT_PROVIDER_ID
    assert payload["source_code"] == "tencent"
    assert payload["declared_trust_level"] == "community"
    assert payload["effective_trust_level"] == "community"
    assert payload["status_after_install"] == "disabled"
    assert payload["manifest_source"] == "manifest.json"
    assert payload["interface_count"] == 1
    assert payload["downloader_count"] == 0
    assert payload["collector_count"] == 0
    assert payload["dependency_count"] == 0
    assert payload["interfaces"] == [TENCENT_INTERFACE_NAME]
    assert payload["collectors"] == []
    assert payload["dependencies"] == []
    assert payload["can_install_offline"] is True
    assert "axdata-core" in {item["name"] for item in payload["dependency_status"]}
    assert payload["wheels"][0]["checksum_status"] == "ok"
    assert "signature_status" not in payload
    assert "signature_present" not in payload
    assert "does not enable the Provider automatically" in " ".join(payload["warnings"])


def test_axp_install_defaults_disabled_and_adds_plugin_path(monkeypatch, tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"

    result = install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=False,
        write_pth=False,
    )
    config = load_plugin_config(data_root=data_root)
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    registry = build_builtin_provider_registry(data_root=data_root)
    provider = registry.snapshot().providers[TENCENT_PROVIDER_ID]

    assert result.preview.provider_id == TENCENT_PROVIDER_ID
    assert result.enabled is False
    assert config.enabled_provider_ids == ()
    assert provider.status == "disabled"
    assert provider.enabled is False
    assert str(install_root / "site-packages") in sys.path
    installed = list_installed_axp_plugins(data_root=data_root, install_root=install_root)
    assert len(installed) == 1
    assert installed[0].provider_id == TENCENT_PROVIDER_ID
    assert installed[0].enabled is False
    assert installed[0].status == "disabled"
    assert installed[0].effective_trust_level == "community"
    assert installed[0].interfaces == (TENCENT_INTERFACE_NAME,)
    assert installed[0].downloaders == ()
    assert installed[0].collectors == ()
    assert installed[0].dependencies == ()
    assert installed[0].installed_at
    assert Path(installed[0].installed_path).exists()


def test_axp_install_can_enable_provider(monkeypatch, tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"

    result = install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=True,
        write_pth=False,
    )
    config = load_plugin_config(data_root=data_root)
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert result.enabled is True
    assert TENCENT_PROVIDER_ID in config.enabled_provider_ids
    assert snapshot.providers[TENCENT_PROVIDER_ID].status == "conflict"
    assert snapshot.providers[BUILTIN_TENCENT_PROVIDER_ID].status == "enabled"
    assert snapshot.interfaces[TENCENT_INTERFACE_NAME].provider_id == BUILTIN_TENCENT_PROVIDER_ID


def test_axp_export_preinstalled_provider_as_previewable_archive(tmp_path) -> None:
    data_root = tmp_path / "data"
    result = export_axp_plugin(
        BUILTIN_TENCENT_PROVIDER_ID,
        data_root=data_root,
        output_dir=tmp_path / "export",
    )

    exported_path = Path(result.path)
    preview = preview_axp(exported_path, data_root=data_root)
    with ZipFile(exported_path) as archive:
        names = set(archive.namelist())

    assert exported_path.is_file()
    assert result.file_name.endswith(".axp")
    assert preview.provider_id == BUILTIN_TENCENT_PROVIDER_ID
    assert preview.wheels
    assert {wheel.checksum_status for wheel in preview.wheels} == {"ok"}
    assert any(interface.name == "stock_zh_a_spot_tx" for interface in preview.manifest.interfaces)
    assert "manifest.json" in names
    assert "checksums.txt" in names
    assert "README.md" in names
    assert not any(name.startswith(("data/", "metadata/", "cache/", "logs/")) for name in names)


def test_axp_export_managed_plugin_reuses_installed_wheel(tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"

    install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=False,
        write_pth=False,
    )

    result = export_axp_plugin(
        TENCENT_PROVIDER_ID,
        data_root=data_root,
        install_root=install_root,
        output_dir=tmp_path / "export",
    )
    preview = preview_axp(result.path, data_root=data_root, install_root=install_root)

    assert preview.provider_id == TENCENT_PROVIDER_ID
    assert [interface.name for interface in preview.manifest.interfaces] == [TENCENT_INTERFACE_NAME]
    assert len(preview.wheels) == 1
    assert preview.wheels[0].checksum_status == "ok"
    assert preview.wheels[0].file_name.startswith("axdata_source_tencent-0.1.0-")


def test_axp_uninstall_removes_managed_plugin_after_disabled(monkeypatch, tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"

    install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=False,
        write_pth=False,
    )
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    assert TENCENT_PROVIDER_ID in build_builtin_provider_registry(data_root=data_root).snapshot().providers

    result = uninstall_axp_plugin(TENCENT_PROVIDER_ID, data_root=data_root, install_root=install_root)

    assert result.provider_id == TENCENT_PROVIDER_ID
    assert result.removed_paths
    assert list_installed_axp_plugins(data_root=data_root, install_root=install_root) == ()
    for removed_path in result.removed_paths:
        assert not Path(removed_path).exists()
    snapshot = build_builtin_provider_registry(data_root=data_root).snapshot()
    if TENCENT_PROVIDER_ID in snapshot.providers:
        assert snapshot.providers[TENCENT_PROVIDER_ID].status == "disabled"
    assert snapshot.interfaces[TENCENT_INTERFACE_NAME].provider_id == BUILTIN_TENCENT_PROVIDER_ID


def test_axp_uninstall_refuses_enabled_plugin_and_clears_config_after_disable_first(monkeypatch, tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"

    install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=False,
        write_pth=False,
    )
    enable_provider(TENCENT_PROVIDER_ID, data_root=data_root)
    set_provider_override(TENCENT_INTERFACE_NAME, TENCENT_PROVIDER_ID, data_root=data_root)
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    with pytest.raises(AxpUninstallError, match="Disable it before uninstalling"):
        uninstall_axp_plugin(TENCENT_PROVIDER_ID, data_root=data_root, install_root=install_root)

    result = uninstall_axp_plugin(
        TENCENT_PROVIDER_ID,
        data_root=data_root,
        install_root=install_root,
        disable_first=True,
    )
    config = load_plugin_config(data_root=data_root)

    assert result.disabled is True
    assert TENCENT_PROVIDER_ID not in config.enabled_provider_ids
    assert TENCENT_PROVIDER_ID not in config.disabled_provider_ids
    assert config.provider_overrides == {}


def test_axp_uninstall_preinstalled_provider_is_logical(tmp_path) -> None:
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"
    record_dir = install_root / "installed"
    record_dir.mkdir(parents=True)
    record_dir.joinpath(f"{BUILTIN_TENCENT_PROVIDER_ID}.json").write_text(
        json.dumps(
            {
                "version": 1,
                "provider_id": BUILTIN_TENCENT_PROVIDER_ID,
                "installed_at": "2026-06-25T00:00:00Z",
                "manifest": build_builtin_provider_registry(data_root=data_root)
                .snapshot()
                .providers[BUILTIN_TENCENT_PROVIDER_ID]
                .manifest.to_dict(),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = uninstall_axp_plugin(BUILTIN_TENCENT_PROVIDER_ID, data_root=data_root, install_root=install_root)

    assert result.provider_id == BUILTIN_TENCENT_PROVIDER_ID
    assert result.uninstall_mode == "managed_disable"
    assert result.removed_paths == ()
    config = load_plugin_config(data_root=data_root)
    assert BUILTIN_TENCENT_PROVIDER_ID in config.removed_provider_ids


def test_axp_reinstall_requires_explicit_replace(tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path)
    data_root = tmp_path / "data"
    install_root = tmp_path / "plugins"

    install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=False,
        write_pth=False,
    )

    with pytest.raises(AxpAlreadyInstalledError, match="already installed"):
        install_axp(
            axp_path,
            data_root=data_root,
            install_root=install_root,
            enable=False,
            write_pth=False,
        )

    result = install_axp(
        axp_path,
        data_root=data_root,
        install_root=install_root,
        enable=False,
        replace=True,
        write_pth=False,
    )

    assert result.replaced is True
    assert len(list_installed_axp_plugins(data_root=data_root, install_root=install_root)) == 1


def test_axp_install_rejects_checksum_mismatch(tmp_path) -> None:
    axp_path = _build_tencent_axp(tmp_path, checksum="0" * 64)

    preview = preview_axp(axp_path)
    assert preview.wheels[0].checksum_status == "mismatch"

    with pytest.raises(AxpError, match="matching sha256 checksum"):
        install_axp(
            axp_path,
            data_root=tmp_path / "data",
            install_root=tmp_path / "plugins",
            write_pth=False,
        )


def test_axp_preview_rejects_invalid_zip(tmp_path) -> None:
    axp_path = tmp_path / "broken.axp"
    axp_path.write_text("not a zip", encoding="utf-8")

    with pytest.raises(AxpError, match="not a valid zip"):
        preview_axp(axp_path)


def test_axp_preview_and_install_reject_missing_required_dependency(tmp_path) -> None:
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata_missing_dependency",
                "version_spec": ">=1.0",
                "optional": False,
                "description": "Missing dependency fixture.",
            }
        ],
    )

    preview = preview_axp(axp_path)
    payload = preview.to_dict()
    status_by_name = {item["name"]: item for item in payload["dependency_status"]}

    assert payload["can_install_offline"] is False
    assert status_by_name["axdata_missing_dependency"]["status"] == "missing"
    assert payload["missing_dependencies"][0]["name"] == "axdata_missing_dependency"

    with pytest.raises(AxpError, match="cannot continue offline"):
        install_axp(
            axp_path,
            data_root=tmp_path / "data",
            install_root=tmp_path / "plugins",
            write_pth=False,
        )


def test_axp_optional_missing_dependency_does_not_block_offline_install(tmp_path) -> None:
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata_optional_dependency",
                "version_spec": ">=1.0",
                "optional": True,
                "description": "Optional dependency fixture.",
            }
        ],
    )

    preview = preview_axp(axp_path)
    status_by_name = {status.name: status for status in preview.dependency_status}
    assert preview.to_dict()["can_install_offline"] is True
    assert status_by_name["axdata_optional_dependency"].status == "optional_missing"

    result = install_axp(
        axp_path,
        data_root=tmp_path / "data",
        install_root=tmp_path / "plugins",
        write_pth=False,
    )

    assert result.preview.provider_id == TENCENT_PROVIDER_ID


def test_axp_installs_bundled_dependency_wheel_before_plugin(tmp_path) -> None:
    dependency_wheel = _build_dependency_wheel(tmp_path, name="axdata-demo-dep", version="1.0.0")
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata-demo-dep",
                "version_spec": ">=1.0",
                "optional": False,
                "wheel": f"wheels/{dependency_wheel.name}",
                "description": "Bundled dependency fixture.",
            }
        ],
        extra_wheels=[dependency_wheel],
    )

    preview = preview_axp(axp_path)
    status_by_name = {status.name: status for status in preview.dependency_status}
    assert status_by_name["axdata-demo-dep"].status == "bundled"
    assert preview.to_dict()["bundled_dependency_wheels"] == [f"wheels/{dependency_wheel.name}"]

    result = install_axp(
        axp_path,
        data_root=tmp_path / "data",
        install_root=tmp_path / "plugins",
        write_pth=False,
    )

    installed_names = [Path(path).name for path in result.installed_wheels]
    assert installed_names[0] == dependency_wheel.name
    assert any(name.startswith("axdata_source_tencent-") for name in installed_names[1:])
    assert (tmp_path / "plugins" / "site-packages" / "axdata_demo_dep").exists()


def test_axp_dependency_detection_uses_managed_plugin_site_packages(tmp_path) -> None:
    dependency_wheel = _build_dependency_wheel(tmp_path, name="axdata-managed-dep", version="1.2.0")
    install_root = tmp_path / "plugins"
    site_packages = install_root / "site-packages"
    site_packages.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(site_packages),
            str(dependency_wheel),
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata-managed-dep",
                "version_spec": ">=1.0",
                "optional": False,
                "description": "Managed dependency fixture.",
            },
            {
                "name": "pip",
                "version_spec": ">=1",
                "optional": False,
                "description": "Global dependency must not satisfy plugin runtime.",
            },
        ],
    )

    preview = preview_axp(axp_path, install_root=install_root)
    status_by_name = {status.name: status for status in preview.dependency_status}

    assert status_by_name["axdata-managed-dep"].status == "satisfied"
    assert status_by_name["axdata-managed-dep"].installed_version == "1.2.0"
    assert status_by_name["pip"].status == "missing"


def test_axp_install_allows_online_dependencies_only_when_explicit(monkeypatch, tmp_path) -> None:
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata_online_dependency",
                "version_spec": ">=1.0",
                "optional": False,
                "description": "Online dependency fixture.",
            }
        ],
    )
    calls = []

    import axdata_core.axp as axp_module

    def fake_pip_install_requirements_online(requirements, site_packages):
        calls.append((requirements, site_packages))

    monkeypatch.setattr(
        axp_module,
        "_pip_install_requirements_online",
        fake_pip_install_requirements_online,
    )

    result = install_axp(
        axp_path,
        data_root=tmp_path / "data",
        install_root=tmp_path / "plugins",
        write_pth=False,
        allow_online_deps=True,
    )

    assert calls
    assert calls[0][0] == ("axdata_online_dependency>=1.0",)
    assert result.installed_dependency_requirements == ("axdata_online_dependency>=1.0",)


def _build_tencent_axp(
    tmp_path: Path,
    *,
    checksum: str | None = None,
    dependencies: list[dict[str, object]] | None = None,
    extra_wheels: list[Path] | None = None,
) -> Path:
    wheel_path = _build_tencent_wheel(tmp_path)
    manifest_path = (
        TENCENT_PACKAGE_ROOT
        / "src"
        / "axdata_source_tencent"
        / "axdata-provider.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if dependencies is not None:
        manifest["dependencies"] = dependencies
    wheel_bytes = wheel_path.read_bytes()
    digest = checksum or hashlib.sha256(wheel_bytes).hexdigest()
    axp_path = tmp_path / "tencent.axp"
    extra_wheels = list(extra_wheels or [])

    with ZipFile(axp_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.write(wheel_path, f"wheels/{wheel_path.name}")
        checksum_lines = [f"{digest}  wheels/{wheel_path.name}"]
        for extra_wheel in extra_wheels:
            archive.write(extra_wheel, f"wheels/{extra_wheel.name}")
            checksum_lines.append(
                f"{hashlib.sha256(extra_wheel.read_bytes()).hexdigest()}  wheels/{extra_wheel.name}"
            )
        archive.writestr("checksums.txt", "\n".join(checksum_lines) + "\n")
        archive.writestr("README.md", "Tencent AXP smoke fixture.\n")
        archive.writestr("LICENSE", "Test fixture only.\n")

    # Validate fixture manifest while the zip is still close to the source of truth.
    assert manifest["provider"]["provider_id"] == TENCENT_PROVIDER_ID
    return axp_path


def _build_tencent_wheel(tmp_path: Path) -> Path:
    wheel_dir = tmp_path / "wheelhouse"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "-w",
            str(wheel_dir),
            str(TENCENT_PACKAGE_ROOT),
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return next(wheel_dir.glob("axdata_source_tencent-0.1.0-*.whl"))


def _build_dependency_wheel(tmp_path: Path, *, name: str, version: str) -> Path:
    package_root = tmp_path / name
    module_name = name.replace("-", "_")
    package_dir = package_root / module_name
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("VALUE = 'dependency fixture'\n", encoding="utf-8")
    (package_root / "pyproject.toml").write_text(
        f"""
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "{version}"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["."]
include = ["{module_name}*"]
""".lstrip(),
        encoding="utf-8",
    )
    wheel_dir = tmp_path / "dependency-wheelhouse"
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
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return next(wheel_dir.glob(f"{module_name}-{version}-*.whl"))
