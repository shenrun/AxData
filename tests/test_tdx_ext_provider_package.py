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

from tests.test_tdx_ext_source_request_adapter import _build_cache_root


REPO_ROOT = Path(__file__).resolve().parents[1]
TDX_EXT_PACKAGE_ROOT = REPO_ROOT / "packages" / "axdata-source-tdx-ext"
TDX_EXT_PROVIDER_ID = "axdata.source.tdx_ext_external"
BUILTIN_TDX_EXT_PROVIDER_ID = "axdata.source.tdx_ext"
TDX_EXT_INTERFACE_NAME = "futures_contracts_tdx"
TDX_EXT_SOURCE_NAME_ZH = "通达信扩展行情"
TDX_EXT_INTERFACE_COUNT = 31


def test_tdx_ext_provider_package_root_import_is_lightweight(monkeypatch, tmp_path) -> None:
    install_root = _install_tdx_ext_provider(tmp_path)

    monkeypatch.syspath_prepend(str(install_root))
    _clear_tdx_ext_provider_modules()

    package = importlib.import_module("axdata_source_tdx_ext")

    assert "axdata_source_tdx_ext.provider" not in sys.modules
    assert package.provider.provider_id == TDX_EXT_PROVIDER_ID
    assert "axdata_source_tdx_ext.provider" in sys.modules
    assert "axdata_source_tdx_ext.adapter" not in sys.modules


def test_tdx_ext_provider_catalog_import_does_not_load_builtin_projection() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_EXT_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_tdx_ext.catalog\n"
        "print('catalog=' + str('axdata_source_tdx_ext.catalog' in sys.modules))\n"
        "print('builtin=' + str('axdata_core.builtin_providers' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
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

    assert "catalog=True" in result.stdout
    assert "builtin=False" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout


def test_tdx_ext_provider_import_does_not_load_builtin_projection() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_EXT_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_tdx_ext.provider\n"
        "print('provider=' + str('axdata_source_tdx_ext.provider' in sys.modules))\n"
        "print('builtin=' + str('axdata_core.builtin_providers' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
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
    assert "builtin=False" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout


def test_tdx_ext_provider_catalog_projection_does_not_load_tdx_or_downloaders() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_EXT_PACKAGE_ROOT / 'src')!r})\n"
        "from axdata_source_tdx_ext.provider import provider\n"
        "interfaces = provider.interfaces()\n"
        "downloaders = provider.downloader_profiles()\n"
        "print('interfaces=' + str(len(interfaces)))\n"
        "print('downloaders=' + str(len(downloaders)))\n"
        "tracked = [\n"
        "    'axdata_core.sources.tdx.catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_core.downloaders',\n"
        "    'axdata_core.downloader_registry',\n"
        "    'axdata_core.source_request',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
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

    assert f"interfaces={TDX_EXT_INTERFACE_COUNT}" in result.stdout
    assert "downloaders=0" in result.stdout
    assert "loaded=\n" in result.stdout


def test_tdx_ext_provider_metadata_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_EXT_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_tdx_ext.metadata as metadata\n"
        "print('provider_id=' + metadata.PROVIDER_ID)\n"
        "print('provider=' + str('axdata_source_tdx_ext.provider' in sys.modules))\n"
        "print('catalog=' + str('axdata_source_tdx_ext.catalog' in sys.modules))\n"
        "print('adapter=' + str('axdata_source_tdx_ext.adapter' in sys.modules))\n"
        "print('plugins=' + str('axdata_core.plugins' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
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

    assert f"provider_id={TDX_EXT_PROVIDER_ID}" in result.stdout
    assert "provider=False" in result.stdout
    assert "catalog=False" in result.stdout
    assert "adapter=False" in result.stdout
    assert "plugins=False" in result.stdout
    assert "request=False" in result.stdout


