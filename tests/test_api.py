from fastapi.testclient import TestClient
from datetime import datetime, timezone
import pandas as pd
import pytest

import apps.api.main as api_main
from apps.api.main import app
from axdata_core import SourceRequestResult, write_core_table
from axdata_core.collector_scheduler import CollectorRun, CollectorSchedulerStore
from axdata_core.plugin_config import disable_provider
from axdata_core.sources import list_request_interfaces as list_builtin_request_interfaces
from tests.test_axp import _build_tencent_axp
from tests.test_tencent_provider_package import (
    BUILTIN_TENCENT_PROVIDER_ID,
    TENCENT_INTERFACE_NAME,
    TENCENT_PROVIDER_ID,
)
from tests.tdx_plugin_helpers import (
    TDX_COLLECTOR_PLUGIN_ID,
    TDX_EXT_PROVIDER_ID,
    TDX_PROVIDER_ID,
    build_registry_with_local_tdx_plugins,
    ensure_local_tdx_plugin_paths,
)

ensure_local_tdx_plugin_paths()

TDX_SOURCE_INTERFACE_COUNT = 90
TDX_EXT_SOURCE_INTERFACE_COUNT = 31
EXPECTED_SOURCE_REQUEST_INTERFACE_COUNT = (
    len(list_builtin_request_interfaces())
    + TDX_SOURCE_INTERFACE_COUNT
    + TDX_EXT_SOURCE_INTERFACE_COUNT
)
TENCENT_BUILTIN_INTERFACE_NAMES = [
    "stock_zh_a_spot_tx",
    "stock_zh_a_hist_tx",
    "stock_zh_index_daily_tx",
    "stock_zh_a_tick_tx_js",
    "get_tx_start_year",
    "tencent_realtime_snapshot",
]
TDX_DOWNLOADER_INTERFACE_NAMES = [
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
]
BUILTIN_GENERIC_INTERFACE_NAMES = {
    "stock_trade_calendar_exchange",
    "stock_historical_list_exchange",
    "stock_basic_info_exchange",
}


@pytest.fixture(autouse=True)
def _enable_local_tdx_plugins(monkeypatch):
    import axdata_core
    import axdata_core.provider_catalog as provider_catalog

    base_builder = provider_catalog.build_builtin_provider_registry

    def build_registry(**kwargs):
        return build_registry_with_local_tdx_plugins(
            base_builder=base_builder,
            **kwargs,
        )

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", build_registry)
    if "build_builtin_provider_registry" in axdata_core.__dict__:
        monkeypatch.setattr(axdata_core, "build_builtin_provider_registry", build_registry)


STOCK_BASIC_ROWS = [
    {
        "instrument_id": "000001.SZ",
        "symbol": "000001",
        "exchange": "SZSE",
        "asset_type": "stock",
        "name": "平安银行",
        "security_full_name": None,
        "market_code": None,
        "market": "主板",
        "industry_code": None,
        "industry": "J 金融业",
        "region_code": None,
        "region": None,
        "company_code": None,
        "company_short_name": None,
        "company_full_name": None,
        "company_short_name_en": None,
        "company_full_name_en": None,
        "listing_status": "listed",
        "list_date": "19910403",
        "delist_date": None,
        "total_share": 194.05,
        "float_share": 194.05,
        "is_profit": "-",
        "is_vie": "-",
        "has_weighted_voting_rights": "-",
        "sponsor": None,
        "share_report_date": None,
    },
    {
        "instrument_id": "600000.SH",
        "symbol": "600000",
        "exchange": "SSE",
        "asset_type": "stock",
        "name": "浦发银行",
        "security_full_name": "浦发银行",
        "market_code": "1",
        "market": "主板",
        "industry_code": "J",
        "industry": "金融业",
        "region_code": "310000",
        "region": "上海市",
        "company_code": "600000",
        "company_short_name": "浦发银行",
        "company_full_name": "上海浦东发展银行股份有限公司",
        "company_short_name_en": "SPD BANK",
        "company_full_name_en": "Shanghai Pudong Development Bank Co.,Ltd.",
        "listing_status": "listed",
        "list_date": "19991110",
        "delist_date": None,
        "total_share": None,
        "float_share": None,
        "is_profit": None,
        "is_vie": None,
        "has_weighted_voting_rights": None,
        "sponsor": None,
        "share_report_date": None,
    },
]


DAILY_ROWS = [
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
        "ts_code": "000001.SZ",
        "trade_date": "20240103",
        "open": 10.2,
        "high": 10.8,
        "low": 10.1,
        "close": 10.6,
        "pre_close": 10.2,
        "change": 0.4,
        "pct_chg": 3.92,
        "vol": 1200.0,
        "amount": 12600.0,
    },
    {
        "ts_code": "600000.SH",
        "trade_date": "20240102",
        "open": 8.0,
        "high": 8.3,
        "low": 7.9,
        "close": 8.1,
        "pre_close": 8.0,
        "change": 0.1,
        "pct_chg": 1.25,
        "vol": 900.0,
        "amount": 7290.0,
    },
]


