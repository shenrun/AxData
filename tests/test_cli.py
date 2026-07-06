from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from axdata_core.cli import main
from axdata_core.collector_scheduler import CollectorRun, CollectorSchedulerStore
from axdata_core.plugin_config import load_plugin_config, set_provider_override
from axdata_core.plugins import (
    CollectorSpec,
    MANIFEST_FILE_NAME,
    PLUGIN_MANIFEST_FILE_NAME,
    PluginInfo,
    ProviderInfo,
    ProviderManifest,
)
from axdata_core.provider_registry import ProviderRegistry
from tests.test_axp import _build_tencent_axp
from tests.test_tencent_provider_package import TENCENT_PROVIDER_ID
from tests.tdx_plugin_helpers import (
    TDX_COLLECTOR_PLUGIN_ID,
    TDX_EXT_PROVIDER_ID,
    TDX_PACKAGE_ROOT,
    TDX_PROVIDER_ID,
    build_registry_with_local_tdx_plugins,
    ensure_local_tdx_plugin_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ensure_local_tdx_plugin_paths()

TENCENT_BUILTIN_INTERFACE_NAMES = [
    "stock_zh_a_spot_tx",
    "stock_zh_a_hist_tx",
    "stock_zh_index_daily_tx",
    "stock_zh_a_tick_tx_js",
    "get_tx_start_year",
    "tencent_realtime_snapshot",
]


def _pythonpath_with_local_tdx_plugins() -> str:
    return os.pathsep.join(
        [
            str(TDX_PACKAGE_ROOT / "src"),
            str(REPO_ROOT / "packages" / "axdata-source-tdx-ext" / "src"),
            str(REPO_ROOT / "libs" / "axdata_core"),
        ]
    )


def _patch_local_tdx_plugin_registry(monkeypatch):
    import axdata_core.provider_catalog as provider_catalog

    base_builder = provider_catalog.build_builtin_provider_registry

    def build_registry(**kwargs):
        return build_registry_with_local_tdx_plugins(
            base_builder=base_builder,
            **kwargs,
        )

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", build_registry)
    return build_registry


def _collector_registry() -> ProviderRegistry:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.plugin.close_refresh",
            name_zh="收盘刷新",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(
            CollectorSpec(
                name="close.refresh.daily",
                display_name_zh="收盘刷新",
                description="每日收盘后刷新基础数据。",
                interfaces=("stock_codes_tdx",),
                downloader_profile="tdx.stock_codes.latest",
                resource_group="tdx.quote",
                default_schedule={"frequency": "daily", "time": "18:05"},
                default_params={"scope": "all"},
            ),
        ),
    )
    registry = ProviderRegistry(enabled_provider_ids={"axdata.plugin.close_refresh"})
    registry.register_manifest(manifest)
    return registry


def _environment_plugin_registry() -> ProviderRegistry:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.env_demo",
            source_code="env_demo",
            source_name_zh="环境示例",
            version="0.1.0",
        ),
        interfaces=(),
    )
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.env_demo"})
    registry.register_manifest(manifest, entry_point=object(), enabled=True)
    return registry


def test_provider_guidance_prioritizes_error_states_over_disabled_flag() -> None:
    from axdata_core.diagnostics import provider_guidance

    failed = provider_guidance(
        provider_id="axdata.source.bad",
        source_code="bad",
        status="failed",
        enabled=False,
        built_in=False,
        error="missing axdata-provider.json",
    )
    assert "manifest" in failed["status_message"]
    assert "重新安装" in failed["next_action"]
    assert failed["action_command"] is None

    incompatible = provider_guidance(
        provider_id="axdata.source.old",
        source_code="old",
        status="incompatible",
        enabled=False,
        built_in=False,
        error="Unsupported plugin_api_version '0'; expected '2'.",
    )
    assert "不兼容" in incompatible["status_message"]
    assert "plugin_api_version" in incompatible["next_action"]
    assert incompatible["action_command"] is None

    conflict = provider_guidance(
        provider_id="axdata.source.conflict",
        source_code="conflict",
        status="conflict",
        enabled=False,
        built_in=False,
        error="Interface name conflict.",
    )
    assert "冲突" in conflict["status_message"]
    assert "override" in conflict["next_action"]
    assert conflict["action_command"] is None


