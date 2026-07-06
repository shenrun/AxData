from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from axdata_core.collector_scheduler import CollectorSchedulerService
from axdata_core.plugins import (
    CollectorSpec,
    DownloaderMode,
    DownloaderProfile as PluginDownloaderProfile,
    FieldSpec,
    FieldType,
    InterfaceCollectionSpec,
    InterfaceSpec,
    ParameterSpec,
    ParameterType,
    PluginInfo,
    ProviderInfo,
    ProviderManifest,
    SourceResult,
)
from axdata_core.provider_registry import ProviderRegistry
from axdata_core.schema import get_schema, normalize_table_name
from axdata_core.storage import core_table_partition_path


CORE_LOOP_MAPPING = {
    "stock_basic": {
        "table": "stock_basic_exchange",
        "source_interfaces": ("stock_codes_tdx", "stock_basic_info_exchange"),
        "downloader_profiles": ("stock_codes_tdx.snapshot", "stock_basic_info_exchange.snapshot"),
        "collector_status": "TDX source snapshot and exchange lightweight CollectorSpec exist; production core rebuild still pending",
        "storage_path": "data/core/table=stock_basic_exchange/*.parquet",
    },
    "trade_cal": {
        "table": "trade_cal",
        "source_interfaces": ("stock_trade_calendar_exchange",),
        "downloader_profiles": ("stock_trade_calendar_exchange.snapshot",),
        "collector_status": "exchange lightweight CollectorSpec exists; production calendar scheduling still pending",
        "storage_path": "data/core/table=trade_cal/exchange=SSE/*.parquet",
    },
    "daily": {
        "table": "daily",
        "source_interfaces": ("stock_kline_daily_tdx",),
        "downloader_profiles": ("stock_kline_daily_tdx.snapshot",),
        "collector_status": "TDX lightweight CollectorSpec exists for explicit code samples; production all-market core conversion still pending",
        "storage_path": "data/core/table=daily/parquet/YYYYMMDD.parquet",
    },
    "adj_factor": {
        "table": "adj_factor",
        "source_interfaces": ("stock_adj_factor_tdx",),
        "downloader_profiles": ("stock_adj_factor_tdx.snapshot",),
        "collector_status": "TDX lightweight CollectorSpec exists for explicit code samples; production all-market core conversion still pending",
        "storage_path": "data/core/table=adj_factor/parquet/YYYYMMDD.parquet",
    },
}


class _LoopAdapter:
    source = "loop_demo"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def call(self, interface_name: str, *, params=None, **_kwargs) -> SourceResult:
        self.calls.append({"interface_name": interface_name, "params": dict(params or {})})
        if interface_name != "daily":
            raise AssertionError(interface_name)
        return SourceResult(
            data=(
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20240102",
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "pre_close": 10.0,
                    "change": 0.2,
                    "pct_chg": 2.0,
                    "vol": 1000.0,
                    "amount": 10200.0,
                },
                {
                    "ts_code": "000002.SZ",
                    "trade_date": "20240102",
                    "open": 20.0,
                    "high": 21.0,
                    "low": 19.5,
                    "close": 20.5,
                    "pre_close": 20.0,
                    "change": 0.5,
                    "pct_chg": 2.5,
                    "vol": 2000.0,
                    "amount": 41000.0,
                },
            ),
            meta={
                "snapshot_date": "20240102",
                "source": "loop_demo",
                "sample": True,
            },
        )


class _LoopProvider:
    provider_id = "axdata.source.loop_demo"

    def __init__(self) -> None:
        self.adapter = _LoopAdapter()

    def create_adapter(self, options=None) -> _LoopAdapter:
        return self.adapter


def _loop_provider_manifest() -> ProviderManifest:
    daily_fields = get_schema("daily").fields
    return ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.loop_demo",
            source_code="loop_demo",
            source_name_zh="Loop demo",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="daily",
                display_name_zh="Daily bars",
                source_code="loop_demo",
                source_name_zh="Loop demo",
                asset_class="stock",
                collection=InterfaceCollectionSpec(
                    supported=True,
                    default_profile="loop_demo.daily.snapshot",
                ),
                parameters=(
                    ParameterSpec(
                        name="trade_date",
                        display_name_zh="Trade date",
                        type=ParameterType.STRING.value,
                        required=True,
                    ),
                ),
                fields=tuple(
                    FieldSpec(
                        name=field.name,
                        display_name_zh=field.description_zh or field.name,
                    type=FieldType.NUMBER.value if field.dtype == "float64" else FieldType.STRING.value,
                        required=not field.nullable,
                    )
                    for field in daily_fields
                ),
            ),
        ),
        downloaders=(
            PluginDownloaderProfile(
                name="loop_demo.daily.snapshot",
                interface_name="daily",
                display_name_zh="Daily sample",
                resource_group="loop_demo.core",
                mode=DownloaderMode.SNAPSHOT.value,
                default_options={
                    "params": {"trade_date": "20240102"},
                    "fields": [field.name for field in daily_fields],
                    "formats": ["parquet"],
                },
                default_limits={"max_active_jobs": 1, "max_connections_total": 1},
                output={
                    "default_dir_name": "daily",
                    "file_name_template": "{interface_name}_{data_date}_{run_time}",
                    "supported_formats": ["parquet", "csv", "jsonl"],
                    "output_layer": "core",
                    "primary_key": ["ts_code", "trade_date"],
                    "required_columns": ["ts_code", "trade_date"],
                    "expected_columns": [field.name for field in daily_fields],
                    "date_field": "trade_date",
                    "numeric_positive_columns": ["open", "high", "low", "close", "vol", "amount"],
                },
            ),
        ),
    )


