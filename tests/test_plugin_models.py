from __future__ import annotations

import re

import pytest

from axdata_core.plugins import (
    MANIFEST_VERSION,
    PLUGIN_API_VERSION,
    AssetClass,
    CollectorSpec,
    ConfigSchema,
    DependencySpec,
    DownloaderMode,
    DownloaderProfile,
    FieldSpec,
    InterfaceCollectionSpec,
    InterfaceSpec,
    ManifestError,
    ParameterSpec,
    PluginInfo,
    PluginTrustLevel,
    ProviderInfo,
    ProviderManifest,
    ReferenceSectionSpec,
    RequiredConfig,
    RequestExample,
    SourceResult,
    manifest_from_provider,
    validate_manifest,
)


def _sample_interface(
    name: str = "fx_codes_tdx",
    *,
    source_code: str = "tdx",
    source_name_zh: str | None = None,
    default_profile: str | None = None,
) -> InterfaceSpec:
    source_name = source_name_zh or ("通达信" if source_code == "tdx" else "示例")
    return InterfaceSpec(
        name=name,
        display_name_zh="外汇品种列表",
        source_code=source_code,
        source_name_zh=source_name,
        category="拓展行情/外汇",
        menu_path=("通达信", "拓展行情", "外汇"),
        asset_class=AssetClass.FX.value,
        collection=InterfaceCollectionSpec(
            supported=default_profile is not None,
            default_profile=default_profile,
        ),
        parameters=(
            ParameterSpec(
                name="code",
                display_name_zh="品种代码",
                type="string",
                multiple=True,
                description="不填表示全量。",
            ),
        ),
        fields=(
            FieldSpec(
                name="instrument_id",
                display_name_zh="品种代码",
                type="string",
                required=True,
            ),
        ),
        examples=(
            RequestExample(
                title="按代码查询",
                request={
                    "interface_name": name,
                    "params": {"code": ["USDCNY.FX"]},
                },
                response={
                    "data": [{"instrument_id": "USDCNY.FX"}],
                    "schema": [{"name": "instrument_id", "type": "string"}],
                    "meta": {"count": 1},
                },
            ),
        ),
        reference_sections=(
            ReferenceSectionSpec(
                id="fx_reference",
                title="外汇说明",
                note="插件提供的静态说明表。",
                columns=("字段", "说明"),
                rows=(("instrument_id", "统一代码"),),
            ),
        ),
        summary_zh="查询外汇品种列表。",
        description_zh="返回插件提供的外汇品种静态示例。",
        params_note_zh="code 可传单个或多个统一代码。",
        params_example_zh='client.call("fx_codes_tdx", code=["USDCNY.FX"])',
    )


def test_provider_manifest_round_trips_with_stable_keys() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.tdx",
            source_code="tdx",
            source_name_zh="通达信",
            version="0.1.0",
            declared_trust_level=PluginTrustLevel.OFFICIAL.value,
            license="Apache-2.0",
        ),
        interfaces=(_sample_interface(default_profile="tdx.fx_codes.latest"),),
        downloaders=(
            DownloaderProfile(
                name="tdx.fx_codes.latest",
                interface_name="fx_codes_tdx",
                display_name_zh="外汇品种列表采集",
                resource_group="tdx.ext",
                mode=DownloaderMode.SNAPSHOT.value,
                default_options={"formats": ["parquet"]},
                default_limits={"max_active_jobs": 1, "max_connections_total": 4},
            ),
        ),
        required_config=(
            RequiredConfig(
                name="TUSHARE_TOKEN",
                kind="env",
                required=True,
                description="仅展示，不由 AxData 托管。",
            ),
        ),
        resources={"samples": []},
        build={"generated_at": "2026-06-22T12:00:00Z"},
    )

    data = manifest.to_dict()

    assert list(data) == [
        "manifest_version",
        "plugin_api_version",
        "plugin",
        "provider",
        "interfaces",
        "downloaders",
        "collectors",
        "dependencies",
        "config_schema",
        "required_config",
        "resources",
        "build",
    ]
    assert data["manifest_version"] == MANIFEST_VERSION
    assert data["plugin_api_version"] == PLUGIN_API_VERSION
    assert data["interfaces"][0]["asset_class"] == "fx"
    assert data["interfaces"][0]["reference_sections"][0]["title"] == "外汇说明"
    assert data["interfaces"][0]["summary_zh"] == "查询外汇品种列表。"
    assert data["interfaces"][0]["params_note_zh"] == "code 可传单个或多个统一代码。"
    assert data["required_config"][0]["kind"] == "env"

    parsed = ProviderManifest.from_dict(data)

    assert parsed == manifest
    assert parsed.interfaces[0].reference_sections[0].rows == (("instrument_id", "统一代码"),)
    assert parsed.interfaces[0].description_zh == "返回插件提供的外汇品种静态示例。"
    assert parsed.interfaces[0].params_example_zh == 'client.call("fx_codes_tdx", code=["USDCNY.FX"])'
    validate_manifest(parsed)


