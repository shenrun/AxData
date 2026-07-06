from __future__ import annotations

import json
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from axdata_core.cli import main
from axdata_core.plugin_config import disable_provider, enable_provider
from axdata_core.plugins import ProviderManifest
from axdata_core.provider_catalog import build_builtin_provider_registry
from axdata_core.source_request import request_interface

from tests.test_external_sources import CninfoOpener


REPO_ROOT = Path(__file__).resolve().parents[1]
CNINFO_PACKAGE_ROOT = REPO_ROOT / "packages" / "axdata-source-cninfo"
CNINFO_PROVIDER_ID = "axdata.source.cninfo_external"
BUILTIN_CNINFO_PROVIDER_ID = "axdata.source.cninfo"
CNINFO_ANNOUNCEMENTS_INTERFACE = "cninfo_announcements"
CNINFO_DETAIL_INTERFACE = "cninfo_announcement_detail"
CNINFO_INTERFACE_NAMES = {CNINFO_ANNOUNCEMENTS_INTERFACE, CNINFO_DETAIL_INTERFACE}


def test_cninfo_provider_package_root_import_is_lightweight(monkeypatch, tmp_path) -> None:
    install_root = _install_cninfo_provider(tmp_path)

    monkeypatch.syspath_prepend(str(install_root))
    _clear_cninfo_modules()

    package = importlib.import_module("axdata_source_cninfo")

    assert "axdata_source_cninfo.provider" not in sys.modules
    assert package.provider.provider_id == CNINFO_PROVIDER_ID
    assert "axdata_source_cninfo.provider" in sys.modules
    assert "axdata_source_cninfo.adapter" not in sys.modules