def test_core_tdx_ext_package_root_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext as tdx_ext\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.local_cache',\n"
        "    'axdata_core.adapters.tdx_ext.models',\n"
        "    'axdata_core.adapters.tdx_ext.exceptions',\n"
        "    'axdata_core._tdx_wire.exceptions',\n"
        "]\n"
        "print('before=' + ','.join(name for name in tracked if name in sys.modules))\n"
        "_ = tdx_ext.ConnectionClosedError\n"
        "print('after_exceptions=' + ','.join(name for name in tracked if name in sys.modules))\n"
        "_ = tdx_ext.TdxExtRequestAdapter\n"
        "print('after_request=' + ','.join(name for name in tracked if name in sys.modules))\n"
        "_ = tdx_ext.TdxExtCachePaths\n"
        "print('after_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
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

    assert "before=\n" in result.stdout
    assert "after_exceptions=axdata_core.adapters.tdx_ext.exceptions\n" in result.stdout
    assert "axdata_core._tdx_wire.exceptions" not in result.stdout
    assert (
        "after_request=axdata_core.adapters.tdx_ext.request,"
        "axdata_core.adapters.tdx_ext.exceptions\n"
    ) in result.stdout
    assert "axdata_core.adapters.tdx_ext.client" not in result.stdout
    assert "axdata_core.adapters.tdx_ext.pool" not in result.stdout
    assert "after_cache=True" in result.stdout


def test_tdx_ext_pool_import_does_not_load_client() -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.tdx_ext.servers import TdxExtServer\n"
        "import axdata_core.adapters.tdx_ext.pool as pool\n"
        "print('client_before=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "class FakeClient:\n"
        "    def __init__(self, **kwargs): pass\n"
        "    def close(self): pass\n"
        "pool.TdxExtClientPool(\n"
        "    servers=(TdxExtServer(index=1, name='demo', host='127.0.0.1', port=7727, is_primary=True),),\n"
        "    connections_per_server=1,\n"
        "    client_factory=FakeClient,\n"
        ").close()\n"
        "print('client_after_fake=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "try:\n"
        "    pool.TdxExtClientPool(\n"
        "        servers=(TdxExtServer(index=1, name='demo', host='127.0.0.1', port=7727, is_primary=True),),\n"
        "        connections_per_server=1,\n"
        "    ).close()\n"
        "except Exception:\n"
        "    pass\n"
        "print('client_after_default=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
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

    assert "client_before=False" in result.stdout
    assert "client_after_fake=False" in result.stdout
    assert "client_after_default=True" in result.stdout


def test_tdx_ext_validation_helpers_do_not_load_source_request_gateway() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.options\n"
        "import axdata_core.adapters.tdx_ext.request\n"
        "print('options=' + str('axdata_core.adapters.tdx_ext.options' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
        "print('local_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
        "print('source_errors=' + str('axdata_core.source_errors' in sys.modules))\n"
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

    assert "options=True" in result.stdout
    assert "request=True" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout
    assert "local_cache=False" in result.stdout
    assert "source_errors=True" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_request_instruments_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.request_instruments\n"
        "print('request_instruments=' + str('axdata_core.adapters.tdx_ext.request_instruments' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
        "print('local_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
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

    assert "request_instruments=True" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout
    assert "local_cache=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_request_execution_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.request_execution\n"
        "print('request_execution=' + str('axdata_core.adapters.tdx_ext.request_execution' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
        "print('local_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
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

    assert "request_execution=True" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout
    assert "local_cache=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_request_series_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.request_series\n"
        "print('request_series=' + str('axdata_core.adapters.tdx_ext.request_series' in sys.modules))\n"
        "print('request_normalize=' + str('axdata_core.adapters.tdx_ext.request_normalize' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
        "print('local_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
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

    assert "request_series=True" in result.stdout
    assert "request_normalize=True" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout
    assert "local_cache=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_source_execution_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.source_execution\n"
        "print('source_execution=' + str('axdata_core.adapters.tdx_ext.source_execution' in sys.modules))\n"
        "print('server_cache=' + str('axdata_core.adapters.tdx_ext.server_cache' in sys.modules))\n"
        "print('server_config=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
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

    assert "source_execution=True" in result.stdout
    assert "server_cache=False" in result.stdout
    assert "server_config=False" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_provider_bridge_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.provider_bridge\n"
        "print('provider_bridge=' + str('axdata_core.adapters.tdx_ext.provider_bridge' in sys.modules))\n"
        "print('request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
        "print('local_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
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

    assert "provider_bridge=True" in result.stdout
    assert "request=False" in result.stdout
    assert "client=False" in result.stdout
    assert "pool=False" in result.stdout
    assert "local_cache=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_helper_module_imports_are_lightweight() -> None:
    modules = [
        "axdata_core.adapters.tdx_ext.host_config",
        "axdata_core.adapters.tdx_ext.interface_sets",
        "axdata_core.adapters.tdx_ext.options",
        "axdata_core.adapters.tdx_ext.request_normalize",
        "axdata_core.adapters.tdx_ext.request_params",
        "axdata_core.adapters.tdx_ext.server_cache",
        "axdata_core.adapters.tdx_ext.source_execution",
    ]
    code = (
        "import importlib\n"
        "import sys\n"
        f"modules = {modules!r}\n"
        "for module in modules:\n"
        "    importlib.import_module(module)\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.local_cache',\n"
        "    'axdata_core.source_request',\n"
        "    'axdata_core.tdx_server_config',\n"
        "]\n"
        "print('helpers=' + ','.join(modules))\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
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

    for module in modules:
        assert module in result.stdout
    assert "loaded=\n" in result.stdout


def test_tdx_ext_provider_adapter_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_EXT_PACKAGE_ROOT / 'src')!r})\n"
        "import axdata_source_tdx_ext.adapter\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.local_cache',\n"
        "    'axdata_core.source_request',\n"
        "]\n"
        "print('provider_adapter=' + str('axdata_source_tdx_ext.adapter' in sys.modules))\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
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

    assert "provider_adapter=True" in result.stdout
    assert "loaded=\n" in result.stdout