def test_v2_manifest_round_trips_collectors_dependencies_and_config_schema() -> None:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.plugin.demo",
            name_zh="示例插件",
            version="0.1.0",
            description="Provider + Collector 示例。",
        ),
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(
            _sample_interface(
                "demo_snapshot",
                source_code="demo",
                default_profile="demo.snapshot.latest",
            ),
        ),
        downloaders=(
            DownloaderProfile(
                name="demo.snapshot.latest",
                interface_name="demo_snapshot",
                display_name_zh="示例快照采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
        ),
        collectors=(
            CollectorSpec(
                name="demo.snapshot.close",
                display_name_zh="示例收盘采集",
                interfaces=("demo_snapshot",),
                downloader_profile="demo.snapshot.latest",
                resource_group="demo.http",
                default_params={"scope": "all"},
                required_interfaces=("stock_trade_calendar_exchange",),
                output={"layer": "raw", "formats": ["parquet"]},
            ),
        ),
        dependencies=(
            DependencySpec(
                name="beautifulsoup4",
                version_spec=">=4.12",
                optional=False,
                source="pypi",
                wheel="wheels/beautifulsoup4-4.12.3-py3-none-any.whl",
                description="解析 HTML。",
            ),
        ),
        config_schema=ConfigSchema(
            required_config=(
                RequiredConfig(
                    name="DEMO_TOKEN",
                    kind="env",
                    required=False,
                    description="仅展示。",
                ),
            )
        ),
    )

    data = manifest.to_dict()
    parsed = ProviderManifest.from_dict(data)

    assert data["plugin"]["plugin_id"] == "axdata.plugin.demo"
    assert data["collectors"][0]["name"] == "demo.snapshot.close"
    assert data["dependencies"][0]["name"] == "beautifulsoup4"
    assert data["config_schema"]["required_config"][0]["name"] == "DEMO_TOKEN"
    assert data["required_config"][0]["name"] == "DEMO_TOKEN"
    assert parsed == manifest
    validate_manifest(parsed)


def test_collector_only_manifest_is_valid_without_provider() -> None:
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
                downloader_profile="tdx.stock_codes.latest",
                resource_group="tdx.quote",
                default_params={"scope": "all"},
            ),
        ),
    )

    validate_manifest(manifest)
    parsed = ProviderManifest.from_dict(manifest.to_dict())
    assert parsed.provider is None
    assert parsed.identity == "axdata.plugin.close_refresh"


