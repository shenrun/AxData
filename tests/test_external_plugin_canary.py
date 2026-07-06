from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from axdata_core.cli import main
from axdata_core.plugin_config import enable_provider, load_plugin_config
from axdata_core.plugins import (
    FieldSpec,
    InterfaceSpec,
    ParameterSpec,
    ProviderInfo,
    ProviderManifest,
    RequestExample,
)
from axdata_core.provider_catalog import build_builtin_provider_registry, list_registry_interface_dicts
from axdata_core.source_request import request_interface


CANARY_PROVIDER_ID = "axdata.source.canary"
CANARY_INTERFACE_NAME = "canary_stock_snapshot"


def test_real_dist_info_external_plugin_discovery_enable_catalog_and_lazy_call(
    tmp_path,
    monkeypatch,
) -> None:
    install_root = _install_canary_provider(tmp_path)
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    sys.modules.pop("axdata_source_canary", None)

    registry = build_builtin_provider_registry(data_root=data_root)
    disabled_snapshot = registry.snapshot()
    disabled_provider = disabled_snapshot.providers[CANARY_PROVIDER_ID]

    assert disabled_provider.status == "disabled"
    assert disabled_provider.enabled is False
    assert disabled_provider.provider is None
    assert CANARY_INTERFACE_NAME not in disabled_snapshot.interfaces
    assert "axdata_source_canary" not in sys.modules

    enable_provider(CANARY_PROVIDER_ID, data_root=data_root)
    enabled_registry = build_builtin_provider_registry(data_root=data_root)
    enabled_snapshot = enabled_registry.snapshot()

    assert enabled_snapshot.providers[CANARY_PROVIDER_ID].status == "enabled"
    assert enabled_snapshot.providers[CANARY_PROVIDER_ID].effective_trust_level == "community"
    assert enabled_snapshot.interfaces[CANARY_INTERFACE_NAME].provider_id == CANARY_PROVIDER_ID
    assert "axdata_source_canary" not in sys.modules

    catalog_entries = {entry["name"]: entry for entry in list_registry_interface_dicts(data_root=data_root)}
    canary_entry = catalog_entries[CANARY_INTERFACE_NAME]

    assert canary_entry["provider_id"] == CANARY_PROVIDER_ID
    assert canary_entry["display_name_zh"] == "Canary 股票快照"
    assert canary_entry["source_code"] == "canary"
    assert canary_entry["asset_class"] == "stock"
    assert canary_entry["declared_trust_level"] == "official"
    assert canary_entry["effective_trust_level"] == "community"
    assert canary_entry["plugin_status"] == "enabled"
    assert canary_entry["parameters"][0]["name"] == "code"
    assert canary_entry["fields"][0]["name"] == "instrument_id"

    result = request_interface(
        CANARY_INTERFACE_NAME,
        params={"code": "000001.SZ"},
        fields=["instrument_id", "name"],
        options={"timeout_ms": 1234},
    )

    assert result.records == [{"instrument_id": "000001.SZ", "name": "平安银行"}]
    assert result.meta["source"] == "canary"
    assert result.meta["options"] == {"timeout_ms": 1234}
    assert result.meta["adapter_options"] == {"timeout_ms": 1234}
    assert "axdata_source_canary" in sys.modules

    client = TestClient(app)
    catalog_response = client.get("/v1/request/interfaces")

    assert catalog_response.status_code == 200
    api_entries = {entry["name"]: entry for entry in catalog_response.json()["data"]}
    assert CANARY_INTERFACE_NAME in api_entries
    assert api_entries[CANARY_INTERFACE_NAME]["provider_id"] == CANARY_PROVIDER_ID

    providers_response = client.get("/v1/plugins/providers")
    assert providers_response.status_code == 200
    providers = {provider["provider_id"]: provider for provider in providers_response.json()["data"]}
    assert providers[CANARY_PROVIDER_ID]["status"] == "enabled"
    assert providers[CANARY_PROVIDER_ID]["declared_trust_level"] == "official"
    assert providers[CANARY_PROVIDER_ID]["effective_trust_level"] == "community"
    assert providers[CANARY_PROVIDER_ID]["interfaces"] == [CANARY_INTERFACE_NAME]

    request_response = client.post(
        f"/v1/request/{CANARY_INTERFACE_NAME}",
        json={
            "params": {"code": "600000.SH"},
            "fields": ["instrument_id", "source_code"],
            "options": {"timeout_ms": 4321},
        },
    )

    assert request_response.status_code == 200
    payload = request_response.json()
    assert payload["data"] == [{"instrument_id": "600000.SH", "source_code": "canary"}]
    assert payload["meta"]["source"] == "canary"
    assert payload["meta"]["adapter_options"] == {"timeout_ms": 4321}


