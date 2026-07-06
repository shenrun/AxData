from __future__ import annotations

from pathlib import Path

import pandas as pd

from axdata_core.collector_scheduler import (
    CollectorRun,
    CollectorSchedulerError,
    CollectorSchedulerService,
    CollectorSchedulerStore,
    CollectorTask,
    TaskStatus,
    TriggerType,
    collector_run_guidance,
    collector_run_signature,
    collector_scheduler_store_path,
    collector_task_guidance,
    compute_next_run_at,
    create_collector_task,
    create_run_from_task,
    seed_default_collector_tasks,
    parse_datetime,
)
import axdata_core.collector_scheduler as collector_scheduler
from axdata_core.collector_templates import (
    get_task_template,
    list_task_templates,
    task_template_to_create_kwargs,
)
from axdata_core.plugin_config import remove_provider


def _task(**overrides):
    base = {
        "task_id": "task_demo",
        "collector_name": "close_refresh_daily",
        "name": "收盘刷新",
        "provider_id": "axdata.plugin.close_refresh",
        "downloader_profile": "demo.stock_codes.snapshot",
        "params": {"scope": "all"},
        "fields": ["instrument_id"],
        "formats": ["jsonl"],
        "resource_group": "demo.quote",
        "trigger_type": TriggerType.MANUAL.value,
    }
    base.update(overrides)
    return CollectorTask(**base)


def _write_trade_calendar_cache(data_root: Path, dates: list[str], *, closed_dates: list[str] | None = None) -> None:
    path = data_root / "cache" / "exchange" / "trade_calendar" / "trade_calendar.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    closed = list(closed_dates or [])
    frame = pd.DataFrame(
        {
            "exchange": ["SZSE"] * (len(dates) + len(closed)),
            "cal_date": [*dates, *closed],
            "is_open": [True] * len(dates) + [False] * len(closed),
            "pretrade_date": [None] * (len(dates) + len(closed)),
            "next_trade_date": [None] * (len(dates) + len(closed)),
        }
    )
    frame.to_parquet(path, engine="pyarrow", index=False)


def test_collector_task_and_run_roundtrip() -> None:
    task = _task(trigger_type="interval", interval_seconds=60, max_retries=2, backoff_seconds=5)
    run = create_run_from_task(task, trigger_type="manual")

    assert CollectorTask.from_dict(task.to_dict()) == task
    assert task.to_dict()["max_retries"] == 2
    assert task.to_dict()["backoff_seconds"] == 5
    assert CollectorRun.from_dict(run.to_dict()) == run
    assert run.status == TaskStatus.QUEUED.value
    assert run.params == {"scope": "all"}
    assert run.fields == ["instrument_id"]
    assert run.formats == ["jsonl"]
    assert run.resource_group == "demo.quote"
    assert run.events[0]["stage"] == "queued"
    assert run.stage_timings["download_ms"] is None


def test_collector_run_from_old_metadata_defaults_diagnostics() -> None:
    run = CollectorRun.from_dict(
        {
            "run_id": "run_old",
            "task_id": "task_demo",
            "collector_name": "close_refresh_daily",
            "trigger_type": "manual",
            "status": "success",
        }
    )

    assert run.events == []
    assert run.stage_timings["total_ms"] is None
    assert run.error_category is None
    assert run.error_summary is None


def test_collector_guidance_prioritizes_actionable_states() -> None:
    disabled_task = _task(enabled=False)
    disabled_guidance = collector_task_guidance(disabled_task)
    assert "手动模式" in disabled_guidance["status_message"]
    assert disabled_guidance["action_command"] == "axdata collector task run task_demo --wait --json"

    failed_task = _task(last_status="failed", last_error="upstream busy")
    failed_task_guidance = collector_task_guidance(failed_task)
    assert "upstream busy" in failed_task_guidance["status_message"]
    assert "--status failed" in failed_task_guidance["action_command"]

    queued = create_run_from_task(
        _task(),
        run_id="run_queued",
        status="queued",
    )
    queued = CollectorRun.from_dict(
        {
            **queued.to_dict(include_guidance=False),
            "metadata": {
                "resource_wait": {
                    "resource_active": 1,
                    "resource_limit": 1,
                    "waiting_count": 2,
                }
            },
        }
    )
    queued_guidance = collector_run_guidance(queued)
    assert "demo.quote" in queued_guidance["status_message"]
    assert "1/1" in queued_guidance["status_message"]

    duplicate = CollectorRun.from_dict(
        {
            **create_run_from_task(_task(), run_id="run_duplicate").to_dict(include_guidance=False),
            "status": "skipped",
            "skip_reason": "active_duplicate",
            "metadata": {"duplicate_run_id": "run_active"},
        }
    )
    assert "run_active" in collector_run_guidance(duplicate)["status_message"]

    backoff = CollectorRun.from_dict(
        {
            **create_run_from_task(_task(), run_id="run_backoff").to_dict(include_guidance=False),
            "status": "skipped",
            "skip_reason": "failure_backoff",
            "backoff_until": "2026-06-28T01:00:00+00:00",
        }
    )
    assert "--status failed" in collector_run_guidance(backoff)["action_command"]


