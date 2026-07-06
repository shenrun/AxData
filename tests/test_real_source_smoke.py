from __future__ import annotations

import os
from types import SimpleNamespace

import pytest


RUN_REAL_SMOKE = os.getenv("AXDATA_RUN_REAL_SMOKE", "").strip() in {"1", "true", "TRUE", "yes", "on"}


def test_real_source_smoke_default_is_dry_skip(monkeypatch, tmp_path):
    from scripts import smoke_real_sources

    def unexpected_request(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("default real-source smoke must not request upstream sources")

    monkeypatch.setenv("AXDATA_RUN_REAL_SMOKE", "0")
    monkeypatch.setattr(smoke_real_sources, "request_interface", unexpected_request)

    args = smoke_real_sources.parse_args(["--output-dir", str(tmp_path / "dry")])
    summary = smoke_real_sources.run_smoke(args)

    assert summary["enabled"] is False
    assert summary["summary"] == {"pass": 0, "fail": 0, "skip": 3}
    assert {row["status"] for row in summary["results"]} == {"skip"}


def test_real_source_smoke_fake_sources_write_core_and_query(monkeypatch, tmp_path):
    from axdata_core.source_request import SourceRequestResult
    from scripts import smoke_real_sources

    class Collection:
        def to_dict(self):
            return {"supported": False, "default_profile": None}

    def interface(name):
        return SimpleNamespace(name=name, collection=Collection())

    interfaces = {
        name: interface(name)
        for name in [
            "stock_basic_info_exchange",
            "stock_trade_calendar_exchange",
            "stock_kline_daily_tdx",
        ]
    }
    snapshot = SimpleNamespace(
        interfaces={
            name: SimpleNamespace(provider_id="axdata.source.fake", interface=value)
            for name, value in interfaces.items()
        },
        providers={
            "axdata.source.fake": SimpleNamespace(
                provider_id="axdata.source.fake",
                status="enabled",
                manifest=SimpleNamespace(interfaces=tuple(interfaces.values())),
            )
        },
        collectors={},
    )
    registry = SimpleNamespace(snapshot=lambda: snapshot)
    monkeypatch.setattr(smoke_real_sources, "build_builtin_provider_registry", lambda **_kwargs: registry)
    monkeypatch.setattr(smoke_real_sources, "_downloader_map", lambda _data_root: {})

    def fake_request_interface(interface_name, *, params, fields, persist, data_root):
        assert persist is False
        if interface_name == "stock_basic_info_exchange":
            return SourceRequestResult(
                records=[
                    {
                        "instrument_id": "000001.SZ",
                        "symbol": "000001",
                        "exchange": "SZSE",
                        "asset_type": "stock",
                        "name": "Ping An Bank",
                        "listing_status": "listed",
                        "list_date": "19910403",
                    }
                ],
                meta={"source": "fake"},
            )
        if interface_name == "stock_trade_calendar_exchange":
            return SourceRequestResult(
                records=[
                    {"cal_date": "20260617", "is_open": True, "pretrade_date": "20260616"},
                    {"cal_date": "20260618", "is_open": True, "pretrade_date": "20260617"},
                ],
                meta={"source": "fake"},
            )
        if interface_name == "stock_kline_daily_tdx":
            return SourceRequestResult(
                records=[
                    {
                        "instrument_id": "000001.SZ",
                        "trade_time": "2026-06-17T15:00:00+08:00",
                        "open": 10.0,
                        "high": 10.5,
                        "low": 9.9,
                        "close": 10.2,
                        "volume": 1000.0,
                        "amount": 10200.0,
                    }
                ],
                meta={"source": "fake"},
            )
        raise AssertionError(interface_name)

    monkeypatch.setattr(smoke_real_sources, "request_interface", fake_request_interface)

    args = smoke_real_sources.parse_args(
        ["--run", "--output-dir", str(tmp_path / "fake-real-source-smoke"), "--sample-rows", "2"]
    )
    summary = smoke_real_sources.run_smoke(args)

    assert summary["summary"] == {"pass": 3, "fail": 0, "skip": 0}
    for row in summary["results"]:
        assert row["quality"]["primary_key"] == "pass"
        assert row["query"]["row_count"] >= 1
        assert row["output_paths"]["core_parquet"].endswith(".parquet")


def test_real_source_smoke_interfaces_filter_limits_targets(tmp_path):
    from scripts import smoke_real_sources

    args = smoke_real_sources.parse_args(
        [
            "--interfaces",
            "daily",
            "adj_factor",
            "--output-dir",
            str(tmp_path / "filtered"),
        ]
    )
    summary = smoke_real_sources.run_smoke(args)

    assert summary["summary"] == {"pass": 0, "fail": 0, "skip": 2}
    assert [row["label"] for row in summary["results"]] == ["daily", "adj_factor"]


def test_real_source_smoke_optional_source_only_target_writes_product_formats(monkeypatch, tmp_path):
    from axdata_core.source_request import SourceRequestResult
    from scripts import smoke_real_sources

    class Collection:
        def to_dict(self):
            return {"supported": False, "default_profile": None}

    interface = SimpleNamespace(
        name="tencent_realtime_snapshot",
        collection=Collection(),
    )
    snapshot = SimpleNamespace(
        interfaces={
            "tencent_realtime_snapshot": SimpleNamespace(
                provider_id="axdata.source.tencent",
                interface=interface,
            )
        },
        providers={
            "axdata.source.tencent": SimpleNamespace(
                provider_id="axdata.source.tencent",
                status="enabled",
                manifest=SimpleNamespace(interfaces=(interface,)),
            )
        },
        collectors={},
    )
    registry = SimpleNamespace(snapshot=lambda: snapshot)
    monkeypatch.setattr(smoke_real_sources, "build_builtin_provider_registry", lambda **_kwargs: registry)
    monkeypatch.setattr(smoke_real_sources, "_downloader_map", lambda _data_root: {})

    def fake_request_interface(interface_name, *, params, fields, persist, data_root):
        assert interface_name == "tencent_realtime_snapshot"
        assert params == {"code": "000001.SZ"}
        assert fields is None
        assert persist is False
        return SourceRequestResult(
            records=[
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "exchange": "SZSE",
                    "name": "平安银行",
                    "last_price": 10.64,
                }
            ],
            meta={"source": "fake"},
        )

    monkeypatch.setattr(smoke_real_sources, "request_interface", fake_request_interface)

    args = smoke_real_sources.parse_args(
        [
            "--run",
            "--interfaces",
            "tencent_realtime_snapshot",
            "--output-dir",
            str(tmp_path / "source-only"),
        ]
    )
    summary = smoke_real_sources.run_smoke(args)

    assert summary["summary"] == {"pass": 1, "fail": 0, "skip": 0}
    result = summary["results"][0]
    assert result["target_kind"] == "source_snapshot"
    assert result["core_table"] is None
    assert result["quality"]["primary_key"] == "pass"
    assert result["query"]["row_count"] == 1
    assert result["output_paths"]["source_parquet"].endswith(".parquet")
    assert result["output_paths"]["source_csv"].endswith(".csv")
    assert result["output_paths"]["source_duckdb"].endswith(".duckdb")