def test_plugin_cli_check_and_manifest_compare_for_real_canary_package(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    install_root = _install_canary_provider(tmp_path)
    manifest_path = install_root / "axdata_source_canary" / "axdata-provider.json"
    data_root = tmp_path / "data"

    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    sys.modules.pop("axdata_source_canary", None)

    assert main(["plugin", "check", "--provider", "axdata_source_canary:provider"]) == 0
    assert f"OK {CANARY_PROVIDER_ID} interfaces=1 downloaders=0 collectors=0" in capsys.readouterr().out

    built_manifest_path = tmp_path / "provider-generated.json"
    assert (
        main(
            [
                "plugin",
                "build",
                "--provider",
                "axdata_source_canary:provider",
                "--output",
                str(built_manifest_path),
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "plugin",
                "check",
                "--provider",
                "axdata_source_canary:provider",
                "--manifest",
                str(built_manifest_path),
            ]
        )
        == 0
    )

    output_path = tmp_path / "built-manifest.json"
    assert (
        main(
            [
                "plugin",
                "build",
                "--provider",
                "axdata_source_canary:provider",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )
    assert json.loads(output_path.read_text(encoding="utf-8")) == json.loads(
        built_manifest_path.read_text(encoding="utf-8")
    )

    assert main(["--data-root", str(data_root), "plugin", "enable", CANARY_PROVIDER_ID]) == 0
    assert load_plugin_config(data_root=data_root).enabled_provider_ids == (CANARY_PROVIDER_ID,)

    capsys.readouterr()
    assert main(["--data-root", str(data_root), "plugin", "list", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    by_id = {row["provider_id"]: row for row in rows}
    assert by_id[CANARY_PROVIDER_ID]["status"] == "enabled"
    assert by_id[CANARY_PROVIDER_ID]["effective_trust_level"] == "community"


def test_plugin_cli_check_fails_when_embedded_manifest_drifts(
    tmp_path,
    monkeypatch,
) -> None:
    install_root = _install_canary_provider(tmp_path)
    manifest_path = install_root / "axdata_source_canary" / "axdata-provider.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["interfaces"][0]["display_name_zh"] = "漂移后的标题"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(install_root))
    sys.modules.pop("axdata_source_canary", None)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "plugin",
                "check",
                "--provider",
                "axdata_source_canary:provider",
                "--manifest",
                str(manifest_path),
            ]
        )

    assert exc_info.value.code == 2


def _install_canary_provider(tmp_path: Path) -> Path:
    install_root = tmp_path / "site-packages"
    package_root = install_root / "axdata_source_canary"
    dist_info = install_root / "axdata_source_canary-0.1.0.dist-info"
    package_root.mkdir(parents=True)
    dist_info.mkdir(parents=True)

    manifest = _canary_manifest()
    manifest_text = json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n"

    (package_root / "__init__.py").write_text(_canary_module_source(), encoding="utf-8")
    (package_root / "axdata-provider.json").write_text(manifest_text, encoding="utf-8")
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: axdata-source-canary\n"
        "Version: 0.1.0\n",
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(
        "[axdata.providers]\n"
        "canary = axdata_source_canary:provider\n",
        encoding="utf-8",
    )
    (dist_info / "RECORD").write_text(
        "\n".join(
            [
                "axdata_source_canary/__init__.py,,",
                "axdata_source_canary/axdata-provider.json,,",
                "axdata_source_canary-0.1.0.dist-info/METADATA,,",
                "axdata_source_canary-0.1.0.dist-info/entry_points.txt,,",
                "axdata_source_canary-0.1.0.dist-info/RECORD,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return install_root


def _canary_manifest() -> ProviderManifest:
    return ProviderManifest(
        provider=ProviderInfo(
            provider_id=CANARY_PROVIDER_ID,
            source_code="canary",
            source_name_zh="Canary 数据源",
            version="0.1.0",
            declared_trust_level="official",
            description="测试用外部 Provider。自报 official 只能展示，Registry 会降级为 community。",
        ),
        interfaces=(
            InterfaceSpec(
                name=CANARY_INTERFACE_NAME,
                display_name_zh="Canary 股票快照",
                source_code="canary",
                source_name_zh="Canary 数据源",
                category="测试数据/快照",
                menu_path=("Canary", "股票数据"),
                asset_class="stock",
                parameters=(
                    ParameterSpec(
                        name="code",
                        display_name_zh="股票代码",
                        type="string",
                        required=True,
                        description="AxData 统一证券代码，例如 000001.SZ。",
                    ),
                ),
                fields=(
                    FieldSpec(
                        name="instrument_id",
                        display_name_zh="证券代码",
                        type="string",
                        required=True,
                    ),
                    FieldSpec(name="name", display_name_zh="证券简称", type="string"),
                    FieldSpec(name="source_code", display_name_zh="来源代码", type="string"),
                ),
                examples=(
                    RequestExample(
                        title="单票查询",
                        request={
                            "interface_name": CANARY_INTERFACE_NAME,
                            "params": {"code": "000001.SZ"},
                            "fields": ["instrument_id", "name"],
                        },
                        response={
                            "data": [
                                {
                                    "instrument_id": "000001.SZ",
                                    "name": "平安银行",
                                    "source_code": "canary",
                                }
                            ]
                        },
                    ),
                ),
                notes="测试外部 Provider 用，不请求网络。",
            ),
        ),
    )


def _canary_module_source() -> str:
    return '''
from axdata_core.plugins import (
    FieldSpec,
    InterfaceSpec,
    ParameterSpec,
    RequestExample,
    SourceResult,
)


class CanaryAdapter:
    def __init__(self, options=None):
        self.options = dict(options or {})

    def call(self, interface_name, params=None, fields=None, options=None):
        if interface_name != "canary_stock_snapshot":
            raise KeyError(interface_name)
        params = dict(params or {})
        merged_options = {**self.options, **dict(options or {})}
        code = params.get("code", "000001.SZ")
        name = "平安银行" if code == "000001.SZ" else "浦发银行"
        return SourceResult(
            data=(
                {
                    "instrument_id": code,
                    "name": name,
                    "source_code": "canary",
                },
            ),
            meta={
                "source": "canary",
                "adapter_options": merged_options,
            },
        )


class CanaryProvider:
    provider_id = "axdata.source.canary"
    source_code = "canary"
    source_name_zh = "Canary 数据源"
    version = "0.1.0"
    plugin_api_version = "1.0"

    def interfaces(self):
        return (
            InterfaceSpec(
                name="canary_stock_snapshot",
                display_name_zh="Canary 股票快照",
                source_code="canary",
                source_name_zh="Canary 数据源",
                category="测试数据/快照",
                menu_path=("Canary", "股票数据"),
                asset_class="stock",
                parameters=(
                    ParameterSpec(
                        name="code",
                        display_name_zh="股票代码",
                        type="string",
                        required=True,
                        description="AxData 统一证券代码，例如 000001.SZ。",
                    ),
                ),
                fields=(
                    FieldSpec(
                        name="instrument_id",
                        display_name_zh="证券代码",
                        type="string",
                        required=True,
                    ),
                    FieldSpec(name="name", display_name_zh="证券简称", type="string"),
                    FieldSpec(name="source_code", display_name_zh="来源代码", type="string"),
                ),
                examples=(
                    RequestExample(
                        title="单票查询",
                        request={
                            "interface_name": "canary_stock_snapshot",
                            "params": {"code": "000001.SZ"},
                            "fields": ["instrument_id", "name"],
                        },
                        response={
                            "data": [
                                {
                                    "instrument_id": "000001.SZ",
                                    "name": "平安银行",
                                    "source_code": "canary",
                                }
                            ]
                        },
                    ),
                ),
                notes="测试外部 Provider 用，不请求网络。",
            ),
        )

    def create_adapter(self, options=None):
        return CanaryAdapter(options=options)

    def downloader_profiles(self):
        return ()


provider = CanaryProvider()
'''