def test_builtin_task_templates_are_safe_and_report_availability() -> None:
    rows = {template.template_id: template for template in list_task_templates()}

    assert {
        "daily",
        "stock_kline_daily_tdx",
    } <= set(rows)
    assert "stock_basic_exchange" not in rows
    assert "trade_cal" not in rows
    assert rows["daily"].default_params["code"] == "000001.SZ"
    assert rows["daily"].safety_limits["full_market_by_default"] is False

    tdx_template = get_task_template("daily")
    assert tdx_template.required_plugin == "axdata.collector.tdx"
    assert tdx_template.required_datasets == ["trade_cal"]


def test_task_without_plugin_dependency_refreshes_to_ok(tmp_path) -> None:
    task = _task(dependency_status=None)

    refreshed = collector_scheduler.refresh_task_dependency_status(task, data_root=tmp_path / "data")

    assert refreshed.dependency_status == "ok"
    assert refreshed.dependency_message is None


def test_trade_calendar_required_task_blocks_without_cache(tmp_path) -> None:
    data_root = tmp_path / "data"
    task = _task(
        required_plugin=None,
        dependency={},
        required_datasets=["trade_cal"],
        params={"trade_date": "20260102"},
        dependency_status=None,
    )

    refreshed = collector_scheduler.refresh_task_dependency_status(task, data_root=data_root)

    assert refreshed.dependency_status == "blocked"
    assert refreshed.dependency_errors[0]["dataset"] == "trade_cal"
    assert refreshed.dependency_errors[0]["status"] == "missing"
    assert "交易日历未同步" in refreshed.dependency_message


def test_trade_calendar_required_task_reports_coverage_gap(tmp_path) -> None:
    data_root = tmp_path / "data"
    _write_trade_calendar_cache(data_root, ["20260102"])
    task = _task(
        required_plugin=None,
        dependency={},
        required_datasets=["trade_cal"],
        params={"start_date": "20260102", "end_date": "20260104"},
        dependency_status=None,
    )

    refreshed = collector_scheduler.refresh_task_dependency_status(task, data_root=data_root)

    assert refreshed.dependency_status == "blocked"
    assert refreshed.dependency_errors[0]["status"] == "coverage_insufficient"
    assert refreshed.dependency_errors[0]["start_date"] == "20260102"
    assert refreshed.dependency_errors[0]["end_date"] == "20260104"
    assert "交易日历未覆盖 20260102-20260104" in refreshed.dependency_message


def test_trade_calendar_required_task_passes_when_range_covered(tmp_path) -> None:
    data_root = tmp_path / "data"
    _write_trade_calendar_cache(data_root, ["20260102", "20260103", "20260104"])
    task = _task(
        required_plugin=None,
        dependency={},
        required_datasets=["trade_cal"],
        params={"start_date": "20260102", "end_date": "20260104"},
        dependency_status=None,
    )

    refreshed = collector_scheduler.refresh_task_dependency_status(task, data_root=data_root)

    assert refreshed.dependency_status == "ok"
    assert refreshed.dependency_message is None
    assert refreshed.dependency_errors == []


def test_removed_collector_dependency_is_missing(tmp_path) -> None:
    data_root = tmp_path / "data"
    task = _task(
        collector_name="removed.stock_snapshot",
        required_plugin=None,
        dependency={"provider_id": "axdata.collector.removed"},
        dependency_status="ok",
    )

    remove_provider("axdata.collector.removed", data_root=data_root)
    refreshed = collector_scheduler.refresh_task_dependency_status(task, data_root=data_root)

    assert refreshed.dependency_status == "uninstalled"
    assert "axdata.collector.removed" in (refreshed.dependency_message or "")


