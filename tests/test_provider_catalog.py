from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from axdata_core.plugin_config import PluginConfig, disable_provider, enable_provider
from axdata_core.plugin_config import remove_provider
from axdata_core.provider_catalog import (
    build_builtin_provider_registry,
    list_registry_collector_dicts,
    list_registry_interface_dicts,
)
from axdata_core.collector_registry import CollectorRegistry
from axdata_core.provider_registry import ProviderRegistry
from axdata_core.source_errors import SourceAdapterNotFound, SourceUnavailableError
from axdata_core.tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE
from axdata_core.sources import list_request_interfaces
from axdata_core.plugins import (
    CollectorSpec,
    InterfaceSpec,
    PluginInfo,
    PluginTrustLevel,
    ProviderInfo,
    ProviderManifest,
    RequiredConfig,
)
from tests.tdx_plugin_helpers import (
    TDX_BASE_COLLECTOR_DATASET_IDS,
    TDX_COLLECTOR_PLUGIN_ID,
    TDX_COLLECTOR_RUNNER_ENTRY,
    TDX_EXT_PROVIDER_ID,
    TDX_LEGACY_COLLECTOR_NAMES,
    TDX_PROVIDER_ID,
    build_registry_with_local_tdx_plugins,
    ensure_local_tdx_plugin_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ensure_local_tdx_plugin_paths()
BUILTIN_GENERIC_INTERFACE_NAMES = {
    interface.name
    for interface in list_request_interfaces()
}
BUILTIN_PROVIDER_IDS = {
    f"axdata.source.{interface.source_code}"
    for interface in list_request_interfaces()
}
BUILTIN_SOURCE_INTERFACE_COUNT = len(BUILTIN_GENERIC_INTERFACE_NAMES)
TDX_SOURCE_INTERFACE_COUNT = 90
TDX_EXT_SOURCE_INTERFACE_COUNT = 31
DEFAULT_REGISTRY_INTERFACE_COUNT = (
    BUILTIN_SOURCE_INTERFACE_COUNT + TDX_SOURCE_INTERFACE_COUNT + TDX_EXT_SOURCE_INTERFACE_COUNT
)
BUILTIN_GENERIC_COLLECTABLE_INTERFACE_NAMES = {
    "stock_trade_calendar_exchange",
    "stock_historical_list_exchange",
    "stock_basic_info_exchange",
}
EXCHANGE_COLLECTOR_DATASET_IDS = {
    "exchange.stock_trade_calendar_exchange.snapshot": "exchange.trade_calendar",
    "exchange.stock_historical_list_exchange.snapshot": "exchange.stock_historical_list",
    "exchange.stock_basic_info_exchange.snapshot": "exchange.stock_basic_info",
}


@pytest.fixture
def local_tdx_plugin_registry(monkeypatch):
    import axdata_core.provider_catalog as provider_catalog

    base_builder = provider_catalog.build_builtin_provider_registry

    def build_registry(**kwargs):
        return build_registry_with_local_tdx_plugins(
            base_builder=base_builder,
            **kwargs,
        )

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", build_registry)
    return build_registry


def test_provider_catalog_import_does_not_eager_load_builtins_or_legacy_catalog() -> None:
    code = (
        "import sys\n"
        "import axdata_core.provider_catalog\n"
        "print('plugin_config=' + str('axdata_core.plugin_config' in sys.modules))\n"
        "print('plugins=' + str('axdata_core.plugins' in sys.modules))\n"
        "print('provider_registry=' + str('axdata_core.provider_registry' in sys.modules))\n"
        "print('builtin=' + str('axdata_core.builtin_providers' in sys.modules))\n"
        "print('sources_catalog=' + str('axdata_core.sources.catalog' in sys.modules))\n"
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

    assert "plugin_config=False" in result.stdout
    assert "plugins=False" in result.stdout
    assert "provider_registry=False" in result.stdout
    assert "builtin=False" in result.stdout
    assert "sources_catalog=False" in result.stdout
    assert "tdx_request=False" in result.stdout


def test_legacy_source_catalog_import_does_not_load_tdx_runtime() -> None:
    code = (
        "import sys\n"
        "import axdata_core.sources.catalog as catalog\n"
        "print('interfaces=' + str(len(catalog.INTERFACES)))\n"
        "tracked = [\n"
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

    assert f"interfaces={BUILTIN_SOURCE_INTERFACE_COUNT}" in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_registry_catalog_listing_does_not_load_tdx_runtime(tmp_path) -> None:
    code = (
        "import sys\n"
        "from axdata_core.provider_catalog import list_registry_interface_dicts\n"
        "entries = list_registry_interface_dicts()\n"
        "print('interfaces=' + str(len(entries)))\n"
        "tracked = [\n"
        "    'axdata_core.sources.catalog',\n"
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
            "AXDATA_DATA_DIR": str(tmp_path / "data"),
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert f"interfaces={DEFAULT_REGISTRY_INTERFACE_COUNT}" in result.stdout
    assert "axdata_core.sources.catalog" in result.stdout
    assert "axdata_core.sources.tdx.catalog" not in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_root_registry_catalog_export_does_not_load_tdx_runtime(tmp_path) -> None:
    code = (
        "import sys\n"
        "import axdata_core\n"
        "print('provider_catalog_before=' + str('axdata_core.provider_catalog' in sys.modules))\n"
        "entries = axdata_core.list_registry_interface_dicts()\n"
        "print('interfaces=' + str(len(entries)))\n"
        "tracked = [\n"
        "    'axdata_core.provider_catalog',\n"
        "    'axdata_core.sources.catalog',\n"
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
            "AXDATA_DATA_DIR": str(tmp_path / "data"),
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "provider_catalog_before=False" in result.stdout
    assert f"interfaces={DEFAULT_REGISTRY_INTERFACE_COUNT}" in result.stdout
    assert "axdata_core.provider_catalog" in result.stdout
    assert "axdata_core.sources.catalog" in result.stdout
    assert "axdata_core.sources.tdx.catalog" not in result.stdout
    assert "axdata_core.tdx_f10_catalog" not in result.stdout
    assert "axdata_core.tdx_f10_specs" not in result.stdout
    assert "axdata_core.adapters.tdx.request" not in result.stdout
    assert "axdata_core.adapters.tdx.f10_request" not in result.stdout
    assert "axdata_core.adapters.tdx.downloader" not in result.stdout
    assert "axdata_core.source_request" not in result.stdout


def test_registry_catalog_preserves_plugin_entries_and_adds_provider_metadata(local_tdx_plugin_registry) -> None:
    entries = {entry["name"]: entry for entry in list_registry_interface_dicts()}

    stock_codes = entries["stock_codes_tdx"]
    fx_codes = entries["fx_codes_tdx"]

    assert stock_codes["display_name_zh"] == "最新股票列表"
    assert stock_codes["source_code"] == "tdx"
    assert stock_codes["provider_id"] == TDX_PROVIDER_ID
    assert stock_codes["asset_class"] == "stock"
    assert stock_codes["effective_trust_level"] == "official"
    assert stock_codes["plugin_status"] == "enabled"
    assert stock_codes["enabled"] is True
    assert stock_codes["built_in"] is True
    assert stock_codes["request_mode"] == "source_request"
    assert stock_codes["menu_path"] == ["通达信", "股票数据", "基础数据"]
    assert stock_codes["persisted"] is False if "persisted" in stock_codes else True

    capital_changes = entries["stock_capital_changes_tdx"]
    category_reference = capital_changes["reference_sections"][0]
    assert category_reference["title"] == "类别码参考"
    assert category_reference["rows"][0] == ["1", "除权除息", "直接参与", "现金分红", "配股价", "送转股", "配股"]
    expected_reference_titles = {
        "stock_realtime_rank_tdx": ["榜单范围对照", "排序字段对照", "过滤条件对照"],
        "stock_shortline_indicators_tdx": ["核心计算口径", "数据来源"],
        "stock_limit_ladder_tdx": ["涨停状态", "题材排序"],
        "stock_theme_strength_rank_tdx": ["排序口径"],
        "stock_daily_price_limit_tdx": ["价格来源"],
        "stock_finance_profile_tdx": ["映射规则", "单位说明"],
        "stock_finance_summary_tdx": ["单位说明"],
        "stock_balance_summary_tdx": ["单位说明"],
        "stock_profit_cashflow_summary_tdx": ["单位说明"],
        "stock_share_capital_tdx": ["单位说明"],
    }
    for interface_name, titles in expected_reference_titles.items():
        assert [section["title"] for section in entries[interface_name]["reference_sections"]] == titles

    realtime_rank_references = entries["stock_realtime_rank_tdx"]["reference_sections"]
    assert len(realtime_rank_references[1]["rows"]) == 28
    assert realtime_rank_references[2]["rows"][2] == ["排除 ST", "exclude_st", "从结果中排除 ST 股票"]

    third_batch = entries["index_intraday_history_tdx"]
    assert third_batch["provider_id"] == TDX_PROVIDER_ID
    assert third_batch["plugin_status"] == "enabled"
    assert third_batch["enabled"] is True
    assert third_batch["request_mode"] == "source_request"
    assert third_batch["collection"] == {"supported": False, "default_profile": None}
    assert third_batch["menu_path"] == ["通达信", "指数数据", "行情数据"]

    assert fx_codes["provider_id"] == TDX_EXT_PROVIDER_ID
    assert fx_codes["asset_class"] == "fx"
    assert fx_codes["source_name_zh"] == "通达信扩展行情"
    assert fx_codes["menu_path"] == ["通达信扩展行情", "外汇数据"]


def test_repo_preinstalled_tdx_ext_defaults_enabled_and_can_be_disabled(tmp_path) -> None:
    data_root = tmp_path / "data"

    enabled_registry = build_builtin_provider_registry(data_root=data_root)
    enabled_snapshot = enabled_registry.snapshot()
    assert TDX_EXT_PROVIDER_ID in enabled_snapshot.providers
    assert enabled_snapshot.providers[TDX_EXT_PROVIDER_ID].status == "enabled"
    assert enabled_snapshot.interfaces["fx_codes_tdx"].provider_id == TDX_EXT_PROVIDER_ID
    enabled_entries = {entry["name"]: entry for entry in list_registry_interface_dicts(data_root=data_root)}
    assert "fx_codes_tdx" in enabled_entries
    assert enabled_entries["fx_codes_tdx"]["source_name_zh"] == "通达信扩展行情"

    disable_provider(TDX_EXT_PROVIDER_ID, data_root=data_root)
    disabled_registry = build_builtin_provider_registry(data_root=data_root)
    disabled_snapshot = disabled_registry.snapshot()
    assert disabled_snapshot.providers[TDX_EXT_PROVIDER_ID].status == "disabled"
    disabled_entries = {entry["name"]: entry for entry in list_registry_interface_dicts(data_root=data_root)}
    assert "fx_codes_tdx" not in disabled_entries


def test_builtin_provider_registry_can_resolve_current_catalog() -> None:
    config = PluginConfig()
    registry = build_builtin_provider_registry(plugin_config=config, discover_entry_points=False)
    snapshot = registry.snapshot()

    built_in_provider_ids = {
        provider_id
        for provider_id, provider in snapshot.providers.items()
        if provider.built_in
    }
    assert built_in_provider_ids == BUILTIN_PROVIDER_IDS
    assert len(snapshot.interfaces) == len(list_request_interfaces())
    assert snapshot.interfaces["cninfo_announcements"].provider_id == "axdata.source.cninfo"
    assert snapshot.interfaces["tencent_realtime_snapshot"].provider_id == "axdata.source.tencent"
    assert snapshot.interfaces["cninfo_announcements"].interface.summary_zh == "按股票和日期范围临时获取巨潮公告元信息。"
    assert snapshot.interfaces["stock_trade_calendar_exchange"].interface.params_note_zh == "日期优先级：start_date/end_date > year > 当前自然年。"
    assert snapshot.collectors == {}

    entries = {entry["name"]: entry for entry in list_registry_interface_dicts(plugin_config=config)}
    assert entries["cninfo_announcements"]["summary_zh"] == "按股票和日期范围临时获取巨潮公告元信息。"
    assert entries["cninfo_announcements"]["description_zh"] == "这个接口返回公告元信息和 PDF 下载地址。"
    assert entries["cninfo_announcements"]["description"] == entries["cninfo_announcements"]["description_zh"]
    assert 'client.call("cninfo_announcements"' in entries["cninfo_announcements"]["params_example_zh"]
    assert "sina_financial_statement" not in entries
    assert entries["stock_financial_report_sina"]["source_name_zh"] == "新浪财经"
    for interface_name in BUILTIN_GENERIC_INTERFACE_NAMES:
        entry = entries[interface_name]
        is_collectable = interface_name in BUILTIN_GENERIC_COLLECTABLE_INTERFACE_NAMES
        expected_profile = (
            f"{interface_name}.snapshot"
            if is_collectable
            else None
        )
        assert entry["collection"] == {
            "supported": is_collectable,
            "default_profile": expected_profile,
        }
        assert entry["collector_count"] == 0


def test_builtin_registry_collector_catalog_lists_first_batch() -> None:
    rows = {row["collector_name"]: row for row in list_registry_collector_dicts(plugin_config=PluginConfig())}

    assert set(rows) == set(TDX_BASE_COLLECTOR_DATASET_IDS)
    assert not (set(EXCHANGE_COLLECTOR_DATASET_IDS) & set(rows))

    stock_codes = rows["tdx.stock_codes_tdx.snapshot"]
    assert stock_codes["provider_id"] == TDX_COLLECTOR_PLUGIN_ID
    assert stock_codes["legacy_provider_id"] is None
    assert stock_codes["collector_plugin_id"] == TDX_COLLECTOR_PLUGIN_ID
    assert stock_codes["dataset_id"] == "tdx.stock_codes"
    assert stock_codes["interfaces"] == []
    assert stock_codes["required_interfaces"] == []
    assert stock_codes["downloader_profile"] is None
    assert stock_codes["runner_entry"] == TDX_COLLECTOR_RUNNER_ENTRY
    assert stock_codes["resource_group"] == "tdx.quote"
    assert stock_codes["default_params"] == {"scope": "all"}
    assert stock_codes["output"]["layer"] == "snapshot"
    assert stock_codes["quality"]["required_columns"] == ["instrument_id"]
    assert stock_codes["is_legacy"] is False
    assert stock_codes["legacy_source"] is None
    assert stock_codes["built_in"] is True
    assert stock_codes["plugin_status"] == "enabled"

    for collector_id, dataset_id in TDX_BASE_COLLECTOR_DATASET_IDS.items():
        row = rows[collector_id]
        assert row["collector_id"] == collector_id
        assert row["collector_plugin_id"] == TDX_COLLECTOR_PLUGIN_ID
        assert row["dataset_id"] == dataset_id
        assert row["runner_entry"] == TDX_COLLECTOR_RUNNER_ENTRY
        assert row["is_legacy"] is False


def test_tdx_enabled_collector_catalog_splits_independent_and_legacy_collectors() -> None:
    config = PluginConfig(enabled_provider_ids=(TDX_PROVIDER_ID,))
    rows = {row["collector_name"]: row for row in list_registry_collector_dicts(plugin_config=config)}

    assert set(rows) == set(TDX_BASE_COLLECTOR_DATASET_IDS)
    assert len(rows) == len(TDX_BASE_COLLECTOR_DATASET_IDS)

    for collector_id, dataset_id in TDX_BASE_COLLECTOR_DATASET_IDS.items():
        row = rows[collector_id]
        assert row["collector_plugin_id"] == TDX_COLLECTOR_PLUGIN_ID
        assert row["provider_id"] == TDX_COLLECTOR_PLUGIN_ID
        assert row["dataset_id"] == dataset_id
        assert row["runner_entry"] == TDX_COLLECTOR_RUNNER_ENTRY
        assert row["downloader_profile"] is None
        assert row["interfaces"] == []
        assert row["required_interfaces"] == []
        assert row["is_legacy"] is False

    daily = rows["tdx.stock_kline_daily_tdx.snapshot"]
    assert daily["collector_plugin_id"] == TDX_COLLECTOR_PLUGIN_ID
    assert daily["provider_id"] == TDX_COLLECTOR_PLUGIN_ID
    assert daily["dataset_id"] == "tdx.stock_daily"
    assert daily["runner_entry"] == TDX_COLLECTOR_RUNNER_ENTRY
    assert daily["downloader_profile"] is None
    assert daily["interfaces"] == []
    assert daily["required_interfaces"] == []
    assert daily["is_legacy"] is False


def test_tdx_base_collectors_survive_disabled_source_provider() -> None:
    config = PluginConfig(disabled_provider_ids=(TDX_PROVIDER_ID,))
    rows = {row["collector_name"]: row for row in list_registry_collector_dicts(plugin_config=config)}

    assert set(TDX_BASE_COLLECTOR_DATASET_IDS) <= set(rows)
    assert rows["tdx.stock_codes_tdx.snapshot"]["collector_plugin_id"] == TDX_COLLECTOR_PLUGIN_ID
    assert rows["tdx.stock_codes_tdx.snapshot"]["is_legacy"] is False
    assert rows["tdx.stock_kline_daily_tdx.snapshot"]["collector_plugin_id"] == TDX_COLLECTOR_PLUGIN_ID
    assert rows["tdx.stock_kline_daily_tdx.snapshot"]["is_legacy"] is False


def test_tdx_base_collectors_can_be_disabled_independently_from_source_provider() -> None:
    config = PluginConfig(
        enabled_provider_ids=(TDX_PROVIDER_ID,),
        disabled_provider_ids=(TDX_COLLECTOR_PLUGIN_ID,),
    )
    rows = {row["collector_name"]: row for row in list_registry_collector_dicts(plugin_config=config)}

    assert not (set(TDX_BASE_COLLECTOR_DATASET_IDS) & set(rows))
    assert not (TDX_LEGACY_COLLECTOR_NAMES & set(rows))


def test_exchange_source_provider_disabled_does_not_register_collectors(tmp_path) -> None:
    config = PluginConfig(disabled_provider_ids=("axdata.source.exchange",))
    interface_rows = {row["name"]: row for row in list_registry_interface_dicts(plugin_config=config)}
    collector_rows = {row["collector_name"]: row for row in list_registry_collector_dicts(plugin_config=config)}
    registry = build_builtin_provider_registry(plugin_config=config, data_root=tmp_path / "data")

    assert "stock_trade_calendar_exchange" in interface_rows
    assert interface_rows["stock_trade_calendar_exchange"]["plugin_status"] == "disabled"
    assert "stock_trade_calendar_exchange" not in registry.snapshot().interfaces
    assert not (set(EXCHANGE_COLLECTOR_DATASET_IDS) & set(collector_rows))


def test_exchange_source_provider_removed_does_not_register_collectors(tmp_path) -> None:
    data_root = tmp_path / "data"

    remove_provider("axdata.source.exchange", data_root=data_root)
    interface_rows = {row["name"]: row for row in list_registry_interface_dicts(data_root=data_root)}
    collector_rows = {row["collector_name"]: row for row in list_registry_collector_dicts(data_root=data_root)}
    registry = build_builtin_provider_registry(data_root=data_root)

    assert "stock_trade_calendar_exchange" not in interface_rows
    assert "stock_trade_calendar_exchange" not in registry.snapshot().interfaces
    assert not (set(EXCHANGE_COLLECTOR_DATASET_IDS) & set(collector_rows))


def test_plugin_config_can_disable_tdx_plugin_from_catalog_and_routes(
    monkeypatch,
    local_tdx_plugin_registry,
) -> None:
    config = PluginConfig(disabled_provider_ids=(TDX_PROVIDER_ID,))
    entries = {entry["name"]: entry for entry in list_registry_interface_dicts(plugin_config=config)}
    registry = local_tdx_plugin_registry(plugin_config=config)

    assert "stock_codes_tdx" in entries
    assert "stock_trade_calendar_exchange" in entries
    assert entries["stock_codes_tdx"]["plugin_status"] == "disabled"
    assert entries["stock_codes_tdx"]["enabled"] is False
    assert entries["stock_codes_tdx"]["action_command"] == f"axdata plugin enable {TDX_PROVIDER_ID}"
    assert "stock_codes_tdx" not in registry.snapshot().interfaces
    assert registry.snapshot().providers[TDX_PROVIDER_ID].enabled is False

    import axdata_core.provider_catalog as provider_catalog
    import axdata_core.source_request as source_request

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_kwargs: registry)

    with pytest.raises(SourceUnavailableError, match=TDX_PLUGIN_REQUIRED_MESSAGE):
        source_request.registry_adapter_for_interface("stock_codes_tdx")


def test_build_builtin_provider_registry_reflects_plugin_config_changes(tmp_path) -> None:
    data_root = tmp_path / "data"

    first = build_builtin_provider_registry(data_root=data_root)
    assert first.snapshot().providers["axdata.source.tencent"].enabled is True
    assert "tencent_realtime_snapshot" in first.snapshot().interfaces

    disable_provider("axdata.source.tencent", data_root=data_root)

    second = build_builtin_provider_registry(data_root=data_root)
    assert second.snapshot().providers["axdata.source.tencent"].enabled is False
    assert "tencent_realtime_snapshot" not in second.snapshot().interfaces


def test_registry_catalog_includes_required_config_as_display_metadata(monkeypatch) -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.token_demo",
            source_code="token_demo",
            source_name_zh="凭据示例",
            version="0.1.0",
            declared_trust_level=PluginTrustLevel.COMMUNITY.value,
        ),
        interfaces=(
            InterfaceSpec(
                name="token_demo_snapshot",
                display_name_zh="凭据示例快照",
                source_code="token_demo",
                source_name_zh="凭据示例",
                asset_class="stock",
            ),
        ),
        required_config=(
            RequiredConfig(
                name="TOKEN_DEMO_KEY",
                kind="env",
                required=True,
                description="用户自己的示例源凭据。",
            ),
        ),
    )
    config = PluginConfig(enabled_provider_ids=("axdata.source.token_demo",))

    registry = build_builtin_provider_registry(plugin_config=config, discover_entry_points=False)
    registry.register_manifest(manifest, enabled=True)
    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )
    entries = {
        entry["name"]: entry
        for entry in list_registry_interface_dicts(plugin_config=config)
    }

    assert entries["token_demo_snapshot"]["required_config"] == [
        {
            "name": "TOKEN_DEMO_KEY",
            "kind": "env",
            "required": True,
            "description": "用户自己的示例源凭据。",
        }
    ]


def test_registry_collector_catalog_lists_enabled_collector_only_plugin(monkeypatch) -> None:
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
                required_interfaces=("stock_codes_tdx",),
                output={"layer": "raw"},
            ),
        ),
    )
    registry = ProviderRegistry(enabled_provider_ids={"axdata.plugin.close_refresh"})
    registry.register_manifest(manifest)

    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )

    rows = list_registry_collector_dicts()

    assert len(rows) == 1
    assert rows[0]["name"] == "close.refresh.daily"
    assert rows[0]["collector_name"] == "close.refresh.daily"
    assert rows[0]["display_name_zh"] == "收盘刷新"
    assert rows[0]["provider_id"] == "axdata.plugin.close_refresh"
    assert rows[0]["source_code"] == "plugin"
    assert rows[0]["source_name_zh"] == "收盘刷新"
    assert rows[0]["plugin_status"] == "enabled"
    assert rows[0]["effective_trust_level"] == "community"
    assert rows[0]["interfaces"] == ["stock_codes_tdx"]
    assert rows[0]["downloader_profile"] == "tdx.stock_codes.latest"
    assert rows[0]["resource_group"] == "tdx.quote"
    assert rows[0]["default_schedule"] == {"frequency": "daily", "time": "18:05"}
    assert rows[0]["default_params"] == {"scope": "all"}
    assert rows[0]["required_interfaces"] == ["stock_codes_tdx"]
    assert rows[0]["output"] == {"layer": "raw"}
    assert rows[0]["collector_id"] == "close.refresh.daily"
    assert rows[0]["collector_plugin_id"] == "axdata.plugin.close_refresh"
    assert rows[0]["dataset_id"] is None
    assert rows[0]["runner_entry"] is None
    assert rows[0]["legacy_source"] is None
    assert rows[0]["is_legacy"] is True