def test_independent_collector_manifest_round_trips_without_provider() -> None:
    collector = CollectorSpec.from_dict(
        {
            "collector_id": "demo.stock_snapshot.snapshot",
            "display_name_zh": "示例股票快照采集",
            "description": "采集示例股票快照并写出本地数据集。",
            "collector_plugin_id": "axdata.collector.demo",
            "dataset_id": "demo.stock_snapshot",
            "asset_class": "stock",
            "category": "snapshot",
            "resource_group": "demo.http",
            "runner_entry": "axdata_collector_demo.runner:run",
            "config_schema": {"params": [{"name": "code", "type": "string"}]},
            "default_schedule": {"kind": "manual"},
            "default_params": {"code": "000001.SZ"},
            "output": {"layer": "snapshot", "formats": ["parquet"]},
            "quality": {
                "required_columns": ["instrument_id"],
                "primary_key": ["instrument_id"],
            },
            "lifecycle_status": "experimental",
        }
    )
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.collector.demo",
            name_zh="示例采集器",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(collector,),
    )

    validate_manifest(manifest)
    data = manifest.to_dict()
    parsed = ProviderManifest.from_dict(data)

    assert data["provider"] is None
    assert data["collectors"][0]["collector_id"] == "demo.stock_snapshot.snapshot"
    assert data["collectors"][0]["name"] == "demo.stock_snapshot.snapshot"
    assert data["collectors"][0]["collector_plugin_id"] == "axdata.collector.demo"
    assert data["collectors"][0]["dataset_id"] == "demo.stock_snapshot"
    assert data["collectors"][0]["runner_entry"] == "axdata_collector_demo.runner:run"
    assert parsed == manifest
    assert parsed.collectors[0].collector_id == "demo.stock_snapshot.snapshot"
    assert parsed.collectors[0].is_independent is True
    assert parsed.collectors[0].is_legacy is False


@pytest.mark.parametrize(
    ("missing_key", "match"),
    (
        ("collector_plugin_id", "collector_plugin_id"),
        ("dataset_id", "dataset_id"),
        ("runner_entry", "runner_entry"),
        ("output", "output"),
        ("quality", "quality"),
    ),
)
def test_independent_collector_manifest_rejects_missing_required_fields(
    missing_key: str,
    match: str,
) -> None:
    payload = {
        "collector_id": "demo.stock_snapshot.snapshot",
        "display_name_zh": "示例股票快照采集",
        "collector_plugin_id": "axdata.collector.demo",
        "dataset_id": "demo.stock_snapshot",
        "resource_group": "demo.http",
        "runner_entry": "axdata_collector_demo.runner:run",
        "output": {"layer": "snapshot", "formats": ["parquet"]},
        "quality": {"required_columns": ["instrument_id"]},
    }
    payload.pop(missing_key)
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.collector.demo",
            name_zh="示例采集器",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(CollectorSpec.from_dict(payload),),
    )

    with pytest.raises(ManifestError, match=match):
        validate_manifest(manifest)


def test_collector_from_dict_rejects_mismatched_name_and_collector_id() -> None:
    with pytest.raises(ManifestError, match="collector_id and collector.name"):
        CollectorSpec.from_dict(
            {
                "collector_id": "demo.stock_snapshot.snapshot",
                "name": "demo.other.snapshot",
                "display_name_zh": "示例股票快照采集",
                "resource_group": "demo.http",
            }
        )


def test_manifest_rejects_interfaces_without_provider() -> None:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.plugin.bad",
            name_zh="坏插件",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(_sample_interface("bad_snapshot", source_code="bad"),),
    )

    with pytest.raises(ManifestError, match="provider is required"):
        validate_manifest(manifest)


def test_manifest_rejects_unknown_asset_class() -> None:
    with pytest.raises(ManifestError, match="asset_class"):
        InterfaceSpec(
            name="unknown_asset_demo",
            display_name_zh="未知资产",
            source_code="demo",
            source_name_zh="示例",
            asset_class="crypto",
        )