def test_health_route():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_static_api_token_still_guards_http_routes(monkeypatch):
    monkeypatch.setenv("AXDATA_API_TOKEN", "secret")
    client = TestClient(app)

    assert client.get("/health").status_code == 401

    response = client.get("/health", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert response.json()["auth_enabled"] is True


def test_named_api_tokens_can_be_created_used_and_revoked(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)

    create_response = client.post("/v1/auth/tokens", json={"name": "notebook-laptop"})

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    token = created["token"]
    token_id = created["record"]["id"]
    assert token.startswith("axd_")
    assert created["record"]["name"] == "notebook-laptop"
    assert created["record"]["token"] == token
    assert "token_hash" not in created["record"]

    local_health = client.get("/health")
    assert local_health.status_code == 200
    assert local_health.json()["auth_enabled"] is False

    authed = client.get("/v1/auth/tokens", headers={"Authorization": f"Bearer {token}"})
    assert authed.status_code == 200
    rows = authed.json()["data"]
    assert rows[0]["active"] is True
    assert rows[0]["token"] == token
    assert "token_hash" not in rows[0]

    revoked = client.delete(f"/v1/auth/tokens/{token_id}", headers={"Authorization": f"Bearer {token}"})
    assert revoked.status_code == 200
    assert revoked.json()["data"]["active"] is False

    assert client.get("/health", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_named_api_tokens_guard_remote_host_and_track_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AXDATA_API_HOST", "0.0.0.0")
    client = TestClient(app)

    create_response = client.post("/v1/auth/tokens", json={"name": "remote-client"})

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    token = created["token"]
    token_id = created["record"]["id"]

    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    authed = client.get("/v1/auth/tokens", headers={"Authorization": f"Bearer {token}"})
    assert authed.status_code == 200
    assert authed.json()["data"][0]["last_used_at"] is not None
    assert authed.json()["data"][0]["token"] == token
    assert "token_hash" not in authed.json()["data"][0]

    revoked = client.delete(f"/v1/auth/tokens/{token_id}", headers={"Authorization": f"Bearer {token}"})
    assert revoked.status_code == 200
    assert revoked.json()["data"]["active"] is False

    assert client.get("/health", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_named_api_tokens_keep_loopback_open_when_remote_host_is_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AXDATA_API_HOST", "0.0.0.0")
    remote_client = TestClient(app, client=("192.168.1.50", 50000))

    create_response = remote_client.post("/v1/auth/tokens", json={"name": "remote-client"})
    assert create_response.status_code == 201
    token = create_response.json()["data"]["token"]

    assert remote_client.get("/health").status_code == 401

    loopback_client = TestClient(app, client=("127.0.0.1", 50000))
    local_health = loopback_client.get("/health")
    assert local_health.status_code == 200
    assert local_health.json()["auth_enabled"] is True

    assert remote_client.get("/health", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_loopback_api_host_keeps_local_mode_even_with_token_registry(tmp_path, monkeypatch):
    token_file = tmp_path / "metadata" / "api_tokens.json"
    token_file.parent.mkdir(parents=True)
    token_file.write_text('{"version": 1, "tokens": []}\n', encoding="utf-8")
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AXDATA_API_HOST", "127.0.0.1")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["auth_enabled"] is False


def test_remote_api_host_token_registry_enables_auth(tmp_path, monkeypatch):
    token_file = tmp_path / "metadata" / "api_tokens.json"
    token_file.parent.mkdir(parents=True)
    token_file.write_text('{"version": 1, "tokens": []}\n', encoding="utf-8")
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AXDATA_API_HOST", "0.0.0.0")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 401


def test_invalid_token_registry_file_fails_closed(tmp_path, monkeypatch):
    token_file = tmp_path / "metadata" / "api_tokens.json"
    token_file.parent.mkdir(parents=True)
    token_file.write_text("{bad json", encoding="utf-8")
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(token_file))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["auth_enabled"] is False


def test_remote_api_host_invalid_token_registry_fails_closed(tmp_path, monkeypatch):
    token_file = tmp_path / "metadata" / "api_tokens.json"
    token_file.parent.mkdir(parents=True)
    token_file.write_text("{bad json", encoding="utf-8")
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AXDATA_API_HOST", "0.0.0.0")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 401


def test_runtime_config_save_reports_pending_restart(tmp_path, monkeypatch):
    runtime_config = tmp_path / "metadata" / "runtime_config.json"
    restart_request = tmp_path / "metadata" / "runtime_restart.json"
    monkeypatch.setenv("AXDATA_RUNTIME_CONFIG_FILE", str(runtime_config))
    monkeypatch.setenv("AXDATA_RESTART_REQUEST_FILE", str(restart_request))
    monkeypatch.setenv("AXDATA_API_HOST", "127.0.0.1")
    monkeypatch.setenv("AXDATA_API_PORT", "8666")
    monkeypatch.setenv("AXDATA_WEB_PORT", "8667")
    client = TestClient(app)

    response = client.put(
        "/v1/config/runtime",
        json={"api_host": "0.0.0.0", "api_port": 8766, "web_port": 8767},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["pending_restart"] is True
    assert payload["next_start"]["api_host"] == "0.0.0.0"
    assert payload["next_start"]["api_port"] == 8766
    assert payload["next_start"]["web_port"] == 8767
    assert runtime_config.exists()

    config_response = client.get("/v1/config")
    assert config_response.status_code == 200
    config_payload = config_response.json()["data"]
    assert config_payload["api_host"] == "127.0.0.1"
    assert config_payload["api_port"] == 8666
    assert config_payload["next_start"]["api_host"] == "0.0.0.0"
    assert config_payload["pending_restart"] is True


def test_remote_runtime_config_keeps_loopback_api_base(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AXDATA_API_HOST", "0.0.0.0")
    monkeypatch.setenv("AXDATA_API_PORT", "8766")
    monkeypatch.setenv("AXDATA_WEB_PORT", "8767")
    client = TestClient(app)

    response = client.get("/v1/config")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["api_host"] == "0.0.0.0"
    assert payload["api_base"] == "http://127.0.0.1:8766"
    assert payload["local_api_base"] == "http://127.0.0.1:8766"
    assert payload["listen_api_base"] == "http://0.0.0.0:8766"


def test_runtime_restart_request_requires_dev_launcher(tmp_path, monkeypatch):
    restart_request = tmp_path / "metadata" / "runtime_restart.json"
    monkeypatch.setenv("AXDATA_RESTART_REQUEST_FILE", str(restart_request))
    monkeypatch.delenv("AXDATA_DEV_LAUNCHER", raising=False)
    client = TestClient(app)

    response = client.post("/v1/config/restart-api")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["accepted"] is False
    assert payload["restart_supported"] is False
    assert not restart_request.exists()


def test_runtime_restart_request_writes_launcher_signal(tmp_path, monkeypatch):
    restart_request = tmp_path / "metadata" / "runtime_restart.json"
    launcher_file = tmp_path / "metadata" / "runtime_launcher.json"
    launcher_file.parent.mkdir(parents=True)
    launcher_file.write_text(
        (
            '{"pid": %d, "restart_request_path": "%s", "heartbeat_at": "%s"}\n'
            % (
                12345,
                str(restart_request).replace("\\", "\\\\"),
                datetime.now(timezone.utc).isoformat(),
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AXDATA_RESTART_REQUEST_FILE", str(restart_request))
    monkeypatch.setenv("AXDATA_LAUNCHER_FILE", str(launcher_file))
    monkeypatch.setenv("AXDATA_DEV_LAUNCHER", "1")
    monkeypatch.setattr(api_main, "_launcher_process_alive", lambda pid: int(pid) == 12345)
    client = TestClient(app)

    response = client.post("/v1/config/restart-api")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["accepted"] is True
    assert payload["restart_supported"] is True
    assert restart_request.exists()
    assert "requested_at" in restart_request.read_text(encoding="utf-8")


def test_runtime_config_handles_launcher_probe_errors(tmp_path, monkeypatch):
    runtime_config = tmp_path / "metadata" / "runtime_config.json"
    restart_request = tmp_path / "metadata" / "runtime_restart.json"
    launcher_file = tmp_path / "metadata" / "runtime_launcher.json"
    launcher_file.parent.mkdir(parents=True)
    runtime_config.write_text(
        '{"version": 1, "api_host": "127.0.0.1", "api_port": 8666, "web_port": 8667}\n',
        encoding="utf-8",
    )
    launcher_file.write_text(
        (
            '{"pid": %d, "restart_request_path": "%s", "heartbeat_at": "%s"}\n'
            % (
                12345,
                str(restart_request).replace("\\", "\\\\"),
                datetime.now(timezone.utc).isoformat(),
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AXDATA_RUNTIME_CONFIG_FILE", str(runtime_config))
    monkeypatch.setenv("AXDATA_RESTART_REQUEST_FILE", str(restart_request))
    monkeypatch.setenv("AXDATA_LAUNCHER_FILE", str(launcher_file))
    monkeypatch.setenv("AXDATA_DEV_LAUNCHER", "1")
    monkeypatch.setattr(api_main.os, "kill", lambda *_args: (_ for _ in ()).throw(SystemError("bad pid probe")))
    client = TestClient(app)

    response = client.get("/v1/config")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["restart_supported"] is False
    assert payload["next_start"]["api_host"] == "127.0.0.1"


def test_status_and_doctor_routes_report_local_diagnostics(tmp_path, monkeypatch):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    client = TestClient(app)

    status_response = client.get("/v1/status")
    doctor_response = client.get("/v1/doctor")

    assert status_response.status_code == 200
    assert doctor_response.status_code == 200
    status_payload = status_response.json()["data"]
    doctor_payload = doctor_response.json()["data"]
    assert status_payload["config"]["data_root"] == str(root.resolve())
    assert doctor_payload["config"]["data_root"] == str(root.resolve())
    assert status_payload["registry"]["loaded"] is True
    assert status_payload["real_source_smoke"]["requires_explicit_run"] is True
    assert {check["category"] for check in status_payload["checks"]} >= {
        "paths",
        "dependencies",
        "registry",
        "ports",
        "collector",
        "smoke",
    }


def test_api_startup_initializes_missing_local_directories(tmp_path, monkeypatch):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(tmp_path / "metadata" / "api_tokens.json"))

    assert not root.exists()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    for path in [
        root / "raw",
        root / "staging",
        root / "core",
        root / "factor",
        tmp_path / "metadata",
        tmp_path / "metadata" / "collector",
        tmp_path / "cache",
        tmp_path / "logs",
        tmp_path / "plugins",
        tmp_path / "plugins" / "site-packages",
    ]:
        assert path.is_dir(), str(path)
    assert (tmp_path / "metadata" / "plugins.json").is_file()


def test_api_startup_initialization_keeps_existing_data_and_config(tmp_path, monkeypatch):
    root = tmp_path / "data"
    core_file = root / "core" / "keep.txt"
    plugin_config = tmp_path / "metadata" / "plugins.json"
    core_file.parent.mkdir(parents=True)
    plugin_config.parent.mkdir(parents=True)
    core_file.write_text("keep-data", encoding="utf-8")
    plugin_config.write_text('{"providers": {"demo": {"enabled": false}}}', encoding="utf-8")
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(tmp_path / "metadata" / "api_tokens.json"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert core_file.read_text(encoding="utf-8") == "keep-data"
    assert plugin_config.read_text(encoding="utf-8") == '{"providers": {"demo": {"enabled": false}}}'


def test_diagnostics_writable_probe_uses_unique_temp_file(tmp_path, monkeypatch):
    from pathlib import Path
    import axdata_core.diagnostics as diagnostics

    written_names: list[str] = []
    original_write_text = Path.write_text

    def spy_write_text(self: Path, *args, **kwargs):
        if self.parent == tmp_path:
            written_names.append(self.name)
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", spy_write_text)

    assert diagnostics._path_writable(tmp_path) is True
    assert written_names
    assert written_names[0].startswith(".axdata_write_probe_")
    assert written_names[0] != ".axdata_write_probe"
    assert not any(tmp_path.glob(".axdata_write_probe*"))


def test_tables_route_lists_initial_tables():
    client = TestClient(app)

    response = client.get("/v1/tables")

    assert response.status_code == 200
    assert set(response.json()["data"]) >= {
        "stock_basic_exchange",
        "trade_cal",
        "daily",
        "adj_factor",
    }
    assert "stock_basic" not in response.json()["data"]


def test_v1_query_supports_sdk_style_params_fields_filters_dates_and_limit(tmp_path, monkeypatch):
    root = tmp_path / "data"
    write_core_table("daily", pd.DataFrame(DAILY_ROWS), root=root)
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    client = TestClient(app)

    response = client.post(
        "/v1/query",
        json={
            "table": "daily",
            "columns": "ts_code,trade_date,close",
            "filters": {"ts_code": "000001.SZ", "ignored": None},
            "params": {
                "start": "2024-01-02",
                "end": "2024-01-03",
                "close": None,
            },
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"] == {"table": "daily", "count": 1}
    assert payload["data"] == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]


def test_v1_query_reads_ingested_tables_without_source_fetch(tmp_path, monkeypatch):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    client = TestClient(app)

    response = client.post(
        "/v1/query",
        json={
            "table": "daily",
            "params": {"ts_code": "000001.SZ", "start_date": "2024-01-02"},
        },
    )

    assert response.status_code == 404
    assert "daily" in response.json()["detail"]


def test_data_dataset_routes_list_inspect_and_preview(tmp_path, monkeypatch):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    parquet_path = tmp_path / "export" / "daily" / "parquet" / "daily.parquet"
    parquet_path.parent.mkdir(parents=True)
    pd.DataFrame(DAILY_ROWS).to_parquet(parquet_path, engine="pyarrow", index=False)
    CollectorSchedulerStore(data_root=root).create_run(
        CollectorRun(
            run_id="run_api_data",
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
                    "row_count": len(DAILY_ROWS),
                    "output_paths": {"parquet": str(parquet_path)},
                    "quality": {
                        "quality_status": "ok",
                        "date_field": "trade_date",
                        "write_mode": "upsert_by_key",
                        "partition_by": ["trade_date"],
                        "primary_key": "pass",
                        "write_primary_key": ["ts_code", "trade_date"],
                        "rows_before": 1,
                        "rows_written": len(DAILY_ROWS),
                        "rows_after": len(DAILY_ROWS),
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
                "rows_written": len(DAILY_ROWS),
                "rows_after": len(DAILY_ROWS),
                "duplicate_rows_dropped": 0,
            },
            created_at="2026-06-29T00:00:00+00:00",
            updated_at="2026-06-29T00:01:00+00:00",
            finished_at="2026-06-29T00:01:00+00:00",
        )
    )
    client = TestClient(app)

    list_response = client.get("/v1/data/datasets")
    inspect_response = client.get("/v1/data/datasets/daily")
    preview_response = client.get(
        "/v1/data/datasets/daily/preview",
        params={
            "symbol": "000001.SZ",
            "start": "2024-01-03",
            "end": "2024-01-31",
            "fields": "ts_code,trade_date,close",
            "limit": 1000,
        },
    )

    assert list_response.status_code == 200
    datasets = list_response.json()["data"]
    assert datasets[0]["dataset"] == "daily"
    assert datasets[0]["row_count"] == len(DAILY_ROWS)
    assert datasets[0]["write_mode"] == "upsert_by_key"
    assert datasets[0]["rows_after"] == len(DAILY_ROWS)

    assert inspect_response.status_code == 200
    assert inspect_response.json()["data"]["output_paths"]["parquet"] == str(parquet_path)
    assert inspect_response.json()["data"]["primary_key"] == ["ts_code", "trade_date"]

    assert preview_response.status_code == 200
    payload = preview_response.json()
    assert payload["meta"]["limit"] == 100
    assert payload["meta"]["columns"] == ["ts_code", "trade_date", "close"]
    assert payload["meta"]["preview_format"] == "parquet"
    assert payload["meta"]["preview_paths"] == [str(parquet_path.resolve())]
    assert payload["data"] == [
        {"ts_code": "000001.SZ", "trade_date": "20240103", "close": 10.6}
    ]


def test_data_dataset_route_deletes_local_dataset(tmp_path, monkeypatch):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    dataset_root = root / "snapshot" / "daily"
    parquet_path = root / "snapshot" / "daily" / "parquet" / "daily.parquet"
    parquet_path.parent.mkdir(parents=True)
    pd.DataFrame(DAILY_ROWS).to_parquet(parquet_path, engine="pyarrow", index=False)
    store = CollectorSchedulerStore(data_root=root)
    store.create_run(
        CollectorRun(
            run_id="run_delete_data",
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
                    "row_count": len(DAILY_ROWS),
                    "output_paths": {"parquet": str(parquet_path)},
                    "quality": {"quality_status": "ok", "date_field": "trade_date"},
                },
            },
            quality={"quality_status": "ok", "date_field": "trade_date"},
            created_at="2026-06-29T00:00:00+00:00",
            updated_at="2026-06-29T00:01:00+00:00",
            finished_at="2026-06-29T00:01:00+00:00",
        )
    )
    client = TestClient(app)

    delete_response = client.delete("/v1/data/datasets/daily")
    list_response = client.get("/v1/data/datasets")

    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted_paths"] == [str(dataset_root.resolve())]
    assert delete_response.json()["data"]["deleted_runs"] == ["run_delete_data"]
    assert not dataset_root.exists()
    assert store.get_run("run_delete_data") is None
    assert list_response.status_code == 200
    rows = list_response.json()["data"]
    daily_rows = [row for row in rows if row["dataset"] == "daily"]
    assert daily_rows == []
    assert "run_delete_data" not in {row.get("latest_run_id") for row in rows}


def test_request_interfaces_catalog_lists_stock_codes_tdx():
    client = TestClient(app)

    response = client.get("/v1/request/interfaces")

    assert response.status_code == 200
    payload = response.json()
    names = [item["name"] for item in payload["data"]]
    display_names = {item["name"]: item["display_name_zh"] for item in payload["data"]}
    source_codes = {item["source_code"] for item in payload["data"]}
    assert "stock_codes_tdx" in names
    assert "stock_st_list_tdx" in names
    assert "stock_suspensions_tdx" in names
    assert "stock_daily_share_tdx" in names
    assert "stock_daily_price_limit_tdx" in names
    assert "stock_trade_calendar_exchange" in names
    assert "stock_historical_list_exchange" in names
    assert "stock_basic_info_exchange" in names
    assert "stock_capital_changes_tdx" in names
    assert "stock_adj_factor_tdx" in names
    assert "stock_limit_ladder_tdx" in names
    assert "stock_theme_strength_rank_tdx" in names
    assert "stock_realtime_rank_tdx" in names
    assert "stock_realtime_snapshot_tdx" in names
    assert "stock_order_book_tdx" in names
    assert "stock_auction_process_tdx" in names
    assert "stock_auction_result_tdx" in names
    assert "stock_auction_result_history_tdx" in names
    assert "stock_shortline_indicators_tdx" in names
    assert "stock_intraday_buy_sell_strength_tdx" in names
    assert "stock_intraday_volume_comparison_tdx" in names
    assert "stock_intraday_today_tdx" in names
    assert "stock_intraday_history_tdx" in names
    assert "stock_trades_today_tdx" in names
    assert "stock_trades_history_tdx" in names
    assert "stock_finance_summary_tdx" in names
    assert "stock_share_capital_tdx" in names
    assert "stock_balance_summary_tdx" in names
    assert "stock_profit_cashflow_summary_tdx" in names
    assert "stock_finance_profile_tdx" in names
    assert "stock_kline_second_tdx" in names
    assert "stock_kline_yearly_tdx" in names
    assert "stock_company_profile_tdx" in names
    assert "stock_disclosure_feed_tdx" in names
    assert "stock_valuation_metrics_tdx" in names
    assert "futures_realtime_snapshot_tdx" in names
    assert "futures_kline_tdx" in names
    assert "futures_trades_today_tdx" in names
    assert "futures_trades_history_tdx" in names
    assert "option_chain_tdx" in names
    assert "option_realtime_snapshot_tdx" in names
    assert "option_trades_today_tdx" not in names
    assert "option_trades_history_tdx" not in names
    assert "fund_nav_tdx" in names
    assert "bond_realtime_snapshot_tdx" in names
    assert "fx_realtime_snapshot_tdx" in names
    assert "fx_trades_today_tdx" in names
    assert "fx_trades_history_tdx" in names
    assert "macro_indicator_snapshot_tdx" in names
    assert "cninfo_announcements" in names
    assert "cninfo_announcement_detail" in names
    assert "tencent_realtime_snapshot" in names
    assert "eastmoney_dragon_tiger_daily" in names
    assert "eastmoney_margin_trading" in names
    assert "eastmoney_research_reports" in names
    assert source_codes <= {"tdx", "tdx_ext", "exchange", "cninfo", "tencent", "eastmoney", "sina", "cls", "kph"}
    assert display_names["stock_codes_tdx"] == "最新股票列表"
    assert display_names["stock_st_list_tdx"] == "最新ST股票列表"
    assert display_names["stock_suspensions_tdx"] == "最新停牌列表"
    assert display_names["stock_daily_share_tdx"] == "每日股本（盘前）"
    assert display_names["stock_daily_price_limit_tdx"] == "涨跌停价格"
    assert display_names["stock_trade_calendar_exchange"] == "交易日历"
    assert display_names["stock_historical_list_exchange"] == "历史股票列表"
    assert display_names["stock_basic_info_exchange"] == "股票基础信息"
    assert display_names["stock_capital_changes_tdx"] == "股本变迁"
    assert display_names["stock_adj_factor_tdx"] == "复权因子"
    assert display_names["stock_limit_ladder_tdx"] == "连板天梯"
    assert display_names["stock_theme_strength_rank_tdx"] == "题材强度排行"
    assert display_names["stock_realtime_rank_tdx"] == "实时榜单"
    assert display_names["stock_realtime_snapshot_tdx"] == "实时快照"
    assert display_names["stock_order_book_tdx"] == "五档盘口"
    assert display_names["stock_auction_process_tdx"] == "竞价明细"
    assert display_names["stock_auction_result_tdx"] == "竞价结果"
    assert display_names["stock_auction_result_history_tdx"] == "历史竞价结果"
    assert display_names["stock_shortline_indicators_tdx"] == "短线指标"
    assert display_names["stock_intraday_buy_sell_strength_tdx"] == "买卖力道"
    assert display_names["stock_intraday_volume_comparison_tdx"] == "成交对比"
    assert display_names["stock_intraday_today_tdx"] == "当日分时"
    assert display_names["stock_intraday_history_tdx"] == "历史分时"
    assert display_names["stock_intraday_recent_history_tdx"] == "近期历史分时"
    assert display_names["stock_trades_today_tdx"] == "当日成交明细"
    assert display_names["stock_trades_history_tdx"] == "历史成交明细"
    assert display_names["stock_finance_summary_tdx"] == "财务基础摘要"
    assert display_names["stock_share_capital_tdx"] == "股本结构"
    assert display_names["stock_balance_summary_tdx"] == "资产负债摘要"
    assert display_names["stock_profit_cashflow_summary_tdx"] == "利润现金流摘要"
    assert display_names["stock_finance_profile_tdx"] == "财务资料标签"
    assert display_names["stock_kline_second_tdx"] == "秒K线"
    assert display_names["stock_company_profile_tdx"] == "公司概况"
    assert display_names["stock_disclosure_feed_tdx"] == "新闻公告路演"
    assert display_names["stock_event_drivers_tdx"] == "历史事件关联"
    assert display_names["stock_valuation_metrics_tdx"] == "估值表"
    assert display_names["futures_realtime_snapshot_tdx"] == "期货实时快照"
    assert display_names["futures_trades_today_tdx"] == "期货当日逐笔"
    assert display_names["futures_trades_history_tdx"] == "期货历史逐笔"
    assert display_names["option_chain_tdx"] == "期权T型报价"
    assert display_names["fund_nav_tdx"] == "基金净值"
    assert display_names["fx_trades_today_tdx"] == "外汇当日逐笔"
    assert display_names["fx_trades_history_tdx"] == "外汇历史逐笔"
    assert display_names["macro_indicator_snapshot_tdx"] == "宏观指标快照"
    assert display_names["cninfo_announcements"] == "公告列表"
    assert display_names["cninfo_announcement_detail"] == "公告PDF元信息"
    assert display_names["tencent_realtime_snapshot"] == "实时快照"
    assert display_names["eastmoney_dragon_tiger_daily"] == "龙虎榜每日汇总"
    assert display_names["eastmoney_margin_trading"] == "融资融券明细"
    assert display_names["eastmoney_research_reports"] == "个股研报列表"
    assert payload["meta"]["count"] == EXPECTED_SOURCE_REQUEST_INTERFACE_COUNT
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False
    assert payload["meta"]["catalog_source"] == "axdata_core.provider_registry"
    stock_codes = next(item for item in payload["data"] if item["name"] == "stock_codes_tdx")
    fx_codes = next(item for item in payload["data"] if item["name"] == "fx_codes_tdx")
    assert stock_codes["provider_id"] == TDX_PROVIDER_ID
    assert stock_codes["effective_trust_level"] == "official"
    assert stock_codes["plugin_status"] == "enabled"
    assert stock_codes["enabled"] is True
    assert stock_codes["asset_class"] == "stock"
    assert fx_codes["provider_id"] == TDX_EXT_PROVIDER_ID
    assert fx_codes["asset_class"] == "fx"


def test_plugin_provider_status_catalog_lists_builtin_providers():
    client = TestClient(app)

    response = client.get("/v1/plugins/providers")

    assert response.status_code == 200
    payload = response.json()
    providers = {item["provider_id"]: item for item in payload["data"]}

    assert "axdata.source.tdx" not in providers
    assert providers[TDX_PROVIDER_ID]["status"] == "enabled"
    assert providers[TDX_PROVIDER_ID]["effective_trust_level"] == "official"
    assert providers[TDX_PROVIDER_ID]["built_in"] is True
    assert providers[TDX_PROVIDER_ID]["install_source"] == "preinstalled"
    assert providers[TDX_PROVIDER_ID]["provider_kind"] == "source_plugin"
    assert providers[TDX_PROVIDER_ID]["can_uninstall"] is True
    assert providers[TDX_PROVIDER_ID]["uninstall_mode"] == "managed_disable"
    assert providers[TDX_PROVIDER_ID]["uninstall_block_reason"] is None
    assert providers[TDX_PROVIDER_ID]["collector_count"] == 0
    assert providers[TDX_PROVIDER_ID]["dependency_count"] == 0
    assert providers[TDX_PROVIDER_ID]["status_message"]
    assert providers[TDX_PROVIDER_ID]["next_action"] is None
    assert providers[TDX_PROVIDER_ID]["collectors"] == []
    assert providers[TDX_PROVIDER_ID]["dependencies"] == []
    assert providers[TDX_PROVIDER_ID]["config_schema"] == {"required_config": []}
    assert providers[TDX_EXT_PROVIDER_ID]["source_name_zh"] == "通达信扩展行情"
    assert providers[TDX_EXT_PROVIDER_ID]["interface_count"] == TDX_EXT_SOURCE_INTERFACE_COUNT
    assert providers[TDX_EXT_PROVIDER_ID]["install_source"] == "preinstalled"
    assert providers[TDX_EXT_PROVIDER_ID]["can_uninstall"] is True
    assert providers["axdata.source.tencent"]["source_code"] == "tencent"
    assert providers["axdata.source.tencent"]["interface_count"] == len(TENCENT_BUILTIN_INTERFACE_NAMES)
    assert providers["axdata.source.tencent"]["install_source"] == "preinstalled"
    assert providers["axdata.source.tencent"]["provider_kind"] == "source_plugin"
    assert providers["axdata.source.tencent"]["can_uninstall"] is True
    assert providers["axdata.source.tencent"]["uninstall_mode"] == "managed_disable"
    assert providers["axdata.source.tencent"]["uninstall_block_reason"] is None
    assert payload["meta"]["catalog_source"] == "axdata_core.provider_registry"


def test_plugin_provider_status_catalog_omits_ignored_entry_point_candidates(monkeypatch, tmp_path):
    import axdata_core.provider_registry as provider_registry

    class FakeDistribution:
        metadata = {"Name": "broken-source"}
        files = []

        def locate_file(self, item):  # pragma: no cover
            raise AssertionError("no manifest files should be located")

    class FakeEntryPoint:
        name = "tdx_ext"
        dist = FakeDistribution()

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(provider_registry, "_provider_entry_points", lambda: (FakeEntryPoint(),))
    client = TestClient(app)

    response = client.get("/v1/plugins/providers")

    assert response.status_code == 200
    providers = {item["provider_id"]: item for item in response.json()["data"]}
    assert "entry_point.tdx_ext" not in providers
    assert TDX_EXT_PROVIDER_ID in providers


def test_preinstalled_provider_uninstall_is_logical_and_keeps_history(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)

    response = client.delete("/v1/plugins/installed/axdata.source.tencent")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["uninstall_mode"] == "managed_disable"
    assert payload["removed_paths"] == []

    provider_response = client.get("/v1/plugins/providers/axdata.source.tencent")
    provider = provider_response.json()["data"]
    assert provider["status"] == "uninstalled"
    assert provider["enabled"] is False
    assert provider["can_enable"] is True


def test_plugin_provider_status_catalog_shows_missing_tdx_providers(monkeypatch, tmp_path):
    import importlib

    import axdata_core
    import axdata_core.provider_catalog as provider_catalog

    provider_catalog = importlib.reload(provider_catalog)
    base_builder = provider_catalog.build_builtin_provider_registry

    def build_registry_without_entry_points(**kwargs):
        kwargs["discover_entry_points"] = False
        return base_builder(**kwargs)

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", build_registry_without_entry_points)
    monkeypatch.setattr(axdata_core, "build_builtin_provider_registry", build_registry_without_entry_points)
    client = TestClient(app)

    response = client.get("/v1/plugins/providers")

    assert response.status_code == 200
    providers = {item["provider_id"]: item for item in response.json()["data"]}
    assert providers[TDX_PROVIDER_ID]["status"] == "missing"
    assert providers[TDX_PROVIDER_ID]["source_name_zh"] == "通达信"
    assert providers[TDX_PROVIDER_ID]["interface_count"] == 90
    assert "普通 TDX 接口不会出现在运行目录" in providers[TDX_PROVIDER_ID]["status_message"]
    assert providers[TDX_EXT_PROVIDER_ID]["status"] == "missing"
    assert providers[TDX_EXT_PROVIDER_ID]["source_name_zh"] == "通达信扩展行情"
    assert providers[TDX_EXT_PROVIDER_ID]["interface_count"] == TDX_EXT_SOURCE_INTERFACE_COUNT
    assert "扩展行情接口不会出现在运行目录" in providers[TDX_EXT_PROVIDER_ID]["status_message"]


def test_plugin_provider_status_detail_route():
    client = TestClient(app)

    response = client.get("/v1/plugins/providers/axdata.source.tencent")

    assert response.status_code == 200
    provider = response.json()["data"]
    assert provider["provider_id"] == "axdata.source.tencent"
    assert provider["interfaces"] == TENCENT_BUILTIN_INTERFACE_NAMES
    assert provider["downloader_count"] == 0
    assert provider["collector_count"] == 0
    assert provider["downloaders"] == []
    assert provider["collectors"] == []
    assert provider["status_message"]
    assert provider["next_action"] is None


def test_plugin_collectors_routes_list_and_get(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    collector = {
        "name": "close.refresh.daily",
        "collector_name": "close.refresh.daily",
        "display_name_zh": "收盘刷新",
        "description": "每日收盘后刷新基础数据。",
        "provider_id": "axdata.plugin.close_refresh",
        "source_code": "plugin",
        "source_name_zh": "收盘刷新",
        "declared_trust_level": "community",
        "effective_trust_level": "community",
        "built_in": False,
        "plugin_status": "enabled",
        "enabled": True,
        "interfaces": ["stock_codes_tdx"],
        "downloader_profile": "tdx.stock_codes.latest",
        "resource_group": "tdx.quote",
        "default_schedule": {"frequency": "daily", "time": "18:05"},
        "default_params": {"scope": "all"},
        "required_interfaces": ["stock_codes_tdx"],
        "output": {"layer": "raw"},
        "required_config": [],
        "config_schema": {"required_config": []},
    }

    import axdata_core

    monkeypatch.setattr(
        axdata_core,
        "list_registry_collector_dicts",
        lambda **_kwargs: (collector,),
    )

    client = TestClient(app)
    list_response = client.get("/v1/plugins/collectors")
    detail_response = client.get("/v1/plugins/collectors/close.refresh.daily")
    missing_response = client.get("/v1/plugins/collectors/missing.collector")

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["data"] == [collector]
    assert list_payload["meta"]["count"] == 1
    assert list_payload["meta"]["catalog_source"] == "axdata_core.collector_registry"

    assert detail_response.status_code == 200
    assert detail_response.json()["data"] == collector

    assert missing_response.status_code == 404
    assert "Unknown collector" in missing_response.json()["detail"]


def test_plugin_collector_run_route_uses_runner(monkeypatch, tmp_path):
    from types import SimpleNamespace

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    import axdata_core

    def fake_build_plan(collector_name, **kwargs):
        assert collector_name == "close_refresh_daily"
        assert kwargs["params"] == {"scope": "stock"}
        return SimpleNamespace(
            target_interface="stock_codes_tdx",
            params={"scope": "stock", "adjust": "none"},
            fields=["instrument_id"],
            formats=["csv"],
        )

    def fake_run_collector(collector_name, **kwargs):
        calls.append({"collector_name": collector_name, **kwargs})
        return {
            "collector_name": collector_name,
            "target_interface": "stock_codes_tdx",
            "status": "success",
            "download_result": {
                "job_id": "run_api_collector",
                "row_count": 1,
                "output_path": str(tmp_path / "export" / "stock_codes.csv"),
            },
        }

    monkeypatch.setattr(axdata_core, "build_collector_run_plan", fake_build_plan)
    monkeypatch.setattr(axdata_core, "run_collector", fake_run_collector)

    client = TestClient(app)
    response = client.post(
        "/v1/plugins/collectors/close_refresh_daily/run",
        json={
            "params": {"scope": "stock"},
            "fields": ["instrument_id"],
            "output_root": str(tmp_path / "export"),
            "formats": ["csv"],
            "concurrency_mode": "low",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["collector_name"] == "close_refresh_daily"
    assert payload["download_result"]["row_count"] == 1
    assert calls == [
        {
            "collector_name": "close_refresh_daily",
            "params": {"scope": "stock", "adjust": "none"},
            "fields": ["instrument_id"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["csv"],
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


def test_plugin_collector_run_route_returns_404_for_missing_collector(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import axdata_core

    def fake_build_plan(collector_name, **_kwargs):
        raise axdata_core.CollectorError(f"Collector {collector_name!r} is not available.")

    monkeypatch.setattr(axdata_core, "build_collector_run_plan", fake_build_plan)
    client = TestClient(app)

    response = client.post("/v1/plugins/collectors/missing_collector/run", json={})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COLLECTOR_NOT_CONFIGURED"


def test_plugin_collector_run_async_enters_download_job_queue(monkeypatch, tmp_path):
    from types import SimpleNamespace

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes
    import axdata_core

    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()

    class InlineExecutor:
        def submit(self, fn, *args, **kwargs):
            fn(*args, **kwargs)

    def fake_build_plan(collector_name, **_kwargs):
        return SimpleNamespace(
            target_interface="stock_codes_tdx",
            params={"scope": "all"},
            fields=["instrument_id"],
            formats=["jsonl"],
        )

    def fake_run_collector(collector_name, **kwargs):
        progress_callback = kwargs.get("progress_callback")
        if progress_callback is not None:
            progress_callback(60, "采集器执行中", progress_current=6, progress_total=10)
        return {
            "collector_name": collector_name,
            "target_interface": "stock_codes_tdx",
            "status": "success",
            "download_result": {
                "job_id": "run_async_collector",
                "row_count": 2,
                "output_path": str(tmp_path / "data" / "stock_codes.jsonl"),
            },
        }

    monkeypatch.setattr(routes, "_executor", InlineExecutor())
    monkeypatch.setattr(axdata_core, "build_collector_run_plan", fake_build_plan)
    monkeypatch.setattr(axdata_core, "run_collector", fake_run_collector)

    client = TestClient(app)
    response = client.post(
        "/v1/plugins/collectors/close_refresh_daily/run",
        json={"params": {"scope": "all"}, "fields": ["instrument_id"], "async_job": True},
    )

    assert response.status_code == 202
    job_id = response.json()["data"]["job_id"]
    job_response = client.get(f"/v1/download/jobs/{job_id}")

    assert job_response.status_code == 200
    job = job_response.json()["data"]
    assert job["job_kind"] == "collector"
    assert job["collector_name"] == "close_refresh_daily"
    assert job["interface_name"] == "stock_codes_tdx"
    assert job["status"] == "success"
    assert job["result"]["download_result"]["row_count"] == 2
    assert job["progress_current"] == 6
    assert job["progress_total"] == 10


def test_collector_task_api_creates_runs_and_status(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.collector_routes as routes
    import axdata_core.collector_runner as collector_runner

    routes._collector_service_cache.clear()

    class Plan:
        collector_name = "close_refresh_daily"
        display_name_zh = "收盘刷新"
        provider_id = "axdata.plugin.close_refresh"
        downloader_profile = "demo.stock_codes.snapshot"
        params = {"scope": "stock"}
        fields = ["instrument_id"]
        formats = ["jsonl"]
        resource_group = "demo.quote"

    def fake_build_plan(collector_name, **_kwargs):
        assert collector_name == "close_refresh_daily"
        return Plan()

    def fake_run_collector(collector_name, **kwargs):
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {
                "row_count": 1,
                "output_paths": {"jsonl": str(tmp_path / "out.jsonl")},
                "quality": {
                    "row_count": "pass",
                    "row_count_value": 1,
                    "write_mode": "upsert_by_key",
                    "write_primary_key": ["instrument_id"],
                    "rows_written": 1,
                    "rows_after": 1,
                },
            },
        }

    monkeypatch.setattr(collector_runner, "build_collector_run_plan", fake_build_plan)
    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)

    client = TestClient(app)
    create_response = client.post(
        "/v1/collector/tasks",
        json={
            "collector_name": "close_refresh_daily",
            "task_id": "task_close",
            "trigger_type": "interval",
            "interval_seconds": 60,
            "params": {"scope": "stock"},
            "fields": ["instrument_id"],
            "formats": ["jsonl"],
            "max_retries": 2,
            "backoff_seconds": 3,
        },
    )

    assert create_response.status_code == 201
    task = create_response.json()["data"]
    assert task["task_id"] == "task_close"
    assert task["provider_id"] == "axdata.plugin.close_refresh"
    assert task["trigger_type"] == "interval"
    assert task["max_retries"] == 2
    assert task["backoff_seconds"] == 3
    assert task["status_message"]
    assert task["action_command"] is None

    run_response = client.post("/v1/collector/tasks/task_close/run", json={})
    assert run_response.status_code == 202
    submitted_run = run_response.json()["data"]
    run_id = submitted_run["run_id"]
    assert submitted_run["status_message"]
    assert submitted_run["action_command"] == "axdata collector status --json"

    for _ in range(20):
        run_payload = client.get(f"/v1/collector/runs/{run_id}").json()["data"]
        if run_payload["status"] == "success":
            break
    else:  # pragma: no cover
        raise AssertionError("collector task run did not finish")

    assert run_payload["output_paths"] == {"jsonl": str(tmp_path / "out.jsonl")}
    assert run_payload["records_read"] == 1
    assert run_payload["rows_written"] == 1
    assert run_payload["write_mode"] == "upsert_by_key"
    assert run_payload["primary_key"] == ["instrument_id"]
    assert run_payload["events"][0]["stage"] == "queued"
    assert run_payload["events"][-1]["stage"] == "finished"
    assert run_payload["stage_timings"]["total_ms"] is not None
    assert run_payload["error_category"] is None
    assert "成功" in run_payload["status_message"]
    assert client.get(f"/v1/runs/{run_id}").json()["data"]["run_id"] == run_id
    task_runs_response = client.get("/v1/tasks/task_close/runs")
    assert task_runs_response.status_code == 200
    assert task_runs_response.json()["data"][0]["run_id"] == run_id
    task_detail = client.get("/v1/collector/tasks/task_close").json()["data"]
    assert task_detail["last_status"] == "success"
    assert "成功" in task_detail["status_message"]
    assert client.get("/v1/collector/runs").json()["meta"]["count"] == 1
    assert client.get("/v1/collector/runs?limit=999999").json()["meta"]["count"] == 1
    status_payload = client.get("/v1/collector/status").json()["data"]
    assert status_payload["task_count"] == 2
    assert status_payload["enabled_task_count"] == 1
    assert status_payload["run_count"] == 1
    assert status_payload["total_run_count"] == 1
    assert status_payload["recent_run_limit"] == 100
    assert status_payload["status_counts"] == {"success": 1}
    assert status_payload["latest_runs"]["task_close"]["run_id"] == run_id
    assert "成功" in status_payload["latest_runs"]["task_close"]["status_message"]

    disable_response = client.post("/v1/collector/tasks/task_close/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["enabled"] is False
    assert disable_response.json()["data"]["action_command"] == "axdata collector task enable task_close"


def test_collector_run_delete_removes_finished_history(monkeypatch, tmp_path):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    store = CollectorSchedulerStore(data_root=root)
    run = store.create_run(
        CollectorRun(
            run_id="run_delete_finished",
            task_id="demo_task",
            collector_name="demo.collector",
            trigger_type="manual",
            status="failed",
            error="stale failure",
        )
    )
    client = TestClient(app)

    delete_response = client.delete(f"/v1/collector/runs/{run.run_id}")
    get_response = client.get(f"/v1/collector/runs/{run.run_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["run_id"] == run.run_id
    assert get_response.status_code == 404


def test_collector_run_delete_refuses_active_run(monkeypatch, tmp_path):
    root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(root))
    store = CollectorSchedulerStore(data_root=root)
    run = store.create_run(
        CollectorRun(
            run_id="run_delete_active",
            task_id="demo_task",
            collector_name="demo.collector",
            trigger_type="manual",
            status="running",
        )
    )
    client = TestClient(app)

    delete_response = client.delete(f"/v1/collector/runs/{run.run_id}")

    assert delete_response.status_code == 409
    assert store.get_run(run.run_id) is not None


def test_collector_task_template_api_and_backfill(monkeypatch, tmp_path):
    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    import apps.api.collector_routes as routes
    import axdata_core.collector_runner as collector_runner

    routes._collector_service_cache.clear()
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

    def fake_build_plan(collector_name, **_kwargs):
        assert collector_name == "tdx.stock_kline_daily_tdx.snapshot"
        return Plan()

    def fake_run_collector(collector_name, **kwargs):
        calls.append(dict(kwargs["params"]))
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {
                "row_count": 1,
                "output_paths": {"parquet": str(tmp_path / "out.parquet")},
                "quality": {"quality_status": "ok"},
            },
        }

    monkeypatch.setattr(collector_runner, "build_collector_run_plan", fake_build_plan)
    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)

    client = TestClient(app)
    templates_response = client.get("/v1/collector/tasks/templates")
    assert templates_response.status_code == 200
    templates = {row["template_id"]: row for row in templates_response.json()["data"]}
    assert "trade_cal" not in templates
    assert "stock_basic_exchange" not in templates
    assert templates["stock_kline_daily_tdx"]["default_params"] == {"code": "000001.SZ", "count": 800, "adjust": "none"}
    assert templates["stock_kline_daily_tdx"]["required_datasets"] == ["trade_cal"]
    assert templates["daily"]["safety_limits"]["full_market_by_default"] is False
    assert templates["daily"]["required_datasets"] == ["trade_cal"]

    create_response = client.post(
        "/v1/collector/tasks/from-template",
        json={"template_id": "stock_kline_daily_tdx", "task_id": "kline_template_test"},
    )
    assert create_response.status_code == 201
    task = create_response.json()["data"]
    assert task["task_id"] == "kline_template_test"
    assert task["last_failure_at"] is None
    assert task["queue_status"] == "ready"
    assert task["can_run_now"] is True

    run_response = client.post(
        "/v1/collector/tasks/kline_template_test/run",
        json={"params": {"adjust": "qfq"}, "symbol": "000002.SZ", "limit": 2},
    )
    assert run_response.status_code == 202
    run_id = run_response.json()["data"]["run_id"]
    for _ in range(20):
        run_payload = client.get(f"/v1/collector/runs/{run_id}").json()["data"]
        if run_payload["status"] == "success":
            break
    assert run_payload["params_override"] == {"adjust": "qfq", "code": "000002.SZ", "limit": 2, "count": 2}
    assert calls[-1] == {"code": "000002.SZ", "count": 2, "adjust": "qfq", "limit": 2}

    backfill_response = client.post(
        "/v1/collector/tasks/kline_template_test/backfill",
        json={"start": "2024-01-02", "end": "20240103", "params": {"adjust": "none"}},
    )
    assert backfill_response.status_code == 202
    backfill_id = backfill_response.json()["data"]["run_id"]
    for _ in range(20):
        backfill_payload = client.get(f"/v1/collector/runs/{backfill_id}").json()["data"]
        if backfill_payload["status"] == "success":
            break
    assert backfill_payload["metadata"]["run_mode"] == "backfill"
    assert backfill_payload["params_override"] == {
        "start_date": "20240102",
        "end_date": "20240103",
        "adjust": "none",
    }


def test_collector_task_api_lists_seeded_default_tasks_and_tdx_dependency(monkeypatch, tmp_path):
    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    import apps.api.collector_routes as routes

    routes._collector_service_cache.clear()
    disable_provider(TDX_COLLECTOR_PLUGIN_ID, data_root=data_root)

    client = TestClient(app)
    response = client.get("/v1/collector/tasks")
    assert response.status_code == 200
    tasks = {row["task_id"]: row for row in response.json()["data"]}

    assert {
        "stock_kline_daily_tdx_sample",
    } <= set(tasks)
    assert "stock_basic_exchange_refresh" not in tasks
    assert "trade_cal_refresh" not in tasks
    assert tasks["stock_kline_daily_tdx_sample"]["write_mode"] == "snapshot"
    assert tasks["stock_kline_daily_tdx_sample"]["required_datasets"] == ["trade_cal"]
    assert tasks["stock_kline_daily_tdx_sample"]["dependency_status"] == "disabled"
    assert "请安装/启用 TDX 采集器插件" in tasks["stock_kline_daily_tdx_sample"]["dependency_message"]

    run_response = client.post("/v1/collector/tasks/stock_kline_daily_tdx_sample/run", json={})
    assert run_response.status_code == 202
    run_payload = run_response.json()["data"]
    assert run_payload["status"] == "failed"
    assert run_payload["error_category"] == "plugin_disabled"
    assert "请安装/启用 TDX 采集器插件" in run_payload["error_summary"]


def test_collector_task_api_returns_trade_calendar_dependency_status(monkeypatch, tmp_path):
    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))

    import apps.api.collector_routes as routes

    routes._collector_service_cache.clear()

    client = TestClient(app)
    response = client.get("/v1/collector/tasks")
    assert response.status_code == 200
    tasks = {row["task_id"]: row for row in response.json()["data"]}
    daily_task = tasks["stock_kline_daily_tdx_sample"]

    assert daily_task["required_datasets"] == ["trade_cal"]
    assert daily_task["dependency_status"] == "blocked"
    assert daily_task["dependency_errors"][0]["dataset"] == "trade_cal"
    assert "交易日历未同步" in daily_task["dependency_message"]
    assert daily_task["next_action"]

    run_response = client.post("/v1/collector/tasks/stock_kline_daily_tdx_sample/run", json={})
    assert run_response.status_code == 202
    run_payload = run_response.json()["data"]
    assert run_payload["status"] == "failed"
    assert run_payload["error_category"] == "dependency_missing"
    assert "交易日历未同步" in run_payload["error_summary"]
    assert run_payload["metadata"]["dependency_errors"][0]["dataset"] == "trade_cal"
    assert run_payload["next_action"]


def test_collector_run_api_returns_failure_diagnostics(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.collector_routes as routes
    import axdata_core.collector_runner as collector_runner

    routes._collector_service_cache.clear()

    class Plan:
        collector_name = "close_refresh_daily"
        display_name_zh = "收盘刷新"
        provider_id = "axdata.plugin.close_refresh"
        downloader_profile = "demo.stock_codes.snapshot"
        params = {"scope": "stock"}
        fields = ["instrument_id"]
        formats = ["jsonl"]
        resource_group = "demo.quote"

    monkeypatch.setattr(collector_runner, "build_collector_run_plan", lambda collector_name, **_kwargs: Plan())

    def failing_run_collector(*_args, **_kwargs):
        raise PermissionError("access is denied")

    monkeypatch.setattr(collector_runner, "run_collector", failing_run_collector)

    client = TestClient(app)
    create_response = client.post(
        "/v1/collector/tasks",
        json={
            "collector_name": "close_refresh_daily",
            "task_id": "task_failed",
        },
    )
    assert create_response.status_code == 201

    run_id = client.post("/v1/collector/tasks/task_failed/run", json={}).json()["data"]["run_id"]
    for _ in range(20):
        run_payload = client.get(f"/v1/collector/runs/{run_id}").json()["data"]
        if run_payload["status"] == "failed":
            break

    assert run_payload["error_category"] == "storage_permission"
    assert run_payload["error_summary"] == "access is denied"
    assert run_payload["events"][-1]["stage"] == "failed"
    assert run_payload["events"][-1]["category"] == "storage_permission"


def test_collector_task_api_reports_missing_task(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.collector_routes as routes

    routes._collector_service_cache.clear()
    client = TestClient(app)

    response = client.post("/v1/collector/tasks/missing/run", json={})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COLLECTOR_TASK_NOT_FOUND"


def test_plugin_provider_enable_disable_routes_update_catalog(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)

    disable_response = client.post("/v1/plugins/providers/axdata.source.tencent/disable")

    assert disable_response.status_code == 200
    disabled = disable_response.json()["data"]
    assert disabled["provider_id"] == "axdata.source.tencent"
    assert disabled["status"] == "disabled"
    assert disabled["enabled"] is False

    catalog_response = client.get("/v1/request/interfaces")
    assert catalog_response.status_code == 200
    items = {item["name"]: item for item in catalog_response.json()["data"]}
    assert items["tencent_realtime_snapshot"]["plugin_status"] == "disabled"
    assert items["tencent_realtime_snapshot"]["enabled"] is False
    assert items["tencent_realtime_snapshot"]["action_command"] == (
        "axdata plugin enable axdata.source.tencent"
    )

    enable_response = client.post("/v1/plugins/providers/axdata.source.tencent/enable")

    assert enable_response.status_code == 200
    enabled = enable_response.json()["data"]
    assert enabled["status"] == "enabled"
    assert enabled["enabled"] is True

    catalog_response = client.get("/v1/request/interfaces")
    assert catalog_response.status_code == 200
    items = {item["name"]: item for item in catalog_response.json()["data"]}
    assert items["tencent_realtime_snapshot"]["plugin_status"] == "enabled"


def test_plugin_provider_override_route_resolves_conflict(monkeypatch, tmp_path):
    from axdata_core.plugin_config import enable_provider, load_plugin_config
    from tests.test_tencent_provider_package import _clear_tencent_modules, _install_tencent_provider

    install_root = _install_tencent_provider(tmp_path)
    data_root = tmp_path / "data"
    monkeypatch.syspath_prepend(str(install_root))
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    enable_provider(TENCENT_PROVIDER_ID, data_root=data_root)
    _clear_tencent_modules()

    client = TestClient(app)

    conflict_response = client.get("/v1/plugins/providers")
    assert conflict_response.status_code == 200
    conflict_providers = {item["provider_id"]: item for item in conflict_response.json()["data"]}
    assert conflict_providers[BUILTIN_TENCENT_PROVIDER_ID]["status"] == "enabled"
    assert conflict_providers[TENCENT_PROVIDER_ID]["status"] == "conflict"

    override_response = client.post(
        f"/v1/plugins/overrides/{TENCENT_INTERFACE_NAME}",
        json={"provider_id": TENCENT_PROVIDER_ID},
    )

    assert override_response.status_code == 200
    assert load_plugin_config(data_root=data_root).provider_overrides == {
        TENCENT_INTERFACE_NAME: TENCENT_PROVIDER_ID,
    }
    providers = {item["provider_id"]: item for item in override_response.json()["data"]["providers"]}
    assert providers[TENCENT_PROVIDER_ID]["status"] == "enabled"
    assert providers[TENCENT_PROVIDER_ID]["overridden_interfaces"] == [TENCENT_INTERFACE_NAME]
    assert providers[BUILTIN_TENCENT_PROVIDER_ID]["status"] == "conflict"

    catalog_response = client.get("/v1/request/interfaces")
    assert catalog_response.status_code == 200
    catalog_entries = {item["name"]: item for item in catalog_response.json()["data"]}
    assert catalog_entries[TENCENT_INTERFACE_NAME]["provider_id"] == TENCENT_PROVIDER_ID

    clear_response = client.delete(f"/v1/plugins/overrides/{TENCENT_INTERFACE_NAME}")

    assert clear_response.status_code == 200
    assert load_plugin_config(data_root=data_root).provider_overrides == {}
    providers = {item["provider_id"]: item for item in clear_response.json()["data"]["providers"]}
    assert providers[TENCENT_PROVIDER_ID]["status"] == "conflict"
    assert providers[TENCENT_PROVIDER_ID]["overridden_interfaces"] == []


def test_plugin_installed_api_lists_and_uninstalls_axdata_managed_plugin(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    axp_path = _build_tencent_axp(tmp_path)
    client = TestClient(app)

    with axp_path.open("rb") as handle:
        install_response = client.post(
            "/v1/plugins/axp/install",
            files={"file": ("tencent.axp", handle, "application/zip")},
        )

    assert install_response.status_code == 200
    install_payload = install_response.json()["data"]
    assert install_payload["provider_id"] == TENCENT_PROVIDER_ID
    assert install_payload["enabled"] is False

    list_response = client.get("/v1/plugins/installed")

    assert list_response.status_code == 200
    installed = list_response.json()["data"]
    assert [item["provider_id"] for item in installed] == [TENCENT_PROVIDER_ID]
    assert installed[0]["status"] == "disabled"
    assert installed[0]["enabled"] is False
    assert installed[0]["effective_trust_level"] == "community"
    assert installed[0]["install_source"] == "axp_managed"
    assert installed[0]["can_uninstall"] is True
    assert installed[0]["uninstall_block_reason"] is None
    assert installed[0]["next_action"]
    assert installed[0]["action_command"] == f"axdata plugin enable {TENCENT_PROVIDER_ID}"
    assert installed[0]["interfaces"] == [TENCENT_INTERFACE_NAME]

    uninstall_response = client.delete(f"/v1/plugins/installed/{TENCENT_PROVIDER_ID}")

    assert uninstall_response.status_code == 200
    assert uninstall_response.json()["data"]["provider_id"] == TENCENT_PROVIDER_ID
    assert client.get("/v1/plugins/installed").json()["data"] == []
    catalog = {
        item["name"]: item
        for item in client.get("/v1/request/interfaces").json()["data"]
    }
    assert catalog[TENCENT_INTERFACE_NAME]["provider_id"] == BUILTIN_TENCENT_PROVIDER_ID


def test_plugin_axp_export_api_downloads_previewable_archive(monkeypatch, tmp_path):
    from axdata_core.axp import preview_axp

    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    client = TestClient(app)

    response = client.get(f"/v1/plugins/axp/export/{BUILTIN_TENCENT_PROVIDER_ID}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert ".axp" in response.headers["content-disposition"]
    exported_path = tmp_path / "exported.axp"
    exported_path.write_bytes(response.content)
    preview = preview_axp(exported_path, data_root=data_root)
    assert preview.provider_id == BUILTIN_TENCENT_PROVIDER_ID
    assert preview.wheels
    assert {wheel.checksum_status for wheel in preview.wheels} == {"ok"}


def test_plugin_installed_api_rejects_enabled_uninstall_and_duplicate_install(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    axp_path = _build_tencent_axp(tmp_path)
    client = TestClient(app)

    with axp_path.open("rb") as handle:
        first_response = client.post(
            "/v1/plugins/axp/install",
            files={"file": ("tencent.axp", handle, "application/zip")},
        )
    assert first_response.status_code == 200

    with axp_path.open("rb") as handle:
        duplicate_response = client.post(
            "/v1/plugins/axp/install",
            files={"file": ("tencent.axp", handle, "application/zip")},
        )
    assert duplicate_response.status_code == 409
    assert "already installed" in duplicate_response.json()["detail"]

    with axp_path.open("rb") as handle:
        replace_response = client.post(
            "/v1/plugins/axp/install",
            data={"replace": "true", "enable": "true"},
            files={"file": ("tencent.axp", handle, "application/zip")},
        )
    assert replace_response.status_code == 200
    replace_payload = replace_response.json()["data"]
    assert replace_payload["replaced"] is True
    assert replace_payload["enabled"] is True
    assert replace_payload["status_after_install"] == "enabled"

    uninstall_enabled = client.delete(f"/v1/plugins/installed/{TENCENT_PROVIDER_ID}")
    assert uninstall_enabled.status_code == 409
    assert "Disable it before uninstalling" in uninstall_enabled.json()["detail"]

    uninstall_after_disable = client.delete(
        f"/v1/plugins/installed/{TENCENT_PROVIDER_ID}",
        params={"disable_first": "true"},
    )
    assert uninstall_after_disable.status_code == 200


def test_plugin_axp_install_api_requires_explicit_online_dependency_opt_in(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    axp_path = _build_tencent_axp(
        tmp_path,
        dependencies=[
            {
                "name": "axdata_api_online_dependency",
                "version_spec": ">=1.0",
                "optional": False,
                "description": "API online dependency fixture.",
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
    client = TestClient(app)

    with axp_path.open("rb") as handle:
        offline_response = client.post(
            "/v1/plugins/axp/install",
            files={"file": ("tencent.axp", handle, "application/zip")},
        )
    assert offline_response.status_code == 400
    assert "cannot continue offline" in offline_response.json()["detail"]
    assert calls == []

    with axp_path.open("rb") as handle:
        online_response = client.post(
            "/v1/plugins/axp/install",
            data={"allow_online_deps": "true"},
            files={"file": ("tencent.axp", handle, "application/zip")},
        )

    assert online_response.status_code == 200
    payload = online_response.json()["data"]
    assert calls[0][0] == ("axdata_api_online_dependency>=1.0",)
    assert payload["installed_dependency_requirements"] == ["axdata_api_online_dependency>=1.0"]


def test_plugin_installed_api_uninstalls_preinstalled_and_rejects_unknown(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)

    preinstalled_response = client.delete("/v1/plugins/installed/axdata.source.tencent")
    assert preinstalled_response.status_code == 200
    assert preinstalled_response.json()["data"]["uninstall_mode"] == "managed_disable"

    unknown_response = client.delete("/v1/plugins/installed/axdata.source.not_installed")
    assert unknown_response.status_code == 404


def test_plugin_installed_api_logically_uninstalls_preinstalled_tdx(monkeypatch, tmp_path):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)

    response = client.delete(f"/v1/plugins/installed/{TDX_PROVIDER_ID}")

    assert response.status_code == 200
    assert response.json()["data"]["uninstall_mode"] == "managed_disable"


def test_request_unregistered_interface_returns_not_found():
    client = TestClient(app)

    response = client.post(
        "/v1/request/not_registered",
        json={
            "params": {"code": "demo"},
            "fields": ["code"],
        },
    )

    assert response.status_code == 404
    assert "not_registered" in response.json()["detail"]


def test_request_unknown_interface_returns_not_found():
    client = TestClient(app)

    response = client.post("/v1/request/not_real", json={"params": {}})

    assert response.status_code == 404
    assert "not_real" in response.json()["detail"]


def test_request_interface_passes_execution_options_outside_params(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    def fake_request_interface(interface_name, *, params, fields, persist, options=None, data_root=None):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "persist": persist,
                "options": options,
                "data_root": data_root,
            }
        )
        return SourceRequestResult(
            records=[{"instrument_id": "000001.SZ"}],
            meta={
                "source": "wrong",
                "requested_fields": ["instrument_id"],
                "persisted": True,
                "options": {"server_cache_root": "internal-cache"},
            },
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_codes_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id"],
            "options": {"source_server_count": 2, "connections_per_server": 3},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["source"] == "wrong"
    assert payload["meta"]["persisted"] is False
    assert payload["meta"]["params"] == {"scope": "all"}
    assert payload["meta"]["options"] == {"source_server_count": 2, "connections_per_server": 3}
    assert calls == [
        {
            "interface_name": "stock_codes_tdx",
            "params": {"scope": "all"},
            "fields": ["instrument_id"],
            "persist": False,
            "options": {"source_server_count": 2, "connections_per_server": 3},
            "data_root": tmp_path / "data",
        }
    ]


def test_request_interface_source_adapter_error_returns_gateway_error(monkeypatch, tmp_path):
    from axdata_core import SourceAdapterError

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    def fake_request_interface(interface_name, *, params, fields, persist, options=None, data_root=None):
        raise SourceAdapterError(f"provider failed while loading {interface_name}")

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_codes_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id"],
            "options": {"source_server_count": 2},
        },
    )

    assert response.status_code == 502
    payload = response.json()
    assert payload["error"]["code"] == "SOURCE_ADAPTER_ERROR"
    assert "provider failed while loading stock_codes_tdx" in payload["error"]["message"]
    assert payload["meta"]["interface_name"] == "stock_codes_tdx"
    assert payload["meta"]["requested_fields"] == ["instrument_id"]
    assert payload["meta"]["params"] == {"scope": "all"}


@pytest.mark.parametrize(
    ("interface_name", "params", "fields"),
    [
        ("stock_realtime_snapshot_tdx", {"code": "000001.SZ"}, ["instrument_id", "last_price"]),
        ("stock_realtime_rank_tdx", {"category": "a_share", "count": 3}, ["rank", "instrument_id"]),
        ("stock_order_book_tdx", {"code": "000001.SZ"}, ["instrument_id", "level", "bid_price"]),
        ("index_realtime_snapshot_tdx", {"code": "000001.SH"}, ["instrument_id", "last_price"]),
        ("index_kline_tdx", {"code": "000001.SH", "count": 3}, ["instrument_id", "trade_time", "close"]),
        ("etf_realtime_snapshot_tdx", {"code": "510050.SH"}, ["instrument_id", "last_price"]),
        ("etf_kline_tdx", {"code": "510050.SH", "count": 3}, ["instrument_id", "trade_time", "close"]),
        ("concept_constituents_tdx", {"concept_code": "881386", "count": 2}, ["instrument_id", "name"]),
        ("stock_intraday_today_tdx", {"code": "000001.SZ"}, ["instrument_id", "time_label", "price"]),
        (
            "stock_intraday_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260519"},
            ["instrument_id", "trade_time", "price"],
        ),
        (
            "stock_intraday_recent_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260519"},
            ["instrument_id", "trade_time", "avg_price"],
        ),
        (
            "stock_intraday_buy_sell_strength_tdx",
            {"code": "000001.SZ"},
            ["instrument_id", "minute_time", "bid_order"],
        ),
        (
            "stock_intraday_volume_comparison_tdx",
            {"code": "000001.SZ"},
            ["instrument_id", "minute_time", "today_volume"],
        ),
        ("stock_trades_today_tdx", {"code": "000001.SZ"}, ["instrument_id", "trade_time", "price"]),
        (
            "stock_trades_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260511"},
            ["instrument_id", "trade_datetime", "price"],
        ),
        ("stock_auction_process_tdx", {"code": "000988.SZ"}, ["instrument_id", "auction_time", "price"]),
        ("stock_auction_result_tdx", {"code": "000001.SZ"}, ["instrument_id", "auction_time", "price"]),
        (
            "stock_auction_result_history_tdx",
            {"code": "000001.SZ", "trade_date": "20260511"},
            ["instrument_id", "auction_datetime", "price"],
        ),
        ("stock_finance_summary_tdx", {"code": "000001.SZ"}, ["instrument_id", "updated_date", "eps"]),
        ("stock_finance_profile_tdx", {"code": "000001.SZ"}, ["instrument_id", "updated_date", "ipo_date"]),
        ("index_realtime_rank_tdx", {"sort": "change_pct", "count": 5}, ["rank", "instrument_id"]),
        ("etf_realtime_rank_tdx", {"sort": "change_pct", "count": 5}, ["rank", "instrument_id"]),
        ("index_intraday_today_tdx", {"code": "000001.SH"}, ["instrument_id", "time_label", "price"]),
        (
            "index_intraday_history_tdx",
            {"code": "000001.SH", "trade_date": "20260617"},
            ["instrument_id", "trade_time", "price"],
        ),
        ("etf_intraday_today_tdx", {"code": "510050.SH"}, ["instrument_id", "time_label", "price"]),
        ("etf_trades_today_tdx", {"code": "510050.SH"}, ["instrument_id", "trade_time", "price"]),
    ],
)
def test_request_source_only_tdx_interfaces_use_gateway(monkeypatch, tmp_path, interface_name, params, fields):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_request_interface(name, *, params, fields, persist, options=None, data_root=None):
        calls.append(
            {
                "name": name,
                "params": params,
                "fields": fields,
                "persist": persist,
                "options": options,
                "data_root": data_root,
            }
        )
        return SourceRequestResult(
            records=[{field: f"{field}_value" for field in fields}],
            meta={"source": "tdx", "persisted": False},
        )

    monkeypatch.setattr(api_main, "core_request_interface", fake_request_interface, raising=False)
    client = TestClient(app)

    response = client.post(
        f"/v1/request/{interface_name}",
        json={"params": params, "fields": fields},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["interface_name"] == interface_name
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False
    assert payload["meta"]["params"] == params
    assert payload["meta"]["interface"]["collection"]["supported"] is False
    assert payload["data"] == [{field: f"{field}_value" for field in fields}]
    assert calls == [
        {
            "name": interface_name,
            "params": params,
            "fields": fields,
            "persist": False,
            "options": None,
            "data_root": tmp_path / "data",
        }
    ]


def test_request_disabled_tdx_interface_returns_unavailable_guidance(monkeypatch, tmp_path):
    from axdata_core.plugin_config import disable_provider

    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    disable_provider(TDX_PROVIDER_ID, data_root=data_root)
    client = TestClient(app)

    response = client.post(
        "/v1/request/stock_realtime_snapshot_tdx",
        json={"params": {"code": "000001.SZ"}, "fields": ["instrument_id"]},
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "SOURCE_UNAVAILABLE"
    assert "TDX" in payload["error"]["message"]
    assert payload["meta"]["interface_name"] == "stock_realtime_snapshot_tdx"
    assert payload["meta"]["interface"]["plugin_status"] == "disabled"
    assert payload["meta"]["action_command"] == "axdata plugin enable axdata.source.tdx_external"
    assert payload["meta"]["request_mode"] == "source_request"
    assert payload["meta"]["persisted"] is False


def test_request_interfaces_catalog_keeps_disabled_tdx_guidance(monkeypatch, tmp_path):
    from axdata_core.plugin_config import disable_provider

    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    disable_provider(TDX_PROVIDER_ID, data_root=data_root)
    client = TestClient(app)

    response = client.get("/v1/request/interfaces")

    assert response.status_code == 200
    payload = response.json()
    items = {item["name"]: item for item in payload["data"]}
    assert "stock_intraday_today_tdx" in items
    assert "stock_intraday_recent_history_tdx" in items
    assert "stock_realtime_snapshot_tdx" in items
    assert items["stock_intraday_today_tdx"]["plugin_status"] == "disabled"
    assert items["stock_intraday_today_tdx"]["enabled"] is False
    assert items["stock_intraday_today_tdx"]["collection"]["supported"] is False
    assert items["stock_intraday_today_tdx"]["action_command"] == (
        "axdata plugin enable axdata.source.tdx_external"
    )
    assert items["stock_intraday_recent_history_tdx"]["plugin_status"] == "disabled"
    assert items["stock_intraday_recent_history_tdx"]["enabled"] is False
    assert items["stock_intraday_recent_history_tdx"]["collection"]["supported"] is False
    assert items["stock_intraday_recent_history_tdx"]["action_command"] == (
        "axdata plugin enable axdata.source.tdx_external"
    )
    assert "cninfo_announcements" in items
    assert items["cninfo_announcements"]["plugin_status"] == "enabled"


def test_downloaders_catalog_lists_stock_suspensions_and_st_tdx():
    client = TestClient(app)

    response = client.get("/v1/downloaders")

    assert response.status_code == 200
    payload = response.json()
    names = [item["interface_name"] for item in payload["data"]]
    assert names[: len(TDX_DOWNLOADER_INTERFACE_NAMES)] == TDX_DOWNLOADER_INTERFACE_NAMES
    assert set(names) == {*TDX_DOWNLOADER_INTERFACE_NAMES, *BUILTIN_GENERIC_INTERFACE_NAMES}
    assert payload["data"][0]["downloader_type"] == "full_snapshot"
    assert payload["data"][0]["default_params"] == {"scope": "all"}
    assert payload["data"][0]["default_connection_count"] == 3
    assert payload["data"][0]["connection_count_editable"] is False
    assert payload["data"][0]["max_connection_count"] == 3
    assert payload["data"][0]["concurrency"]["mode"] == "fixed"
    assert payload["data"][0]["concurrency"]["default_source_server_count"] == 1
    assert payload["data"][0]["concurrency"]["default_connections_per_server"] == 3
    assert payload["data"][0]["concurrency"]["default_max_concurrent_tasks"] == 3
    assert payload["data"][1]["downloader_type"] == "full_snapshot"
    assert payload["data"][1]["default_params"] == {"scope": "all"}
    assert payload["data"][1]["default_connection_count"] == 8
    assert payload["data"][1]["connection_count_editable"] is False
    assert payload["data"][1]["max_connection_count"] == 8
    assert payload["data"][1]["concurrency"]["mode"] == "fixed"
    assert payload["data"][1]["concurrency"]["default_source_server_count"] == 4
    assert payload["data"][1]["concurrency"]["default_connections_per_server"] == 2
    assert payload["data"][1]["concurrency"]["default_max_concurrent_tasks"] == 8
    assert payload["data"][1]["concurrency"]["default_batch_size"] == 80
    assert "停牌状态" in payload["data"][1]["concurrency"]["description"]
    assert payload["data"][2]["downloader_type"] == "full_snapshot"
    assert payload["data"][2]["default_params"] == {"scope": "all"}
    assert payload["data"][2]["default_connection_count"] == 3
    assert payload["data"][3]["downloader_type"] == "full_snapshot"
    assert payload["data"][3]["default_params"] == {"scope": "all"}
    assert payload["data"][3]["default_connection_count"] == 8
    assert payload["data"][3]["connection_count_editable"] is False
    assert payload["data"][3]["max_connection_count"] == 8
    assert payload["data"][3]["concurrency"]["mode"] == "fixed"
    assert payload["data"][3]["concurrency"]["default_source_server_count"] == 4
    assert payload["data"][3]["concurrency"]["default_connections_per_server"] == 2
    assert payload["data"][3]["concurrency"]["default_max_concurrent_tasks"] == 8
    assert payload["data"][3]["concurrency"]["max_concurrent_tasks_editable"] is False
    assert payload["data"][3]["concurrency"]["max_source_server_count"] == 4
    assert payload["data"][3]["concurrency"]["max_connections_per_server"] == 2
    assert payload["data"][3]["concurrency"]["max_max_concurrent_tasks"] == 8
    assert payload["data"][3]["concurrency"]["default_batch_size"] == 80
    assert payload["data"][3]["primary_key"] == ["trade_date", "instrument_id"]
    assert payload["data"][3]["params"][1] == ["code", "string/list", "否", "证券代码：可选；不填则按股票范围拉取全量"]
    assert payload["data"][4]["downloader_type"] == "full_snapshot"
    assert payload["data"][4]["default_params"] == {"scope": "all"}
    assert payload["data"][4]["default_connection_count"] == 8
    assert payload["data"][4]["connection_count_editable"] is False
    assert payload["data"][4]["max_connection_count"] == 8
    assert payload["data"][4]["concurrency"]["mode"] == "fixed"
    assert payload["data"][4]["concurrency"]["default_source_server_count"] == 4
    assert payload["data"][4]["concurrency"]["default_connections_per_server"] == 2
    assert payload["data"][4]["concurrency"]["default_max_concurrent_tasks"] == 8
    assert payload["data"][4]["concurrency"]["default_batch_size"] == 80
    assert payload["data"][4]["primary_key"] == ["trade_date", "instrument_id"]
    assert len(payload["data"][4]["params"]) == 2
    assert payload["data"][4]["params"][1] == ["code", "string/list", "否", "证券代码：可选；不填则按股票范围拉取全量"]
    assert payload["data"][5]["downloader_type"] == "full_snapshot"
    assert payload["data"][5]["default_params"] == {"scope": "all"}
    assert payload["data"][5]["default_connection_count"] == 16
    assert payload["data"][5]["connection_count_editable"] is False
    assert payload["data"][5]["max_connection_count"] == 16
    assert payload["data"][5]["concurrency"]["mode"] == "fixed"
    assert payload["data"][5]["concurrency"]["default_source_server_count"] == 8
    assert payload["data"][5]["concurrency"]["default_connections_per_server"] == 2
    assert payload["data"][5]["concurrency"]["default_max_concurrent_tasks"] == 16
    assert payload["data"][5]["concurrency"]["default_batch_size"] == 1
    assert payload["data"][5]["primary_key"] == ["instrument_id", "record_hex"]
    assert [row[0] for row in payload["data"][5]["params"]] == ["scope", "code", "category"]
    assert payload["data"][6]["interface_name"] == "stock_kline_daily_tdx"
    assert payload["data"][6]["downloader_type"] == "history"
    assert payload["data"][6]["default_params"] == {"code": "000001.SZ", "count": 800, "adjust": "none"}
    assert payload["data"][6]["default_connection_count"] == 1
    assert payload["data"][6]["connection_count_editable"] is False
    assert payload["data"][6]["max_connection_count"] == 1
    assert payload["data"][6]["primary_key"] == ["instrument_id", "trade_time", "period"]
    assert payload["data"][6]["output_layer"] == "core"
    assert [row[0] for row in payload["data"][6]["params"]] == ["code", "count", "adjust", "anchor_date"]
    assert payload["data"][7]["interface_name"] == "stock_adj_factor_tdx"
    assert payload["data"][7]["downloader_type"] == "history"
    assert payload["data"][7]["default_params"] == {"code": "000001.SZ", "adjust": "qfq"}
    assert payload["data"][7]["default_connection_count"] == 1
    assert payload["data"][7]["connection_count_editable"] is False
    assert payload["data"][7]["max_connection_count"] == 1
    assert payload["data"][7]["primary_key"] == ["ts_code", "trade_date"]
    assert payload["data"][7]["output_layer"] == "core"
    assert [row[0] for row in payload["data"][7]["params"]] == ["code", "adjust", "anchor_date"]
    assert payload["data"][8]["interface_name"] == "stock_limit_ladder_tdx"
    assert payload["data"][8]["downloader_type"] == "full_snapshot"
    assert payload["data"][8]["default_params"] == {
        "count": "all",
        "scope": "main",
        "include_touched": False,
        "topic_type": "theme",
    }
    assert payload["data"][8]["default_connection_count"] == 1
    assert payload["data"][8]["connection_count_editable"] is False
    assert payload["data"][8]["max_connection_count"] == 1
    assert payload["data"][8]["primary_key"] == ["trade_date", "ladder_level", "instrument_id"]
    assert [row[0] for row in payload["data"][8]["params"]] == [
        "count",
        "scope",
        "include_touched",
        "topic_type",
    ]
    assert payload["data"][9]["interface_name"] == "stock_theme_strength_rank_tdx"
    assert payload["data"][9]["downloader_type"] == "full_snapshot"
    assert payload["data"][9]["default_params"] == {
        "count": "all",
        "scope": "main",
        "topic_type": "theme",
    }
    assert payload["data"][9]["primary_key"] == ["trade_date", "topic_type", "topic_name"]
    assert [row[0] for row in payload["data"][9]["params"]] == ["count", "scope", "topic_type"]
    historical_list = {item["interface_name"]: item for item in payload["data"]}["stock_historical_list_exchange"]
    assert historical_list["provider_id"] == "axdata.source.exchange"
    assert historical_list["manifest_downloader_name"] == "stock_historical_list_exchange.snapshot"
    assert historical_list["resource_group"] == "exchange.http"
    assert historical_list["default_params"] == {"trade_date": "20260102"}
    assert historical_list["default_connection_count"] == 1
    assert historical_list["primary_key"] == ["trade_date", "instrument_id"]


def test_downloaders_catalog_and_async_download_respect_provider_disable(tmp_path, monkeypatch):
    from axdata_core.plugin_config import disable_provider

    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    disable_provider(TDX_PROVIDER_ID, data_root=data_root)
    client = TestClient(app)

    list_response = client.get("/v1/downloaders")
    assert list_response.status_code == 200
    names = {item["interface_name"] for item in list_response.json()["data"]}
    assert "stock_codes_tdx" not in names
    assert names == BUILTIN_GENERIC_INTERFACE_NAMES

    detail_response = client.get("/v1/downloaders/stock_codes_tdx")
    assert detail_response.status_code == 404
    assert detail_response.json()["error"]["code"] == "DOWNLOADER_NOT_CONFIGURED"

    async_response = client.post(
        "/v1/download/stock_codes_tdx",
        json={"params": {"scope": "all"}, "formats": ["parquet"], "async_job": True},
    )
    assert async_response.status_code == 404
    assert async_response.json()["error"]["code"] == "DOWNLOADER_NOT_CONFIGURED"


def test_tdx_server_config_routes_save_probe_and_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)

    response = client.get("/v1/tdx/servers")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["quote"]["source"] == "built_in"
    assert payload["extended"]["source"] == "built_in"

    response = client.put(
        "/v1/tdx/servers/quote",
        json={"servers": [{"name": "测试", "host": "127.0.0.1", "port": 1, "enabled": True}]},
    )
    assert response.status_code == 200
    assert response.json()["data"]["source"] == "user"
    assert response.json()["data"]["servers"][0]["host"] == "127.0.0.1"

    response = client.post("/v1/tdx/servers/quote/probe", json={"timeout": 0.2, "save": True})
    assert response.status_code == 200
    assert response.json()["data"]["servers"][0]["last_checked_at"]

    response = client.post("/v1/tdx/servers/quote/reset")
    assert response.status_code == 200
    assert response.json()["data"]["source"] == "built_in"


def test_tdx_server_probe_schedule_can_be_enabled_and_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    import apps.api.tdx_server_routes as routes

    monkeypatch.setattr(routes, "start_tdx_server_probe_scheduler_loop", lambda: None)
    client = TestClient(app)

    response = client.get("/v1/tdx/servers/probe-schedule")
    assert response.status_code == 200
    assert response.json()["data"]["enabled"] is False

    response = client.post(
        "/v1/tdx/servers/probe-schedule",
        json={
            "enabled": True,
            "frequency": "daily",
            "time": "08:45",
            "kinds": ["quote"],
            "timeout": 0.2,
            "max_workers": 2,
        },
    )
    assert response.status_code == 200
    schedule = response.json()["data"]
    assert schedule["enabled"] is True
    assert schedule["time"] == "08:45"
    assert schedule["kinds"] == ["quote"]
    assert (tmp_path / "data" / "cache" / "tdx_servers" / "probe_schedule.json").exists()

    response = client.delete("/v1/tdx/servers/probe-schedule")
    assert response.status_code == 200
    assert response.json()["data"]["enabled"] is False


def test_tdx_server_probe_schedule_ticks_once(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    import apps.api.tdx_server_routes as routes
    from datetime import datetime

    calls = []

    def fake_run(schedule):
        calls.append(dict(schedule))
        return {"quote": {"server_count": 1, "enabled_count": 1, "fastest_latency_ms": 10.0}}

    monkeypatch.setattr(routes, "_run_scheduled_probe", fake_run)
    routes._write_probe_schedule(
        {
            "enabled": True,
            "frequency": "daily",
            "time": "08:45",
            "weekday": "1",
            "timeout": 0.2,
            "max_workers": 2,
            "kinds": ["quote"],
            "last_run_key": None,
            "last_checked_at": None,
            "last_result": None,
            "updated_at": None,
        }
    )

    first = routes._tick_probe_schedule(now=datetime(2026, 6, 20, 8, 45))
    second = routes._tick_probe_schedule(now=datetime(2026, 6, 20, 8, 45))

    assert first is not None
    assert second is None
    assert len(calls) == 1
    assert routes._read_probe_schedule()["last_run_key"] == "20260620_0845"


def test_download_stock_codes_tdx_uses_downloader_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_run_downloader(
        interface_name,
        *,
        params=None,
        fields=None,
        data_root=None,
        output_root=None,
        output_dir=None,
        formats=None,
        collect_mode=None,
        connection_mode=None,
        concurrency_mode=None,
        connection_count=None,
        source_server_count=None,
        connections_per_server=None,
        max_concurrent_tasks=None,
        batch_size=None,
        request_interval_ms=None,
        retry_count=None,
        timeout_ms=None,
    ):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "data_root": data_root,
                "output_root": output_root,
                "output_dir": output_dir,
                "formats": formats,
                "collect_mode": collect_mode,
                "connection_mode": connection_mode,
                "concurrency_mode": concurrency_mode,
                "connection_count": connection_count,
                "source_server_count": source_server_count,
                "connections_per_server": connections_per_server,
                "max_concurrent_tasks": max_concurrent_tasks,
                "batch_size": batch_size,
                "request_interval_ms": request_interval_ms,
                "retry_count": retry_count,
                "timeout_ms": timeout_ms,
            }
        )
        return {
            "job_id": "run_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 1,
            "output_path": str(tmp_path / "data" / "raw" / "stock_codes_tdx.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_codes_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name"],
            "output_root": str(tmp_path / "export"),
            "output_dir": str(tmp_path / "export" / "raw" / "stock_codes_tdx"),
            "formats": ["parquet", "csv"],
            "collect_mode": "incremental",
            "connection_mode": "long_connection",
            "connection_count": 1,
            "source_server_count": 2,
            "connections_per_server": 3,
            "max_concurrent_tasks": 6,
            "batch_size": 80,
            "request_interval_ms": 50,
            "retry_count": 2,
            "timeout_ms": 15000,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["job_id"] == "run_test"
    assert payload["data"]["row_count"] == 1
    assert calls == [
        {
            "interface_name": "stock_codes_tdx",
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": str(tmp_path / "export" / "raw" / "stock_codes_tdx"),
            "formats": ["parquet", "csv"],
            "collect_mode": "incremental",
            "connection_mode": "long_connection",
            "concurrency_mode": None,
            "connection_count": 1,
            "source_server_count": 2,
            "connections_per_server": 3,
            "max_concurrent_tasks": 6,
            "batch_size": 80,
            "request_interval_ms": 50,
            "retry_count": 2,
            "timeout_ms": 15000,
        }
    ]


def test_download_stock_st_list_tdx_uses_downloader_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_run_downloader(
        interface_name,
        *,
        params=None,
        fields=None,
        data_root=None,
        output_root=None,
        output_dir=None,
        formats=None,
        collect_mode=None,
        connection_mode=None,
        concurrency_mode=None,
        connection_count=None,
        source_server_count=None,
        connections_per_server=None,
        max_concurrent_tasks=None,
        batch_size=None,
        request_interval_ms=None,
        retry_count=None,
        timeout_ms=None,
    ):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "data_root": data_root,
                "output_root": output_root,
                "output_dir": output_dir,
                "formats": formats,
                "collect_mode": collect_mode,
                "connection_mode": connection_mode,
                "concurrency_mode": concurrency_mode,
                "connection_count": connection_count,
                "source_server_count": source_server_count,
                "connections_per_server": connections_per_server,
                "max_concurrent_tasks": max_concurrent_tasks,
                "batch_size": batch_size,
                "request_interval_ms": request_interval_ms,
                "retry_count": retry_count,
                "timeout_ms": timeout_ms,
            }
        )
        return {
            "job_id": "run_st_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 2,
            "output_path": str(tmp_path / "data" / "raw" / "stock_st_list_tdx.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_st_list_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name", "st_type"],
            "output_root": str(tmp_path / "export"),
            "formats": ["parquet", "jsonl"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["job_id"] == "run_st_test"
    assert payload["data"]["row_count"] == 2
    assert calls == [
        {
            "interface_name": "stock_st_list_tdx",
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name", "st_type"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["parquet", "jsonl"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": None,
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


def test_download_stock_suspensions_tdx_uses_downloader_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_run_downloader(
        interface_name,
        *,
        params=None,
        fields=None,
        data_root=None,
        output_root=None,
        output_dir=None,
        formats=None,
        collect_mode=None,
        connection_mode=None,
        concurrency_mode=None,
        connection_count=None,
        source_server_count=None,
        connections_per_server=None,
        max_concurrent_tasks=None,
        batch_size=None,
        request_interval_ms=None,
        retry_count=None,
        timeout_ms=None,
    ):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "data_root": data_root,
                "output_root": output_root,
                "output_dir": output_dir,
                "formats": formats,
                "collect_mode": collect_mode,
                "connection_mode": connection_mode,
                "concurrency_mode": concurrency_mode,
                "connection_count": connection_count,
                "source_server_count": source_server_count,
                "connections_per_server": connections_per_server,
                "max_concurrent_tasks": max_concurrent_tasks,
                "batch_size": batch_size,
                "request_interval_ms": request_interval_ms,
                "retry_count": retry_count,
                "timeout_ms": timeout_ms,
            }
        )
        return {
            "job_id": "run_suspensions_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 2,
            "output_path": str(tmp_path / "data" / "raw" / "stock_suspensions_tdx.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_suspensions_tdx",
        json={
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name", "market"],
            "output_root": str(tmp_path / "export"),
            "formats": ["parquet", "jsonl"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["job_id"] == "run_suspensions_test"
    assert payload["data"]["row_count"] == 2
    assert calls == [
        {
            "interface_name": "stock_suspensions_tdx",
            "params": {"scope": "all"},
            "fields": ["instrument_id", "name", "market"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["parquet", "jsonl"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": None,
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


def test_download_stock_daily_share_tdx_uses_downloader_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_run_downloader(
        interface_name,
        *,
        params=None,
        fields=None,
        data_root=None,
        output_root=None,
        output_dir=None,
        formats=None,
        collect_mode=None,
        connection_mode=None,
        concurrency_mode=None,
        connection_count=None,
        source_server_count=None,
        connections_per_server=None,
        max_concurrent_tasks=None,
        batch_size=None,
        request_interval_ms=None,
        retry_count=None,
        timeout_ms=None,
    ):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "data_root": data_root,
                "output_root": output_root,
                "output_dir": output_dir,
                "formats": formats,
                "collect_mode": collect_mode,
                "connection_mode": connection_mode,
                "concurrency_mode": concurrency_mode,
                "connection_count": connection_count,
                "source_server_count": source_server_count,
                "connections_per_server": connections_per_server,
                "max_concurrent_tasks": max_concurrent_tasks,
                "batch_size": batch_size,
                "request_interval_ms": request_interval_ms,
                "retry_count": retry_count,
                "timeout_ms": timeout_ms,
            }
        )
        return {
            "job_id": "run_daily_share_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 2,
            "output_path": str(tmp_path / "data" / "raw" / "stock_daily_share_tdx.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_daily_share_tdx",
        json={
            "params": {"scope": "all", "refresh_stats": "true"},
            "fields": ["trade_date", "instrument_id", "total_share"],
            "output_root": str(tmp_path / "export"),
            "formats": ["parquet", "jsonl"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": "high",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["job_id"] == "run_daily_share_test"
    assert payload["data"]["row_count"] == 2
    assert calls == [
        {
            "interface_name": "stock_daily_share_tdx",
            "params": {"scope": "all", "refresh_stats": "true"},
            "fields": ["trade_date", "instrument_id", "total_share"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["parquet", "jsonl"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": "high",
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


def test_download_stock_daily_price_limit_tdx_uses_downloader_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_run_downloader(
        interface_name,
        *,
        params=None,
        fields=None,
        data_root=None,
        output_root=None,
        output_dir=None,
        formats=None,
        collect_mode=None,
        connection_mode=None,
        concurrency_mode=None,
        connection_count=None,
        source_server_count=None,
        connections_per_server=None,
        max_concurrent_tasks=None,
        batch_size=None,
        request_interval_ms=None,
        retry_count=None,
        timeout_ms=None,
    ):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "data_root": data_root,
                "output_root": output_root,
                "output_dir": output_dir,
                "formats": formats,
                "collect_mode": collect_mode,
                "connection_mode": connection_mode,
                "concurrency_mode": concurrency_mode,
                "connection_count": connection_count,
                "source_server_count": source_server_count,
                "connections_per_server": connections_per_server,
                "max_concurrent_tasks": max_concurrent_tasks,
                "batch_size": batch_size,
                "request_interval_ms": request_interval_ms,
                "retry_count": retry_count,
                "timeout_ms": timeout_ms,
            }
        )
        return {
            "job_id": "run_daily_price_limit_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 2,
            "output_path": str(tmp_path / "data" / "raw" / "stock_daily_price_limit_tdx.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_daily_price_limit_tdx",
        json={
            "params": {"scope": "all", "trade_date": "20260617"},
            "fields": ["trade_date", "instrument_id", "limit_up_price"],
            "output_root": str(tmp_path / "export"),
            "formats": ["parquet"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": "medium",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["job_id"] == "run_daily_price_limit_test"
    assert payload["data"]["row_count"] == 2
    assert calls == [
        {
            "interface_name": "stock_daily_price_limit_tdx",
            "params": {"scope": "all", "trade_date": "20260617"},
            "fields": ["trade_date", "instrument_id", "limit_up_price"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["parquet"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": "medium",
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


def test_download_stock_capital_changes_tdx_uses_downloader_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_run_downloader(
        interface_name,
        *,
        params=None,
        fields=None,
        data_root=None,
        output_root=None,
        output_dir=None,
        formats=None,
        collect_mode=None,
        connection_mode=None,
        concurrency_mode=None,
        connection_count=None,
        source_server_count=None,
        connections_per_server=None,
        max_concurrent_tasks=None,
        batch_size=None,
        request_interval_ms=None,
        retry_count=None,
        timeout_ms=None,
    ):
        calls.append(
            {
                "interface_name": interface_name,
                "params": params,
                "fields": fields,
                "data_root": data_root,
                "output_root": output_root,
                "output_dir": output_dir,
                "formats": formats,
                "collect_mode": collect_mode,
                "connection_mode": connection_mode,
                "concurrency_mode": concurrency_mode,
                "connection_count": connection_count,
                "source_server_count": source_server_count,
                "connections_per_server": connections_per_server,
                "max_concurrent_tasks": max_concurrent_tasks,
                "batch_size": batch_size,
                "request_interval_ms": request_interval_ms,
                "retry_count": retry_count,
                "timeout_ms": timeout_ms,
            }
        )
        return {
            "job_id": "run_capital_changes_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 2,
            "output_path": str(tmp_path / "data" / "raw" / "stock_capital_changes_tdx.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_capital_changes_tdx",
        json={
            "params": {"scope": "all", "category": "xdxr"},
            "fields": ["instrument_id", "event_date", "category_raw"],
            "output_root": str(tmp_path / "export"),
            "formats": ["parquet"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": "high",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["job_id"] == "run_capital_changes_test"
    assert payload["data"]["row_count"] == 2
    assert calls == [
        {
            "interface_name": "stock_capital_changes_tdx",
            "params": {"scope": "all", "category": "xdxr"},
            "fields": ["instrument_id", "event_date", "category_raw"],
            "data_root": tmp_path / "data",
            "output_root": str(tmp_path / "export"),
            "output_dir": None,
            "formats": ["parquet"],
            "collect_mode": "manual_fill",
            "connection_mode": "long_connection",
            "concurrency_mode": "high",
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


def test_download_stock_codes_tdx_async_job_returns_progress(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()

    def fake_run_downloader(interface_name, **kwargs):
        progress_callback = kwargs.get("progress_callback")
        if progress_callback:
            progress_callback(
                45,
                "计算涨跌停价格 3/10 只",
                progress_current=3,
                progress_total=10,
                progress_unit="只",
                progress_label="已处理",
                eta_ms=7000,
            )
            progress_callback(100, "采集完成")
        return {
            "job_id": "run_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 1,
            "output_path": str(tmp_path / "data" / "raw" / "stock_codes_tdx" / "parquet" / "run_test.parquet"),
            "output_paths": {
                "parquet": str(tmp_path / "data" / "raw" / "stock_codes_tdx" / "parquet" / "run_test.parquet")
            },
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    response = client.post(
        "/v1/download/stock_codes_tdx",
        json={"params": {"scope": "all"}, "formats": ["parquet"], "async_job": True},
    )

    assert response.status_code == 202
    job_id = response.json()["data"]["job_id"]

    for _ in range(20):
        job_response = client.get(f"/v1/download/jobs/{job_id}")
        assert job_response.status_code == 200
        job = job_response.json()["data"]
        if job["status"] == "success":
            break
    else:  # pragma: no cover
        raise AssertionError("async job did not finish")

    assert job["progress_pct"] == 100
    assert job["result"]["row_count"] == 1
    assert job["progress_current"] == 3
    assert job["progress_total"] == 10
    assert job["progress_unit"] == "只"
    assert job["progress_label"] == "已处理"
    assert job["resource_group"] == "tdx.quote"
    assert job["resource_requested"] == 3
    assert job["resource_limit"] == 3


def test_async_resource_request_uses_projected_downloader_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes
    from axdata_core.plugins import (
        DownloaderProfile as PluginDownloaderProfile,
        InterfaceCollectionSpec,
        InterfaceSpec,
        ProviderInfo,
        ProviderManifest,
    )
    from axdata_core.provider_registry import ProviderRegistry

    manifest = ProviderManifest(
        provider=ProviderInfo(
            provider_id="axdata.source.resource_demo",
            source_code="resource_demo",
            source_name_zh="资源示例",
            version="0.1.0",
        ),
        interfaces=(
            InterfaceSpec(
                name="stock_codes_tdx",
                display_name_zh="资源示例股票列表",
                source_code="resource_demo",
                source_name_zh="资源示例",
                asset_class="stock",
                collection=InterfaceCollectionSpec(
                    supported=True,
                    default_profile="resource_demo.stock_codes.snapshot",
                ),
            ),
        ),
        downloaders=(
            PluginDownloaderProfile(
                name="resource_demo.stock_codes.snapshot",
                interface_name="stock_codes_tdx",
                display_name_zh="资源示例股票采集",
                resource_group="resource.demo.quote",
                mode="snapshot",
                default_limits={"max_connections_total": 9},
            ),
        ),
    )
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.resource_demo"})
    registry.register_manifest(manifest)

    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(
        provider_catalog,
        "build_builtin_provider_registry",
        lambda **_kwargs: registry,
    )

    resource_request = routes._resolve_resource_request(
        "stock_codes_tdx",
        {
            "connection_count": None,
            "source_server_count": None,
            "connections_per_server": None,
            "max_concurrent_tasks": None,
            "concurrency_mode": None,
        },
    )

    assert resource_request.provider_id == "axdata.source.resource_demo"
    assert resource_request.resource_group == "resource.demo.quote"
    assert resource_request.requested_connections == 3
    assert resource_request.limit_connections == 9


def test_download_async_duplicate_job_is_skipped(tmp_path, monkeypatch):
    from threading import Event

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()

    first_started = Event()
    release_first = Event()
    calls = []

    def fake_run_downloader(interface_name, **kwargs):
        calls.append(interface_name)
        first_started.set()
        assert release_first.wait(timeout=5)
        return {
            "job_id": "run_duplicate_test",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 1,
            "output_path": str(tmp_path / "data" / "raw" / interface_name / "run_duplicate_test.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)
    payload = {"params": {"scope": "all"}, "formats": ["parquet"], "async_job": True}

    first_response = client.post("/v1/download/stock_codes_tdx", json=payload)
    assert first_response.status_code == 202
    first_job_id = first_response.json()["data"]["job_id"]
    assert first_started.wait(timeout=5)

    second_response = client.post("/v1/download/stock_codes_tdx", json=payload)
    assert second_response.status_code == 202
    second_job = second_response.json()["data"]

    try:
        assert second_job["status"] == "skipped"
        assert second_job["skip_reason"] == "active_duplicate"
        assert second_job["duplicate_job_id"] == first_job_id
        assert calls == ["stock_codes_tdx"]
    finally:
        release_first.set()

    for _ in range(20):
        job_response = client.get(f"/v1/download/jobs/{first_job_id}")
        assert job_response.status_code == 200
        first_job = job_response.json()["data"]
        if first_job["status"] == "success":
            break
    else:  # pragma: no cover
        raise AssertionError("first async job did not finish")


def test_download_async_jobs_wait_for_same_resource_group(tmp_path, monkeypatch):
    from threading import Event

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()

    first_started = Event()
    release_first = Event()
    calls = []

    def fake_run_downloader(interface_name, **kwargs):
        calls.append(interface_name)
        if len(calls) == 1:
            first_started.set()
            assert release_first.wait(timeout=5)
        return {
            "job_id": f"run_{len(calls)}",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 1,
            "output_path": str(tmp_path / "data" / "raw" / interface_name / f"run_{len(calls)}.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)

    first_response = client.post(
        "/v1/download/stock_codes_tdx",
        json={"params": {"scope": "all"}, "formats": ["parquet"], "async_job": True},
    )
    assert first_response.status_code == 202
    first_job_id = first_response.json()["data"]["job_id"]
    assert first_started.wait(timeout=5)

    second_response = client.post(
        "/v1/download/stock_codes_tdx",
        json={"params": {"scope": "stock"}, "formats": ["parquet"], "async_job": True},
    )
    assert second_response.status_code == 202
    second_job_id = second_response.json()["data"]["job_id"]

    try:
        for _ in range(20):
            second_job_response = client.get(f"/v1/download/jobs/{second_job_id}")
            assert second_job_response.status_code == 200
            second_job = second_job_response.json()["data"]
            if second_job["status"] == "waiting_resource":
                break
        else:  # pragma: no cover
            raise AssertionError("second async job did not wait for resource group")

        assert second_job["resource_group"] == "tdx.quote"
        assert second_job["resource_requested"] == 3
        assert second_job["resource_granted"] == 0
        assert second_job["resource_used"] == 3
        assert second_job["resource_limit"] == 3
        assert "tdx.quote" in second_job["resource_wait_reason"]
        assert calls == ["stock_codes_tdx"]
    finally:
        release_first.set()

    for job_id in (first_job_id, second_job_id):
        for _ in range(20):
            job_response = client.get(f"/v1/download/jobs/{job_id}")
            assert job_response.status_code == 200
            job = job_response.json()["data"]
            if job["status"] == "success":
                break
        else:  # pragma: no cover
            raise AssertionError(f"async job {job_id} did not finish")

    assert calls == ["stock_codes_tdx", "stock_codes_tdx"]


def test_download_async_jobs_wait_for_same_output_target(tmp_path, monkeypatch):
    from threading import Event

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()

    monkeypatch.setattr(
        routes,
        "_resolve_resource_request",
        lambda interface_name, kwargs: routes._ResourceRequest(
            resource_group="test.resource",
            requested_connections=1,
            limit_connections=2,
            provider_id="test.provider",
        ),
    )

    first_started = Event()
    release_first = Event()
    calls = []
    output_dir = tmp_path / "shared-output"

    def fake_run_downloader(interface_name, **kwargs):
        calls.append(interface_name)
        if len(calls) == 1:
            first_started.set()
            assert release_first.wait(timeout=5)
        return {
            "job_id": f"run_{len(calls)}",
            "interface_name": interface_name,
            "status": "success",
            "row_count": 1,
            "output_path": str(output_dir / f"run_{len(calls)}.parquet"),
        }

    import axdata_core

    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)
    client = TestClient(app)
    payload = {
        "params": {"scope": "all"},
        "formats": ["parquet"],
        "output_dir": str(output_dir),
        "async_job": True,
    }

    first_response = client.post("/v1/download/stock_codes_tdx", json=payload)
    assert first_response.status_code == 202
    first_job_id = first_response.json()["data"]["job_id"]
    assert first_started.wait(timeout=5)

    payload = {**payload, "params": {"scope": "stock"}}
    second_response = client.post("/v1/download/stock_codes_tdx", json=payload)
    assert second_response.status_code == 202
    second_job_id = second_response.json()["data"]["job_id"]

    try:
        for _ in range(20):
            second_job_response = client.get(f"/v1/download/jobs/{second_job_id}")
            assert second_job_response.status_code == 200
            second_job = second_job_response.json()["data"]
            if second_job["status"] == "waiting_output":
                break
        else:  # pragma: no cover
            raise AssertionError("second async job did not wait for output target")

        assert second_job["resource_group"] == "test.resource"
        assert second_job["resource_granted"] == 1
        assert second_job["output_wait_reason"]
        assert "stock_codes_tdx" in second_job["output_lock_key"]
        assert str(output_dir.resolve()) in second_job["output_lock_key"]
        assert calls == ["stock_codes_tdx"]
    finally:
        release_first.set()

    for job_id in (first_job_id, second_job_id):
        for _ in range(20):
            job_response = client.get(f"/v1/download/jobs/{job_id}")
            assert job_response.status_code == 200
            job = job_response.json()["data"]
            if job["status"] == "success":
                break
        else:  # pragma: no cover
            raise AssertionError(f"async job {job_id} did not finish")

    assert calls == ["stock_codes_tdx", "stock_codes_tdx"]


def test_download_schedule_can_be_enabled_and_persisted(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    with routes._schedules_lock:
        routes._schedules.clear()
    monkeypatch.setattr(routes, "start_download_scheduler_loop", lambda: None)

    client = TestClient(app)

    response = client.post(
        "/v1/download/schedules/stock_codes_tdx",
        json={
            "frequency": "daily",
            "time": "18:05",
            "params": {"scope": "all"},
            "formats": ["parquet", "csv"],
            "output_dir": str(tmp_path / "out"),
            "connection_mode": "long_connection",
        },
    )

    assert response.status_code == 200
    schedule = response.json()["data"]
    assert schedule["enabled"] is True
    assert schedule["frequency"] == "daily"
    assert schedule["time"] == "18:05"
    assert schedule["download_kwargs"]["data_root"] == str(tmp_path / "data")
    assert schedule["download_kwargs"]["output_dir"] == str(tmp_path / "out")
    assert (tmp_path / "data" / "cache" / "schedules" / "download_schedules.json").exists()

    get_response = client.get("/v1/download/schedules/stock_codes_tdx")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["frequency"] == "daily"


def test_download_scheduler_triggers_matching_schedule_once(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    now = datetime(2026, 6, 20, 18, 5, tzinfo=timezone(timedelta(hours=8)))
    submissions = []

    schedule = {
        "interface_name": "stock_codes_tdx",
        "enabled": True,
        "frequency": "daily",
        "time": "18:05",
        "weekday": "6",
        "download_kwargs": {"params": {"scope": "all"}, "data_root": str(tmp_path / "data")},
        "last_run_key": None,
    }
    with routes._schedules_lock:
        routes._schedules.clear()
    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()
    routes._write_schedules_to_disk({"stock_codes_tdx": schedule})

    class FakeExecutor:
        def submit(self, fn, *args, **kwargs):
            submissions.append((fn, args, kwargs))
            return object()

    monkeypatch.setattr(routes, "_executor", FakeExecutor())

    first = routes._tick_download_schedules(now=now)
    second = routes._tick_download_schedules(now=now)

    assert len(first) == 1
    assert first[0]["interface_name"] == "stock_codes_tdx"
    assert first[0]["trigger_type"] == "schedule"
    assert first[0]["resource_group"] == "tdx.quote"
    assert first[0]["resource_requested"] == 3
    assert second == []
    assert len(submissions) == 1
    with routes._schedules_lock:
        schedule = routes._schedules["stock_codes_tdx"]
    assert schedule["last_run_key"] == "20260620_1805"
    assert schedule["last_job_id"] == first[0]["job_id"]


def test_download_scheduler_skips_unavailable_downloader(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from axdata_core.plugin_config import disable_provider

    data_root = tmp_path / "data"
    monkeypatch.setenv("AXDATA_DATA_DIR", str(data_root))
    disable_provider(TDX_PROVIDER_ID, data_root=data_root)

    import apps.api.downloader_routes as routes

    now = datetime(2026, 6, 20, 18, 5, tzinfo=timezone(timedelta(hours=8)))
    schedule = {
        "interface_name": "stock_codes_tdx",
        "enabled": True,
        "frequency": "daily",
        "time": "18:05",
        "weekday": "6",
        "download_kwargs": {"params": {"scope": "all"}, "data_root": str(data_root)},
        "last_run_key": None,
    }
    with routes._schedules_lock:
        routes._schedules.clear()
    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()
    routes._write_schedules_to_disk({"stock_codes_tdx": schedule})

    class FakeExecutor:
        def submit(self, fn, *args, **kwargs):
            raise AssertionError("unavailable downloader schedule should not submit a job")

    monkeypatch.setattr(routes, "_executor", FakeExecutor())

    triggered = routes._tick_download_schedules(now=now)

    assert triggered == []
    with routes._schedules_lock:
        schedule = routes._schedules["stock_codes_tdx"]
    assert schedule["last_checked_at"] == now.isoformat()
    assert schedule.get("last_run_key") is None


def test_download_scheduler_skips_during_failure_backoff(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    first_now = datetime(2026, 6, 20, 18, 5, tzinfo=timezone(timedelta(hours=8)))
    second_now = datetime(2026, 6, 20, 18, 6, tzinfo=timezone(timedelta(hours=8)))
    submissions = []

    schedule = {
        "interface_name": "stock_codes_tdx",
        "enabled": True,
        "frequency": "daily",
        "time": "18:05",
        "weekday": "6",
        "download_kwargs": {"params": {"scope": "all"}, "data_root": str(tmp_path / "data")},
        "last_run_key": None,
    }
    with routes._schedules_lock:
        routes._schedules.clear()
    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
    routes._collector_resources.reset()
    routes._output_locks.reset()
    routes._write_schedules_to_disk({"stock_codes_tdx": schedule})

    class InlineExecutor:
        def submit(self, fn, *args, **kwargs):
            submissions.append((fn, args, kwargs))
            fn(*args, **kwargs)
            return object()

    def fake_run_downloader(interface_name, **kwargs):
        raise TimeoutError("source timeout")

    import axdata_core

    monkeypatch.setattr(routes, "_executor", InlineExecutor())
    monkeypatch.setattr(axdata_core, "run_downloader", fake_run_downloader)

    first = routes._tick_download_schedules(now=first_now)
    assert len(first) == 1
    assert len(submissions) == 1
    with routes._jobs_lock:
        failed_job = routes._jobs[first[0]["job_id"]]
    assert failed_job["status"] == "failed"
    assert failed_job["backoff_until"]

    schedule = {**schedule, "time": "18:06", "last_run_key": None}
    routes._write_schedules_to_disk({"stock_codes_tdx": schedule})

    second = routes._tick_download_schedules(now=second_now)

    assert len(second) == 1
    assert second[0]["status"] == "skipped"
    assert second[0]["skip_reason"] == "failure_backoff"
    assert second[0]["backoff_until"] == failed_job["backoff_until"]
    assert len(submissions) == 1


def test_download_scheduler_skips_same_day_success_duplicate(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone

    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))

    import apps.api.downloader_routes as routes

    now = datetime(2026, 6, 20, 18, 6, tzinfo=timezone(timedelta(hours=8)))
    kwargs = {"params": {"scope": "all"}, "data_root": str(tmp_path / "data")}
    output_key = routes._output_lock_key("stock_codes_tdx", kwargs=kwargs)
    run_signature = routes._run_signature("stock_codes_tdx", kwargs=kwargs, output_lock_key=output_key)
    schedule = {
        "interface_name": "stock_codes_tdx",
        "enabled": True,
        "frequency": "daily",
        "time": "18:06",
        "weekday": "6",
        "download_kwargs": kwargs,
        "last_run_key": None,
    }
    with routes._schedules_lock:
        routes._schedules.clear()
    with routes._jobs_lock:
        routes._jobs.clear()
        routes._failure_backoff.clear()
        routes._jobs["job_previous_success"] = {
            "job_id": "job_previous_success",
            "interface_name": "stock_codes_tdx",
            "status": "success",
            "run_signature": run_signature,
            "schedule_run_key": "20260620_1805",
            "finished_at": now.astimezone(timezone.utc).isoformat(),
            "updated_at": now.astimezone(timezone.utc).isoformat(),
        }
    routes._collector_resources.reset()
    routes._output_locks.reset()
    routes._write_schedules_to_disk({"stock_codes_tdx": schedule})

    class FakeExecutor:
        def submit(self, fn, *args, **kwargs):
            raise AssertionError("duplicate successful schedule should not submit a job")

    monkeypatch.setattr(routes, "_executor", FakeExecutor())

    triggered = routes._tick_download_schedules(now=now)

    assert len(triggered) == 1
    assert triggered[0]["status"] == "skipped"
    assert triggered[0]["skip_reason"] == "duplicate_success"
    assert triggered[0]["duplicate_job_id"] == "job_previous_success"


def test_trade_calendar_cache_routes_use_data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("AXDATA_DATA_DIR", str(tmp_path / "data"))
    calls = []

    def fake_status(data_root):
        calls.append(("status", data_root))
        return {"path": str(data_root / "cache" / "exchange" / "trade_calendar" / "trade_calendar.parquet"), "exists": False}

    def fake_refresh(data_root, **kwargs):
        calls.append(("refresh", data_root, kwargs))
        return {"path": str(data_root / "cache" / "exchange" / "trade_calendar" / "trade_calendar.parquet"), "exists": True}

    def fake_check(data_root, **kwargs):
        calls.append(("check", data_root, kwargs))
        return {"is_available": True, "missing_count": 0}

    import axdata_core

    monkeypatch.setattr(axdata_core, "get_trade_calendar_cache_status", fake_status)
    monkeypatch.setattr(axdata_core, "refresh_trade_calendar_cache", fake_refresh)
    monkeypatch.setattr(axdata_core, "check_trade_calendar_cache", fake_check)
    client = TestClient(app)

    status_response = client.get("/v1/trade-calendar/cache")
    refresh_response = client.post(
        "/v1/trade-calendar/cache/refresh",
        json={"start_date": "20260617", "end_date": "20260622", "recheck_past_days": 0},
    )
    check_response = client.post(
        "/v1/trade-calendar/cache/check",
        json={"start_date": "20260617", "end_date": "20260622"},
    )

    assert status_response.status_code == 200
    assert refresh_response.status_code == 200
    assert check_response.status_code == 200
    assert calls[0] == ("status", tmp_path / "data")
    assert calls[1][0:2] == ("refresh", tmp_path / "data")
    assert calls[1][2]["start_date"] == "20260617"
    assert calls[1][2]["end_date"] == "20260622"
    assert calls[2][0:2] == ("check", tmp_path / "data")
    assert calls[2][2] == {"start_date": "20260617", "end_date": "20260622"}


def test_trade_calendar_maintenance_config_routes_use_metadata_file(tmp_path, monkeypatch):
    config_path = tmp_path / "metadata" / "trade_calendar_maintenance.json"
    monkeypatch.setenv("AXDATA_TRADE_CALENDAR_MAINTENANCE_FILE", str(config_path))
    client = TestClient(app)

    status_response = client.get("/v1/trade-calendar/maintenance")
    save_response = client.put(
        "/v1/trade-calendar/maintenance",
        json={
            "enabled": True,
            "time": "22:45",
            "past_days": 45,
            "future_days": 365,
            "recheck_past_days": 7,
        },
    )
    saved_response = client.get("/v1/trade-calendar/maintenance")

    assert status_response.status_code == 200
    assert save_response.status_code == 200
    assert saved_response.status_code == 200
    assert status_response.json()["data"]["recheck_past_days"] == 7
    saved = saved_response.json()["data"]
    assert saved["enabled"] is True
    assert saved["time"] == "22:45"
    assert saved["past_days"] == 45
    assert saved["future_days"] == 365
    assert saved["recheck_past_days"] == 7
    assert saved["path"] == str(config_path)
    assert config_path.exists()


def test_trade_calendar_maintenance_schedule_rules():
    from apps.api.main import should_maintain_trade_calendar_cache

    now = datetime(2026, 6, 20, 22, 31, tzinfo=timezone.utc)
    config = {
        "enabled": True,
        "time": "22:30",
        "past_days": 30,
        "future_days": 180,
        "recheck_past_days": 30,
    }

    assert should_maintain_trade_calendar_cache(
        now=now,
        startup_checked=False,
        last_daily_key=None,
        config={"enabled": False, "time": "22:30"},
    ) is True
    assert should_maintain_trade_calendar_cache(
        now=now,
        startup_checked=True,
        last_daily_key=None,
        config={"enabled": False, "time": "22:30"},
    ) is False
    assert should_maintain_trade_calendar_cache(
        now=datetime(2026, 6, 20, 22, 29, tzinfo=timezone.utc),
        startup_checked=True,
        last_daily_key=None,
        config=config,
    ) is False
    assert should_maintain_trade_calendar_cache(
        now=now,
        startup_checked=True,
        last_daily_key=None,
        config=config,
    ) is True
    assert should_maintain_trade_calendar_cache(
        now=now,
        startup_checked=True,
        last_daily_key="20260620",
        config=config,
    ) is False