def test_tdx_ext_provider_create_adapter_does_not_load_core_request() -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_EXT_PACKAGE_ROOT / 'src')!r})\n"
        "from axdata_source_tdx_ext.provider import provider\n"
        "adapter = provider.create_adapter(options={'tdx_root': 'demo'})\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.local_cache',\n"
        "    'axdata_core.source_request',\n"
        "]\n"
        "print('provider_adapter=' + str('axdata_source_tdx_ext.adapter' in sys.modules))\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
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

    assert "provider_adapter=True" in result.stdout
    assert "loaded=\n" in result.stdout
    assert "has_adapter=True" in result.stdout


def test_tdx_ext_provider_package_manifest_matches_provider(monkeypatch, tmp_path, capsys) -> None:
    install_root = _install_tdx_ext_provider(tmp_path)
    manifest_path = install_root / "axdata_source_tdx_ext" / "axdata-provider.json"

    monkeypatch.syspath_prepend(str(install_root))
    _clear_tdx_ext_provider_modules()

    assert (
        main(
            [
                "plugin",
                "check",
                "--provider",
                "axdata_source_tdx_ext.provider:provider",
                "--manifest",
                str(manifest_path),
            ]
        )
        == 0
    )
    assert (
        f"OK {TDX_EXT_PROVIDER_ID} interfaces={TDX_EXT_INTERFACE_COUNT} downloaders=0 collectors=0"
        in capsys.readouterr().out
    )
    assert "axdata_source_tdx_ext.provider" in sys.modules
    assert "axdata_source_tdx_ext.adapter" not in sys.modules


def test_tdx_ext_provider_package_discovery_defaults_enabled(monkeypatch, tmp_path) -> None:
    install_root = _install_tdx_ext_provider(tmp_path)
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    _clear_tdx_ext_provider_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    provider = snapshot.providers[TDX_EXT_PROVIDER_ID]
    assert provider.status == "enabled"
    assert provider.enabled is True
    assert provider.provider is None
    assert BUILTIN_TDX_EXT_PROVIDER_ID not in snapshot.providers
    assert snapshot.interfaces[TDX_EXT_INTERFACE_NAME].provider_id == TDX_EXT_PROVIDER_ID
    assert "axdata_source_tdx_ext.provider" not in sys.modules

    from axdata_core.plugin_status import provider_status_row

    row = provider_status_row(provider, snapshot=snapshot)
    assert row["source_name_zh"] == TDX_EXT_SOURCE_NAME_ZH
    assert row["install_source"] == "preinstalled"
    assert row["can_enable"] is False
    assert row["can_disable"] is True
    assert row["can_uninstall"] is True
    assert row["uninstall_mode"] == "managed_disable"
    assert row["uninstall_block_reason"] is None
    assert row["action_command"] is None