def test_validate_manifest_rejects_duplicate_interfaces() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(
            _sample_interface("demo_snapshot", source_code="demo"),
            _sample_interface("demo_snapshot", source_code="demo"),
        ),
    )

    with pytest.raises(ManifestError, match="Duplicate interface name"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_duplicate_required_config_names() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(_sample_interface("demo_snapshot", source_code="demo"),),
        required_config=(
            RequiredConfig(name="DEMO_TOKEN", kind="env"),
            RequiredConfig(name="DEMO_TOKEN", kind="env"),
        ),
    )

    with pytest.raises(ManifestError, match="Duplicate required_config name"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_interface_source_code_mismatch() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="other_snapshot",
                display_name_zh="示例",
                source_code="other",
                source_name_zh="其它",
                asset_class="stock",
            ),
        ),
    )

    with pytest.raises(ManifestError, match="does not match provider source_code"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_downloader_unknown_interface() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(_sample_interface("demo_snapshot", source_code="demo"),),
        downloaders=(
            DownloaderProfile(
                name="demo.missing",
                interface_name="missing_interface",
                display_name_zh="缺失接口采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
        ),
    )

    with pytest.raises(ManifestError, match="references unknown interface"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_collection_unknown_default_profile() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="demo_snapshot",
                display_name_zh="示例",
                source_code="demo",
                source_name_zh="示例",
                asset_class="stock",
                collection=InterfaceCollectionSpec(
                    supported=True,
                    default_profile="demo.snapshot.missing",
                ),
            ),
        ),
    )

    with pytest.raises(ManifestError, match="collection.default_profile"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_downloader_when_collection_is_not_supported() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(_sample_interface("demo_snapshot", source_code="demo"),),
        downloaders=(
            DownloaderProfile(
                name="demo.snapshot",
                interface_name="demo_snapshot",
                display_name_zh="示例采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
        ),
    )

    with pytest.raises(ManifestError, match="collection.supported is false"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_default_profile_when_collection_is_not_supported() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="demo_snapshot",
                display_name_zh="示例",
                source_code="demo",
                source_name_zh="示例",
                asset_class="stock",
                collection=InterfaceCollectionSpec(
                    supported=False,
                    default_profile="demo.snapshot",
                ),
            ),
        ),
        downloaders=(
            DownloaderProfile(
                name="demo.snapshot",
                interface_name="demo_snapshot",
                display_name_zh="示例采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
        ),
    )

    with pytest.raises(ManifestError, match="collection.supported is false"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_default_profile_for_another_interface() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(
            _sample_interface("demo_snapshot", source_code="demo", default_profile="demo.other"),
            _sample_interface("demo_other", source_code="demo", default_profile="demo.other"),
        ),
        downloaders=(
            DownloaderProfile(
                name="demo.other",
                interface_name="demo_other",
                display_name_zh="其它采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
        ),
    )

    with pytest.raises(ManifestError, match="for another interface"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_duplicate_parameter_names() -> None:
    interface = InterfaceSpec(
        name="demo_snapshot",
        display_name_zh="示例",
        source_code="demo",
        source_name_zh="示例",
        asset_class="stock",
        parameters=(
            ParameterSpec(name="code", display_name_zh="代码", type="string"),
            ParameterSpec(name="code", display_name_zh="代码", type="string"),
        ),
    )
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(interface,),
    )

    with pytest.raises(ManifestError, match="Duplicate parameter name"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_duplicate_field_names() -> None:
    interface = InterfaceSpec(
        name="demo_snapshot",
        display_name_zh="示例",
        source_code="demo",
        source_name_zh="示例",
        asset_class="stock",
        fields=(
            FieldSpec(name="trade_date", display_name_zh="交易日期", type="date"),
            FieldSpec(name="trade_date", display_name_zh="交易日期", type="date"),
        ),
    )
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(interface,),
    )

    with pytest.raises(ManifestError, match="Duplicate field name"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_duplicate_downloader_names() -> None:
    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(_sample_interface("demo_snapshot", source_code="demo"),),
        downloaders=(
            DownloaderProfile(
                name="demo.snapshot",
                interface_name="demo_snapshot",
                display_name_zh="示例采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
            DownloaderProfile(
                name="demo.snapshot",
                interface_name="demo_snapshot",
                display_name_zh="示例采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
        ),
    )

    with pytest.raises(ManifestError, match="Duplicate downloader profile name"):
        validate_manifest(manifest)


def _manifest_with_example(example: RequestExample) -> ProviderManifest:
    interface = InterfaceSpec(
        name="demo_snapshot",
        display_name_zh="示例快照",
        source_code="demo",
        source_name_zh="示例",
        asset_class="stock",
        parameters=(
            ParameterSpec(
                name="code",
                display_name_zh="证券代码",
                type="string",
            ),
        ),
        fields=(
            FieldSpec(
                name="instrument_id",
                display_name_zh="证券代码",
                type="string",
            ),
            FieldSpec(
                name="name",
                display_name_zh="证券简称",
                type="string",
            ),
        ),
        examples=(example,),
    )
    return ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.demo",
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
        ),
        interfaces=(interface,),
    )


@pytest.mark.parametrize(
    ("example", "match"),
    (
        (
            RequestExample(
                title="错接口",
                request={"interface_name": "other_snapshot"},
                response={"data": []},
            ),
            "references interface",
        ),
        (
            RequestExample(
                title="未知参数",
                request={
                    "interface_name": "demo_snapshot",
                    "params": {"unknown_code": "000001.SZ"},
                },
                response={"data": []},
            ),
            r"unknown params.*unknown_code",
        ),
        (
            RequestExample(
                title="未知请求字段",
                request={
                    "interface_name": "demo_snapshot",
                    "fields": ["missing_field"],
                },
                response={"data": []},
            ),
            r"unknown fields.*missing_field",
        ),
        (
            RequestExample(
                title="未知 schema 字段",
                request={"interface_name": "demo_snapshot"},
                response={"schema": [{"name": "missing_field", "type": "string"}]},
            ),
            r"unknown schema fields.*missing_field",
        ),
        (
            RequestExample(
                title="未知返回字段",
                request={"interface_name": "demo_snapshot"},
                response={"data": [{"instrument_id": "000001.SZ", "extra_field": "x"}]},
            ),
            r"unknown data fields.*extra_field",
        ),
    ),
)
def test_validate_manifest_rejects_example_contract_drift(
    example: RequestExample,
    match: str,
) -> None:
    with pytest.raises(ManifestError, match=match):
        validate_manifest(_manifest_with_example(example))


def test_manifest_from_provider_uses_provider_protocol() -> None:
    class DemoAdapter:
        def call(self, interface_name, params=None, fields=None, options=None):
            return SourceResult(data=({"ok": True},), meta={"interface_name": interface_name})

    class DemoProvider:
        provider_id = "axdata.source.demo"
        source_code = "demo"
        source_name_zh = "示例"
        version = "0.1.0"
        plugin_api_version = "1.0"

        def interfaces(self):
            return (_sample_interface("demo_snapshot", source_code="demo"),)

        def create_adapter(self, options=None):
            return DemoAdapter()

        def downloader_profiles(self):
            return ()

    manifest = manifest_from_provider(DemoProvider())

    assert manifest.provider.provider_id == "axdata.source.demo"
    assert manifest.provider.declared_trust_level == "community"
    assert manifest.provider.homepage is None
    assert manifest.provider.license is None
    assert manifest.provider.description == ""
    assert manifest.interfaces[0].name == "demo_snapshot"
    assert manifest.required_config == ()
    validate_manifest(manifest)


def test_manifest_from_provider_includes_display_only_required_config() -> None:
    class DemoProvider:
        provider_id = "axdata.source.token_demo"
        source_code = "token_demo"
        source_name_zh = "凭据示例"
        version = "0.1.0"
        plugin_api_version = "1.0"

        def interfaces(self):
            return (_sample_interface("token_demo_snapshot", source_code="token_demo"),)

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

    manifest = manifest_from_provider(DemoProvider())

    assert manifest.required_config == (
        RequiredConfig(
            name="TOKEN_DEMO_KEY",
            kind="env",
            required=True,
            description="用户自己的示例源凭据。",
        ),
    )
    assert manifest.to_dict()["required_config"] == [
        {
            "name": "TOKEN_DEMO_KEY",
            "kind": "env",
            "required": True,
            "description": "用户自己的示例源凭据。",
        }
    ]
    validate_manifest(manifest)


def test_manifest_identifier_validation_preserves_config_env_names() -> None:
    ProviderInfo(
        provider_id="axdata.source.demo-provider",
        source_code="demo_source",
        source_name_zh="示例",
        version="0.1.0",
    )
    DownloaderProfile(
        name="demo.snapshot.latest",
        interface_name="demo_snapshot",
        display_name_zh="示例采集",
        resource_group="demo.http",
        mode="snapshot",
    )

    assert RequiredConfig(name="TOKEN_DEMO_KEY", kind="env").name == "TOKEN_DEMO_KEY"


@pytest.mark.parametrize(
    ("factory", "match"),
    (
        (
            lambda: ProviderInfo(
                provider_id="AxData.source.demo",
                source_code="demo",
                source_name_zh="示例",
                version="0.1.0",
            ),
            "provider.provider_id",
        ),
        (
            lambda: ProviderInfo(
                provider_id="axdata.source.demo",
                source_code="demo-source",
                source_name_zh="示例",
                version="0.1.0",
            ),
            "provider.source_code",
        ),
        (
            lambda: InterfaceSpec(
                name="demo.snapshot",
                display_name_zh="示例",
                source_code="demo",
                source_name_zh="示例",
                asset_class="stock",
            ),
            "interface.demo.snapshot.name",
        ),
        (
            lambda: ParameterSpec(
                name="TradeDate",
                display_name_zh="交易日期",
                type="date",
            ),
            "parameter.TradeDate.name",
        ),
        (
            lambda: FieldSpec(
                name="trade-date",
                display_name_zh="交易日期",
                type="date",
            ),
            "field.trade-date.name",
        ),
        (
            lambda: DownloaderProfile(
                name="demo.snapshot",
                interface_name="demo.snapshot",
                display_name_zh="示例采集",
                resource_group="demo.http",
                mode="snapshot",
            ),
            "downloader.demo.snapshot.interface_name",
        ),
    ),
)
def test_manifest_rejects_invalid_identifiers(factory, match: str) -> None:
    with pytest.raises(ManifestError, match=re.escape(match)):
        factory()


def test_manifest_from_provider_includes_optional_provider_display_metadata() -> None:
    class DemoProvider:
        provider_id = "axdata.source.display_demo"
        source_code = "display_demo"
        source_name_zh = "展示示例"
        version = "0.1.0"
        plugin_api_version = "1.0"
        declared_trust_level = PluginTrustLevel.COMMUNITY
        homepage = "https://example.test/axdata-source-display-demo"
        license = "Apache-2.0"
        description = "展示元信息应由 Provider 代码生成。"

        def interfaces(self):
            return (_sample_interface("display_demo_snapshot", source_code="display_demo"),)

        def create_adapter(self, options=None):
            raise AssertionError("adapter should not be created while building manifest")

        def downloader_profiles(self):
            return ()

    manifest = manifest_from_provider(DemoProvider())

    assert manifest.provider.declared_trust_level == PluginTrustLevel.COMMUNITY.value
    assert manifest.provider.homepage == "https://example.test/axdata-source-display-demo"
    assert manifest.provider.license == "Apache-2.0"
    assert manifest.provider.description == "展示元信息应由 Provider 代码生成。"
    validate_manifest(manifest)