def test_registry_collector_catalog_projects_independent_collector_fields(monkeypatch) -> None:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.collector.close_refresh",
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
                collector_plugin_id="axdata.collector.close_refresh",
                dataset_id="demo.stock_codes",
                asset_class="stock",
                category="snapshot",
                resource_group="demo.http",
                runner_entry="axdata_collector_close.runner:run",
                config_schema={"params": [{"name": "scope", "type": "string"}]},
                default_schedule={"kind": "manual"},
                default_params={"scope": "all"},
                output={"layer": "snapshot", "formats": ["parquet"]},
                quality={"required_columns": ["instrument_id"]},
                lifecycle_status="experimental",
            ),
        ),
    )
    registry = ProviderRegistry(enabled_provider_ids={"axdata.collector.close_refresh"})
    registry.register_manifest(manifest)

    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )

    rows = list_registry_collector_dicts()

    assert len(rows) == 1
    assert rows[0]["name"] == "close.refresh.daily"
    assert rows[0]["collector_id"] == "close.refresh.daily"
    assert rows[0]["collector_plugin_id"] == "axdata.collector.close_refresh"
    assert rows[0]["dataset_id"] == "demo.stock_codes"
    assert rows[0]["asset_class"] == "stock"
    assert rows[0]["category"] == "snapshot"
    assert rows[0]["runner_entry"] == "axdata_collector_close.runner:run"
    assert rows[0]["collector_config_schema"] == {"params": [{"name": "scope", "type": "string"}]}
    assert rows[0]["config_schema"] == {"required_config": []}
    assert rows[0]["quality"] == {"required_columns": ["instrument_id"]}
    assert rows[0]["lifecycle_status"] == "experimental"
    assert rows[0]["legacy_source"] is None
    assert rows[0]["is_legacy"] is False