def test_external_tdx_ext_routes_when_enabled(monkeypatch, tmp_path) -> None:
    install_root = _install_tdx_ext_provider(tmp_path)
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    enable_provider(TDX_EXT_PROVIDER_ID, data_root=data_root)
    _clear_tdx_ext_provider_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert BUILTIN_TDX_EXT_PROVIDER_ID not in snapshot.providers
    assert snapshot.interfaces[TDX_EXT_INTERFACE_NAME].provider_id == TDX_EXT_PROVIDER_ID
    assert snapshot.providers[TDX_EXT_PROVIDER_ID].status == "enabled"
    assert snapshot.providers[TDX_EXT_PROVIDER_ID].effective_trust_level == "community"
    assert "axdata_source_tdx_ext.provider" not in sys.modules


def test_external_tdx_ext_routes_when_builtin_tdx_ext_disabled(monkeypatch, tmp_path) -> None:
    install_root = _install_tdx_ext_provider(tmp_path)
    data_root = tmp_path / "data"
    tdx_root = _build_cache_root(tmp_path)

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    enable_provider(TDX_EXT_PROVIDER_ID, data_root=data_root)
    disable_provider(BUILTIN_TDX_EXT_PROVIDER_ID, data_root=data_root)
    _clear_tdx_ext_provider_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert BUILTIN_TDX_EXT_PROVIDER_ID not in snapshot.providers
    assert snapshot.providers[TDX_EXT_PROVIDER_ID].status == "enabled"
    assert snapshot.interfaces[TDX_EXT_INTERFACE_NAME].provider_id == TDX_EXT_PROVIDER_ID
    assert "axdata_source_tdx_ext.provider" not in sys.modules

    result = request_interface(
        TDX_EXT_INTERFACE_NAME,
        params={"tdx_root": str(tdx_root), "limit": 1},
        fields=["instrument_id", "symbol", "product_name"],
        data_root=data_root,
    )

    assert result.records == [
        {"instrument_id": "IC2606.CFFEX", "symbol": "IC2606", "product_name": "中证"}
    ]
    assert result.meta["source"] == "tdx_ext"
    assert result.meta["provider_id"] == TDX_EXT_PROVIDER_ID
    assert result.meta["data_origin"] == "local_tdx_extended_cache"
    assert "axdata_source_tdx_ext.provider" in sys.modules
    assert "axdata_core.adapters.tdx_ext.provider_bridge" in sys.modules
    assert "axdata_core.adapters.tdx_ext.request" in sys.modules