def _loop_collector_manifest() -> ProviderManifest:
    return ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.plugin.core_loop_demo",
            name_zh="Core loop demo collector",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(
            CollectorSpec(
                name="core.daily.sample",
                display_name_zh="Daily sample loop",
                description="Local test-only daily sample collector.",
                interfaces=("daily",),
                required_interfaces=("daily",),
                downloader_profile="loop_demo.daily.snapshot",
                resource_group="loop_demo.core",
                default_params={"trade_date": "20240102"},
                output={"layer": "core", "formats": ["parquet", "csv", "jsonl"]},
            ),
        ),
    )


def _loop_registry(provider: _LoopProvider) -> ProviderRegistry:
    registry = ProviderRegistry(
        enabled_provider_ids={
            "axdata.source.loop_demo",
            "axdata.plugin.core_loop_demo",
        }
    )
    registry.register_manifest(
        _loop_provider_manifest(),
        provider=provider,
        enabled=True,
    )
    registry.register_manifest(_loop_collector_manifest(), enabled=True)
    return registry


def test_core_loop_mapping_documents_current_interfaces_and_gaps() -> None:
    assert normalize_table_name("stock_basic") == "stock_basic_exchange"

    for core_name, mapping in CORE_LOOP_MAPPING.items():
        schema = get_schema(mapping["table"])
        assert schema.name == mapping["table"]
        assert mapping["source_interfaces"]
        assert mapping["storage_path"].startswith(f"data/core/table={mapping['table']}")
        if core_name in {"daily", "adj_factor"}:
            assert schema.primary_key == ("ts_code", "trade_date")
        if core_name == "trade_cal":
            assert schema.primary_key == ("exchange", "cal_date")


def test_core_collection_loop_records_run_writes_files_and_query_reads_back(monkeypatch, tmp_path) -> None:
    import axdata_core.provider_catalog as provider_catalog

    provider = _LoopProvider()
    registry = _loop_registry(provider)
    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_kwargs: registry)

    data_root = tmp_path / "data"
    export_root = tmp_path / "export"
    trade_cal_partition = core_table_partition_path("trade_cal", data_root) / "exchange=SZSE"
    trade_cal_partition.mkdir(parents=True)
    pd.DataFrame(
        [
            {"exchange": "SZSE", "cal_date": "20240102", "is_open": True, "pretrade_date": None},
        ]
    ).to_parquet(trade_cal_partition / "part-0.parquet", engine="pyarrow", index=False)
    service = CollectorSchedulerService(data_root=data_root, max_workers=1)
    task = service.create_task(
        "core.daily.sample",
        task_id="daily_sample",
        trigger_type="manual",
        output_root=export_root,
        formats=["parquet", "csv", "jsonl"],
    )

    submitted = service.submit_task("daily_sample")
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert finished is not None
    assert finished.status == "success"
    assert finished.output_paths.keys() == {"csv", "jsonl", "parquet"}
    assert finished.quality["primary_key"] == "pass"
    assert finished.quality["row_count"] == "pass"
    assert finished.quality["schema"] == "pass"
    assert finished.quality["quality_status"] == "ok"
    assert finished.quality["duplicate_key_count"] == 0
    assert finished.quality["date_range"] == {"min": "20240102", "max": "20240102"}
    assert finished.quality["numeric_positive_checks"]["amount"]["status"] == "pass"
    assert finished.result["download_result"]["row_count"] == 2
    assert finished.result["target_interface"] == "daily"
    assert finished.result["downloader_profile"] == "loop_demo.daily.snapshot"
    assert task.downloader_profile == "loop_demo.daily.snapshot"
    assert provider.adapter.calls == [
        {"interface_name": "daily", "params": {"trade_date": "20240102"}}
    ]

    for path_text in finished.output_paths.values():
        assert Path(path_text).exists()

    log_path = Path(finished.result["download_result"]["log_path"])
    log_payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert log_payload["interface_name"] == "daily"
    assert log_payload["row_count"] == 2
    assert log_payload["output_paths"] == finished.output_paths
    assert log_payload["quality"]["primary_key"] == "pass"
    assert log_payload["source_meta"]["sample"] is True

    parquet_frame = pd.read_parquet(finished.output_paths["parquet"], engine="pyarrow")
    core_partition = core_table_partition_path("daily", data_root) / "trade_date=20240102"
    core_partition.mkdir(parents=True)
    parquet_frame.to_parquet(core_partition / "part-0.parquet", engine="pyarrow", index=False)

    from axdata_core import query_table, read_core_table

    saved = read_core_table("daily", root=data_root)
    assert saved.sort_values("ts_code")["ts_code"].tolist() == ["000001.SZ", "000002.SZ"]

    queried = query_table(
        "daily",
        root=data_root,
        fields=["ts_code", "trade_date", "close"],
        filters={"ts_code": "000001.SZ"},
        start_date="20240101",
        end_date="20240131",
    )
    assert queried.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]