def test_registry_collector_catalog_omits_disabled_collector_plugin(monkeypatch) -> None:
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
                interfaces=("stock_codes_tdx",),
                resource_group="tdx.quote",
            ),
        ),
    )
    registry = ProviderRegistry()
    registry.register_manifest(manifest)

    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )

    assert list_registry_collector_dicts() == ()


def test_collector_registry_imports_legacy_provider_collectors_with_marker() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.legacy_demo",
            source_code="legacy_demo",
            source_name_zh="旧式示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="legacy_demo_snapshot",
                display_name_zh="旧式示例",
                source_code="legacy_demo",
                source_name_zh="旧式示例",
                asset_class="stock",
            ),
        ),
        collectors=(
            CollectorSpec(
                name="legacy.demo.snapshot",
                display_name_zh="旧式示例采集",
                interfaces=("legacy_demo_snapshot",),
                resource_group="legacy.http",
            ),
        ),
    )
    provider_registry = ProviderRegistry(enabled_provider_ids={"axdata.source.legacy_demo"})
    provider_registry.register_manifest(manifest)

    collector_registry = CollectorRegistry.from_provider_registry(provider_registry)
    snapshot = collector_registry.snapshot()
    route = snapshot.collectors["legacy.demo.snapshot"]

    assert route.provider_id == "axdata.source.legacy_demo"
    assert route.collector_plugin_id == "axdata.source.legacy_demo"
    assert route.is_legacy is True
    assert route.legacy_source == "provider_manifest"
    assert route.collector.legacy_source == "provider_manifest"