def test_task_fails_after_collector_plugin_removal(monkeypatch, tmp_path) -> None:
    data_root = tmp_path / "data"
    store = CollectorSchedulerStore(data_root=data_root)
    task = store.create_task(
        _task(
            collector_name="removed.stock_snapshot",
            required_plugin=None,
            dependency={"provider_id": "axdata.collector.removed"},
            dependency_status="ok",
        )
    )
    historical = store.create_run(create_run_from_task(task, run_id="run_history"))
    store.update_run(historical.run_id, status="success", finished_at="2026-07-01T01:00:00+00:00")

    remove_provider("axdata.collector.removed", data_root=data_root)
    import axdata_core.collector_runner as collector_runner

    monkeypatch.setattr(
        collector_runner,
        "run_collector",
        lambda collector_name, **_kwargs: {
            "collector_name": collector_name,
            "status": "success",
            "runner_entry": "tests.removed_collectors:run_removed_collector",
            "download_result": {
                "row_count": 1,
                "output_paths": {"jsonl": str(tmp_path / "export" / "out.jsonl")},
                "quality": {"quality_status": "ok", "row_count_value": 1},
            },
        },
    )
    service = CollectorSchedulerService(data_root=data_root, store=store, max_workers=1)
    submitted = service.submit_task_object(task)
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert store.get_task(task.task_id) is not None
    assert store.get_run("run_history") is not None
    refreshed_task = store.get_task(task.task_id)
    assert refreshed_task is not None
    assert refreshed_task.dependency_status == "uninstalled"
    assert finished is not None
    assert finished.status == "failed"
    assert finished.error_category == "provider_missing"


def test_service_blocks_run_until_trade_calendar_dependency_is_covered(monkeypatch, tmp_path) -> None:
    data_root = tmp_path / "data"
    store = CollectorSchedulerStore(data_root=data_root)
    task = store.create_task(
        _task(
            collector_name="tdx.stock_kline_daily_tdx.snapshot",
            required_plugin=None,
            dependency={},
            required_datasets=["trade_cal"],
            params={"trade_date": "20260102"},
            dependency_status="ok",
        )
    )
    calls = []

    import axdata_core.collector_runner as collector_runner

    def fake_run_collector(collector_name, **kwargs):
        calls.append({"collector_name": collector_name, "params": dict(kwargs["params"])})
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {
                "row_count": 1,
                "output_paths": {"jsonl": str(tmp_path / "export" / "out.jsonl")},
                "quality": {"quality_status": "ok", "row_count_value": 1},
            },
        }

    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)
    service = CollectorSchedulerService(data_root=data_root, store=store, max_workers=1)
    blocked = service.submit_task_object(task)

    assert blocked.status == "failed"
    assert blocked.error_category == "dependency_missing"
    assert "交易日历未同步" in (blocked.error_summary or "")
    assert blocked.metadata["dependency_errors"][0]["dataset"] == "trade_cal"
    assert calls == []

    _write_trade_calendar_cache(data_root, ["20260102"])
    ready_task = store.get_task(task.task_id)
    assert ready_task is not None
    submitted = service.submit_task_object(ready_task)
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert finished is not None
    assert finished.status == "success"
    assert calls[-1]["params"] == {"trade_date": "20260102"}


def test_task_template_to_create_kwargs_rejects_unavailable_template(monkeypatch, tmp_path) -> None:
    from axdata_core import collector_templates

    class Snapshot:
        collectors = {}
        providers = {}

    monkeypatch.setattr(collector_templates, "_registry_snapshot", lambda **_kwargs: Snapshot())

    try:
        task_template_to_create_kwargs("daily", data_root=tmp_path / "data")
    except Exception as exc:
        assert "axdata.collector.tdx" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("CollectorTemplateError was not raised")


def test_store_path_uses_metadata_next_to_data_root(tmp_path) -> None:
    data_root = tmp_path / "data"

    path = collector_scheduler_store_path(data_root=data_root)

    assert path == tmp_path / "metadata" / "collector" / "collector_scheduler.json"