def test_cninfo_provider_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(CNINFO_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_cninfo.provider\n"
        "print('provider=' + str('axdata_source_cninfo.provider' in sys.modules))\n"
        "print('adapter=' + str('axdata_source_cninfo.adapter' in sys.modules))\n"
        "print('legacy=' + str('axdata_core.adapters.cninfo.request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "provider=True" in result.stdout
    assert "adapter=False" in result.stdout
    assert "legacy=False" in result.stdout


def test_cninfo_provider_metadata_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(CNINFO_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_cninfo.metadata as metadata\n"
        "print('provider_id=' + metadata.PROVIDER_ID)\n"
        "print('provider=' + str('axdata_source_cninfo.provider' in sys.modules))\n"
        "print('catalog=' + str('axdata_source_cninfo.catalog' in sys.modules))\n"
        "print('adapter=' + str('axdata_source_cninfo.adapter' in sys.modules))\n"
        "print('plugins=' + str('axdata_core.plugins' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert f"provider_id={CNINFO_PROVIDER_ID}" in result.stdout
    assert "provider=False" in result.stdout
    assert "catalog=False" in result.stdout
    assert "adapter=False" in result.stdout
    assert "plugins=False" in result.stdout


def test_cninfo_provider_adapter_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(CNINFO_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_cninfo.adapter\n"
        "print('adapter=' + str('axdata_source_cninfo.adapter' in sys.modules))\n"
        "print('bridge=' + str('axdata_core.adapters.cninfo.provider_bridge' in sys.modules))\n"
        "print('legacy=' + str('axdata_core.adapters.cninfo.request' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "adapter=True" in result.stdout
    assert "bridge=False" in result.stdout
    assert "legacy=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_cninfo_provider_create_adapter_does_not_load_legacy_request() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(CNINFO_PACKAGE_ROOT / 'src')!r})\n"
        "from axdata_source_cninfo.provider import provider\n"
        "adapter = provider.create_adapter(options={'opener': object()})\n"
        "print('adapter=' + str('axdata_source_cninfo.adapter' in sys.modules))\n"
        "print('bridge=' + str('axdata_core.adapters.cninfo.provider_bridge' in sys.modules))\n"
        "print('legacy=' + str('axdata_core.adapters.cninfo.request' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
        "print('has_adapter=' + str(adapter is not None))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "adapter=True" in result.stdout
    assert "bridge=False" in result.stdout
    assert "legacy=False" in result.stdout
    assert "source_request=False" in result.stdout
    assert "has_adapter=True" in result.stdout


def test_cninfo_provider_field_projection_does_not_load_source_request() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(CNINFO_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_cninfo.adapter as adapter_module\n"
        "class FakeLegacyAdapter:\n"
        "    source = 'cninfo'\n"
        "    def request(self, interface_name, params):\n"
        "        return [{'instrument_id': '000001.SZ', 'title': 'demo', 'extra': 'drop'}]\n"
        "adapter_module._create_legacy_adapter = lambda options: FakeLegacyAdapter()\n"
        "adapter = adapter_module.CninfoProviderAdapter()\n"
        "result = adapter.call('cninfo_announcements', fields=['instrument_id', 'title'])\n"
        "print('data=' + str(result.to_dict()['data']))\n"
        "print('source_projection=' + str('axdata_core.source_projection' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "data=[{'instrument_id': '000001.SZ', 'title': 'demo'}]" in result.stdout
    assert "source_projection=True" in result.stdout
    assert "source_request=False" in result.stdout


def test_cninfo_provider_call_with_options_does_not_create_default_adapter() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(CNINFO_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_cninfo.adapter as adapter_module\n"
        "calls = []\n"
        "class FakeLegacyAdapter:\n"
        "    source = 'cninfo'\n"
        "    def __init__(self, options): self.options = dict(options)\n"
        "    def request(self, interface_name, params):\n"
        "        return [{'announcement_id': '1218968511', 'timeout': self.options.get('timeout_ms')}]\n"
        "def fake_create(options):\n"
        "    calls.append(dict(options))\n"
        "    return FakeLegacyAdapter(options)\n"
        "adapter_module._create_legacy_adapter = fake_create\n"
        "adapter = adapter_module.CninfoProviderAdapter(options={'timeout_ms': 1000})\n"
        "first = adapter.call('cninfo_announcement_detail', options={'timeout_ms': 2000})\n"
        "second = adapter.call('cninfo_announcement_detail')\n"
        "print('calls=' + str(calls))\n"
        "print('first=' + str(first.to_dict()['data']))\n"
        "print('second=' + str(second.to_dict()['data']))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "calls=[{'timeout_ms': 2000}, {'timeout_ms': 1000}]" in result.stdout
    assert "first=[{'announcement_id': '1218968511', 'timeout': 2000}]" in result.stdout
    assert "second=[{'announcement_id': '1218968511', 'timeout': 1000}]" in result.stdout


def test_cninfo_provider_package_manifest_matches_provider(monkeypatch, tmp_path, capsys) -> None:
    install_root = _install_cninfo_provider(tmp_path)
    manifest_path = install_root / "axdata_source_cninfo" / "axdata-provider.json"

    monkeypatch.syspath_prepend(str(install_root))
    _clear_cninfo_modules()

    assert (
        main(
            [
                "plugin",
                "check",
                "--provider",
                "axdata_source_cninfo.provider:provider",
                "--manifest",
                str(manifest_path),
            ]
        )
        == 0
    )
    assert f"OK {CNINFO_PROVIDER_ID} interfaces=2 downloaders=0 collectors=0" in capsys.readouterr().out
    assert "axdata_source_cninfo.provider" in sys.modules
    assert "axdata_source_cninfo.adapter" not in sys.modules


def test_cninfo_provider_package_discovery_defaults_disabled(monkeypatch, tmp_path) -> None:
    install_root = _install_cninfo_provider(tmp_path)
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    _clear_cninfo_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    provider = snapshot.providers[CNINFO_PROVIDER_ID]
    assert provider.status == "disabled"
    assert provider.enabled is False
    assert provider.provider is None
    assert "axdata_source_cninfo.provider" not in sys.modules
    assert CNINFO_INTERFACE_NAMES <= set(snapshot.interfaces)
    assert snapshot.interfaces[CNINFO_ANNOUNCEMENTS_INTERFACE].provider_id == BUILTIN_CNINFO_PROVIDER_ID
    assert snapshot.interfaces[CNINFO_DETAIL_INTERFACE].provider_id == BUILTIN_CNINFO_PROVIDER_ID


def test_builtin_cninfo_wins_when_external_cninfo_conflicts(monkeypatch, tmp_path) -> None:
    install_root = _install_cninfo_provider(tmp_path)
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    enable_provider(CNINFO_PROVIDER_ID, data_root=data_root)
    _clear_cninfo_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert snapshot.interfaces[CNINFO_ANNOUNCEMENTS_INTERFACE].provider_id == BUILTIN_CNINFO_PROVIDER_ID
    assert snapshot.providers[BUILTIN_CNINFO_PROVIDER_ID].status == "enabled"
    assert snapshot.providers[CNINFO_PROVIDER_ID].status == "conflict"
    assert snapshot.providers[CNINFO_PROVIDER_ID].effective_trust_level == "community"
    assert "axdata_source_cninfo.provider" not in sys.modules


def test_external_cninfo_routes_when_builtin_cninfo_disabled(monkeypatch, tmp_path) -> None:
    install_root = _install_cninfo_provider(tmp_path)
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    enable_provider(CNINFO_PROVIDER_ID, data_root=data_root)
    disable_provider(BUILTIN_CNINFO_PROVIDER_ID, data_root=data_root)
    _clear_cninfo_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert snapshot.providers[BUILTIN_CNINFO_PROVIDER_ID].status == "disabled"
    assert snapshot.providers[CNINFO_PROVIDER_ID].status == "enabled"
    assert snapshot.interfaces[CNINFO_ANNOUNCEMENTS_INTERFACE].provider_id == CNINFO_PROVIDER_ID
    assert snapshot.interfaces[CNINFO_DETAIL_INTERFACE].provider_id == CNINFO_PROVIDER_ID
    assert "axdata_source_cninfo.provider" not in sys.modules

    result = request_interface(
        CNINFO_ANNOUNCEMENTS_INTERFACE,
        params={"code": "000001.SZ", "start_date": "20240101", "end_date": "20240131", "limit": 1},
        fields=["instrument_id", "title", "download_url"],
        options={"opener": CninfoOpener(), "timeout_ms": 1000},
    )

    assert result.records == [
        {
            "instrument_id": "000001.SZ",
            "title": "关联交易公告",
            "download_url": "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF",
        }
    ]
    assert result.meta["source"] == "cninfo"
    assert result.meta["provider_id"] == CNINFO_PROVIDER_ID
    assert result.meta["source_name"] == "巨潮"
    assert "axdata_source_cninfo.provider" in sys.modules
    assert "axdata_core.adapters.cninfo.provider_bridge" in sys.modules
    assert "axdata_core.adapters.cninfo.request" in sys.modules

    detail = request_interface(
        CNINFO_DETAIL_INTERFACE,
        params={
            "announcement_id": "1218968511",
            "url": "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF",
        },
        fields=["announcement_id", "content_type", "file_size_bytes"],
        options={"opener": CninfoOpener(), "timeout_ms": 1000},
    )

    assert detail.records == [
        {
            "announcement_id": "1218968511",
            "content_type": "application/pdf",
            "file_size_bytes": 158287,
        }
    ]
    assert detail.meta["provider_id"] == CNINFO_PROVIDER_ID


def test_cninfo_provider_package_pyproject_declares_entry_point() -> None:
    import tomllib

    pyproject = tomllib.loads((CNINFO_PACKAGE_ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["name"] == "axdata-source-cninfo"
    assert "axdata-core>=0.1.0" in set(pyproject["project"]["dependencies"])
    assert (
        pyproject["project"]["entry-points"]["axdata.providers"]["cninfo"]
        == "axdata_source_cninfo.provider:provider"
    )
    assert "axdata-provider.json" in pyproject["tool"]["setuptools"]["package-data"]["axdata_source_cninfo"]


def test_cninfo_provider_package_builds_wheel_with_manifest_and_entry_point(tmp_path) -> None:
    wheel_path = _build_cninfo_wheel(tmp_path)

    with ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
        assert "axdata_source_cninfo/axdata-provider.json" in names
        assert "axdata_source_cninfo/metadata.py" in names
        assert "axdata_source_cninfo-0.1.0.dist-info/entry_points.txt" in names
        entry_points = wheel.read(
            "axdata_source_cninfo-0.1.0.dist-info/entry_points.txt"
        ).decode("utf-8")
        manifest = ProviderManifest.from_dict(
            json.loads(wheel.read("axdata_source_cninfo/axdata-provider.json"))
        )

    assert "cninfo = axdata_source_cninfo.provider:provider" in entry_points
    assert manifest.provider.provider_id == CNINFO_PROVIDER_ID
    assert {interface.name for interface in manifest.interfaces} == CNINFO_INTERFACE_NAMES


def test_cninfo_provider_installed_from_wheel_is_discovered_and_can_route(
    monkeypatch,
    tmp_path,
) -> None:
    wheel_path = _build_cninfo_wheel(tmp_path)
    install_root = tmp_path / "installed"
    data_root = tmp_path / "data"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(install_root),
            str(wheel_path),
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    enable_provider(CNINFO_PROVIDER_ID, data_root=data_root)
    disable_provider(BUILTIN_CNINFO_PROVIDER_ID, data_root=data_root)
    _clear_cninfo_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert snapshot.providers[CNINFO_PROVIDER_ID].status == "enabled"
    assert snapshot.interfaces[CNINFO_ANNOUNCEMENTS_INTERFACE].provider_id == CNINFO_PROVIDER_ID
    assert "axdata_source_cninfo.provider" not in sys.modules

    result = request_interface(
        CNINFO_ANNOUNCEMENTS_INTERFACE,
        params={"code": "000001.SZ", "start_date": "20240101", "end_date": "20240131", "limit": 1},
        fields=["instrument_id", "publish_date"],
        options={"opener": CninfoOpener()},
    )

    assert result.records == [{"instrument_id": "000001.SZ", "publish_date": "20240123"}]
    assert result.meta["provider_id"] == CNINFO_PROVIDER_ID
    assert "axdata_source_cninfo.provider" in sys.modules
    assert "axdata_core.adapters.cninfo.provider_bridge" in sys.modules
    assert "axdata_core.adapters.cninfo.request" in sys.modules


def _build_cninfo_wheel(tmp_path: Path) -> Path:
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
            str(CNINFO_PACKAGE_ROOT),
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return next(wheel_dir.glob("axdata_source_cninfo-0.1.0-*.whl"))


def _install_cninfo_provider(tmp_path: Path) -> Path:
    install_root = tmp_path / "site-packages"
    package_root = install_root / "axdata_source_cninfo"
    dist_info = install_root / "axdata_source_cninfo-0.1.0.dist-info"
    shutil.copytree(CNINFO_PACKAGE_ROOT / "src" / "axdata_source_cninfo", package_root)
    dist_info.mkdir(parents=True)

    manifest_path = package_root / "axdata-provider.json"
    manifest = ProviderManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    assert manifest.provider.provider_id == CNINFO_PROVIDER_ID

    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: axdata-source-cninfo\n"
        "Version: 0.1.0\n",
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(
        "[axdata.providers]\n"
        "cninfo = axdata_source_cninfo.provider:provider\n",
        encoding="utf-8",
    )
    (dist_info / "RECORD").write_text(
        "\n".join(
            [
                "axdata_source_cninfo/__init__.py,,",
                "axdata_source_cninfo/adapter.py,,",
                "axdata_source_cninfo/catalog.py,,",
                "axdata_source_cninfo/metadata.py,,",
                "axdata_source_cninfo/provider.py,,",
                "axdata_source_cninfo/axdata-provider.json,,",
                "axdata_source_cninfo-0.1.0.dist-info/METADATA,,",
                "axdata_source_cninfo-0.1.0.dist-info/entry_points.txt,,",
                "axdata_source_cninfo-0.1.0.dist-info/RECORD,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return install_root


def _clear_cninfo_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "axdata_source_cninfo" or module_name.startswith("axdata_source_cninfo."):
            sys.modules.pop(module_name, None)