def test_collector_registry_omits_disabled_provider_manifest_collectors() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.disabled_demo",
            source_code="disabled_demo",
            source_name_zh="禁用示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="disabled_demo_snapshot",
                display_name_zh="禁用示例",
                source_code="disabled_demo",
                source_name_zh="禁用示例",
                asset_class="stock",
            ),
        ),
        collectors=(
            CollectorSpec(
                name="disabled.demo.snapshot",
                display_name_zh="禁用示例采集",
                interfaces=("disabled_demo_snapshot",),
                resource_group="disabled.http",
            ),
        ),
    )
    provider_registry = ProviderRegistry()
    provider_registry.register_manifest(manifest)

    collector_registry = CollectorRegistry.from_provider_registry(provider_registry)

    assert collector_registry.snapshot().collectors == {}


def test_collector_registry_does_not_mark_provider_independent_collectors_as_legacy() -> None:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.plugin.mixed_demo",
            name_zh="混合示例",
            version="0.1.0",
        ),
        provider=ProviderInfo(
            provider_id="axdata.source.mixed_demo",
            source_code="mixed_demo",
            source_name_zh="混合示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="mixed_demo_snapshot",
                display_name_zh="混合示例",
                source_code="mixed_demo",
                source_name_zh="混合示例",
                asset_class="stock",
            ),
        ),
        collectors=(
            CollectorSpec(
                name="mixed.demo.snapshot",
                display_name_zh="混合示例采集",
                collector_plugin_id="axdata.plugin.mixed_demo",
                dataset_id="mixed.demo",
                asset_class="stock",
                category="snapshot",
                runner_entry="axdata_mixed_demo.runner:run",
                resource_group="mixed.http",
                output={"layer": "snapshot"},
                quality={"required_columns": ["instrument_id"]},
            ),
        ),
    )
    provider_registry = ProviderRegistry(enabled_provider_ids={"axdata.source.mixed_demo"})
    provider_registry.register_manifest(manifest)

    route = CollectorRegistry.from_provider_registry(provider_registry).snapshot().collectors[
        "mixed.demo.snapshot"
    ]

    assert route.provider_id is None
    assert route.collector_plugin_id == "axdata.plugin.mixed_demo"
    assert route.is_legacy is False
    assert route.legacy_source is None