def test_store_saves_tasks_and_runs(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    task = store.create_task(_task(trigger_type="interval", interval_seconds=30))
    run = store.create_run(create_run_from_task(task))
    store.update_run(run.run_id, status="running", started_at="2026-06-28T01:00:00+00:00")
    finished = store.update_run(
        run.run_id,
        status="success",
        finished_at="2026-06-28T01:00:01+00:00",
        duration_ms=1000,
        output_paths={"jsonl": str(tmp_path / "out.jsonl")},
        result={"row_count": 1},
    )

    reloaded = CollectorSchedulerStore(data_root=tmp_path / "data")
    assert reloaded.get_task(task.task_id) is not None
    assert reloaded.get_run(run.run_id) == finished
    assert reloaded.latest_run_by_task(task.task_id) == finished
    assert reloaded.active_runs() == ()
    task_after_run = reloaded.get_task(task.task_id)
    assert task_after_run is not None
    assert task_after_run.last_run_id == run.run_id
    assert task_after_run.last_status == "success"
    assert task_after_run.last_success_at == "2026-06-28T01:00:01+00:00"
    assert "status_message" in finished.to_dict()
    store_payload = store.path.read_text(encoding="utf-8")
    assert "status_message" not in store_payload
    assert "next_action" not in store_payload


def test_store_rejects_duplicate_task(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    store.create_task(_task())

    try:
        store.create_task(_task())
    except CollectorSchedulerError as exc:
        assert "already exists" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("CollectorSchedulerError was not raised")


def test_default_collector_tasks_seed_once_and_preserve_user_changes(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")

    seeded = seed_default_collector_tasks(store, data_root=tmp_path / "data")

    task_ids = {task.task_id for task in seeded}
    assert {
        "stock_kline_daily_tdx_sample",
    } <= task_ids
    default_tasks = {task.task_id: task for task in store.list_tasks()}
    assert "stock_basic_exchange_refresh" not in default_tasks
    assert "trade_cal_refresh" not in default_tasks
    assert default_tasks["stock_kline_daily_tdx_sample"].write_mode == "snapshot"

    edited = store.update_task(
        "stock_kline_daily_tdx_sample",
        enabled=True,
        params={"code": "000002.SZ", "count": 100, "adjust": "none"},
        trigger_type="interval",
        interval_seconds=3600,
    )
    seed_default_collector_tasks(store, data_root=tmp_path / "data")
    preserved = store.get_task("stock_kline_daily_tdx_sample")
    assert preserved is not None
    assert preserved.enabled is True
    assert preserved.params == {"code": "000002.SZ", "count": 100, "adjust": "none"}
    assert preserved.trigger_type == "interval"
    assert preserved.interval_seconds == 3600
    assert preserved.updated_at == edited.updated_at


def test_default_collector_task_seed_adds_new_templates_without_overwrite(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    seed_default_collector_tasks(store, data_root=tmp_path / "data")
    original = store.update_task("stock_kline_daily_tdx_sample", name="用户改名")

    def fake_default_task_templates(**_kwargs):
        base = list(default_templates)
        base.append(
            base[0].__class__(
                template_id="new_default",
                title="新增默认任务",
                description="新增模板",
                collector_name="tdx.stock_codes_tdx.snapshot",
                interface_name="stock_codes_tdx",
                provider="axdata.collector.tdx",
                resource_group="tdx.quote",
                task_id="new_default_refresh",
                system_default=True,
                enabled_by_default=False,
            )
        )
        return tuple(base)

    from axdata_core.collector_templates import default_task_templates as real_default_templates

    default_templates = real_default_templates(data_root=tmp_path / "data")
    monkeypatch.setattr("axdata_core.collector_templates.default_task_templates", fake_default_task_templates)

    seed_default_collector_tasks(store, data_root=tmp_path / "data")

    assert store.get_task("new_default_refresh") is not None
    assert store.get_task("stock_kline_daily_tdx_sample").name == "用户改名"
    assert store.get_task("stock_kline_daily_tdx_sample").enabled == original.enabled


def test_store_queries_active_runs_and_filters(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    task = store.create_task(_task())
    queued = store.create_run(create_run_from_task(task, run_id="run_queued"))
    skipped = store.create_run(create_run_from_task(task, run_id="run_skipped"))
    store.update_run(skipped.run_id, status="skipped", skip_reason="active_duplicate")

    assert store.find_active_run(task_id=task.task_id) == queued
    assert store.find_active_run(run_signature=queued.run_signature) == queued
    assert [run.run_id for run in store.list_runs(status="skipped")] == ["run_skipped"]
    assert [run.run_id for run in store.list_runs(task_id=task.task_id, limit=1)] == ["run_skipped"]


def test_store_run_summary_keeps_total_count_with_recent_window(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    task = store.create_task(_task())

    for index in range(5):
        run = store.create_run(
            create_run_from_task(
                task,
                run_id=f"run_summary_{index}",
                status="queued",
            )
        )
        store.update_run(
            run.run_id,
            status="success" if index % 2 else "failed",
            finished_at=f"2026-06-28T01:00:0{index}+00:00",
        )

    summary = store.run_summary(recent_limit=2)

    assert summary["total_run_count"] == 5
    assert summary["recent_run_count"] == 2
    assert summary["recent_run_limit"] == 2
    assert [run.run_id for run in summary["recent_runs"]] == ["run_summary_4", "run_summary_3"]
    assert summary["status_counts"] == {"failed": 3, "success": 2}
    assert summary["latest_by_task"][task.task_id].run_id == "run_summary_4"


def test_run_event_history_is_bounded(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    task = store.create_task(_task())
    run = store.create_run(create_run_from_task(task, run_id="run_events"))

    for index in range(collector_scheduler.RUN_EVENT_HISTORY_LIMIT + 25):
        run = store.update_run(
            run.run_id,
            events=collector_scheduler._append_run_event(  # type: ignore[attr-defined]
                run,
                stage="downloaded",
                message=f"progress {index}",
            ),
        )

    assert len(run.events) == collector_scheduler.RUN_EVENT_HISTORY_LIMIT
    assert run.events[0]["stage"] == "queued"
    assert run.events[-1]["message"] == "progress 124"
    assert run.events[-1]["sequence"] == collector_scheduler.RUN_EVENT_HISTORY_LIMIT + 26


def test_store_recovers_interrupted_runs(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    task = store.create_task(_task())
    run = store.create_run(create_run_from_task(task, status="running"))

    recovered = store.recover_interrupted_runs()

    assert len(recovered) == 1
    assert recovered[0].run_id == run.run_id
    assert recovered[0].status == "failed"
    assert "stopped" in (recovered[0].error or "")
    assert recovered[0].error_category == "scheduler_interrupted"
    assert recovered[0].events[-1]["category"] == "scheduler_interrupted"
    assert "调度器" in collector_run_guidance(recovered[0])["next_action"]
    assert store.get_task(task.task_id).last_status == "failed"  # type: ignore[union-attr]


def test_success_after_interruption_clears_stale_errors(tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    task = store.create_task(_task())
    run = store.create_run(create_run_from_task(task, status="running"))
    interrupted = store.recover_interrupted_runs()[0]

    finished = store.update_run(
        interrupted.run_id,
        status="success",
        finished_at="2026-07-05T06:10:55+00:00",
        duration_ms=20575,
        error=None,
        error_category=None,
        error_summary=None,
        backoff_until=None,
        skip_reason=None,
        output_paths={"parquet": str(tmp_path / "out.parquet")},
        result={"status": "success"},
        quality={"quality_status": "ok", "row_count_value": 327},
    )

    assert finished.status == "success"
    assert finished.error is None
    assert finished.error_category is None
    assert finished.error_summary is None
    task_after_run = store.get_task(task.task_id)
    assert task_after_run is not None
    assert task_after_run.last_status == "success"
    assert task_after_run.last_error is None
    assert task_after_run.last_success_at == "2026-07-05T06:10:55+00:00"
    assert task_after_run.last_failure_at == interrupted.finished_at


def test_compute_next_run_at_interval_and_daily(tmp_path) -> None:
    data_root = tmp_path / "data"
    _write_trade_calendar_cache(data_root, ["20260629"], closed_dates=["20260628"])
    now = parse_datetime("2026-06-28T09:00:00+08:00")
    interval_task = _task(trigger_type="interval", interval_seconds=90)
    daily_task = _task(trigger_type="daily", daily_time="09:30")

    assert compute_next_run_at(interval_task, now=now) == "2026-06-28T01:01:30+00:00"
    assert compute_next_run_at(daily_task, now=now, data_root=data_root) == "2026-06-29T01:30:00+00:00"

    later = parse_datetime("2026-06-28T10:00:00+08:00")
    assert compute_next_run_at(daily_task, now=later, data_root=data_root) == "2026-06-29T01:30:00+00:00"
    assert compute_next_run_at(daily_task, now=later, data_root=tmp_path / "missing-data") is None

    guidance = collector_task_guidance(daily_task)
    assert "交易日历缓存" in guidance["status_message"]


def test_run_signature_is_stable() -> None:
    first = _task(params={"b": 2, "a": 1}, fields=["x", "y"])
    second = _task(params={"a": 1, "b": 2}, fields=["x", "y"])

    assert collector_run_signature(first) == collector_run_signature(second)


def test_create_collector_task_resolves_runner_plan(monkeypatch, tmp_path) -> None:
    class Plan:
        collector_name = "close_refresh_daily"
        display_name_zh = "收盘刷新"
        provider_id = "axdata.plugin.close_refresh"
        downloader_profile = "demo.stock_codes.snapshot"
        params = {"scope": "stock"}
        fields = ["instrument_id"]
        formats = ["jsonl"]
        resource_group = "demo.quote"

    import axdata_core.collector_runner as collector_runner

    def fake_build_plan(collector_name, **kwargs):
        assert collector_name == "close_refresh_daily"
        assert kwargs["params"] == {"scope": "stock"}
        assert kwargs["fields"] == ["instrument_id"]
        assert kwargs["formats"] == ["jsonl"]
        assert kwargs["data_root"] == tmp_path / "data"
        return Plan()

    monkeypatch.setattr(collector_runner, "build_collector_run_plan", fake_build_plan)

    task = create_collector_task(
        "close_refresh_daily",
        task_id="task_close",
        params={"scope": "stock"},
        fields="instrument_id",
        formats="jsonl",
        data_root=tmp_path / "data",
        output_root=tmp_path / "export",
        trigger_type="interval",
        interval_seconds=60,
    )

    assert task.task_id == "task_close"
    assert task.name == "收盘刷新"
    assert task.provider_id == "axdata.plugin.close_refresh"
    assert task.downloader_profile == "demo.stock_codes.snapshot"
    assert task.resource_group == "demo.quote"
    assert task.params == {"scope": "stock"}
    assert task.output_root == str((tmp_path / "export").resolve())
    assert task.next_run_at is not None


def test_invalid_daily_task_requires_time() -> None:
    try:
        _task(trigger_type="daily")
    except CollectorSchedulerError as exc:
        assert "daily_time" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("CollectorSchedulerError was not raised")


def test_scheduler_service_runs_task_and_records_history(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(_task(output_root=str(tmp_path / "export")))

    import axdata_core.collector_runner as collector_runner

    def fake_run_collector(collector_name, **kwargs):
        progress = kwargs["progress_callback"]
        progress(50, "halfway", progress_current=1, progress_total=2)
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {
                "row_count": 1,
                "output_paths": {"jsonl": str(tmp_path / "export" / "out.jsonl")},
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

    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)

    submitted = service.submit_task(task.task_id)
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert finished is not None
    assert finished.status == "success"
    assert finished.output_paths == {"jsonl": str(tmp_path / "export" / "out.jsonl")}
    assert finished.quality["row_count"] == "pass"
    run_payload = finished.to_dict()
    assert run_payload["records_read"] == 1
    assert run_payload["rows_written"] == 1
    assert run_payload["write_mode"] == "upsert_by_key"
    assert run_payload["primary_key"] == ["instrument_id"]
    stages = [event["stage"] for event in finished.events]
    for stage in [
        "queued",
        "started",
        "params_resolved",
        "request_planned",
        "downloaded",
        "written",
        "quality_checked",
        "metadata_recorded",
        "finished",
    ]:
        assert stage in stages
    assert stages[-1] == "finished"
    assert finished.stage_timings["queue_wait_ms"] is not None
    assert finished.stage_timings["total_ms"] is not None
    assert store.get_task(task.task_id).last_status == "success"  # type: ignore[union-attr]


def test_scheduler_service_runs_independent_collector_and_records_history(monkeypatch, tmp_path) -> None:
    from axdata_core.plugins import CollectorSpec, PluginInfo, ProviderManifest
    from axdata_core.provider_registry import ProviderRegistry

    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.collector.sample",
            name_zh="独立样例采集器",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(
            CollectorSpec(
                name="sample.stock_snapshot.snapshot",
                display_name_zh="样例股票快照采集",
                collector_plugin_id="axdata.collector.sample",
                dataset_id="sample.stock_snapshot",
                asset_class="stock",
                category="snapshot",
                resource_group="sample.local",
                runner_entry="axdata_core.sample_collectors:sample_stock_snapshot",
                default_params={"instrument_id": "000001.SZ", "trade_date": "20260701"},
                output={
                    "layer": "snapshot",
                    "formats": ["parquet", "jsonl"],
                    "primary_key": ["instrument_id"],
                    "required_columns": ["instrument_id", "trade_date"],
                    "expected_columns": ["instrument_id", "trade_date", "name", "last_price"],
                    "date_field": "trade_date",
                },
                quality={
                    "required_columns": ["instrument_id", "trade_date"],
                    "expected_columns": ["instrument_id", "trade_date", "name", "last_price"],
                    "numeric_positive_columns": ["last_price"],
                },
            ),
        ),
    )
    registry = ProviderRegistry(enabled_provider_ids={"axdata.collector.sample"})
    registry.register_manifest(manifest)

    import axdata_core.downloaders as downloaders
    import axdata_core.provider_catalog as provider_catalog

    monkeypatch.setattr(provider_catalog, "build_builtin_provider_registry", lambda **_kwargs: registry)

    def unexpected_run_downloader(*_args, **_kwargs):  # pragma: no cover
        raise AssertionError("independent scheduler run must not call run_downloader")

    monkeypatch.setattr(downloaders, "run_downloader", unexpected_run_downloader)

    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(
        create_collector_task(
            "sample.stock_snapshot.snapshot",
            task_id="sample_snapshot",
            params={"instrument_id": "600000.SH"},
            data_root=tmp_path / "data",
            output_root=tmp_path / "export",
            formats=["parquet", "jsonl"],
        )
    )

    submitted = service.submit_task(task.task_id)
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert finished is not None
    assert finished.status == "success"
    assert finished.provider_id == "axdata.collector.sample"
    assert finished.downloader_profile is None
    assert set(finished.output_paths) == {"parquet", "jsonl"}
    assert Path(finished.output_paths["parquet"]).is_file()
    assert Path(finished.output_paths["jsonl"]).is_file()
    assert finished.quality["quality_status"] == "ok"
    assert finished.quality["write_primary_key"] == ["instrument_id"]
    assert finished.result["runner_entry"] == "axdata_core.sample_collectors:sample_stock_snapshot"
    assert finished.result["download_result"]["dataset_id"] == "sample.stock_snapshot"
    assert finished.result["download_result"]["log_path"]
    assert finished.stage_timings["download_ms"] is not None
    assert finished.stage_timings["write_ms"] is not None
    assert finished.stage_timings["quality_ms"] is not None
    payload = finished.to_dict()
    assert payload["records_read"] == 1
    assert payload["rows_written"] == 1
    assert payload["primary_key"] == ["instrument_id"]


def test_scheduler_service_maps_downloader_breakdown_to_stage_timings(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(_task())

    import axdata_core.collector_runner as collector_runner

    monkeypatch.setattr(
        collector_runner,
        "run_collector",
        lambda collector_name, **_kwargs: {
            "collector_name": collector_name,
            "status": "success",
            "collector_duration_breakdown_ms": {
                "params_resolve": 1,
                "provider_resolve": 2,
                "download": 30,
                "total": 40,
            },
            "download_result": {
                "row_count": 1,
                "duration_breakdown_ms": {
                    "connection": 3,
                    "source_request": 20,
                    "transform": 4,
                    "write": 5,
                    "quality": 6,
                    "total": 38,
                },
                "quality": {"quality_status": "ok"},
            },
        },
    )

    submitted = service.submit_task(task.task_id)
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert finished is not None
    assert finished.stage_timings["params_resolve_ms"] == 1
    assert finished.stage_timings["provider_resolve_ms"] == 2
    assert finished.stage_timings["download_ms"] == 30
    assert finished.stage_timings["write_ms"] == 5
    assert finished.stage_timings["quality_ms"] == 6


def test_scheduler_service_run_overrides_params_and_backfill(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(_task(params={"code": "000001.SZ", "count": 800}))

    import axdata_core.collector_runner as collector_runner

    calls = []

    def fake_run_collector(collector_name, **kwargs):
        calls.append(dict(kwargs["params"]))
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {"row_count": 1},
        }

    monkeypatch.setattr(collector_runner, "run_collector", fake_run_collector)

    first = service.submit_task(task.task_id, params_override={"code": "600000.SH", "count": 5})
    finished_first = service.wait_for_run(first.run_id, timeout=5)
    second = service.backfill_task(
        task.task_id,
        start="2024-01-02",
        end="20240105",
        params_override={"code": "000002.SZ", "limit": 3},
    )
    finished_second = service.wait_for_run(second.run_id, timeout=5)
    service.shutdown()

    assert finished_first is not None
    assert finished_first.params_override == {"code": "600000.SH", "count": 5}
    assert finished_first.params["code"] == "600000.SH"
    assert finished_second is not None
    assert finished_second.params_override == {
        "start_date": "20240102",
        "end_date": "20240105",
        "code": "000002.SZ",
        "limit": 3,
    }
    assert finished_second.metadata["run_mode"] == "backfill"
    assert calls == [
        {"code": "600000.SH", "count": 5},
        {
            "code": "000002.SZ",
            "count": 800,
            "start_date": "20240102",
            "end_date": "20240105",
            "limit": 3,
        },
    ]


def test_scheduler_service_skips_active_duplicate(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(_task())
    running = store.create_run(create_run_from_task(task, run_id="run_running", status="running"))

    import axdata_core.collector_runner as collector_runner

    def unexpected_run_collector(*_args, **_kwargs):  # pragma: no cover
        raise AssertionError("duplicate run should be skipped before execution")

    monkeypatch.setattr(collector_runner, "run_collector", unexpected_run_collector)

    skipped = service.submit_task(task.task_id)
    service.shutdown()

    assert running.status == "running"
    assert skipped.status == "skipped"
    assert skipped.skip_reason == "active_duplicate"
    assert skipped.metadata["duplicate_run_id"] == "run_running"
    assert "run_running" in skipped.to_dict()["status_message"]


def test_scheduler_service_applies_failure_backoff(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(
        data_root=tmp_path / "data",
        store=store,
        max_workers=1,
        failure_backoff_seconds=60,
    )
    task = store.create_task(_task())

    import axdata_core.collector_runner as collector_runner

    class TemporaryUpstreamError(RuntimeError):
        pass

    def failing_run_collector(*_args, **_kwargs):
        raise TemporaryUpstreamError("upstream busy")

    monkeypatch.setattr(collector_runner, "run_collector", failing_run_collector)

    first = service.submit_task(task.task_id)
    failed = service.wait_for_run(first.run_id, timeout=5)
    second = service.submit_task(task.task_id)
    service.shutdown()

    assert failed is not None
    assert failed.status == "failed"
    assert failed.backoff_until is not None
    assert failed.error_category == "upstream_error"
    assert failed.error_summary == "upstream busy"
    assert failed.events[-1]["stage"] == "failed"
    assert failed.events[-1]["category"] == "upstream_error"
    assert second.status == "skipped"
    assert second.skip_reason == "failure_backoff"
    assert second.error_category == "backoff_blocked"
    assert second.backoff_until == failed.backoff_until
    assert "--status failed" in second.to_dict()["action_command"]


def test_scheduler_service_retries_transient_failure(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(
        data_root=tmp_path / "data",
        store=store,
        max_workers=1,
        failure_backoff_seconds=60,
    )
    task = store.create_task(_task(max_retries=1, backoff_seconds=0))

    import axdata_core.collector_runner as collector_runner

    calls = {"count": 0}

    class TemporaryUpstreamError(RuntimeError):
        pass

    def flaky_run_collector(collector_name, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise TemporaryUpstreamError("upstream busy")
        return {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {
                "row_count": 1,
                "output_paths": {"jsonl": str(tmp_path / "out.jsonl")},
                "quality": {"quality_status": "ok"},
            },
        }

    monkeypatch.setattr(collector_runner, "run_collector", flaky_run_collector)

    submitted = service.submit_task(task.task_id)
    finished = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert calls["count"] == 2
    assert finished is not None
    assert finished.status == "success"
    assert finished.retry_count == 1
    assert finished.error is None
    assert finished.error_category is None
    assert finished.metadata["max_retries"] == 1
    assert any(
        event["message"] == "Collector run attempt 1 failed; retrying."
        and event["details"]["next_retry_at"]
        for event in finished.events
    )


def test_scheduler_service_does_not_retry_validation_failure(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(_task(max_retries=2, backoff_seconds=0))

    import axdata_core.collector_runner as collector_runner

    calls = {"count": 0}

    def failing_run_collector(*_args, **_kwargs):
        calls["count"] += 1
        raise ValueError("bad params")

    monkeypatch.setattr(collector_runner, "run_collector", failing_run_collector)

    submitted = service.submit_task(task.task_id)
    failed = service.wait_for_run(submitted.run_id, timeout=5)
    service.shutdown()

    assert calls["count"] == 1
    assert failed is not None
    assert failed.status == "failed"
    assert failed.retry_count == 0
    assert failed.error_category == "invalid_params"


def test_scheduler_service_ticks_due_interval_task(monkeypatch, tmp_path) -> None:
    store = CollectorSchedulerStore(data_root=tmp_path / "data")
    service = CollectorSchedulerService(data_root=tmp_path / "data", store=store, max_workers=1)
    task = store.create_task(
        _task(
            trigger_type="interval",
            interval_seconds=30,
            next_run_at="2026-06-28T01:00:00+00:00",
        )
    )

    import axdata_core.collector_runner as collector_runner

    monkeypatch.setattr(
        collector_runner,
        "run_collector",
        lambda collector_name, **_kwargs: {
            "collector_name": collector_name,
            "status": "success",
            "download_result": {"row_count": 0},
        },
    )

    submitted = service.tick_due_tasks(now=parse_datetime("2026-06-28T01:00:00+00:00"))
    finished = service.wait_for_run(submitted[0].run_id, timeout=5)
    service.shutdown()

    assert len(submitted) == 1
    assert submitted[0].trigger_type == "interval"
    assert finished is not None
    assert finished.status == "success"
    updated_task = store.get_task(task.task_id)
    assert updated_task is not None
    assert updated_task.next_run_at is not None