def test_tdx_ext_provider_package_pyproject_declares_entry_point() -> None:
    import tomllib

    pyproject = tomllib.loads((TDX_EXT_PACKAGE_ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["name"] == "axdata-source-tdx-ext"
    assert "axdata-core>=0.1.0" in set(pyproject["project"]["dependencies"])
    assert (
        pyproject["project"]["entry-points"]["axdata.providers"]["tdx_ext"]
        == "axdata_source_tdx_ext.provider:provider"
    )
    assert (
        "axdata-provider.json"
        in pyproject["tool"]["setuptools"]["package-data"]["axdata_source_tdx_ext"]
    )


def test_tdx_ext_provider_package_builds_wheel_with_manifest_and_entry_point(tmp_path) -> None:
    wheel_path = _build_tdx_ext_wheel(tmp_path)

    with ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
        assert "axdata_source_tdx_ext/axdata-provider.json" in names
        assert "axdata_source_tdx_ext/metadata.py" in names
        assert "axdata_source_tdx_ext-0.1.0.dist-info/entry_points.txt" in names
        entry_points = wheel.read(
            "axdata_source_tdx_ext-0.1.0.dist-info/entry_points.txt"
        ).decode("utf-8")
        manifest = ProviderManifest.from_dict(
            json.loads(wheel.read("axdata_source_tdx_ext/axdata-provider.json"))
        )

    assert "tdx_ext = axdata_source_tdx_ext.provider:provider" in entry_points
    assert manifest.provider.provider_id == TDX_EXT_PROVIDER_ID
    assert manifest.provider.source_name_zh == TDX_EXT_SOURCE_NAME_ZH
    interfaces = {interface.name: interface for interface in manifest.interfaces}
    assert TDX_EXT_INTERFACE_NAME in interfaces
    assert interfaces[TDX_EXT_INTERFACE_NAME].source_name_zh == TDX_EXT_SOURCE_NAME_ZH
    assert interfaces[TDX_EXT_INTERFACE_NAME].menu_path[0] == TDX_EXT_SOURCE_NAME_ZH
    assert interfaces["fx_codes_tdx"].source_name_zh == TDX_EXT_SOURCE_NAME_ZH
    assert interfaces["futures_contracts_tdx"].asset_class == "future"
    assert interfaces["option_contracts_tdx"].asset_class == "option"
    assert interfaces["fx_codes_tdx"].asset_class == "fx"
    assert interfaces["fx_realtime_snapshot_tdx"].asset_class == "fx"
    assert interfaces["macro_indicator_snapshot_tdx"].asset_class == "macro"
    assert manifest.downloaders == ()


def test_tdx_ext_provider_installed_from_wheel_is_discovered_and_can_route(
    monkeypatch,
    tmp_path,
) -> None:
    wheel_path = _build_tdx_ext_wheel(tmp_path)
    install_root = tmp_path / "installed"
    data_root = tmp_path / "data"
    tdx_root = _build_cache_root(tmp_path)

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
    enable_provider(TDX_EXT_PROVIDER_ID, data_root=data_root)
    disable_provider(BUILTIN_TDX_EXT_PROVIDER_ID, data_root=data_root)
    _clear_tdx_ext_provider_modules()

    registry = build_builtin_provider_registry(data_root=data_root)
    snapshot = registry.snapshot()

    assert snapshot.providers[TDX_EXT_PROVIDER_ID].status == "enabled"
    assert snapshot.interfaces[TDX_EXT_INTERFACE_NAME].provider_id == TDX_EXT_PROVIDER_ID
    assert snapshot.interfaces["fx_codes_tdx"].provider_id == TDX_EXT_PROVIDER_ID
    assert snapshot.interfaces["fx_codes_tdx"].interface.asset_class == "fx"
    assert snapshot.interfaces["macro_indicator_snapshot_tdx"].interface.asset_class == "macro"
    assert "axdata_source_tdx_ext.provider" not in sys.modules

    result = request_interface(
        TDX_EXT_INTERFACE_NAME,
        params={"tdx_root": str(tdx_root), "limit": 1},
        fields=["instrument_id", "product_name"],
        data_root=data_root,
    )

    assert result.records == [{"instrument_id": "IC2606.CFFEX", "product_name": "中证"}]
    assert result.meta["provider_id"] == TDX_EXT_PROVIDER_ID
    assert "axdata_source_tdx_ext.provider" in sys.modules
    assert "axdata_core.adapters.tdx_ext.provider_bridge" in sys.modules
    assert "axdata_core.adapters.tdx_ext.request" in sys.modules


def _build_tdx_ext_wheel(tmp_path: Path) -> Path:
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
            str(TDX_EXT_PACKAGE_ROOT),
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return next(wheel_dir.glob("axdata_source_tdx_ext-0.1.0-*.whl"))


def _install_tdx_ext_provider(tmp_path: Path) -> Path:
    install_root = tmp_path / "site-packages"
    package_root = install_root / "axdata_source_tdx_ext"
    dist_info = install_root / "axdata_source_tdx_ext-0.1.0.dist-info"
    shutil.copytree(TDX_EXT_PACKAGE_ROOT / "src" / "axdata_source_tdx_ext", package_root)
    dist_info.mkdir(parents=True)

    manifest_path = package_root / "axdata-provider.json"
    manifest = ProviderManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    assert manifest.provider.provider_id == TDX_EXT_PROVIDER_ID

    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: axdata-source-tdx-ext\n"
        "Version: 0.1.0\n",
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(
        "[axdata.providers]\n"
        "tdx_ext = axdata_source_tdx_ext.provider:provider\n",
        encoding="utf-8",
    )
    (dist_info / "RECORD").write_text(
        "\n".join(
            [
                "axdata_source_tdx_ext/__init__.py,,",
                "axdata_source_tdx_ext/adapter.py,,",
                "axdata_source_tdx_ext/catalog.py,,",
                "axdata_source_tdx_ext/metadata.py,,",
                "axdata_source_tdx_ext/provider.py,,",
                "axdata_source_tdx_ext/axdata-provider.json,,",
                "axdata_source_tdx_ext-0.1.0.dist-info/METADATA,,",
                "axdata_source_tdx_ext-0.1.0.dist-info/entry_points.txt,,",
                "axdata_source_tdx_ext-0.1.0.dist-info/RECORD,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return install_root


def _clear_tdx_ext_provider_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "axdata_source_tdx_ext" or module_name.startswith("axdata_source_tdx_ext."):
            sys.modules.pop(module_name, None)
