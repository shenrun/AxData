from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from axdata_core.builtin_providers import get_builtin_provider, list_builtin_providers
from axdata_core.plugins import (
    AssetClass,
    FieldSpec,
    InterfaceSpec,
    ParameterSpec,
    SourceResult,
    manifest_from_provider,
    validate_manifest,
)
from axdata_core.provider_registry import ProviderRegistry
from axdata_core.source_errors import SourceAdapterError, SourceAdapterNotFound, SourceUnavailableError
from axdata_core.source_execution_options import execution_options_for_source
from axdata_core.sources import list_request_interface_names, list_request_interfaces

from tests.test_external_sources import CninfoOpener, TencentOpener
from tests.tdx_plugin_helpers import (
    TDX_EXT_PROVIDER_ID,
    TDX_PACKAGE_ROOT,
    TDX_PROVIDER_ID,
    build_registry_with_local_tdx_plugins,
    ensure_local_tdx_plugin_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TDX_EXT_PACKAGE_ROOT = REPO_ROOT / "packages" / "axdata-source-tdx-ext"
TDX_PLUGIN_PYTHONPATH = os.pathsep.join(
    [
        str(TDX_PACKAGE_ROOT / "src"),
        str(TDX_EXT_PACKAGE_ROOT / "src"),
        str(REPO_ROOT / "libs" / "axdata_core"),
    ]
)
TDX_PLUGIN_REQUIRED_MESSAGE = "TDX 插件未安装或不可用，请安装并启用 TDX 插件。"
BUILTIN_GENERIC_INTERFACE_NAMES = set(list_request_interface_names())
BUILTIN_GENERIC_COLLECTABLE_INTERFACE_NAMES = {
    "stock_trade_calendar_exchange",
    "stock_historical_list_exchange",
    "stock_basic_info_exchange",
}
BUILTIN_GENERIC_PROVIDER_COUNTS = {
    "axdata.source.exchange": (3, 3, 0),
    "axdata.source.cninfo": (32, 0, 0),
    "axdata.source.tencent": (6, 0, 0),
    "axdata.source.eastmoney": (13, 0, 0),
    "axdata.source.cls": (12, 0, 0),
    "axdata.source.kph": (9, 0, 0),
    "axdata.source.sina": (60, 0, 0),
}


def _core_without_site_subprocess(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", "-c", code],
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


def test_source_request_gateway_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "import axdata_core.source_request\n"
        "tracked = [\n"
        "    'axdata_core.sources.catalog',\n"
        "    'axdata_core.plugins',\n"
        "    'axdata_core.sources.tdx.catalog',\n"
        "    'axdata_core.sources.tdx_ext.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.provider_catalog',\n"
        "    'axdata_core.provider_registry',\n"
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

    assert "loaded=\n" in result.stdout


def test_builtin_providers_cover_current_source_catalog() -> None:
    providers = list_builtin_providers()
    source_codes = {provider.source_code for provider in providers}
    interface_names = {
        interface.name
        for provider in providers
        for interface in provider.interfaces()
    }

    assert source_codes == {"exchange", "cninfo", "tencent", "eastmoney", "cls", "kph", "sina"}
    assert interface_names == set(list_request_interface_names())
    assert len(interface_names) == len(list_request_interfaces())


def test_tdx_ext_plugin_manifest_validates_and_preserves_key_interfaces() -> None:
    ensure_local_tdx_plugin_paths()
    from axdata_source_tdx_ext.provider import provider as ext_provider

    manifest = manifest_from_provider(ext_provider)
    manifest_dict = manifest.to_dict()
    interfaces = {interface["name"]: interface for interface in manifest_dict["interfaces"]}

    validate_manifest(manifest)

    assert manifest.provider.provider_id == TDX_EXT_PROVIDER_ID
    assert manifest.provider.source_name_zh == "通达信扩展行情"
    assert interfaces["futures_contracts_tdx"]["source_name_zh"] == "通达信扩展行情"
    assert interfaces["futures_contracts_tdx"]["menu_path"][0] == "通达信扩展行情"
    assert interfaces["fx_codes_tdx"]["source_name_zh"] == "通达信扩展行情"
    assert interfaces["fx_codes_tdx"]["asset_class"] == AssetClass.FX.value
    assert interfaces["futures_contracts_tdx"]["asset_class"] == AssetClass.FUTURE.value
    assert interfaces["option_chain_tdx"]["asset_class"] == AssetClass.OPTION.value
    assert interfaces["macro_indicator_snapshot_tdx"]["asset_class"] == AssetClass.MACRO.value


def test_tdx_plugin_provider_exposes_collection_profiles_in_manifest() -> None:
    ensure_local_tdx_plugin_paths()
    from axdata_source_tdx.provider import provider

    manifest = manifest_from_provider(provider)
    interfaces = {interface.name: interface for interface in manifest.interfaces}
    downloaders = {downloader.interface_name: downloader for downloader in manifest.downloaders}

    validate_manifest(manifest)

    assert set(downloaders) == {
        "stock_codes_tdx",
        "stock_suspensions_tdx",
        "stock_st_list_tdx",
        "stock_daily_share_tdx",
        "stock_daily_price_limit_tdx",
        "stock_capital_changes_tdx",
        "stock_kline_daily_tdx",
        "stock_adj_factor_tdx",
        "stock_limit_ladder_tdx",
        "stock_theme_strength_rank_tdx",
    }
    assert interfaces["stock_codes_tdx"].collection.supported is True
    assert interfaces["stock_codes_tdx"].collection.default_profile == "stock_codes_tdx.snapshot"
    assert interfaces["stock_codes_tdx"].menu_path == ("通达信", "股票数据", "基础数据")
    assert interfaces["stock_kline_daily_tdx"].collection.supported is True
    assert interfaces["stock_kline_daily_tdx"].collection.default_profile == "stock_kline_daily_tdx.snapshot"
    assert interfaces["stock_kline_daily_tdx"].menu_path == ("通达信", "股票数据", "行情数据")
    assert interfaces["stock_adj_factor_tdx"].collection.supported is True
    assert interfaces["stock_adj_factor_tdx"].collection.default_profile == "stock_adj_factor_tdx.snapshot"
    assert interfaces["stock_capital_changes_tdx"].menu_path == ("通达信", "股票数据", "基础数据")
    assert interfaces["index_kline_tdx"].menu_path == ("通达信", "指数数据", "行情数据")
    assert interfaces["etf_auction_process_tdx"].menu_path == ("通达信", "ETF数据", "竞价数据")
    assert downloaders["stock_codes_tdx"].resource_group == "tdx.quote"
    assert downloaders["stock_limit_ladder_tdx"].resource_group == "tdx.f10"
    assert downloaders["stock_daily_share_tdx"].default_options["source_server_count"] == 4
    assert downloaders["stock_daily_share_tdx"].default_limits["max_connections_total"] == 8
    assert downloaders["stock_kline_daily_tdx"].default_options["params"]["code"] == "000001.SZ"
    assert downloaders["stock_adj_factor_tdx"].output["output_layer"] == "core"


def test_builtin_generic_providers_expose_downloader_and_collector_specs() -> None:
    providers = list_builtin_providers()

    for provider in providers:
        manifest = manifest_from_provider(provider)
        validate_manifest(manifest)

        expected_interfaces, expected_downloaders, expected_collectors = BUILTIN_GENERIC_PROVIDER_COUNTS[
            provider.provider_id
        ]
        assert len(manifest.interfaces) == expected_interfaces
        assert len(manifest.downloaders) == expected_downloaders
        assert len(manifest.collectors) == expected_collectors

    manifest_by_interface = {
        interface.name: (manifest, interface)
        for provider in providers
        for manifest in (manifest_from_provider(provider),)
        for interface in manifest.interfaces
    }
    assert set(manifest_by_interface) == BUILTIN_GENERIC_INTERFACE_NAMES
    _, trade_calendar = manifest_by_interface["stock_trade_calendar_exchange"]
    assert trade_calendar.summary_zh == "从深交所官方交易日历返回指定日期范围内的开闭市信息。"
    assert trade_calendar.description_zh == "不传日期时默认返回当前自然年；传 year 返回全年；传 start_date/end_date 返回指定范围。"
    assert trade_calendar.params_note_zh == "日期优先级：start_date/end_date > year > 当前自然年。"
    assert 'client.call("stock_trade_calendar_exchange", year=2026)' in trade_calendar.params_example_zh

    _, cninfo_announcements = manifest_by_interface["cninfo_announcements"]
    assert cninfo_announcements.summary_zh == "按股票和日期范围临时获取巨潮公告元信息。"
    assert cninfo_announcements.description_zh == "这个接口返回公告元信息和 PDF 下载地址。"
    assert cninfo_announcements.params_note_zh == "不传 fields 时返回上方全部字段；临时调用只查一次。"
    assert 'client.call("cninfo_announcements"' in cninfo_announcements.params_example_zh

    assert "sina_financial_statement" not in manifest_by_interface
    _, sina_statement = manifest_by_interface["stock_financial_report_sina"]
    assert sina_statement.source_name_zh == "新浪财经"

    for interface_name in BUILTIN_GENERIC_INTERFACE_NAMES:
        manifest, interface = manifest_by_interface[interface_name]
        downloaders = {downloader.name: downloader for downloader in manifest.downloaders}
        collectors = {collector.name: collector for collector in manifest.collectors}
        downloader_name = f"{interface_name}.snapshot"
        collector_name = f"{interface.source_code}.{interface_name}.snapshot"

        if interface_name in BUILTIN_GENERIC_COLLECTABLE_INTERFACE_NAMES:
            assert interface.collection.supported is True
            assert interface.collection.default_profile == downloader_name
            assert downloader_name in downloaders
            assert downloaders[downloader_name].interface_name == interface_name
            assert downloaders[downloader_name].resource_group == f"{interface.source_code}.http"
            assert downloaders[downloader_name].output["supported_formats"] == ["parquet", "csv", "jsonl"]
            assert collector_name not in collectors
        else:
            assert interface.collection.supported is False
            assert interface.collection.default_profile is None
            assert downloader_name not in downloaders
            assert collector_name not in collectors


def test_tdx_ext_plugin_provider_is_single_source_lightweight() -> None:
    code = (
        "import sys\n"
        "from axdata_source_tdx_ext.provider import provider\n"
        "interfaces = provider.interfaces()\n"
        "downloaders = provider.downloader_profiles()\n"
        "print('provider_id=' + provider.provider_id)\n"
        "print('interfaces=' + str(len(interfaces)))\n"
        "print('downloaders=' + str(len(downloaders)))\n"
        "tracked = [\n"
        "    'axdata_core.sources.tdx.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
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
            "PYTHONPATH": TDX_PLUGIN_PYTHONPATH,
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert f"provider_id={TDX_EXT_PROVIDER_ID}" in result.stdout
    assert "interfaces=31" in result.stdout
    assert "downloaders=0" in result.stdout
    assert "loaded=\n" in result.stdout


def test_tdx_plugin_provider_projection_does_not_load_downloader_runtime() -> None:
    code = (
        "import sys\n"
        "from axdata_source_tdx.provider import provider\n"
        "interfaces = provider.interfaces()\n"
        "downloaders = provider.downloader_profiles()\n"
        "collectors = provider.collectors()\n"
        "print('provider_id=' + provider.provider_id)\n"
        "print('interfaces=' + str(len(interfaces)))\n"
        "print('downloaders=' + str(len(downloaders)))\n"
        "print('collectors=' + str(len(collectors)))\n"
        "tracked = [\n"
        "    'axdata_core.sources.tdx.catalog',\n"
        "    'axdata_core.tdx_f10_catalog',\n"
        "    'axdata_core.tdx_f10_specs',\n"
        "    'axdata_core.downloaders',\n"
        "    'axdata_core.downloader_registry',\n"
        "    'axdata_core.source_request',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": TDX_PLUGIN_PYTHONPATH,
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert f"provider_id={TDX_PROVIDER_ID}" in result.stdout
    assert "interfaces=90" in result.stdout
    assert "downloaders=10" in result.stdout
    assert "collectors=0" in result.stdout
    assert "axdata_core.sources.tdx.catalog" not in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_core.downloaders" not in result.stdout
    assert "axdata_core.downloader_registry" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout


def test_builtin_provider_works_with_registry_as_official_enabled() -> None:
    registry = ProviderRegistry()

    for provider in list_builtin_providers():
        registry.register_builtin_provider(provider)

    snapshot = registry.snapshot()

    assert len(snapshot.providers) == 7
    assert len(snapshot.interfaces) == len(list_request_interfaces())
    assert "stock_codes_tdx" not in snapshot.interfaces
    assert "fx_codes_tdx" not in snapshot.interfaces
    assert all(provider.effective_trust_level == "official" for provider in snapshot.providers.values())


def test_tdx_plugins_work_with_registry_as_external_enabled() -> None:
    registry = build_registry_with_local_tdx_plugins(discover_entry_points=False)
    snapshot = registry.snapshot()

    assert snapshot.interfaces["stock_codes_tdx"].provider_id == TDX_PROVIDER_ID
    assert snapshot.interfaces["fx_codes_tdx"].provider_id == TDX_EXT_PROVIDER_ID
    assert snapshot.providers[TDX_PROVIDER_ID].built_in is True
    assert snapshot.providers[TDX_EXT_PROVIDER_ID].built_in is True
    assert snapshot.providers[TDX_PROVIDER_ID].effective_trust_level == "official"
    assert snapshot.providers[TDX_EXT_PROVIDER_ID].effective_trust_level == "official"


def test_builtin_adapter_delegates_by_builtin_source_code(monkeypatch) -> None:
    class FakeLegacyAdapter:
        source = "fake"

        def supports(self, interface_name):
            return True

        def request(self, interface_name, params):
            assert interface_name == "stock_codes_tdx"
            assert params == {"code": "000001.SZ"}
            return [
                {
                    "instrument_id": "000001.SZ",
                    "name": "平安银行",
                    "extra": "drop",
                }
            ]

    from axdata_core.builtin_providers import BuiltinSourceAdapter

    adapter = BuiltinSourceAdapter("tdx", provider_id=TDX_PROVIDER_ID)

    import axdata_core.builtin_providers as builtin_providers

    calls = []

    def fake_adapter_for_builtin_source(source_code, *, provider_id=None, options=None):
        calls.append(
            {
                "source_code": source_code,
                "provider_id": provider_id,
                "options": options,
            }
        )
        return FakeLegacyAdapter()

    monkeypatch.setattr(
        builtin_providers,
        "_adapter_for_builtin_source",
        fake_adapter_for_builtin_source,
    )

    result = adapter.call(
        "stock_codes_tdx",
        params={"code": "000001.SZ"},
        fields=["instrument_id", "name"],
    )

    assert isinstance(result, SourceResult)
    assert result.to_dict()["data"] == [{"instrument_id": "000001.SZ", "name": "平安银行"}]
    assert result.meta["source"] == "fake"
    assert calls == [
        {
            "source_code": "tdx",
            "provider_id": TDX_PROVIDER_ID,
            "options": {},
        }
    ]


def test_builtin_adapter_field_projection_does_not_load_source_request_gateway() -> None:
    code = (
        "import sys\n"
        "from axdata_core.builtin_providers import BuiltinSourceAdapter\n"
        "import axdata_core.builtin_providers as builtin_providers\n"
        "class FakeLegacyAdapter:\n"
        "    source = 'fake'\n"
        "    def request(self, interface_name, params):\n"
        "        return [{'instrument_id': '000001.SZ', 'name': '平安银行', 'extra': 'drop'}]\n"
        "builtin_providers._adapter_for_builtin_source = "
        "lambda source_code, provider_id=None, options=None: FakeLegacyAdapter()\n"
        "result = BuiltinSourceAdapter('tdx').call('stock_codes_tdx', fields=['instrument_id'])\n"
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

    assert "data=[{'instrument_id': '000001.SZ'}]" in result.stdout
    assert "source_projection=True" in result.stdout
    assert "source_request=False" in result.stdout


def test_source_request_gateway_uses_registry_adapter_before_legacy(monkeypatch, tmp_path) -> None:
    calls = []
    expected_cache_root = str((tmp_path / "cache" / "tdx_servers").resolve())
    expected_stats_cache_root = str((tmp_path / "cache" / "tdx" / "stats").resolve())

    class FakeProviderAdapter:
        def call(self, interface_name, params=None, fields=None, options=None):
            calls.append(
                {
                    "interface_name": interface_name,
                    "params": params,
                    "fields": fields,
                    "options": options,
                }
            )
            return SourceResult(
                data=(
                    {
                        "instrument_id": "000001.SZ",
                        "name": "平安银行",
                        "extra": "drop",
                    },
                ),
            )

    class FakeProvider:
        source_code = "tdx"

        def create_adapter(self, options=None):
            calls.append({"create_options": options})
            return FakeProviderAdapter()

    class FakeRegisteredProvider:
        source_code = "tdx"
        provider = FakeProvider()

    class FakeRoute:
        provider_id = "axdata.source.tdx"
        interface = InterfaceSpec(
            name="stock_codes_tdx",
            display_name_zh="股票列表",
            source_code="tdx",
            source_name_zh="通达信",
            asset_class=AssetClass.STOCK.value,
            parameters=(
                ParameterSpec(
                    name="code",
                    display_name_zh="证券代码",
                    type="string",
                    required=False,
                ),
            ),
            fields=(
                FieldSpec(
                    name="instrument_id",
                    display_name_zh="证券代码",
                    type="string",
                    required=True,
                ),
                FieldSpec(
                    name="name",
                    display_name_zh="名称",
                    type="string",
                    required=True,
                ),
            ),
        )

    class FakeSnapshot:
        providers = {"axdata.source.tdx": FakeRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "stock_codes_tdx"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())
    monkeypatch.setattr(
        source_request,
        "adapter_for_interface",
        lambda interface_name, options=None: (_ for _ in ()).throw(AssertionError("legacy fallback used")),
    )

    result = source_request.request_interface(
        "stock_codes_tdx",
        params={"code": "000001.SZ"},
        fields=["instrument_id", "name"],
        options={"source_server_count": 1},
        data_root=tmp_path,
    )

    assert result.records == [{"instrument_id": "000001.SZ", "name": "平安银行"}]
    assert result.meta["source"] == "tdx"
    assert result.meta["options"] == {"source_server_count": 1}
    assert calls == [
        {
            "create_options": {
                "source_server_count": 1,
                "server_cache_root": expected_cache_root,
                "stats_cache_root": expected_stats_cache_root,
            }
        },
        {
            "interface_name": "stock_codes_tdx",
            "params": {"code": "000001.SZ"},
            "fields": None,
            "options": None,
        },
    ]


def test_source_request_gateway_uses_registry_contract_before_legacy_catalog(monkeypatch) -> None:
    calls = []

    class FakeProviderAdapter:
        def call(self, interface_name, params=None, fields=None, options=None):
            calls.append(
                {
                    "interface_name": interface_name,
                    "params": dict(params or {}),
                    "fields": fields,
                    "options": options,
                }
            )
            return SourceResult(
                data=(
                    {
                        "external_only": "from registry",
                        "legacy_only": "drop",
                    },
                ),
                meta={"contract_source": "registry"},
            )

    class FakeProvider:
        source_code = "external"

        def create_adapter(self, options=None):
            calls.append({"create_options": options})
            return FakeProviderAdapter()

    class FakeRegisteredProvider:
        source_code = "external"
        provider = FakeProvider()

    class FakeRoute:
        provider_id = "axdata.source.external"
        interface = InterfaceSpec(
            name="stock_codes_tdx",
            display_name_zh="外部股票列表",
            source_code="external",
            source_name_zh="外部源",
            category="测试",
            asset_class=AssetClass.STOCK.value,
            parameters=(
                ParameterSpec(
                    name="external_code",
                    display_name_zh="外部代码",
                    type="string",
                    required=True,
                ),
            ),
            fields=(
                FieldSpec(
                    name="external_only",
                    display_name_zh="外部字段",
                    type="string",
                    required=True,
                ),
            ),
        )

    class FakeSnapshot:
        providers = {"axdata.source.external": FakeRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "stock_codes_tdx"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    result = source_request.request_interface(
        "stock_codes_tdx",
        params={"external_code": "000001.SZ"},
        fields=["external_only"],
    )

    assert result.records == [{"external_only": "from registry"}]
    assert result.meta["source"] == "external"
    assert result.meta["contract_source"] == "registry"
    assert calls == [
        {"create_options": {}},
        {
            "interface_name": "stock_codes_tdx",
            "params": {"external_code": "000001.SZ"},
            "fields": None,
            "options": None,
        },
    ]


def test_source_request_gateway_does_not_apply_tdx_enricher_to_unknown_shared_source_code(
    monkeypatch,
    tmp_path,
) -> None:
    calls = []

    class FakeProviderAdapter:
        def call(self, interface_name, params=None, fields=None, options=None):
            calls.append(
                {
                    "interface_name": interface_name,
                    "params": dict(params or {}),
                    "fields": fields,
                    "options": options,
                }
            )
            return SourceResult(data=({"instrument_id": "000001.SZ"},))

    class FakeProvider:
        source_code = "tdx"

        def create_adapter(self, options=None):
            calls.append({"create_options": dict(options or {})})
            return FakeProviderAdapter()

    class FakeRegisteredProvider:
        source_code = "tdx"
        provider = FakeProvider()

    class FakeRoute:
        provider_id = "community.source.custom_tdx"
        interface = InterfaceSpec(
            name="community_stock_codes",
            display_name_zh="社区 TDX 股票列表",
            source_code="tdx",
            source_name_zh="社区通达信",
            category="测试",
            asset_class=AssetClass.STOCK.value,
            parameters=(),
            fields=(
                FieldSpec(
                    name="instrument_id",
                    display_name_zh="证券代码",
                    type="string",
                    required=True,
                ),
            ),
        )

    class FakeSnapshot:
        providers = {"community.source.custom_tdx": FakeRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "community_stock_codes"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    result = source_request.request_interface(
        "community_stock_codes",
        fields=["instrument_id"],
        data_root=tmp_path,
    )

    assert result.records == [{"instrument_id": "000001.SZ"}]
    assert calls == [
        {"create_options": {}},
        {
            "interface_name": "community_stock_codes",
            "params": {},
            "fields": None,
            "options": None,
        },
    ]


def test_source_request_gateway_injects_tdx_ext_server_cache_without_meta_leak(monkeypatch, tmp_path) -> None:
    calls = []
    expected_cache_root = str((tmp_path / "cache" / "tdx_servers").resolve())

    class FakeProviderAdapter:
        def call(self, interface_name, params=None, fields=None, options=None):
            calls.append(
                {
                    "interface_name": interface_name,
                    "params": params,
                    "fields": fields,
                    "options": options,
                }
            )
            return SourceResult(
                data=(
                    {
                        "instrument_id": "IC2606.CFFEX",
                        "symbol": "IC2606",
                        "extra": "drop",
                    },
                ),
                meta={
                    "source": "wrong",
                    "persisted": True,
                    "options": {"server_cache_root": expected_cache_root},
                    "provider_meta": "ok",
                },
            )

    class FakeProvider:
        source_code = "tdx_ext"

        def create_adapter(self, options=None):
            calls.append({"create_options": options})
            return FakeProviderAdapter()

    class FakeRegisteredProvider:
        source_code = "tdx_ext"
        provider = FakeProvider()

    class FakeRoute:
        provider_id = "axdata.source.tdx_ext"
        interface = InterfaceSpec(
            name="futures_contracts_tdx",
            display_name_zh="期货合约",
            source_code="tdx_ext",
            source_name_zh="通达信扩展行情",
            asset_class=AssetClass.FUTURE.value,
            parameters=(
                ParameterSpec(
                    name="exchange",
                    display_name_zh="交易所",
                    type="string",
                    required=False,
                ),
            ),
            fields=(
                FieldSpec(
                    name="instrument_id",
                    display_name_zh="证券代码",
                    type="string",
                    required=True,
                ),
                FieldSpec(
                    name="symbol",
                    display_name_zh="代码",
                    type="string",
                    required=True,
                ),
            ),
        )

    class FakeSnapshot:
        providers = {"axdata.source.tdx_ext": FakeRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "futures_contracts_tdx"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())
    monkeypatch.setattr(
        source_request,
        "adapter_for_interface",
        lambda interface_name, options=None: (_ for _ in ()).throw(AssertionError("legacy fallback used")),
    )

    result = source_request.request_interface(
        "futures_contracts_tdx",
        params={"exchange": "CFFEX"},
        fields=["instrument_id", "symbol"],
        options={"source_server_count": 2, "connections_per_server": 3},
        data_root=tmp_path,
    )

    assert result.records == [{"instrument_id": "IC2606.CFFEX", "symbol": "IC2606"}]
    assert result.meta["source"] == "tdx_ext"
    assert result.meta["persisted"] is False
    assert result.meta["provider_meta"] == "ok"
    assert result.meta["options"] == {"source_server_count": 2, "connections_per_server": 3}
    assert "server_cache_root" not in result.meta["options"]
    assert calls == [
        {
            "create_options": {
                "source_server_count": 2,
                "connections_per_server": 3,
                "server_cache_root": expected_cache_root,
            }
        },
        {
            "interface_name": "futures_contracts_tdx",
            "params": {"exchange": "CFFEX"},
            "fields": None,
            "options": None,
        },
    ]


def test_source_execution_options_inject_tdx_server_cache_root(tmp_path) -> None:
    expected_cache_root = str((tmp_path / "cache" / "tdx_servers").resolve())
    expected_stats_cache_root = str((tmp_path / "cache" / "tdx" / "stats").resolve())

    assert execution_options_for_source(
        {"source_server_count": 1},
        data_root=tmp_path,
        provider_id=TDX_PROVIDER_ID,
        source_code="tdx",
    ) == {
        "source_server_count": 1,
        "server_cache_root": expected_cache_root,
        "stats_cache_root": expected_stats_cache_root,
    }
    assert execution_options_for_source(
        {"server_cache_root": "custom-cache", "stats_cache_root": "custom-stats"},
        data_root=tmp_path,
        provider_id=TDX_PROVIDER_ID,
        source_code="tdx",
    ) == {"server_cache_root": "custom-cache", "stats_cache_root": "custom-stats"}
    assert execution_options_for_source(
        {"server_cache_root": "custom-cache"},
        data_root=tmp_path,
        provider_id=TDX_EXT_PROVIDER_ID,
        source_code="tdx_ext",
    ) == {"server_cache_root": "custom-cache"}
    assert execution_options_for_source(
        {"source_server_count": 2, "connections_per_server": 3},
        data_root=tmp_path,
        provider_id=TDX_EXT_PROVIDER_ID,
        source_code="tdx_ext",
    ) == {
        "source_server_count": 2,
        "connections_per_server": 3,
        "server_cache_root": expected_cache_root,
    }
    assert execution_options_for_source(
        {"source_server_count": 1},
        data_root=tmp_path,
        provider_id="community.source.custom_tdx",
        source_code="tdx",
    ) == {"source_server_count": 1}
    assert execution_options_for_source(
        {"source_server_count": 1},
        data_root=tmp_path,
        source_code="tencent",
    ) == {"source_server_count": 1}


def test_source_execution_options_do_not_eager_load_tdx_request_or_downloader(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_execution_options import execution_options_for_source\n"
        f"options = execution_options_for_source({{}}, data_root={str(tmp_path)!r}, provider_id={TDX_PROVIDER_ID!r}, source_code='tdx')\n"
        "print('server_cache_root=' + str(options.get('server_cache_root')).replace('\\\\', '/'))\n"
        "print('stats_cache_root=' + str(options.get('stats_cache_root')).replace('\\\\', '/'))\n"
        "print('tdx_source_execution=' + str('axdata_core.adapters.tdx.source_execution' in sys.modules))\n"
        "print('tdx_server_config=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
        "print('tdx_downloader=' + str('axdata_core.adapters.tdx.downloader' in sys.modules))\n"
        "print('tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": TDX_PLUGIN_PYTHONPATH,
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    expected_cache_root = str((tmp_path / "cache" / "tdx_servers").resolve()).replace("\\", "/")
    expected_stats_cache_root = str((tmp_path / "cache" / "tdx" / "stats").resolve()).replace("\\", "/")
    assert f"server_cache_root={expected_cache_root}" in result.stdout
    assert f"stats_cache_root={expected_stats_cache_root}" in result.stdout
    assert "tdx_source_execution=False" in result.stdout
    assert "tdx_server_config=False" in result.stdout
    assert "tdx_downloader=False" in result.stdout
    assert "tdx_request=False" in result.stdout


def test_tdx_server_cache_import_does_not_load_server_config(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_errors import SourceUnavailableError\n"
        "from axdata_core.adapters.tdx import server_cache\n"
        "print('server_config_before=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
        "try:\n"
        f"    server_cache.tdx_server_cache_root({str(tmp_path)!r})\n"
        "except SourceUnavailableError as exc:\n"
        "    print('server_cache_unavailable=True')\n"
        "    print('server_cache_message=' + str(exc))\n"
        "try:\n"
        f"    server_cache.tdx_stats_cache_root({str(tmp_path)!r})\n"
        "except SourceUnavailableError as exc:\n"
        "    print('stats_cache_unavailable=True')\n"
        "    print('stats_cache_message=' + str(exc))\n"
        "print('server_config_after=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
    )
    result = _core_without_site_subprocess(code)

    assert "server_config_before=False" in result.stdout
    assert "server_cache_unavailable=True" in result.stdout
    assert f"server_cache_message={TDX_PLUGIN_REQUIRED_MESSAGE}" in result.stdout
    assert "stats_cache_unavailable=True" in result.stdout
    assert f"stats_cache_message={TDX_PLUGIN_REQUIRED_MESSAGE}" in result.stdout
    assert "server_config_after=False" in result.stdout


def test_source_execution_options_do_not_eager_load_tdx_ext_request_or_pool(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_execution_options import execution_options_for_source\n"
        f"options = execution_options_for_source({{}}, data_root={str(tmp_path)!r}, source_code='tdx_ext')\n"
        "print('server_cache_root=' + str(options.get('server_cache_root')).replace('\\\\', '/'))\n"
        "print('tdx_ext_source_execution=' + str('axdata_core.adapters.tdx_ext.source_execution' in sys.modules))\n"
        "print('tdx_server_config=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
        "print('tdx_ext_request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('tdx_ext_client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('tdx_ext_pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
        "print('tdx_ext_local_cache=' + str('axdata_core.adapters.tdx_ext.local_cache' in sys.modules))\n"
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

    expected_cache_root = str((tmp_path / "cache" / "tdx_servers").resolve()).replace("\\", "/")
    assert f"server_cache_root={expected_cache_root}" in result.stdout
    assert "tdx_ext_source_execution=True" in result.stdout
    assert "tdx_server_config=False" in result.stdout
    assert "tdx_ext_request=False" in result.stdout
    assert "tdx_ext_client=False" in result.stdout
    assert "tdx_ext_pool=False" in result.stdout
    assert "tdx_ext_local_cache=False" in result.stdout


def test_tdx_ext_server_cache_import_does_not_load_server_config(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.tdx_ext import server_cache\n"
        "print('server_config_before=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
        f"print('cache_root=' + str(server_cache.tdx_ext_server_cache_root({str(tmp_path)!r})).replace('\\\\', '/'))\n"
        "print('server_config_after=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
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

    expected_cache_root = str((tmp_path / "cache" / "tdx_servers").resolve()).replace("\\", "/")
    assert "server_config_before=False" in result.stdout
    assert f"cache_root={expected_cache_root}" in result.stdout
    assert "server_config_after=False" in result.stdout


def test_source_execution_options_for_plain_source_does_not_load_tdx_enrichers(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_execution_options import execution_options_for_source\n"
        f"options = execution_options_for_source({{'timeout_ms': 1000}}, data_root={str(tmp_path)!r}, source_code='tencent')\n"
        "print('options=' + str(options))\n"
        "print('tdx_source_execution=' + str('axdata_core.adapters.tdx.source_execution' in sys.modules))\n"
        "print('tdx_ext_source_execution=' + str('axdata_core.adapters.tdx_ext.source_execution' in sys.modules))\n"
        "print('tdx_downloader=' + str('axdata_core.adapters.tdx.downloader' in sys.modules))\n"
        "print('tdx_ext_request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
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

    assert "options={'timeout_ms': 1000}" in result.stdout
    assert "tdx_source_execution=False" in result.stdout
    assert "tdx_ext_source_execution=False" in result.stdout
    assert "tdx_downloader=False" in result.stdout
    assert "tdx_ext_request=False" in result.stdout


def test_source_adapter_factory_import_does_not_eager_load_source_adapters() -> None:
    code = (
        "import sys\n"
        "import axdata_core.source_adapter_factory as factory\n"
        "names = factory.legacy_source_adapter_factories().keys()\n"
        "print('sources=' + ','.join(sorted(names)))\n"
        "print('tdx_source_adapter_registry=' + str('axdata_core.adapters.tdx.source_adapter_registry' in sys.modules))\n"
        "print('tdx_ext_source_adapter_registry=' + str('axdata_core.adapters.tdx_ext.source_adapter_registry' in sys.modules))\n"
        "print('exchange_source_adapter_registry=' + str('axdata_core.adapters.exchange.source_adapter_registry' in sys.modules))\n"
        "print('cninfo_source_adapter_registry=' + str('axdata_core.adapters.cninfo.source_adapter_registry' in sys.modules))\n"
        "print('tencent_source_adapter_registry=' + str('axdata_core.adapters.tencent.source_adapter_registry' in sys.modules))\n"
        "print('eastmoney_source_adapter_registry=' + str('axdata_core.adapters.eastmoney.source_adapter_registry' in sys.modules))\n"
        "print('sina_source_adapter_registry=' + str('axdata_core.adapters.sina.source_adapter_registry' in sys.modules))\n"
        "print('tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
        "print('tdx_ext_request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('exchange_provider_bridge=' + str('axdata_core.adapters.exchange.provider_bridge' in sys.modules))\n"
        "print('cninfo_provider_bridge=' + str('axdata_core.adapters.cninfo.provider_bridge' in sys.modules))\n"
        "print('tencent_provider_bridge=' + str('axdata_core.adapters.tencent.provider_bridge' in sys.modules))\n"
        "print('eastmoney_provider_bridge=' + str('axdata_core.adapters.eastmoney.provider_bridge' in sys.modules))\n"
        "print('sina_provider_bridge=' + str('axdata_core.adapters.sina.provider_bridge' in sys.modules))\n"
        "print('exchange_request=' + str('axdata_core.adapters.exchange.request' in sys.modules))\n"
        "print('cninfo_request=' + str('axdata_core.adapters.cninfo.request' in sys.modules))\n"
        "print('tencent_request=' + str('axdata_core.adapters.tencent.request' in sys.modules))\n"
        "print('eastmoney_request=' + str('axdata_core.adapters.eastmoney.request' in sys.modules))\n"
        "print('sina_request=' + str('axdata_core.adapters.sina.request' in sys.modules))\n"
    )
    result = _core_without_site_subprocess(code)

    assert "sources=cls,cninfo,eastmoney,exchange,kph,sina,tdx_ext,tencent" in result.stdout
    assert "tdx_source_adapter_registry=False" in result.stdout
    assert "tdx_ext_source_adapter_registry=True" in result.stdout
    assert "exchange_source_adapter_registry=True" in result.stdout
    assert "cninfo_source_adapter_registry=True" in result.stdout
    assert "tencent_source_adapter_registry=True" in result.stdout
    assert "eastmoney_source_adapter_registry=True" in result.stdout
    assert "sina_source_adapter_registry=True" in result.stdout
    assert "tdx_request=False" in result.stdout
    assert "tdx_ext_request=False" in result.stdout
    assert "exchange_provider_bridge=False" in result.stdout
    assert "cninfo_provider_bridge=False" in result.stdout
    assert "tencent_provider_bridge=False" in result.stdout
    assert "eastmoney_provider_bridge=False" in result.stdout
    assert "sina_provider_bridge=False" in result.stdout
    assert "exchange_request=False" in result.stdout
    assert "cninfo_request=False" in result.stdout
    assert "tencent_request=False" in result.stdout
    assert "eastmoney_request=False" in result.stdout
    assert "sina_request=False" in result.stdout


def test_source_adapter_factory_provider_id_map_is_lightweight() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_adapter_factory import builtin_provider_adapter_factories\n"
        "factories = builtin_provider_adapter_factories()\n"
        "names = factories.keys()\n"
        "print('providers=' + ','.join(sorted(names)))\n"
        "print('tdx_ext_module=' + factories['axdata.source.tdx_ext'].__module__)\n"
        "print('exchange_module=' + factories['axdata.source.exchange'].__module__)\n"
        "print('cninfo_module=' + factories['axdata.source.cninfo'].__module__)\n"
        "print('tencent_module=' + factories['axdata.source.tencent'].__module__)\n"
        "print('eastmoney_module=' + factories['axdata.source.eastmoney'].__module__)\n"
        "print('sina_module=' + factories['axdata.source.sina'].__module__)\n"
        "print('tdx_source_adapter_registry=' + str('axdata_core.adapters.tdx.source_adapter_registry' in sys.modules))\n"
        "print('tdx_ext_source_adapter_registry=' + str('axdata_core.adapters.tdx_ext.source_adapter_registry' in sys.modules))\n"
        "print('exchange_source_adapter_registry=' + str('axdata_core.adapters.exchange.source_adapter_registry' in sys.modules))\n"
        "print('cninfo_source_adapter_registry=' + str('axdata_core.adapters.cninfo.source_adapter_registry' in sys.modules))\n"
        "print('tencent_source_adapter_registry=' + str('axdata_core.adapters.tencent.source_adapter_registry' in sys.modules))\n"
        "print('eastmoney_source_adapter_registry=' + str('axdata_core.adapters.eastmoney.source_adapter_registry' in sys.modules))\n"
        "print('sina_source_adapter_registry=' + str('axdata_core.adapters.sina.source_adapter_registry' in sys.modules))\n"
        "print('tdx_provider_bridge=' + str('axdata_core.adapters.tdx.provider_bridge' in sys.modules))\n"
        "print('tdx_ext_provider_bridge=' + str('axdata_core.adapters.tdx_ext.provider_bridge' in sys.modules))\n"
        "print('exchange_provider_bridge=' + str('axdata_core.adapters.exchange.provider_bridge' in sys.modules))\n"
        "print('cninfo_provider_bridge=' + str('axdata_core.adapters.cninfo.provider_bridge' in sys.modules))\n"
        "print('tencent_provider_bridge=' + str('axdata_core.adapters.tencent.provider_bridge' in sys.modules))\n"
        "print('eastmoney_provider_bridge=' + str('axdata_core.adapters.eastmoney.provider_bridge' in sys.modules))\n"
        "print('sina_provider_bridge=' + str('axdata_core.adapters.sina.provider_bridge' in sys.modules))\n"
        "print('tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
        "print('tdx_ext_request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
    )
    result = _core_without_site_subprocess(code)

    assert (
        "providers=axdata.source.cls,axdata.source.cninfo,"
        "axdata.source.eastmoney,axdata.source.exchange,"
        "axdata.source.kph,axdata.source.sina,"
        "axdata.source.tdx_ext,axdata.source.tencent"
    ) in result.stdout
    assert "tdx_ext_module=axdata_core.adapters.tdx_ext.source_adapter_registry" in result.stdout
    assert "exchange_module=axdata_core.adapters.exchange.source_adapter_registry" in result.stdout
    assert "cninfo_module=axdata_core.adapters.cninfo.source_adapter_registry" in result.stdout
    assert "tencent_module=axdata_core.adapters.tencent.source_adapter_registry" in result.stdout
    assert "eastmoney_module=axdata_core.adapters.eastmoney.source_adapter_registry" in result.stdout
    assert "sina_module=axdata_core.adapters.sina.source_adapter_registry" in result.stdout
    assert "tdx_source_adapter_registry=False" in result.stdout
    assert "tdx_ext_source_adapter_registry=True" in result.stdout
    assert "exchange_source_adapter_registry=True" in result.stdout
    assert "cninfo_source_adapter_registry=True" in result.stdout
    assert "tencent_source_adapter_registry=True" in result.stdout
    assert "eastmoney_source_adapter_registry=True" in result.stdout
    assert "sina_source_adapter_registry=True" in result.stdout
    assert "tdx_provider_bridge=False" in result.stdout
    assert "tdx_ext_provider_bridge=False" in result.stdout
    assert "exchange_provider_bridge=False" in result.stdout
    assert "cninfo_provider_bridge=False" in result.stdout
    assert "tencent_provider_bridge=False" in result.stdout
    assert "eastmoney_provider_bridge=False" in result.stdout
    assert "sina_provider_bridge=False" in result.stdout
    assert "tdx_request=False" in result.stdout
    assert "tdx_ext_request=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_source_adapter_factory_prefers_tdx_provider_package_when_available() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_adapter_factory import (\n"
        "    builtin_provider_adapter_factories,\n"
        "    legacy_source_adapter_factories,\n"
        ")\n"
        "provider_factories = builtin_provider_adapter_factories()\n"
        "source_factories = legacy_source_adapter_factories()\n"
        "print('tdx_provider_module=' + provider_factories['axdata.source.tdx'].__module__)\n"
        "print('tdx_source_module=' + source_factories['tdx'].__module__)\n"
        "print('provider_registry=' + str('axdata_source_tdx.source_adapter_registry' in sys.modules))\n"
        "print('provider_bridge=' + str('axdata_source_tdx.provider_bridge' in sys.modules))\n"
        "print('core_tdx_registry=' + str('axdata_core.adapters.tdx.source_adapter_registry' in sys.modules))\n"
        "print('core_tdx_bridge=' + str('axdata_core.adapters.tdx.provider_bridge' in sys.modules))\n"
        "print('tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(REPO_ROOT / "packages" / "axdata-source-tdx" / "src"),
                    str(REPO_ROOT / "libs" / "axdata_core"),
                ]
            ),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "tdx_provider_module=axdata_source_tdx.source_adapter_registry" in result.stdout
    assert "tdx_source_module=axdata_source_tdx.source_adapter_registry" in result.stdout
    assert "provider_registry=True" in result.stdout
    assert "provider_bridge=False" in result.stdout
    assert "core_tdx_registry=False" in result.stdout
    assert "core_tdx_bridge=False" in result.stdout
    assert "tdx_request=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_provider_package_source_adapter_factory_create_uses_provider_bridge() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_adapter_factory import adapter_for_provider_id\n"
        "class FakeRequestAdapter:\n"
        "    def __init__(self, client=None, options=None):\n"
        "        self.client = client\n"
        "        self.options = options\n"
        "import axdata_source_tdx.provider_bridge as provider_bridge\n"
        "provider_bridge.TdxRequestAdapter = FakeRequestAdapter\n"
        "client = object()\n"
        "adapter = adapter_for_provider_id(\n"
        "    'axdata.source.tdx',\n"
        "    options={'client': client, 'server_cache_root': 'cache'},\n"
        ")\n"
        "print('adapter_class=' + adapter.__class__.__name__)\n"
        "print('client_same=' + str(adapter.client is client))\n"
        "print('options=' + str(adapter.options))\n"
        "print('provider_registry=' + str('axdata_source_tdx.source_adapter_registry' in sys.modules))\n"
        "print('provider_bridge=' + str('axdata_source_tdx.provider_bridge' in sys.modules))\n"
        "print('provider_request_adapter=' + str('axdata_source_tdx.request_adapter' in sys.modules))\n"
        "print('core_tdx_registry=' + str('axdata_core.adapters.tdx.source_adapter_registry' in sys.modules))\n"
        "print('core_tdx_bridge=' + str('axdata_core.adapters.tdx.provider_bridge' in sys.modules))\n"
        "print('core_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(REPO_ROOT / "packages" / "axdata-source-tdx" / "src"),
                    str(REPO_ROOT / "libs" / "axdata_core"),
                ]
            ),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "adapter_class=FakeRequestAdapter" in result.stdout
    assert "client_same=True" in result.stdout
    assert "options={'server_cache_root': 'cache'}" in result.stdout
    assert "provider_registry=True" in result.stdout
    assert "provider_bridge=True" in result.stdout
    assert "provider_request_adapter=False" in result.stdout
    assert "core_tdx_registry=False" in result.stdout
    assert "core_tdx_bridge=False" in result.stdout
    assert "core_request=False" in result.stdout


def test_builtin_source_declarations_aggregate_source_owned_registries_lightly() -> None:
    code = (
        "import sys\n"
        "from axdata_core.builtin_source_declarations import (\n"
        "    builtin_downloader_declarations,\n"
        "    builtin_source_adapter_factory_declarations,\n"
        "    builtin_source_execution_enricher_declarations,\n"
        ")\n"
        "adapter_provider_keys = []\n"
        "adapter_source_keys = []\n"
        "for provider_factories, source_factories in builtin_source_adapter_factory_declarations():\n"
        "    adapter_provider_keys.extend(provider_factories)\n"
        "    adapter_source_keys.extend(source_factories)\n"
        "execution_keys = []\n"
        "for enrichers in builtin_source_execution_enricher_declarations():\n"
        "    execution_keys.extend(enrichers)\n"
        "downloader_profile_names = []\n"
        "downloader_adapter_keys = []\n"
        "downloader_runtime_keys = []\n"
        "for profile_declarations, adapter_factories, runtime_factories in builtin_downloader_declarations():\n"
        "    downloader_profile_names.append(profile_declarations.__name__)\n"
        "    downloader_adapter_keys.extend(adapter_factories)\n"
        "    downloader_runtime_keys.extend(runtime_factories)\n"
        "print('adapter_providers=' + ','.join(sorted(adapter_provider_keys)))\n"
        "print('adapter_sources=' + ','.join(sorted(adapter_source_keys)))\n"
        "print('execution_keys=' + ','.join(sorted(execution_keys)))\n"
        "print('downloader_profiles=' + ','.join(sorted(downloader_profile_names)))\n"
        "print('downloader_adapters=' + ','.join(sorted(downloader_adapter_keys)))\n"
        "print('downloader_runtime=' + ','.join(sorted(downloader_runtime_keys)))\n"
        "tracked = [\n"
        "    'axdata_core.source_adapter_factory',\n"
        "    'axdata_core.source_execution_registry',\n"
        "    'axdata_core.downloader_registry',\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.adapters.tdx.downloader_profiles',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.exchange.provider_bridge',\n"
        "    'axdata_core.adapters.cninfo.provider_bridge',\n"
        "    'axdata_core.adapters.tencent.provider_bridge',\n"
        "    'axdata_core.adapters.eastmoney.provider_bridge',\n"
        "    'axdata_core.adapters.sina.provider_bridge',\n"
        "    'axdata_core.adapters.exchange.request',\n"
        "    'axdata_core.adapters.cninfo.request',\n"
        "    'axdata_core.adapters.tencent.request',\n"
        "    'axdata_core.adapters.eastmoney.request',\n"
        "    'axdata_core.adapters.sina.request',\n"
        "    'axdata_core.source_request',\n"
        "    'axdata_core._tdx_wire.client',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
    )
    result = _core_without_site_subprocess(code)

    assert (
        "adapter_providers=axdata.source.cls,axdata.source.cninfo,"
        "axdata.source.eastmoney,axdata.source.exchange,"
        "axdata.source.kph,axdata.source.sina,"
        "axdata.source.tdx_ext,axdata.source.tencent"
    ) in result.stdout
    assert "adapter_sources=cls,cninfo,eastmoney,exchange,kph,sina,tdx_ext,tencent" in result.stdout
    assert "execution_keys=axdata.source.tdx_ext,axdata.source.tdx_ext_external,tdx_ext" in result.stdout
    assert "downloader_profiles=empty_downloader_profile_declarations" in result.stdout
    assert "downloader_adapters=" in result.stdout
    assert "downloader_runtime=" in result.stdout
    assert "loaded=\n" in result.stdout


def test_tdx_plugin_declarations_are_loaded_from_provider_package_lightly() -> None:
    code = (
        "import sys\n"
        "from axdata_core.builtin_source_declarations import (\n"
        "    builtin_downloader_declarations,\n"
        "    builtin_source_adapter_factory_declarations,\n"
        "    builtin_source_execution_enricher_declarations,\n"
        ")\n"
        "adapter_provider_keys = []\n"
        "adapter_source_keys = []\n"
        "for provider_factories, source_factories in builtin_source_adapter_factory_declarations():\n"
        "    adapter_provider_keys.extend(provider_factories)\n"
        "    adapter_source_keys.extend(source_factories)\n"
        "execution_keys = []\n"
        "for enrichers in builtin_source_execution_enricher_declarations():\n"
        "    execution_keys.extend(enrichers)\n"
        "downloader_profile_names = []\n"
        "downloader_adapter_keys = []\n"
        "downloader_runtime_keys = []\n"
        "for profile_declarations, adapter_factories, runtime_factories in builtin_downloader_declarations():\n"
        "    downloader_profile_names.append(profile_declarations.__name__)\n"
        "    downloader_adapter_keys.extend(adapter_factories)\n"
        "    downloader_runtime_keys.extend(runtime_factories)\n"
        "print('adapter_providers=' + ','.join(sorted(adapter_provider_keys)))\n"
        "print('adapter_sources=' + ','.join(sorted(adapter_source_keys)))\n"
        "print('execution_keys=' + ','.join(sorted(execution_keys)))\n"
        "print('downloader_profiles=' + ','.join(sorted(downloader_profile_names)))\n"
        "print('downloader_adapters=' + ','.join(sorted(downloader_adapter_keys)))\n"
        "print('downloader_runtime=' + ','.join(sorted(downloader_runtime_keys)))\n"
        "tracked = [\n"
        "    'axdata_source_tdx.source_adapter_registry',\n"
        "    'axdata_source_tdx.source_execution_registry',\n"
        "    'axdata_source_tdx.downloader_registry',\n"
        "    'axdata_source_tdx.provider_bridge',\n"
        "    'axdata_source_tdx.request_adapter',\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core._tdx_wire.client',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": TDX_PLUGIN_PYTHONPATH,
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert TDX_PROVIDER_ID in result.stdout
    assert "adapter_sources=" in result.stdout
    assert "tdx" in result.stdout
    assert "axdata.source.tdx" in result.stdout
    assert TDX_PROVIDER_ID in result.stdout
    assert "tdx" in result.stdout
    assert "downloader_profiles=tdx_downloader_profile_declarations" in result.stdout
    assert "downloader_adapters=tdx" in result.stdout
    assert "downloader_runtime=tdx" in result.stdout
    assert "axdata_source_tdx.provider_bridge" not in result.stdout
    assert "axdata_source_tdx.request_adapter" not in result.stdout
    assert "axdata_core.adapters.tdx.provider_bridge" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core._tdx_wire.client" not in result.stdout


def test_tdx_source_adapter_registry_import_does_not_load_runtime_modules() -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.tdx.source_adapter_registry import (\n"
        "    tdx_legacy_source_adapter_factories,\n"
        "    tdx_provider_adapter_factories,\n"
        "    tdx_source_adapter_factory_declarations,\n"
        ")\n"
        "provider_factories = tdx_provider_adapter_factories()\n"
        "source_factories = tdx_legacy_source_adapter_factories()\n"
        "declared_provider_factories, declared_source_factories = tdx_source_adapter_factory_declarations()\n"
        "print('providers=' + ','.join(sorted(provider_factories)))\n"
        "print('sources=' + ','.join(sorted(source_factories)))\n"
        "print('declared_providers=' + ','.join(sorted(declared_provider_factories)))\n"
        "print('declared_sources=' + ','.join(sorted(declared_source_factories)))\n"
        "print('tdx_source_adapter_registry=' + str('axdata_core.adapters.tdx.source_adapter_registry' in sys.modules))\n"
        "print('tdx_provider_bridge=' + str('axdata_core.adapters.tdx.provider_bridge' in sys.modules))\n"
        "print('tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
    )
    result = _core_without_site_subprocess(code)

    assert "providers=\n" in result.stdout
    assert "sources=\n" in result.stdout
    assert "declared_providers=\n" in result.stdout
    assert "declared_sources=\n" in result.stdout
    assert "tdx_source_adapter_registry=True" in result.stdout
    assert "tdx_provider_bridge=False" in result.stdout
    assert "tdx_request=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_tdx_ext_source_adapter_registry_import_does_not_load_runtime_modules() -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.tdx_ext.source_adapter_registry import (\n"
        "    tdx_ext_legacy_source_adapter_factories,\n"
        "    tdx_ext_provider_adapter_factories,\n"
        "    tdx_ext_source_adapter_factory_declarations,\n"
        ")\n"
        "provider_factories = tdx_ext_provider_adapter_factories()\n"
        "source_factories = tdx_ext_legacy_source_adapter_factories()\n"
        "declared_provider_factories, declared_source_factories = tdx_ext_source_adapter_factory_declarations()\n"
        "print('providers=' + ','.join(sorted(provider_factories)))\n"
        "print('sources=' + ','.join(sorted(source_factories)))\n"
        "print('declared_providers=' + ','.join(sorted(declared_provider_factories)))\n"
        "print('declared_sources=' + ','.join(sorted(declared_source_factories)))\n"
        "print('tdx_ext_source_adapter_registry=' + str('axdata_core.adapters.tdx_ext.source_adapter_registry' in sys.modules))\n"
        "print('tdx_ext_provider_bridge=' + str('axdata_core.adapters.tdx_ext.provider_bridge' in sys.modules))\n"
        "print('tdx_ext_request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('tdx_ext_client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('tdx_ext_pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
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

    assert "providers=axdata.source.tdx_ext" in result.stdout
    assert "sources=tdx_ext" in result.stdout
    assert "declared_providers=axdata.source.tdx_ext" in result.stdout
    assert "declared_sources=tdx_ext" in result.stdout
    assert "tdx_ext_source_adapter_registry=True" in result.stdout
    assert "tdx_ext_provider_bridge=False" in result.stdout
    assert "tdx_ext_request=False" in result.stdout
    assert "tdx_ext_client=False" in result.stdout
    assert "tdx_ext_pool=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_builtin_http_source_adapter_registries_do_not_load_runtime_modules() -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.cninfo.source_adapter_registry import (\n"
        "    cninfo_legacy_source_adapter_factories,\n"
        "    cninfo_provider_adapter_factories,\n"
        "    cninfo_source_adapter_factory_declarations,\n"
        ")\n"
        "from axdata_core.adapters.cls.source_adapter_registry import (\n"
        "    cls_legacy_source_adapter_factories,\n"
        "    cls_provider_adapter_factories,\n"
        "    cls_source_adapter_factory_declarations,\n"
        ")\n"
        "from axdata_core.adapters.eastmoney.source_adapter_registry import (\n"
        "    eastmoney_legacy_source_adapter_factories,\n"
        "    eastmoney_provider_adapter_factories,\n"
        "    eastmoney_source_adapter_factory_declarations,\n"
        ")\n"
        "from axdata_core.adapters.exchange.source_adapter_registry import (\n"
        "    exchange_legacy_source_adapter_factories,\n"
        "    exchange_provider_adapter_factories,\n"
        "    exchange_source_adapter_factory_declarations,\n"
        ")\n"
        "from axdata_core.adapters.sina.source_adapter_registry import (\n"
        "    sina_legacy_source_adapter_factories,\n"
        "    sina_provider_adapter_factories,\n"
        "    sina_source_adapter_factory_declarations,\n"
        ")\n"
        "from axdata_core.adapters.tencent.source_adapter_registry import (\n"
        "    tencent_legacy_source_adapter_factories,\n"
        "    tencent_provider_adapter_factories,\n"
        "    tencent_source_adapter_factory_declarations,\n"
        ")\n"
        "from axdata_core.adapters.kph.source_adapter_registry import (\n"
        "    kph_legacy_source_adapter_factories,\n"
        "    kph_provider_adapter_factories,\n"
        "    kph_source_adapter_factory_declarations,\n"
        ")\n"
        "providers = {}\n"
        "providers.update(cninfo_provider_adapter_factories())\n"
        "providers.update(cls_provider_adapter_factories())\n"
        "providers.update(eastmoney_provider_adapter_factories())\n"
        "providers.update(exchange_provider_adapter_factories())\n"
        "providers.update(kph_provider_adapter_factories())\n"
        "providers.update(sina_provider_adapter_factories())\n"
        "providers.update(tencent_provider_adapter_factories())\n"
        "sources = {}\n"
        "sources.update(cninfo_legacy_source_adapter_factories())\n"
        "sources.update(cls_legacy_source_adapter_factories())\n"
        "sources.update(eastmoney_legacy_source_adapter_factories())\n"
        "sources.update(exchange_legacy_source_adapter_factories())\n"
        "sources.update(kph_legacy_source_adapter_factories())\n"
        "sources.update(sina_legacy_source_adapter_factories())\n"
        "sources.update(tencent_legacy_source_adapter_factories())\n"
        "declared_providers = {}\n"
        "declared_sources = {}\n"
        "for provider_factories, source_factories in [\n"
        "    cninfo_source_adapter_factory_declarations(),\n"
        "    cls_source_adapter_factory_declarations(),\n"
        "    eastmoney_source_adapter_factory_declarations(),\n"
        "    exchange_source_adapter_factory_declarations(),\n"
        "    kph_source_adapter_factory_declarations(),\n"
        "    sina_source_adapter_factory_declarations(),\n"
        "    tencent_source_adapter_factory_declarations(),\n"
        "]:\n"
        "    declared_providers.update(provider_factories)\n"
        "    declared_sources.update(source_factories)\n"
        "print('providers=' + ','.join(sorted(providers)))\n"
        "print('sources=' + ','.join(sorted(sources)))\n"
        "print('declared_providers=' + ','.join(sorted(declared_providers)))\n"
        "print('declared_sources=' + ','.join(sorted(declared_sources)))\n"
        "tracked = [\n"
        "    'axdata_core.adapters.cninfo.provider_bridge',\n"
        "    'axdata_core.adapters.cls.provider_bridge',\n"
        "    'axdata_core.adapters.eastmoney.provider_bridge',\n"
        "    'axdata_core.adapters.exchange.provider_bridge',\n"
        "    'axdata_core.adapters.kph.provider_bridge',\n"
        "    'axdata_core.adapters.sina.provider_bridge',\n"
        "    'axdata_core.adapters.tencent.provider_bridge',\n"
        "    'axdata_core.adapters.cninfo.request',\n"
        "    'axdata_core.adapters.cls.request',\n"
        "    'axdata_core.adapters.eastmoney.request',\n"
        "    'axdata_core.adapters.exchange.request',\n"
        "    'axdata_core.adapters.kph.request',\n"
        "    'axdata_core.adapters.sina.request',\n"
        "    'axdata_core.adapters.tencent.request',\n"
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

    assert (
        "providers=axdata.source.cls,axdata.source.cninfo,"
        "axdata.source.eastmoney,axdata.source.exchange,"
        "axdata.source.kph,axdata.source.sina,axdata.source.tencent"
    ) in result.stdout
    assert "sources=cls,cninfo,eastmoney,exchange,kph,sina,tencent" in result.stdout
    assert (
        "declared_providers=axdata.source.cls,axdata.source.cninfo,"
        "axdata.source.eastmoney,axdata.source.exchange,"
        "axdata.source.kph,axdata.source.sina,axdata.source.tencent"
    ) in result.stdout
    assert "declared_sources=cls,cninfo,eastmoney,exchange,kph,sina,tencent" in result.stdout
    assert "loaded=\n" in result.stdout


def test_source_adapter_factory_unknown_source_does_not_load_source_adapters() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_adapter_factory import adapter_for_source_code\n"
        "try:\n"
        "    adapter_for_source_code('unknown_tdx')\n"
        "except KeyError as exc:\n"
        "    print('error=' + str(exc))\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.exchange.provider_bridge',\n"
        "    'axdata_core.adapters.tencent.provider_bridge',\n"
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

    assert "No legacy source adapter is registered for source 'unknown_tdx'." in result.stdout
    assert "loaded=\n" in result.stdout


def test_builtin_tdx_provider_lookup_requires_plugin() -> None:
    code = (
        "import sys\n"
        "from axdata_core.builtin_providers import get_builtin_provider\n"
        "for source_code in ('tdx', 'tdx_ext'):\n"
        "    try:\n"
        "        get_builtin_provider(source_code)\n"
        "    except KeyError as exc:\n"
        "        print(source_code + '_missing=True')\n"
        "        print(source_code + '_error=' + str(exc))\n"
        "    else:\n"
        "        print(source_code + '_missing=False')\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
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

    assert "tdx_missing=True" in result.stdout
    assert "tdx_ext_missing=True" in result.stdout
    assert "loaded=\n" in result.stdout


def test_registry_adapter_for_tdx_requires_plugin(tmp_path) -> None:
    from axdata_core.plugin_config import disable_provider

    plugin_config_path = tmp_path / "metadata" / "plugins.json"
    disable_provider(TDX_PROVIDER_ID, path=plugin_config_path)

    code = (
        "import sys\n"
        "from axdata_core.source_errors import SourceUnavailableError\n"
        "from axdata_core.source_request import registry_adapter_for_interface\n"
        "try:\n"
        "    registry_adapter_for_interface('stock_codes_tdx', options={'source_server_count': 1})\n"
        "except SourceUnavailableError as exc:\n"
        "    print('unavailable=True')\n"
        "    print('message=' + str(exc))\n"
        "else:\n"
        "    print('unavailable=False')\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
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
            "AXDATA_DATA_DIR": str(tmp_path / "data"),
            "AXDATA_PLUGIN_CONFIG_PATH": str(plugin_config_path),
            "AXDATA_PLUGIN_INSTALL_ROOT": str(tmp_path / "plugins"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "unavailable=True" in result.stdout
    assert f"message={TDX_PLUGIN_REQUIRED_MESSAGE}" in result.stdout
    assert "loaded=\n" in result.stdout


def test_registry_adapter_for_tdx_ext_requires_plugin(tmp_path) -> None:
    from axdata_core.plugin_config import disable_provider

    plugin_config_path = tmp_path / "metadata" / "plugins.json"
    disable_provider(TDX_EXT_PROVIDER_ID, path=plugin_config_path)

    code = (
        "import sys\n"
        "from axdata_core.source_errors import SourceUnavailableError\n"
        "from axdata_core.source_request import registry_adapter_for_interface\n"
        "try:\n"
        "    registry_adapter_for_interface('futures_contracts_tdx', options={'server_cache_root': 'cache'})\n"
        "except SourceUnavailableError as exc:\n"
        "    print('unavailable=True')\n"
        "    print('message=' + str(exc))\n"
        "else:\n"
        "    print('unavailable=False')\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx.downloader',\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core.adapters.tdx_ext.client',\n"
        "    'axdata_core.adapters.tdx_ext.pool',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
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
            "AXDATA_DATA_DIR": str(tmp_path / "data"),
            "AXDATA_PLUGIN_CONFIG_PATH": str(plugin_config_path),
            "AXDATA_PLUGIN_INSTALL_ROOT": str(tmp_path / "plugins"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "unavailable=True" in result.stdout
    assert f"message={TDX_PLUGIN_REQUIRED_MESSAGE}" in result.stdout
    assert "loaded=\n" in result.stdout


def test_tdx_plugin_provider_bridge_import_does_not_load_request_module() -> None:
    code = (
        "import sys\n"
        "from axdata_source_tdx.provider_bridge import split_tdx_provider_options\n"
        "client, options = split_tdx_provider_options({'client': object(), 'source_server_count': 1})\n"
        "print('has_client=' + str(client is not None))\n"
        "print('options=' + str(options))\n"
        "print('tdx_request=' + str('axdata_source_tdx.request_adapter' in sys.modules))\n"
        "print('core_tdx_request=' + str('axdata_core.adapters.tdx.request' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": TDX_PLUGIN_PYTHONPATH,
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "has_client=True" in result.stdout
    assert "options={'source_server_count': 1}" in result.stdout
    assert "tdx_request=False" in result.stdout
    assert "core_tdx_request=False" in result.stdout


def test_tdx_plugin_provider_bridge_create_adapter_splits_client_from_options() -> None:
    ensure_local_tdx_plugin_paths()
    from axdata_source_tdx.provider_bridge import create_tdx_request_adapter

    client = object()
    adapter = create_tdx_request_adapter(
        {
            "client": client,
            "source_server_count": 2,
            "server_cache_root": "server-cache",
        }
    )

    assert adapter._client is client
    assert adapter._options["source_server_count"] == 2
    assert adapter._options["server_cache_root"] == "server-cache"
    assert "client" not in adapter._options


def test_tdx_ext_provider_bridge_import_does_not_load_request_module() -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.tdx_ext.provider_bridge import create_tdx_ext_request_adapter\n"
        "print('bridge=' + str('axdata_core.adapters.tdx_ext.provider_bridge' in sys.modules))\n"
        "print('has_factory=' + str(create_tdx_ext_request_adapter is not None))\n"
        "print('tdx_ext_request=' + str('axdata_core.adapters.tdx_ext.request' in sys.modules))\n"
        "print('tdx_ext_client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('tdx_ext_pool=' + str('axdata_core.adapters.tdx_ext.pool' in sys.modules))\n"
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

    assert "bridge=True" in result.stdout
    assert "has_factory=True" in result.stdout
    assert "tdx_ext_request=False" in result.stdout
    assert "tdx_ext_client=False" in result.stdout
    assert "tdx_ext_pool=False" in result.stdout


def test_tdx_ext_provider_bridge_create_adapter_preserves_options() -> None:
    from axdata_core.adapters.tdx_ext.provider_bridge import create_tdx_ext_request_adapter

    adapter = create_tdx_ext_request_adapter(
        {
            "source_server_count": 2,
            "connections_per_server": 3,
            "server_cache_root": "server-cache",
        }
    )

    assert adapter._options == {
        "source_server_count": 2,
        "connections_per_server": 3,
        "server_cache_root": "server-cache",
    }


def test_http_provider_bridge_imports_do_not_load_request_modules() -> None:
    code = (
        "import sys\n"
        "from axdata_core.adapters.cninfo.provider_bridge import create_cninfo_request_adapter\n"
        "from axdata_core.adapters.cls.provider_bridge import create_cls_request_adapter\n"
        "from axdata_core.adapters.eastmoney.provider_bridge import create_eastmoney_request_adapter\n"
        "from axdata_core.adapters.exchange.provider_bridge import create_exchange_request_adapter\n"
        "from axdata_core.adapters.kph.provider_bridge import create_kph_request_adapter\n"
        "from axdata_core.adapters.sina.provider_bridge import create_sina_request_adapter\n"
        "from axdata_core.adapters.tencent.provider_bridge import create_tencent_request_adapter\n"
        "factories = [\n"
        "    create_cninfo_request_adapter,\n"
        "    create_cls_request_adapter,\n"
        "    create_eastmoney_request_adapter,\n"
        "    create_exchange_request_adapter,\n"
        "    create_kph_request_adapter,\n"
        "    create_sina_request_adapter,\n"
        "    create_tencent_request_adapter,\n"
        "]\n"
        "print('factory_count=' + str(len(factories)))\n"
        "tracked = [\n"
        "    'axdata_core.adapters.cninfo.request',\n"
        "    'axdata_core.adapters.cls.request',\n"
        "    'axdata_core.adapters.eastmoney.request',\n"
        "    'axdata_core.adapters.exchange.request',\n"
        "    'axdata_core.adapters.kph.request',\n"
        "    'axdata_core.adapters.sina.request',\n"
        "    'axdata_core.adapters.tencent.request',\n"
        "]\n"
        "print('loaded=' + ','.join(name for name in tracked if name in sys.modules))\n"
        "print('plugins=' + str('axdata_core.plugins' in sys.modules))\n"
        "print('legacy_provider_adapter=' + str('axdata_core.legacy_provider_adapter' in sys.modules))\n"
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

    assert "factory_count=7" in result.stdout
    assert "loaded=\n" in result.stdout
    assert "plugins=False" in result.stdout
    assert "legacy_provider_adapter=False" in result.stdout
    assert "source_request=False" in result.stdout


def test_builtin_http_source_adapter_factory_passes_opener_and_timeout_options() -> None:
    from axdata_core.source_adapter_factory import adapter_for_source_code

    tencent = adapter_for_source_code(
        "tencent",
        options={"opener": TencentOpener(), "timeout_ms": 1000},
    )
    tencent_rows = tencent.request("tencent_realtime_snapshot", {"code": "000001.SZ"})
    assert tencent_rows[0]["instrument_id"] == "000001.SZ"
    assert tencent_rows[0]["last_price"] == 10.64

    cninfo = adapter_for_source_code(
        "cninfo",
        options={"opener": CninfoOpener(), "timeout_seconds": 1},
    )
    cninfo_rows = cninfo.request(
        "cninfo_announcements",
        {
            "code": "000001.SZ",
            "start_date": "20240101",
            "end_date": "20240131",
            "limit": 1,
        },
    )
    assert cninfo_rows[0]["instrument_id"] == "000001.SZ"
    assert cninfo_rows[0]["title"] == "关联交易公告"


def test_source_adapter_factory_prefers_provider_identity_over_source_code() -> None:
    from axdata_core.source_adapter_factory import adapter_for_source_identity

    calls = []

    def provider_factory(options):
        calls.append({"factory": "provider", "options": options})
        return "provider-adapter"

    def source_factory(options):
        calls.append({"factory": "source", "options": options})
        return "source-adapter"

    adapter = adapter_for_source_identity(
        provider_id="axdata.source.demo",
        source_code="demo",
        options={"x": 1},
        provider_factories={"axdata.source.demo": provider_factory},
        source_factories={"demo": source_factory},
    )

    assert adapter == "provider-adapter"
    assert calls == [{"factory": "provider", "options": {"x": 1}}]


def test_source_adapter_factory_uses_source_code_for_legacy_identity() -> None:
    from axdata_core.source_adapter_factory import adapter_for_source_identity

    calls = []

    def source_factory(options):
        calls.append({"factory": "source", "options": options})
        return "source-adapter"

    adapter = adapter_for_source_identity(
        source_code="demo",
        options={"x": 1},
        source_factories={"demo": source_factory},
    )

    assert adapter == "source-adapter"
    assert calls == [{"factory": "source", "options": {"x": 1}}]


def test_tdx_plugin_source_adapter_factory_supports_injected_client_options() -> None:
    ensure_local_tdx_plugin_paths()
    from axdata_core.source_adapter_factory import adapter_for_source_code

    class FakeClient:
        def __init__(self) -> None:
            self.connected = False
            self.calls = []

        def connect(self) -> None:
            self.connected = True

        def get_codes(self, market, *, start=0, limit=None):
            self.calls.append({"market": market, "start": start, "limit": limit})
            if market == "sz" and start == 0:
                return [
                    SimpleNamespace(
                        full_code="sz000001",
                        code="000001",
                        exchange="sz",
                        name="平安银行",
                        category="a_share",
                        category_reason="test",
                        board="main",
                        board_reason="test",
                        decimal=2,
                        multiple=100,
                        previous_close_price=10.0,
                        volume_ratio_base=1.0,
                    )
                ]
            return []

    client = FakeClient()
    adapter = adapter_for_source_code(
        "tdx",
        options={"client": client, "source_server_count": 1},
    )

    rows = adapter.request(
        "stock_codes_tdx",
        {"scope": "all", "code": "000001.SZ"},
    )

    assert rows[0]["instrument_id"] == "000001.SZ"
    assert rows[0]["symbol"] == "000001"
    assert rows[0]["tdx_code"] == "sz000001"
    assert rows[0]["exchange"] == "SZSE"
    assert rows[0]["name"] == "平安银行"
    assert client.connected is True
    assert client.calls
    assert adapter._options["source_server_count"] == 1
    assert "client" not in adapter._options


def test_source_execution_options_accepts_registered_enricher(tmp_path) -> None:
    def demo_enricher_factory(data_root):
        def enrich(options):
            options["demo_data_root"] = str(data_root)
            options.setdefault("preserved", "yes")

        return enrich

    assert execution_options_for_source(
        {"preserved": "custom"},
        data_root=tmp_path,
        provider_id="axdata.source.demo",
        source_code="demo",
        enrichers={"axdata.source.demo": demo_enricher_factory},
    ) == {
        "preserved": "custom",
        "demo_data_root": str(tmp_path),
    }

    assert execution_options_for_source(
        {"preserved": "custom"},
        data_root=tmp_path,
        provider_id="unknown.provider",
        source_code="demo",
        enrichers={"demo": demo_enricher_factory},
    ) == {"preserved": "custom"}

    assert execution_options_for_source(
        {"preserved": "custom"},
        data_root=tmp_path,
        source_code="demo",
        enrichers={"demo": demo_enricher_factory},
    ) == {
        "preserved": "custom",
        "demo_data_root": str(tmp_path),
    }


def test_legacy_adapter_for_interface_uses_catalog_source_code(monkeypatch) -> None:
    calls = []

    class FakeAdapter:
        source = "fake"

        def supports(self, interface_name):
            return True

        def request(self, interface_name, params):
            return []

    import axdata_core.source_request as source_request

    def fake_adapter_for_source_code(source_code, *, options=None):
        calls.append({"source_code": source_code, "options": options})
        return FakeAdapter()

    monkeypatch.setattr(source_request, "adapter_for_source_code", fake_adapter_for_source_code)

    adapter = source_request.adapter_for_interface(
        "tencent_realtime_snapshot",
        options={"timeout_ms": 1000},
    )

    assert adapter.source == "fake"
    assert calls == [{"source_code": "tencent", "options": {"timeout_ms": 1000}}]


def test_registry_adapter_falls_back_to_legacy_when_route_missing(monkeypatch) -> None:
    class FakeSnapshot:
        providers = {}

    class FakeRegistry:
        def get_interface(self, interface_name):
            raise KeyError(interface_name)

        def snapshot(self):
            return FakeSnapshot()

    class LegacyAdapter:
        source = "legacy"

        def supports(self, interface_name):
            return True

        def request(self, interface_name, params):
            return [{"instrument_id": "000001.SZ"}]

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())
    monkeypatch.setattr(
        source_request,
        "adapter_for_interface",
        lambda interface_name, options=None: LegacyAdapter(),
    )

    adapter = source_request.registry_adapter_for_interface("stock_codes_tdx")

    assert adapter.source == "legacy"


def test_registry_adapter_reflects_plugin_config_disable_without_stale_route(monkeypatch, tmp_path) -> None:
    from axdata_core.plugin_config import disable_provider
    import axdata_core.source_request as source_request

    data_root = tmp_path / "data"
    legacy_calls = []

    def fake_legacy_adapter(interface_name, options=None):
        legacy_calls.append(interface_name)
        raise AssertionError("disabled registry route must not use legacy fallback")

    monkeypatch.setattr(source_request, "adapter_for_interface", fake_legacy_adapter)

    adapter = source_request.registry_adapter_for_interface(
        "tencent_realtime_snapshot",
        data_root=data_root,
    )
    assert adapter.source == "tencent"

    disable_provider("axdata.source.tencent", data_root=data_root)

    with pytest.raises(SourceAdapterNotFound, match="disabled"):
        source_request.registry_adapter_for_interface(
            "tencent_realtime_snapshot",
            data_root=data_root,
        )
    assert legacy_calls == []


def test_unregistered_tdx_suffix_no_longer_routes_to_tdx_adapter(monkeypatch) -> None:
    class FakeSnapshot:
        providers = {}

    class FakeRegistry:
        def get_interface(self, interface_name):
            raise KeyError(interface_name)

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    with pytest.raises(SourceUnavailableError, match=TDX_PLUGIN_REQUIRED_MESSAGE):
        source_request.registry_adapter_for_interface("community_shadow_tdx")


def test_unregistered_tdx_suffix_does_not_load_tdx_runtime() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_errors import SourceUnavailableError\n"
        "import axdata_core.provider_catalog as provider_catalog\n"
        "import axdata_core.source_request as source_request\n"
        "class FakeSnapshot:\n"
        "    providers = {}\n"
        "class FakeRegistry:\n"
        "    def get_interface(self, interface_name):\n"
        "        raise KeyError(interface_name)\n"
        "    def snapshot(self):\n"
        "        return FakeSnapshot()\n"
        "provider_catalog.build_builtin_provider_registry = lambda **_: FakeRegistry()\n"
        "try:\n"
        "    source_request.registry_adapter_for_interface('community_shadow_tdx')\n"
        "except SourceUnavailableError as exc:\n"
        "    print('unavailable=True')\n"
        "    print('message=' + str(exc))\n"
        "else:\n"
        "    print('unavailable=False')\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core._tdx_wire.client',\n"
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

    assert "unavailable=True" in result.stdout
    assert f"message={TDX_PLUGIN_REQUIRED_MESSAGE}" in result.stdout
    assert "loaded=\n" in result.stdout


def test_request_interface_unknown_tdx_suffix_does_not_load_tdx_runtime() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_errors import SourceUnavailableError\n"
        "from axdata_core.source_request import request_interface\n"
        "try:\n"
        "    request_interface('community_shadow_tdx')\n"
        "except SourceUnavailableError as exc:\n"
        "    print('unavailable=True')\n"
        "    print('message=' + str(exc))\n"
        "else:\n"
        "    print('unavailable=False')\n"
        "tracked = [\n"
        "    'axdata_core.adapters.tdx.provider_bridge',\n"
        "    'axdata_core.adapters.tdx.request',\n"
        "    'axdata_core.adapters.tdx_ext.provider_bridge',\n"
        "    'axdata_core.adapters.tdx_ext.request',\n"
        "    'axdata_core._tdx_wire.client',\n"
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

    assert "unavailable=True" in result.stdout
    assert f"message={TDX_PLUGIN_REQUIRED_MESSAGE}" in result.stdout
    assert "loaded=\n" in result.stdout


def test_registry_conflict_interface_does_not_fall_back_to_legacy(monkeypatch) -> None:
    class FakeProvider:
        provider_id = "axdata.source.community"
        status = "conflict"
        error = "Interface name conflict."
        manifest = SimpleNamespace(
            interfaces=(
                InterfaceSpec(
                    name="community_shadow_tdx",
                    display_name_zh="社区同名接口",
                    source_code="community",
                    source_name_zh="社区源",
                    asset_class="stock",
                ),
            )
        )

    class FakeSnapshot:
        providers = {"axdata.source.community": FakeProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            raise KeyError(interface_name)

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    with pytest.raises(SourceAdapterNotFound, match="conflict"):
        source_request.registry_adapter_for_interface("community_shadow_tdx")


def test_registry_unavailable_provider_interface_does_not_fall_back_to_legacy(monkeypatch) -> None:
    class FakeProvider:
        provider_id = "axdata.source.bad"
        status = "incompatible"
        error = "Unsupported plugin_api_version."
        manifest = SimpleNamespace(
            interfaces=(
                InterfaceSpec(
                    name="bad_shadow_tdx",
                    display_name_zh="坏插件接口",
                    source_code="bad",
                    source_name_zh="坏插件",
                    asset_class="stock",
                ),
            )
        )

    class FakeSnapshot:
        providers = {"axdata.source.bad": FakeProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            raise KeyError(interface_name)

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    with pytest.raises(SourceAdapterNotFound, match="incompatible"):
        source_request.registry_adapter_for_interface("bad_shadow_tdx")


def test_external_registry_provider_is_loaded_only_when_called(monkeypatch) -> None:
    calls = []

    class ExternalProviderAdapter:
        def call(self, interface_name, params=None, fields=None, options=None):
            calls.append({"call": interface_name, "params": params})
            return SourceResult(
                data=(
                    {
                        "instrument_id": "000001.SZ",
                        "name": "平安银行",
                    },
                ),
                meta={"loaded": True},
            )

    class ExternalProvider:
        source_code = "external"

        def create_adapter(self, options=None):
            calls.append({"create_options": options})
            return ExternalProviderAdapter()

    class ExternalRegisteredProvider:
        provider_id = "axdata.source.external"
        source_code = "external"
        provider = None

        def load_provider(self):
            calls.append({"load": "entry_point"})
            return ExternalProvider()

    class FakeRoute:
        provider_id = "axdata.source.external"
        interface = InterfaceSpec(
            name="external_snapshot",
            display_name_zh="外部快照",
            source_code="external",
            source_name_zh="外部源",
            asset_class="stock",
            parameters=(
                ParameterSpec(
                    name="code",
                    display_name_zh="股票代码",
                    type="string",
                    required=True,
                ),
            ),
            fields=(
                FieldSpec(name="instrument_id", display_name_zh="证券代码", type="string"),
                FieldSpec(name="name", display_name_zh="名称", type="string"),
            ),
        )

    class FakeSnapshot:
        providers = {"axdata.source.external": ExternalRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "external_snapshot"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    result = source_request.request_interface(
        "external_snapshot",
        params={"code": "000001.SZ"},
        fields=["instrument_id"],
        options={"timeout_ms": 1000},
    )

    assert result.records == [{"instrument_id": "000001.SZ"}]
    assert result.meta["source"] == "external"
    assert result.meta["loaded"] is True
    assert calls == [
        {"load": "entry_point"},
        {"create_options": {"timeout_ms": 1000}},
        {"call": "external_snapshot", "params": {"code": "000001.SZ"}},
    ]


def test_registry_provider_load_failure_is_wrapped_as_adapter_error(monkeypatch) -> None:
    class ExternalRegisteredProvider:
        provider_id = "axdata.source.external"
        source_code = "external"
        provider = None

        def load_provider(self):
            raise RuntimeError("broken import")

    class FakeRoute:
        provider_id = "axdata.source.external"

    class FakeSnapshot:
        providers = {"axdata.source.external": ExternalRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "external_snapshot"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    with pytest.raises(SourceAdapterError, match="Failed to load provider 'axdata.source.external'"):
        source_request.registry_adapter_for_interface("external_snapshot")


def test_registry_provider_none_does_not_fall_back_to_legacy(monkeypatch) -> None:
    class ExternalRegisteredProvider:
        provider_id = "axdata.source.external"
        source_code = "external"
        provider = None

        def load_provider(self):
            return None

    class FakeRoute:
        provider_id = "axdata.source.external"

    class FakeSnapshot:
        providers = {"axdata.source.external": ExternalRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "external_snapshot"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())
    monkeypatch.setattr(
        source_request,
        "adapter_for_interface",
        lambda interface_name, options=None: (_ for _ in ()).throw(AssertionError("legacy fallback used")),
    )

    with pytest.raises(SourceAdapterError, match="could not be loaded"):
        source_request.registry_adapter_for_interface("external_snapshot")


def test_registry_provider_create_adapter_failure_is_wrapped_as_adapter_error(monkeypatch) -> None:
    class ExternalProvider:
        def create_adapter(self, options=None):
            raise RuntimeError("adapter boom")

    class ExternalRegisteredProvider:
        provider_id = "axdata.source.external"
        source_code = "external"

        def load_provider(self):
            return ExternalProvider()

    class FakeRoute:
        provider_id = "axdata.source.external"

    class FakeSnapshot:
        providers = {"axdata.source.external": ExternalRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "external_snapshot"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    with pytest.raises(SourceAdapterError, match="failed to create adapter"):
        source_request.registry_adapter_for_interface("external_snapshot")


def test_registry_provider_create_adapter_preserves_source_request_error(monkeypatch) -> None:
    class ExternalProvider:
        def create_adapter(self, options=None):
            raise SourceUnavailableError("source offline")

    class ExternalRegisteredProvider:
        provider_id = "axdata.source.external"
        source_code = "external"

        def load_provider(self):
            return ExternalProvider()

    class FakeRoute:
        provider_id = "axdata.source.external"

    class FakeSnapshot:
        providers = {"axdata.source.external": ExternalRegisteredProvider()}

    class FakeRegistry:
        def get_interface(self, interface_name):
            assert interface_name == "external_snapshot"
            return FakeRoute()

        def snapshot(self):
            return FakeSnapshot()

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_: FakeRegistry())

    with pytest.raises(SourceUnavailableError, match="source offline"):
        source_request.registry_adapter_for_interface("external_snapshot")