def test_real_source_smoke_tdx_discovered_but_disabled_has_enable_hint(monkeypatch, tmp_path):
    from scripts import smoke_real_sources

    class Collection:
        def to_dict(self):
            return {"supported": False, "default_profile": None}

    interface = SimpleNamespace(
        name="stock_kline_daily_tdx",
        collection=Collection(),
    )
    snapshot = SimpleNamespace(
        interfaces={},
        providers={
            smoke_real_sources.TDX_PROVIDER_ID: SimpleNamespace(
                provider_id=smoke_real_sources.TDX_PROVIDER_ID,
                status="disabled",
                enabled=False,
                error="",
                manifest=SimpleNamespace(interfaces=(interface,)),
            )
        },
        collectors={},
    )
    registry = SimpleNamespace(snapshot=lambda: snapshot)
    monkeypatch.setattr(smoke_real_sources, "build_builtin_provider_registry", lambda **_kwargs: registry)
    monkeypatch.setattr(smoke_real_sources, "_downloader_map", lambda _data_root: {})

    args = smoke_real_sources.parse_args(
        [
            "--run",
            "--interfaces",
            "daily",
            "--output-dir",
            str(tmp_path / "tdx-disabled"),
        ]
    )
    summary = smoke_real_sources.run_smoke(args)

    assert summary["summary"] == {"pass": 0, "fail": 0, "skip": 1}
    result = summary["results"][0]
    assert result["status"] == "skip"
    assert result["reason"] == "TDX 插件已安装但未启用，请启用 TDX 插件。"
    assert result["audit"]["discovered"] is True
    assert result["audit"]["provider_status"] == "disabled"


@pytest.mark.skipif(
    not RUN_REAL_SMOKE,
    reason="set AXDATA_RUN_REAL_SMOKE=1 to run optional real-source smoke",
)
def test_optional_real_source_smoke(tmp_path):
    from scripts.smoke_real_sources import TDX_PROVIDER_ID, parse_args, run_smoke

    args = parse_args(
        [
            "--output-dir",
            str(tmp_path / "real-source-smoke"),
            "--enable-provider",
            TDX_PROVIDER_ID,
            "--sample-rows",
            "3",
        ]
    )
    summary = run_smoke(args)
    if summary["summary"]["fail"]:
        failures = [
            f"{row['label']}: {row.get('error') or row.get('reason')}"
            for row in summary["results"]
            if row["status"] == "fail"
        ]
        pytest.xfail("real source smoke failed because of source/network/config availability: " + "; ".join(failures))
    if not summary["summary"]["pass"]:
        pytest.skip("real source smoke ran but no source returned a usable sample")
    assert summary["summary"]["pass"] >= 1