def test_cli_import_does_not_eager_load_provider_catalog_or_builtins() -> None:
    code = (
        "import sys\n"
        "import axdata_core.cli\n"
        "print('provider_catalog=' + str('axdata_core.provider_catalog' in sys.modules))\n"
        "print('builtin=' + str('axdata_core.builtin_providers' in sys.modules))\n"
        "print('tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
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

    assert "provider_catalog=False" in result.stdout
    assert "builtin=False" in result.stdout
    assert "tdx_request=False" in result.stdout


def test_plugin_list_does_not_load_tdx_runtime(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.cli import main\n"
        f"exit_code = main(['--data-root', {str(tmp_path / 'data')!r}, 'plugin', 'list', '--json'])\n"
        "print('exit=' + str(exit_code))\n"
        "tracked = [\n"
        "    'axdata_core.provider_catalog',\n"
        "    'axdata_core.builtin_providers',\n"
        "    'axdata_core.sources.tdx.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.f10_request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.source_request',\n"
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

    assert "exit=0" in result.stdout
    assert "axdata_core.provider_catalog" in result.stdout
    assert "axdata_core.builtin_providers" in result.stdout
    assert "axdata_core.sources.tdx.catalog" not in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_plugin_info_external_tdx_provider_does_not_load_tdx_runtime(monkeypatch, tmp_path) -> None:
    _patch_local_tdx_plugin_registry(monkeypatch)
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TDX_PACKAGE_ROOT / 'src')!r})\n"
        f"sys.path.insert(0, {str(REPO_ROOT / 'packages' / 'axdata-source-tdx-ext' / 'src')!r})\n"
        "from tests.tdx_plugin_helpers import build_registry_with_local_tdx_plugins\n"
        "import axdata_core.provider_catalog as provider_catalog\n"
        "base_builder = provider_catalog.build_builtin_provider_registry\n"
        "provider_catalog.build_builtin_provider_registry = lambda **kwargs: build_registry_with_local_tdx_plugins(base_builder=base_builder, **kwargs)\n"
        "from axdata_core.cli import main\n"
        f"exit_code = main(['--data-root', {str(tmp_path / 'data')!r}, 'plugin', 'info', {TDX_PROVIDER_ID!r}, '--json'])\n"
        "print('exit=' + str(exit_code))\n"
        "tracked = [\n"
        "    'axdata_core.provider_catalog',\n"
        "    'axdata_core.builtin_providers',\n"
        "    'axdata_source_tdx.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_source_tdx.tdx_f10_catalog',\n"
        "    'axdata_source_tdx.tdx_f10_specs',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.f10_request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.source_request',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": f"{REPO_ROOT};{_pythonpath_with_local_tdx_plugins()}",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "exit=0" in result.stdout
    assert f'"provider_id": "{TDX_PROVIDER_ID}"' in result.stdout
    assert "axdata_core.provider_catalog" in result.stdout
    assert "axdata_core.builtin_providers" in result.stdout
    assert "axdata_source_tdx.catalog" in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_source_tdx.tdx_f10_catalog" not in result.stdout
    assert "axdata_source_tdx.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_plugin_check_external_tdx_provider_does_not_load_tdx_runtime() -> None:
    code = (
        "import sys\n"
        "from axdata_core.cli import main\n"
        "exit_code = main(['plugin', 'check', '--provider', 'axdata_source_tdx.provider:provider'])\n"
        "print('exit=' + str(exit_code))\n"
        "tracked = [\n"
        "    'axdata_core.builtin_providers',\n"
        "    'axdata_source_tdx.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_source_tdx.tdx_f10_catalog',\n"
        "    'axdata_source_tdx.tdx_f10_specs',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.f10_request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.source_request',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath_with_local_tdx_plugins(),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert f"OK {TDX_PROVIDER_ID} interfaces=90 downloaders=10 collectors=0" in result.stdout
    assert "exit=0" in result.stdout
    assert "axdata_core.builtin_providers" not in result.stdout
    assert "axdata_source_tdx.catalog" in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_source_tdx.tdx_f10_catalog" not in result.stdout
    assert "axdata_source_tdx.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_plugin_build_external_tdx_provider_does_not_load_tdx_runtime(tmp_path) -> None:
    output = tmp_path / MANIFEST_FILE_NAME
    code = (
        "import sys\n"
        "from axdata_core.cli import main\n"
        f"exit_code = main(['plugin', 'build', '--provider', 'axdata_source_tdx.provider:provider', '--output', {str(output)!r}])\n"
        "print('exit=' + str(exit_code))\n"
        "tracked = [\n"
        "    'axdata_core.builtin_providers',\n"
        "    'axdata_source_tdx.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_source_tdx.tdx_f10_catalog',\n"
        "    'axdata_source_tdx.tdx_f10_specs',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.f10_request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.source_request',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath_with_local_tdx_plugins(),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "exit=0" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["provider"]["provider_id"] == TDX_PROVIDER_ID
    assert len(payload["interfaces"]) == 90
    assert len(payload["downloaders"]) == 10
    assert payload["collectors"] == []
    assert "axdata_core.builtin_providers" not in result.stdout
    assert "axdata_source_tdx.catalog" in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_source_tdx.tdx_f10_catalog" not in result.stdout
    assert "axdata_source_tdx.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_plugin_list_outputs_providers_json(capsys, monkeypatch, tmp_path) -> None:
    _patch_local_tdx_plugin_registry(monkeypatch)
    exit_code = main(["--data-root", str(tmp_path / "data"), "plugin", "list", "--json"])

    assert exit_code == 0
    providers = json.loads(capsys.readouterr().out)
    by_id = {provider["provider_id"]: provider for provider in providers}

    assert "axdata.source.tdx" not in by_id
    assert by_id[TDX_PROVIDER_ID]["status"] == "enabled"
    assert by_id[TDX_PROVIDER_ID]["effective_trust_level"] == "official"
    assert by_id[TDX_PROVIDER_ID]["built_in"] is True
    assert by_id[TDX_PROVIDER_ID]["install_source"] == "preinstalled"
    assert by_id[TDX_PROVIDER_ID]["provider_kind"] == "source_plugin"
    assert by_id[TDX_PROVIDER_ID]["can_uninstall"] is True
    assert by_id[TDX_PROVIDER_ID]["uninstall_mode"] == "managed_disable"
    assert by_id[TDX_PROVIDER_ID]["uninstall_block_reason"] is None
    assert by_id[TDX_PROVIDER_ID]["downloader_count"] > 0
    assert by_id[TDX_PROVIDER_ID]["collector_count"] == 0
    assert by_id[TDX_PROVIDER_ID]["dependency_count"] == 0
    assert by_id[TDX_PROVIDER_ID]["status_message"]
    assert by_id[TDX_PROVIDER_ID]["next_action"] is None
    assert by_id[TDX_PROVIDER_ID]["action_command"] is None
    assert "stock_codes_tdx" in by_id[TDX_PROVIDER_ID]["interfaces"]
    assert by_id[TDX_PROVIDER_ID]["downloaders"]
    assert by_id[TDX_PROVIDER_ID]["collectors"] == []
    assert by_id[TDX_PROVIDER_ID]["dependencies"] == []
    assert by_id[TDX_PROVIDER_ID]["required_config"] == []
    assert by_id[TDX_PROVIDER_ID]["config_schema"] == {"required_config": []}
    assert by_id[TDX_EXT_PROVIDER_ID]["source_name_zh"] == "通达信扩展行情"
    assert by_id[TDX_EXT_PROVIDER_ID]["install_source"] == "preinstalled"
    assert by_id[TDX_EXT_PROVIDER_ID]["can_uninstall"] is True
    assert by_id["axdata.source.tencent"]["source_code"] == "tencent"
    assert by_id["axdata.source.tencent"]["install_source"] == "preinstalled"
    assert by_id["axdata.source.tencent"]["provider_kind"] == "source_plugin"
    assert by_id["axdata.source.tencent"]["can_uninstall"] is True
    assert by_id["axdata.source.tencent"]["uninstall_mode"] == "managed_disable"
    assert by_id["axdata.source.tencent"]["uninstall_block_reason"] is None


def test_plugin_list_omits_ignored_entry_point_candidates(capsys, monkeypatch, tmp_path) -> None:
    import axdata_core.provider_registry as provider_registry

    class FakeDistribution:
        metadata = {"Name": "broken-source"}
        files = []

        def locate_file(self, item):  # pragma: no cover
            raise AssertionError("no manifest files should be located")

    class FakeEntryPoint:
        name = "tdx_ext"
        dist = FakeDistribution()

    monkeypatch.setattr(provider_registry, "_provider_entry_points", lambda: (FakeEntryPoint(),))

    exit_code = main(["--data-root", str(tmp_path / "data"), "plugin", "list", "--json"])

    assert exit_code == 0
    providers = json.loads(capsys.readouterr().out)
    provider_ids = {provider["provider_id"] for provider in providers}
    assert "entry_point.tdx_ext" not in provider_ids
    assert "axdata.source.tdx_ext_external" in provider_ids


def test_doctor_reports_ignored_plugin_candidates(capsys, monkeypatch, tmp_path) -> None:
    import axdata_core.provider_registry as provider_registry

    class FakeDistribution:
        metadata = {"Name": "broken-source"}
        files = []

        def locate_file(self, item):  # pragma: no cover
            raise AssertionError("no manifest files should be located")

    class FakeEntryPoint:
        name = "tdx_ext"
        dist = FakeDistribution()

    monkeypatch.setattr(provider_registry, "_provider_entry_points", lambda: (FakeEntryPoint(),))

    exit_code = main(["--data-root", str(tmp_path / "data"), "doctor", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["registry"]["ignored_candidate_count"] == 1
    ignored = payload["plugins"]["ignored_candidates"]
    assert ignored == [
        {
            "candidate_id": "entry_point.tdx_ext",
            "status": "ignored",
            "reason": "missing_manifest",
            "message": ignored[0]["message"],
            "entry_point_name": "tdx_ext",
            "distribution": "broken-source",
            "provider_id": None,
            "covered_by_provider_id": None,
        }
    ]
    assert "axdata-provider.json" in ignored[0]["message"]
    assert "entry_point.tdx_ext" not in {provider["provider_id"] for provider in payload["plugins"]["providers"]}


def test_plugin_uninstall_preinstalled_provider_marks_uninstalled(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"

    exit_code = main(["--data-root", str(data_root), "plugin", "uninstall", "axdata.source.tencent", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["provider_id"] == "axdata.source.tencent"
    assert payload["uninstall_mode"] == "managed_disable"
    assert payload["removed_paths"] == []

    exit_code = main(["--data-root", str(data_root), "plugin", "list", "--json"])

    assert exit_code == 0
    providers = {provider["provider_id"]: provider for provider in json.loads(capsys.readouterr().out)}
    assert providers["axdata.source.tencent"]["status"] == "uninstalled"
    assert providers["axdata.source.tencent"]["enabled"] is False
    assert providers["axdata.source.tencent"]["can_enable"] is True


def test_plugin_list_shows_missing_tdx_providers_when_not_discovered(capsys, monkeypatch, tmp_path) -> None:
    from axdata_core.provider_catalog import build_builtin_provider_registry
    import axdata_core.provider_catalog as provider_catalog

    def build_registry_without_entry_points(**kwargs):
        kwargs["discover_entry_points"] = False
        return build_builtin_provider_registry(**kwargs)

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", build_registry_without_entry_points)

    exit_code = main(["--data-root", str(tmp_path / "data"), "plugin", "list", "--json"])

    assert exit_code == 0
    providers = {provider["provider_id"]: provider for provider in json.loads(capsys.readouterr().out)}
    quote = providers[TDX_PROVIDER_ID]
    assert quote["status"] == "missing"
    assert quote["source_name_zh"] == "通达信"
    assert quote["interface_count"] == 90
    assert quote["install_source"] == "missing"
    assert quote["can_enable"] is False
    assert quote["can_uninstall"] is False
    assert "普通 TDX 接口不会出现在运行目录" in quote["status_message"]
    ext = providers[TDX_EXT_PROVIDER_ID]
    assert ext["status"] == "missing"
    assert ext["source_name_zh"] == "通达信扩展行情"
    assert ext["interface_count"] == 31
    assert ext["install_source"] == "missing"
    assert ext["can_enable"] is False
    assert ext["can_uninstall"] is False
    assert "扩展行情接口不会出现在运行目录" in ext["status_message"]


def test_tdx_diagnostics_report_missing_only_status() -> None:
    from axdata_core.diagnostics import _tdx_report
    from axdata_core.plugin_status import expected_provider_statuses

    report = _tdx_report(expected_provider_statuses(()))

    assert report["status"] == "missing"
    assert report["installed"] is False
    assert report["enabled"] is False
    assert report["quote_enabled"] is False
    assert report["extended_enabled"] is False
    assert {provider["provider_id"] for provider in report["providers"]} == {
        TDX_PROVIDER_ID,
        TDX_EXT_PROVIDER_ID,
    }


def test_cli_request_calls_source_gateway_without_persisting(capsys, monkeypatch, tmp_path) -> None:
    from axdata_core import SourceRequestResult
    import axdata_core.source_request as source_request_module

    calls = []

    def fake_request_interface(interface, *, params=None, fields=None, persist=False, options=None, data_root=None):
        calls.append(
            {
                "interface": interface,
                "params": params,
                "fields": fields,
                "persist": persist,
                "options": options,
                "data_root": data_root,
            }
        )
        return SourceRequestResult(
            records=[{"instrument_id": "000001.SZ", "last_price": 10.14}],
            meta={"source": "tdx", "tdx_protocol": "0x054c"},
        )

    monkeypatch.setattr(source_request_module, "request_interface", fake_request_interface)

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "request",
            "stock_realtime_snapshot_tdx",
            "--param",
            "code=000001.SZ",
            "--fields",
            "instrument_id,last_price",
            "--option",
            "source_server_count=2",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is True
    assert payload["data"] == [{"instrument_id": "000001.SZ", "last_price": 10.14}]
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False
    assert calls == [
        {
            "interface": "stock_realtime_snapshot_tdx",
            "params": {"code": "000001.SZ"},
            "fields": ["instrument_id", "last_price"],
            "persist": False,
            "options": {"source_server_count": 2},
            "data_root": str(tmp_path / "data"),
        }
    ]


def test_cli_request_second_batch_source_only_sample_uses_json_params(capsys, monkeypatch, tmp_path) -> None:
    from axdata_core import SourceRequestResult
    import axdata_core.source_request as source_request_module

    calls = []

    def fake_request_interface(interface, *, params=None, fields=None, persist=False, options=None, data_root=None):
        calls.append(
            {
                "interface": interface,
                "params": params,
                "fields": fields,
                "persist": persist,
                "options": options,
                "data_root": data_root,
            }
        )
        return SourceRequestResult(
            records=[{"instrument_id": "000001.SZ", "trade_time": "20260511 09:30:00", "price": 10.14}],
            meta={"source": "tdx", "tdx_protocol": "0x0fc6"},
        )

    monkeypatch.setattr(source_request_module, "request_interface", fake_request_interface)

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "request",
            "stock_trades_history_tdx",
            "--params",
            '{"code":"000001.SZ","trade_date":"20260511"}',
            "--fields",
            "instrument_id,trade_time,price",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is True
    assert payload["meta"]["interface_name"] == "stock_trades_history_tdx"
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False
    assert calls == [
        {
            "interface": "stock_trades_history_tdx",
            "params": {"code": "000001.SZ", "trade_date": "20260511"},
            "fields": ["instrument_id", "trade_time", "price"],
            "persist": False,
            "options": None,
            "data_root": str(tmp_path / "data"),
        }
    ]


def test_cli_request_third_batch_source_only_sample_uses_json_params(capsys, monkeypatch, tmp_path) -> None:
    from axdata_core import SourceRequestResult
    import axdata_core.source_request as source_request_module

    calls = []

    def fake_request_interface(interface, *, params=None, fields=None, persist=False, options=None, data_root=None):
        calls.append(
            {
                "interface": interface,
                "params": params,
                "fields": fields,
                "persist": persist,
                "options": options,
                "data_root": data_root,
            }
        )
        return SourceRequestResult(
            records=[{"instrument_id": "000001.SH", "trade_time": "20260617 09:31:00", "price": 4079.36}],
            meta={"source": "tdx", "tdx_protocol": "0x0fb4"},
        )

    monkeypatch.setattr(source_request_module, "request_interface", fake_request_interface)

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "request",
            "index_intraday_history_tdx",
            "--params",
            '{"code":"000001.SH","trade_date":"20260617"}',
            "--fields",
            "instrument_id,trade_time,price",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is True
    assert payload["meta"]["interface_name"] == "index_intraday_history_tdx"
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False
    assert calls == [
        {
            "interface": "index_intraday_history_tdx",
            "params": {"code": "000001.SH", "trade_date": "20260617"},
            "fields": ["instrument_id", "trade_time", "price"],
            "persist": False,
            "options": None,
            "data_root": str(tmp_path / "data"),
        }
    ]


def test_cli_request_json_params_single_quote_example_is_powershell_copyable(tmp_path) -> None:
    if os.name != "nt":
        pytest.skip("Windows PowerShell copyability test.")
    if not (REPO_ROOT / ".venv" / "Scripts" / "python.exe").exists():
        pytest.skip("Project .venv is required for the Windows copyable command example.")
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available in this environment.")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(REPO_ROOT / "libs" / "axdata_core"),
            env.get("PYTHONPATH", ""),
        ]
    )
    command = (
        ".\\.venv\\Scripts\\python -m axdata_core.cli "
        f"--data-root '{tmp_path / 'data'}' "
        "request stock_order_book_tdx "
        "--params '{\\\"trade_date\\\":\\\"20260511\\\"}' "
        "--json\n"
        "exit $LASTEXITCODE\n"
    )
    script_path = tmp_path / "request_params_copyable.ps1"
    script_path.write_text(command, encoding="utf-8")

    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2, result.stderr.decode("utf-8", errors="replace")
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["error"]["code"] == "SOURCE_REQUEST_VALIDATION_ERROR"
    assert payload["meta"]["params"] == {"trade_date": "20260511"}
    assert payload["meta"]["request_mode"] == "source_request"


def test_cli_request_validation_error_is_json_guidance(capsys, monkeypatch, tmp_path) -> None:
    from axdata_core.source_errors import SourceRequestValidationError
    import axdata_core.source_request as source_request_module

    def fake_request_interface(*_args, **_kwargs):
        raise SourceRequestValidationError("Missing required param(s) for stock_order_book_tdx: code.")

    monkeypatch.setattr(source_request_module, "request_interface", fake_request_interface)

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "request",
            "stock_order_book_tdx",
            "--json",
        ]
    )

    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is False
    assert payload["error"]["code"] == "SOURCE_REQUEST_VALIDATION_ERROR"
    assert "code" in payload["error"]["message"]
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False
    assert payload["meta"]["next_action"]


def test_init_config_and_doctor_cli_report_local_environment(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"

    assert main(["--data-root", str(data_root), "init", "--json"]) == 0
    init_payload = json.loads(capsys.readouterr().out)

    assert init_payload["data_root"] == str(data_root.resolve())
    assert Path(init_payload["plugin_config_path"]).exists()
    for layer in ("raw", "staging", "core", "factor"):
        assert (data_root / layer).is_dir()

    assert main(["--data-root", str(data_root), "init", "--json"]) == 0
    second_init_payload = json.loads(capsys.readouterr().out)
    assert second_init_payload["config_created"] is False

    assert main(["--data-root", str(data_root), "config", "show", "--json"]) == 0
    config_payload = json.loads(capsys.readouterr().out)
    assert config_payload["data_root"] == str(data_root.resolve())
    assert config_payload["api_port"] == 8666
    assert config_payload["web_port"] == 8667
    assert config_payload["plugin_config_path"] == init_payload["plugin_config_path"]

    assert main(["--data-root", str(data_root), "doctor", "--json"]) == 0
    doctor_payload = json.loads(capsys.readouterr().out)
    assert doctor_payload["config"]["data_root"] == str(data_root.resolve())
    assert doctor_payload["registry"]["loaded"] is True
    assert doctor_payload["plugins"]["providers"]
    assert doctor_payload["collector"]["store_path"].endswith("collector_scheduler.json")
    assert doctor_payload["real_source_smoke"]["requires_explicit_run"] is True
    assert {check["category"] for check in doctor_payload["checks"]} >= {
        "paths",
        "dependencies",
        "registry",
        "ports",
        "collector",
        "smoke",
    }

    assert main(["--data-root", str(data_root), "status", "--json"]) == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["config"]["data_root"] == str(data_root.resolve())


def test_plugin_info_outputs_manifest(capsys, tmp_path) -> None:
    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "plugin",
            "info",
            "axdata.source.tencent",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["provider_id"] == "axdata.source.tencent"
    assert payload["status_message"]
    assert payload["next_action"] is None
    assert payload["downloader_count"] == 0
    assert payload["collector_count"] == 0
    assert payload["dependency_count"] == 0
    assert payload["interfaces"] == TENCENT_BUILTIN_INTERFACE_NAMES
    assert payload["downloaders"] == []
    assert payload["collectors"] == []
    assert payload["dependencies"] == []
    assert payload["overridden_interfaces"] == []
    assert payload["conflicting_interfaces"] == []
    assert payload["manifest"]["provider"]["source_code"] == "tencent"
    assert [interface["name"] for interface in payload["manifest"]["interfaces"]] == TENCENT_BUILTIN_INTERFACE_NAMES


def test_plugin_info_outputs_provider_overrides(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"
    set_provider_override(
        "tencent_realtime_snapshot",
        "axdata.source.tencent",
        data_root=data_root,
    )

    exit_code = main(
        [
            "--data-root",
            str(data_root),
            "plugin",
            "info",
            "axdata.source.tencent",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["overridden_interfaces"] == ["tencent_realtime_snapshot"]


def test_plugin_collectors_outputs_enabled_collectors_json(capsys, monkeypatch, tmp_path) -> None:
    registry = _collector_registry()

    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "plugin",
            "collectors",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)

    assert len(payload) == 1
    assert payload[0]["name"] == "close.refresh.daily"
    assert payload[0]["provider_id"] == "axdata.plugin.close_refresh"
    assert payload[0]["plugin_status"] == "enabled"
    assert payload[0]["resource_group"] == "tdx.quote"
    assert payload[0]["interfaces"] == ["stock_codes_tdx"]


def test_plugin_collector_info_outputs_one_collector(capsys, monkeypatch, tmp_path) -> None:
    registry = _collector_registry()

    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "plugin",
            "collector-info",
            "close.refresh.daily",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["name"] == "close.refresh.daily"
    assert payload["display_name_zh"] == "收盘刷新"
    assert payload["default_params"] == {"scope": "all"}
    assert payload["default_schedule"] == {"frequency": "daily", "time": "18:05"}


def test_plugin_collector_run_outputs_result_json(capsys, monkeypatch, tmp_path) -> None:
    calls = []

    import axdata_core.collector_runner as collector_runner

    def fake_run_collector(collector_name, **kwargs):
        calls.append({"collector_name": collector_name, **kwargs})
        return {
            "collector_name": collector_name,
            "target_interface": "stock_codes_tdx",
            "status": "success",
            "download_result": {
                "job_id": "run_cli_collector",
                "row_count": 1,
                "output_path": str(tmp_path / "export" / "stock_codes.csv"),
            },
        }

    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)

    exit_code = main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "plugin",
            "collector-run",
            "close_refresh_daily",
            "--params",
            '{"scope":"stock"}',
            "--fields",
            "instrument_id,name",
            "--output-root",
            str(tmp_path / "export"),
            "--formats",
            "jsonl,csv",
            "--concurrency-mode",
            "low",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["collector_name"] == "close_refresh_daily"
    assert payload["download_result"]["row_count"] == 1
    assert calls == [
        {
            "collector_name": "close_refresh_daily",
            "params": {"scope": "stock"},
            "fields": ["instrument_id", "name"],
            "data_root": str(tmp_path / "data"),
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["jsonl", "csv"],
            "collect_mode": None,
            "connection_mode": None,
            "concurrency_mode": "low",
            "connection_count": None,
            "source_server_count": None,
            "connections_per_server": None,
            "max_concurrent_tasks": None,
            "batch_size": None,
            "request_interval_ms": None,
            "retry_count": None,
            "timeout_ms": None,
        }
    ]


def test_collector_task_cli_add_run_and_list_json(capsys, monkeypatch, tmp_path) -> None:
    import axdata_core.collector_runner as collector_runner

    class Plan:
        collector_name = "close_refresh_daily"
        display_name_zh = "收盘刷新"
        provider_id = "axdata.plugin.close_refresh"
        downloader_profile = "demo.stock_codes.snapshot"
        params = {"scope": "stock"}
        fields = ["instrument_id"]
        formats = ["jsonl"]
        resource_group = "demo.quote"

    monkeypatch.setattr(
        collector_runner,
        "build_collector_run_plan",
        lambda collector_name, **_kwargs: Plan(),
    )
    monkeypatch.setattr(
        collector_runner,
        "run_collector",
        lambda collector_name, **_kwargs: {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {
                "row_count": 1,
                "output_paths": {"jsonl": str(tmp_path / "out.jsonl")},
                "quality": {
                    "quality_status": "ok",
                    "row_count_value": 1,
                    "write_mode": "upsert_by_key",
                    "write_primary_key": ["instrument_id"],
                    "rows_written": 1,
                    "rows_after": 1,
                },
            },
        },
    )

    data_root = tmp_path / "data"
    assert main(
        [
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "add",
            "close_refresh_daily",
            "--task-id",
            "task_close",
            "--trigger-type",
            "interval",
            "--interval-seconds",
            "60",
            "--params",
            '{"scope":"stock"}',
            "--fields",
            "instrument_id",
            "--formats",
            "jsonl",
            "--max-retries",
            "2",
            "--backoff-seconds",
            "3",
            "--json",
        ]
    ) == 0
    task_payload = json.loads(capsys.readouterr().out)
    assert task_payload["task_id"] == "task_close"
    assert task_payload["provider_id"] == "axdata.plugin.close_refresh"
    assert task_payload["max_retries"] == 2
    assert task_payload["backoff_seconds"] == 3
    assert task_payload["status_message"]
    assert task_payload["action_command"] is None

    assert main(["--data-root", str(data_root), "collector", "task", "list", "--json"]) == 0
    tasks = json.loads(capsys.readouterr().out)
    assert "task_close" in {task["task_id"] for task in tasks}
    assert tasks[0]["status_message"]

    assert main(
        [
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "run",
            "task_close",
            "--wait",
            "--json",
        ]
    ) == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["status"] == "success"
    assert run_payload["output_paths"] == {"jsonl": str(tmp_path / "out.jsonl")}
    assert run_payload["records_read"] == 1
    assert run_payload["rows_written"] == 1
    assert run_payload["write_mode"] == "upsert_by_key"
    assert run_payload["events"][0]["stage"] == "queued"
    assert run_payload["stage_timings"]["total_ms"] is not None
    assert "成功" in run_payload["status_message"]
    assert run_payload["next_action"] is None

    assert main(["--data-root", str(data_root), "collector", "run", "list", "--json"]) == 0
    runs = json.loads(capsys.readouterr().out)
    assert [run["run_id"] for run in runs] == [run_payload["run_id"]]
    assert runs[0]["status_message"] == run_payload["status_message"]

    assert main(["--data-root", str(data_root), "collector", "run", "info", run_payload["run_id"]]) == 0
    info_text = capsys.readouterr().out
    assert "stage_timings" in info_text
    assert "events" in info_text
    assert "finished" in info_text
    assert "write_mode\tupsert_by_key" in info_text
    assert "rows_written\t1" in info_text

    assert main(["--data-root", str(data_root), "collector", "status", "--json"]) == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["task_count"] == 2
    assert status_payload["enabled_task_count"] == 1
    assert status_payload["run_count"] == 1
    assert status_payload["total_run_count"] == 1
    assert status_payload["recent_run_limit"] == 100
    assert status_payload["status_counts"] == {"success": 1}
    assert status_payload["latest_runs"]["task_close"]["run_id"] == run_payload["run_id"]
    assert "成功" in status_payload["latest_runs"]["task_close"]["status_message"]


def test_collector_task_cli_templates_run_overrides_and_backfill(capsys, monkeypatch, tmp_path) -> None:
    import axdata_core.collector_runner as collector_runner

    class Plan:
        collector_name = "tdx.stock_kline_daily_tdx.snapshot"
        display_name_zh = "TDX 日 K 线"
        provider_id = TDX_COLLECTOR_PLUGIN_ID
        downloader_profile = None
        params = {"code": "000001.SZ", "count": 800, "adjust": "none"}
        fields = None
        formats = ["parquet"]
        resource_group = "tdx.quote"

    calls = []

    monkeypatch.setattr(
        collector_runner,
        "build_collector_run_plan",
        lambda collector_name, **_kwargs: Plan(),
    )

    def fake_run_collector(collector_name, **kwargs):
        calls.append(dict(kwargs["params"]))
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {"row_count": 1},
        }

    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)

    data_root = tmp_path / "data"
    trade_calendar_path = data_root / "cache" / "exchange" / "trade_calendar" / "trade_calendar.parquet"
    trade_calendar_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "exchange": ["SZSE", "SZSE"],
            "cal_date": ["20240102", "20240103"],
            "is_open": [True, True],
            "pretrade_date": [None, "20240102"],
            "next_trade_date": ["20240103", None],
        }
    ).to_parquet(trade_calendar_path, engine="pyarrow", index=False)
    assert main(["--data-root", str(data_root), "collector", "task", "templates", "--json"]) == 0
    templates = {template["template_id"]: template for template in json.loads(capsys.readouterr().out)}
    assert "trade_cal" not in templates
    assert "stock_basic_exchange" not in templates
    assert templates["stock_kline_daily_tdx"]["default_params"] == {"code": "000001.SZ", "count": 800, "adjust": "none"}
    assert templates["daily"]["safety_limits"]["full_market_by_default"] is False

    assert main(
        [
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "create-from-template",
            "stock_kline_daily_tdx",
            "--task-id",
            "kline_template_test",
            "--json",
        ]
    ) == 0
    task = json.loads(capsys.readouterr().out)
    assert task["task_id"] == "kline_template_test"
    assert task["queue_status"] == "ready"

    assert main(
        [
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "run",
            "kline_template_test",
            "--params",
            '{"adjust":"qfq"}',
            "--symbol",
            "000002.SZ",
            "--limit",
            "2",
            "--wait",
            "--json",
        ]
    ) == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["params_override"] == {"adjust": "qfq", "code": "000002.SZ", "limit": 2, "count": 2}

    assert main(
        [
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "backfill",
            "kline_template_test",
            "--start",
            "2024-01-02",
            "--end",
            "20240103",
            "--params",
            '{"adjust":"none"}',
            "--wait",
            "--json",
        ]
    ) == 0
    backfill_payload = json.loads(capsys.readouterr().out)
    assert backfill_payload["metadata"]["run_mode"] == "backfill"
    assert backfill_payload["params_override"] == {
        "start_date": "20240102",
        "end_date": "20240103",
        "adjust": "none",
    }
    assert calls[-1] == {
        "code": "000001.SZ",
        "count": 800,
        "adjust": "none",
        "start_date": "20240102",
        "end_date": "20240103",
    }


def test_collector_task_cli_lists_seeded_default_tasks_and_dependency(capsys, monkeypatch, tmp_path) -> None:
    from axdata_core.plugin_config import disable_provider

    _patch_local_tdx_plugin_registry(monkeypatch)
    data_root = tmp_path / "data"
    disable_provider(TDX_COLLECTOR_PLUGIN_ID, data_root=data_root)

    assert main(["--data-root", str(data_root), "collector", "task", "list", "--json"]) == 0
    tasks = {task["task_id"]: task for task in json.loads(capsys.readouterr().out)}

    assert {
        "stock_kline_daily_tdx_sample",
    } <= set(tasks)
    assert "stock_basic_exchange_refresh" not in tasks
    assert "trade_cal_refresh" not in tasks
    assert tasks["stock_kline_daily_tdx_sample"]["dependency_status"] == "disabled"
    assert "请安装/启用 TDX 采集器插件" in tasks["stock_kline_daily_tdx_sample"]["dependency_message"]

    assert main(
        [
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "run",
            "stock_kline_daily_tdx_sample",
            "--wait",
            "--json",
        ]
    ) == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["status"] == "failed"
    assert run_payload["error_category"] == "plugin_disabled"
    assert "请安装/启用 TDX 采集器插件" in run_payload["error_summary"]


def test_collector_task_run_json_subprocess_outputs_ascii_safe_guidance(tmp_path) -> None:
    data_root = tmp_path / "data"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(REPO_ROOT / "libs" / "axdata_core"),
            env.get("PYTHONPATH", ""),
        ]
    )

    create = subprocess.run(
        [
            sys.executable,
            "-m",
            "axdata_core.cli",
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "create-from-template",
            "stock_kline_daily_tdx",
            "--task-id",
            "kline_disabled_ascii_safe",
            "--disabled",
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert create.returncode == 0, create.stderr.decode("utf-8", errors="replace")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "axdata_core.cli",
            "--data-root",
            str(data_root),
            "collector",
            "task",
            "run",
            "kline_disabled_ascii_safe",
            "--wait",
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stdout.isascii()
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["status"] == "failed"
    assert payload["error_category"] == "dependency_missing"
    assert payload["metadata"]["dependency_errors"][0]["dataset"] == "trade_cal"
    assert payload["action_command"] == "axdata collector task run trade_cal_refresh --wait --json"


def test_data_cli_lists_inspects_and_previews_local_dataset(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"
    parquet_path = tmp_path / "export" / "daily" / "parquet" / "daily.parquet"
    parquet_path.parent.mkdir(parents=True)
    import pandas as pd

    pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2},
            {"ts_code": "600000.SH", "trade_date": "20240102", "close": 8.1},
        ]
    ).to_parquet(parquet_path, engine="pyarrow", index=False)

    store = CollectorSchedulerStore(data_root=data_root)
    store.create_run(
        CollectorRun(
            run_id="run_cli_data",
            task_id="daily_task",
            collector_name="daily.collector",
            trigger_type="manual",
            status="success",
            provider_id="axdata.source.demo",
            output_paths={"parquet": str(parquet_path)},
            result={
                "target_interface": "daily",
                "download_result": {
                    "interface_name": "daily",
                    "row_count": 2,
                    "output_paths": {"parquet": str(parquet_path)},
                    "quality": {
                        "quality_status": "ok",
                        "date_field": "trade_date",
                        "write_mode": "upsert_by_key",
                        "partition_by": ["trade_date"],
                        "primary_key": "pass",
                        "write_primary_key": ["ts_code", "trade_date"],
                        "rows_before": 1,
                        "rows_written": 2,
                        "rows_after": 2,
                        "duplicate_rows_dropped": 0,
                    },
                },
            },
            quality={
                "quality_status": "ok",
                "date_field": "trade_date",
                "write_mode": "upsert_by_key",
                "partition_by": ["trade_date"],
                "primary_key": "pass",
                "write_primary_key": ["ts_code", "trade_date"],
                "rows_before": 1,
                "rows_written": 2,
                "rows_after": 2,
                "duplicate_rows_dropped": 0,
            },
            created_at="2026-06-29T00:00:00+00:00",
            updated_at="2026-06-29T00:01:00+00:00",
            finished_at="2026-06-29T00:01:00+00:00",
        )
    )

    assert main(["--data-root", str(data_root), "data", "list", "--json"]) == 0
    datasets = json.loads(capsys.readouterr().out)
    assert datasets[0]["dataset"] == "daily"
    assert datasets[0]["row_count"] == 2
    assert datasets[0]["write_mode"] == "upsert_by_key"

    assert main(["--data-root", str(data_root), "data", "inspect", "daily", "--json"]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["output_paths"]["parquet"] == str(parquet_path)
    assert inspected["columns"] == ["ts_code", "trade_date", "close"]
    assert inspected["primary_key"] == ["ts_code", "trade_date"]

    assert main(["--data-root", str(data_root), "data", "inspect", "daily"]) == 0
    text = capsys.readouterr().out
    assert "write_mode\tupsert_by_key" in text
    assert "rows_after\t2" in text

    assert main(
        [
            "--data-root",
            str(data_root),
            "query",
            "daily",
            "--symbol",
            "000001.SZ",
            "--fields",
            "ts_code,close",
            "--limit",
            "5",
            "--json",
        ]
    ) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["rows"] == [{"ts_code": "000001.SZ", "close": 10.2}]


def test_query_cli_uses_axdata_data_dir_for_core_tables(capsys, monkeypatch, tmp_path) -> None:
    import pandas as pd

    data_root = tmp_path / "data"
    partition = data_root / "core" / "table=adj_factor" / "parquet"
    partition.mkdir(parents=True)
    pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "20260618", "adj_factor": 101.25},
            {"ts_code": "000002.SZ", "trade_date": "20260618", "adj_factor": 88.5},
        ]
    ).to_parquet(partition / "20260618.parquet", engine="pyarrow", index=False)

    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    assert main(
        [
            "query",
            "adj_factor",
            "--symbol",
            "000001.SZ",
            "--start",
            "20260618",
            "--end",
            "20260618",
            "--fields",
            "ts_code,trade_date,adj_factor",
            "--json",
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["dataset"]["dataset"] == "adj_factor"
    assert payload["rows"] == [
        {"ts_code": "000001.SZ", "trade_date": "20260618", "adj_factor": 101.25}
    ]


def test_plugin_enable_and_disable_update_axdata_config(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"

    assert main(["--data-root", str(data_root), "plugin", "enable", "axdata.source.demo"]) == 0
    assert main(["--data-root", str(data_root), "plugin", "disable", TDX_PROVIDER_ID]) == 0

    config = load_plugin_config(data_root=data_root)

    assert config.enabled_provider_ids == ("axdata.source.demo",)
    assert config.disabled_provider_ids == (TDX_PROVIDER_ID,)
    assert "config" in capsys.readouterr().out


def test_plugin_installed_outputs_axdata_managed_plugins_json(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"
    axp_path = _build_tencent_axp(tmp_path)

    assert main(["--data-root", str(data_root), "plugin", "axp-install", str(axp_path), "--no-pth"]) == 0
    capsys.readouterr()

    exit_code = main(["--data-root", str(data_root), "plugin", "installed", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["provider_id"] for item in payload] == [TENCENT_PROVIDER_ID]
    assert payload[0]["enabled"] is False
    assert payload[0]["status"] == "disabled"
    assert payload[0]["effective_trust_level"] == "community"
    assert payload[0]["next_action"]
    assert payload[0]["action_command"] == f"axdata plugin enable {TENCENT_PROVIDER_ID}"
    assert payload[0]["interfaces"] == ["tencent_realtime_snapshot"]
    assert payload[0]["installed_path"]


def test_plugin_installed_discovers_axp_install_in_later_cli_process(tmp_path) -> None:
    data_root = tmp_path / "data"
    axp_path = _build_tencent_axp(tmp_path)
    env = {
        **os.environ,
        "PYTHONPATH": f"{REPO_ROOT};{REPO_ROOT / 'libs' / 'axdata_core'};{REPO_ROOT / 'packages' / 'axdata-sdk'}",
    }

    subprocess.run(
        [
            sys.executable,
            "-m",
            "axdata_core.cli",
            "--data-root",
            str(data_root),
            "plugin",
            "axp-install",
            str(axp_path),
            "--no-pth",
            "--json",
        ],
        check=True,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "axdata_core.cli",
            "--data-root",
            str(data_root),
            "plugin",
            "installed",
            "--json",
        ],
        check=True,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert [item["provider_id"] for item in payload] == [TENCENT_PROVIDER_ID]
    assert payload[0]["enabled"] is False
    assert payload[0]["status"] == "disabled"
    assert payload[0]["install_source"] == "axp_managed"
    assert payload[0]["can_uninstall"] is True
    assert payload[0]["uninstall_block_reason"] is None
    assert payload[0]["interfaces"] == ["tencent_realtime_snapshot"]


def test_plugin_uninstall_removes_axdata_managed_plugin(capsys, tmp_path, monkeypatch) -> None:
    data_root = tmp_path / "data"
    axp_path = _build_tencent_axp(tmp_path)
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    assert main(["--data-root", str(data_root), "plugin", "axp-install", str(axp_path), "--no-pth"]) == 0
    capsys.readouterr()

    exit_code = main(["--data-root", str(data_root), "plugin", "uninstall", TENCENT_PROVIDER_ID, "--json"])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["provider_id"] == TENCENT_PROVIDER_ID
    assert result["removed_paths"]

    assert main(["--data-root", str(data_root), "plugin", "installed", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_plugin_uninstall_rejects_environment_plugin(capsys, tmp_path, monkeypatch) -> None:
    data_root = tmp_path / "data"
    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: _environment_plugin_registry(),
    )

    with pytest.raises(SystemExit) as exc:
        main(["--data-root", str(data_root), "plugin", "uninstall", "axdata.source.env_demo", "--json"])

    assert exc.value.code == 2
    assert "pip uninstall" in capsys.readouterr().err


def test_plugin_axp_install_requires_replace_for_existing_provider(capsys, tmp_path) -> None:
    data_root = tmp_path / "data"
    axp_path = _build_tencent_axp(tmp_path)

    assert main(["--data-root", str(data_root), "plugin", "axp-install", str(axp_path), "--no-pth"]) == 0
    capsys.readouterr()

    try:
        main(["--data-root", str(data_root), "plugin", "axp-install", str(axp_path), "--no-pth"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("duplicate install should require --replace")
    assert "already installed" in capsys.readouterr().err

    assert main(
        [
            "--data-root",
            str(data_root),
            "plugin",
            "axp-install",
            str(axp_path),
            "--replace",
            "--no-pth",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["provider_id"] == TENCENT_PROVIDER_ID
    assert payload["replaced"] is True


def test_plugin_axp_install_allows_online_dependencies_when_explicit(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    data_root = tmp_path / "data"
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata_cli_online_dependency",
                "version_spec": ">=1.0",
                "optional": False,
                "description": "CLI online dependency fixture.",
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

    try:
        main(["--data-root", str(data_root), "plugin", "axp-install", str(axp_path), "--no-pth"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("missing dependency should fail without --allow-online-deps")
    assert "cannot continue offline" in capsys.readouterr().err

    assert main(
        [
            "--data-root",
            str(data_root),
            "plugin",
            "axp-install",
            str(axp_path),
            "--allow-online-deps",
            "--no-pth",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert calls[0][0] == ("axdata_cli_online_dependency>=1.0",)
    assert payload["installed_dependency_requirements"] == ["axdata_cli_online_dependency>=1.0"]


def test_plugin_check_builtin_provider(capsys) -> None:
    exit_code = main(["plugin", "check", "--builtin", "tencent"])

    assert exit_code == 0
    assert "OK axdata.source.tencent interfaces=6 downloaders=0 collectors=0" in capsys.readouterr().out


def test_plugin_build_builtin_provider_manifest(capsys, tmp_path) -> None:
    output = tmp_path / MANIFEST_FILE_NAME

    exit_code = main(["plugin", "build", "--builtin", "tencent", "--output", str(output)])

    assert exit_code == 0
    assert str(output.resolve()) in capsys.readouterr().out
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["provider"]["provider_id"] == "axdata.source.tencent"
    assert [interface["name"] for interface in payload["interfaces"]] == TENCENT_BUILTIN_INTERFACE_NAMES


def test_plugin_check_manifest_ignores_build_metadata(capsys, tmp_path) -> None:
    output = tmp_path / MANIFEST_FILE_NAME
    assert main(["plugin", "build", "--builtin", "tencent", "--output", str(output)]) == 0
    capsys.readouterr()

    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["build"] = {
        "generated_at": "2026-06-22T12:00:00Z",
        "axdata_plugin_api_version": "1.0",
        "manifest_hash": "sha256:test",
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    exit_code = main(["plugin", "check", "--builtin", "tencent", "--manifest", str(output)])

    assert exit_code == 0
    assert "OK axdata.source.tencent interfaces=6 downloaders=0 collectors=0" in capsys.readouterr().out


def test_plugin_check_accepts_manifest_only_collector_plugin(capsys, tmp_path) -> None:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.collector.demo",
            name_zh="示例采集器",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(
            CollectorSpec(
                name="demo.stock_snapshot.snapshot",
                display_name_zh="示例股票快照采集",
                collector_plugin_id="axdata.collector.demo",
                dataset_id="demo.stock_snapshot",
                asset_class="stock",
                category="snapshot",
                resource_group="demo.http",
                runner_entry="axdata_collector_demo.runner:run",
                default_params={"code": "000001.SZ"},
                output={"layer": "snapshot", "formats": ["parquet"]},
                quality={"required_columns": ["instrument_id"]},
                lifecycle_status="experimental",
            ),
        ),
    )
    output = tmp_path / PLUGIN_MANIFEST_FILE_NAME
    output.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    exit_code = main(["plugin", "check", "--manifest", str(output)])

    assert exit_code == 0
    assert "OK axdata.collector.demo interfaces=0 downloaders=0 collectors=1" in capsys.readouterr().out


def test_plugin_check_manifest_only_rejects_incomplete_collector(capsys, tmp_path) -> None:
    payload = {
        "manifest_version": "1.0",
        "plugin_api_version": "1.0",
        "plugin": {
            "plugin_id": "axdata.collector.demo",
            "name_zh": "示例采集器",
            "version": "0.1.0",
        },
        "provider": None,
        "interfaces": [],
        "downloaders": [],
        "collectors": [
            {
                "collector_id": "demo.stock_snapshot.snapshot",
                "display_name_zh": "示例股票快照采集",
                "collector_plugin_id": "axdata.collector.demo",
                "resource_group": "demo.http",
                "runner_entry": "axdata_collector_demo.runner:run",
                "output": {"layer": "snapshot", "formats": ["parquet"]},
                "quality": {"required_columns": ["instrument_id"]},
            }
        ],
        "dependencies": [],
        "config_schema": {"required_config": []},
        "required_config": [],
        "resources": {},
        "build": {},
    }
    output = tmp_path / PLUGIN_MANIFEST_FILE_NAME
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        main(["plugin", "check", "--manifest", str(output)])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("plugin check should fail when independent collector is incomplete")

    assert "dataset_id" in capsys.readouterr().err


def test_plugin_check_manifest_still_rejects_contract_drift(capsys, tmp_path) -> None:
    output = tmp_path / MANIFEST_FILE_NAME
    assert main(["plugin", "build", "--builtin", "tencent", "--output", str(output)]) == 0
    capsys.readouterr()

    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["interfaces"][0]["display_name_zh"] = "漂移后的标题"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        main(["plugin", "check", "--builtin", "tencent", "--manifest", str(output)])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("plugin check should fail when interface metadata drifts")

    assert "does not match Provider" in capsys.readouterr().err


def test_plugin_check_and_build_reject_unsupported_plugin_api_version(
    capsys,
    tmp_path,
    monkeypatch,
) -> None:
    package_root = tmp_path / "plugin_src"
    package_dir = package_root / "future_provider"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(
        """
from axdata_core.plugins import InterfaceSpec


class FutureProvider:
    provider_id = "axdata.source.future_demo"
    source_code = "future_demo"
    source_name_zh = "未来协议示例"
    version = "0.1.0"
    plugin_api_version = "9.0"

    def interfaces(self):
        return (
            InterfaceSpec(
                name="future_demo_snapshot",
                display_name_zh="未来协议示例",
                source_code="future_demo",
                source_name_zh="未来协议示例",
                asset_class="stock",
            ),
        )

    def create_adapter(self, options=None):
        raise AssertionError("adapter should not be created while checking manifest")

    def downloader_profiles(self):
        return ()


provider = FutureProvider()
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(package_root))
    output = tmp_path / MANIFEST_FILE_NAME

    commands = [
        ["plugin", "check", "--provider", "future_provider:provider"],
        [
            "plugin",
            "build",
            "--provider",
            "future_provider:provider",
            "--output",
            str(output),
        ],
    ]
    for command in commands:
        try:
            main(command)
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("unsupported plugin_api_version should fail")
        assert "Unsupported plugin_api_version '9.0'" in capsys.readouterr().err

    assert not output.exists()


def test_plugin_build_provider_manifest_includes_required_config(capsys, tmp_path, monkeypatch) -> None:
    package_root = tmp_path / "plugin_src"
    package_dir = package_root / "token_demo_provider"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(
        """
from axdata_core.plugins import InterfaceSpec, RequiredConfig


class DemoProvider:
    provider_id = "axdata.source.token_demo"
    source_code = "token_demo"
    source_name_zh = "凭据示例"
    version = "0.1.0"
    plugin_api_version = "1.0"

    def interfaces(self):
        return (
            InterfaceSpec(
                name="token_demo_snapshot",
                display_name_zh="凭据示例快照",
                source_code="token_demo",
                source_name_zh="凭据示例",
                asset_class="stock",
            ),
        )

    def create_adapter(self, options=None):
        raise AssertionError("adapter should not be created while building manifest")

    def downloader_profiles(self):
        return ()

    def required_config(self):
        return (
            RequiredConfig(
                name="TOKEN_DEMO_KEY",
                kind="env",
                required=True,
                description="用户自己的示例源凭据。",
            ),
        )


provider = DemoProvider()
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(package_root))
    output = tmp_path / MANIFEST_FILE_NAME

    exit_code = main(
        [
            "plugin",
            "build",
            "--provider",
            "token_demo_provider:provider",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert str(output.resolve()) in capsys.readouterr().out
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["provider"]["provider_id"] == "axdata.source.token_demo"
    assert payload["required_config"] == [
        {
            "name": "TOKEN_DEMO_KEY",
            "kind": "env",
            "required": True,
            "description": "用户自己的示例源凭据。",
        }
    ]
    assert payload["config_schema"]["required_config"] == payload["required_config"]
