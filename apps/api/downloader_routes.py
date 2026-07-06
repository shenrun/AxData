from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Condition, Event, Lock, Thread
from time import sleep
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import data_root
from .serialization import error_payload, parse_fields, response_payload, to_jsonable


router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="axdata-collector")
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = Lock()
_failure_backoff: dict[str, datetime] = {}
_schedules: dict[str, dict[str, Any]] = {}
_schedules_lock = Lock()
_scheduler_started = Event()
_LOCAL_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
_ACTIVE_JOB_STATUSES = {"queued", "waiting_resource", "waiting_output", "running"}
_FAILURE_BACKOFF_SECONDS = 300


@dataclass(frozen=True)
class _ResourceRequest:
    resource_group: str
    requested_connections: int
    limit_connections: int
    provider_id: str | None = None


@dataclass(frozen=True)
class _ResourceLease:
    manager: "_CollectorResourceManager"
    job_id: str
    resource_group: str
    granted_connections: int
    limit_connections: int

    def release(self) -> None:
        self.manager.release(self)


class _CollectorResourceManager:
    """Single-process resource-group lease manager for collector jobs."""

    def __init__(self) -> None:
        self._condition = Condition(Lock())
        self._limits: dict[str, int] = {}
        self._used: dict[str, int] = {}
        self._waiters: dict[str, tuple[str, int]] = {}
        self._sequence = 0

    def acquire(
        self,
        *,
        job_id: str,
        resource_group: str,
        requested_connections: int,
        limit_connections: int,
        on_wait: Any | None = None,
    ) -> _ResourceLease:
        group = resource_group or "default"
        requested = max(int(requested_connections or 1), 1)
        incoming_limit = max(int(limit_connections or requested), requested, 1)
        with self._condition:
            current_limit = self._limits.get(group)
            if current_limit is None or incoming_limit > current_limit:
                self._limits[group] = incoming_limit
            effective_limit = self._limits[group]
            granted = min(requested, effective_limit)
            self._sequence += 1
            sequence = self._sequence
            while self._used.get(group, 0) + granted > effective_limit:
                self._waiters[job_id] = (group, sequence)
                wait_snapshot = self._snapshot_locked(group, job_id=job_id)
                if on_wait is not None:
                    self._condition.release()
                    try:
                        on_wait(wait_snapshot)
                    finally:
                        self._condition.acquire()
                self._condition.wait(timeout=0.5)
                effective_limit = self._limits.get(group, effective_limit)
                granted = min(requested, effective_limit)
            self._waiters.pop(job_id, None)
            self._used[group] = self._used.get(group, 0) + granted
            return _ResourceLease(
                manager=self,
                job_id=job_id,
                resource_group=group,
                granted_connections=granted,
                limit_connections=effective_limit,
            )

    def release(self, lease: _ResourceLease) -> None:
        with self._condition:
            current = self._used.get(lease.resource_group, 0)
            remaining = max(current - lease.granted_connections, 0)
            if remaining:
                self._used[lease.resource_group] = remaining
            else:
                self._used.pop(lease.resource_group, None)
            self._condition.notify_all()

    def usage(self, resource_group: str) -> dict[str, int]:
        with self._condition:
            return self._snapshot_locked(resource_group)

    def reset(self) -> None:
        with self._condition:
            self._limits.clear()
            self._used.clear()
            self._waiters.clear()
            self._sequence = 0
            self._condition.notify_all()

    def _snapshot_locked(self, resource_group: str, *, job_id: str | None = None) -> dict[str, int]:
        queue_position: int | None = None
        if job_id is not None and job_id in self._waiters:
            group, sequence = self._waiters[job_id]
            queue_position = 1 + sum(
                1
                for waiter_group, waiter_sequence in self._waiters.values()
                if waiter_group == group and waiter_sequence < sequence
            )
        waiting_count = sum(1 for group, _ in self._waiters.values() if group == resource_group)
        return {
            "resource_used": self._used.get(resource_group, 0),
            "resource_limit": self._limits.get(resource_group, 0),
            "waiting_count": waiting_count,
            "queue_position": queue_position or 0,
        }


@dataclass(frozen=True)
class _OutputLease:
    manager: "_OutputLockManager"
    key: str

    def release(self) -> None:
        self.manager.release(self)


class _OutputLockManager:
    """Best-effort in-process lock for collector output targets."""

    def __init__(self) -> None:
        self._condition = Condition(Lock())
        self._active: set[str] = set()
        self._waiters: dict[str, tuple[str, int]] = {}
        self._sequence = 0

    def acquire(self, *, job_id: str, key: str, on_wait: Any | None = None) -> _OutputLease:
        with self._condition:
            self._sequence += 1
            sequence = self._sequence
            while key in self._active:
                self._waiters[job_id] = (key, sequence)
                wait_snapshot = self._snapshot_locked(key, job_id=job_id)
                if on_wait is not None:
                    self._condition.release()
                    try:
                        on_wait(wait_snapshot)
                    finally:
                        self._condition.acquire()
                self._condition.wait(timeout=0.5)
            self._waiters.pop(job_id, None)
            self._active.add(key)
            return _OutputLease(manager=self, key=key)

    def release(self, lease: _OutputLease) -> None:
        with self._condition:
            self._active.discard(lease.key)
            self._condition.notify_all()

    def reset(self) -> None:
        with self._condition:
            self._active.clear()
            self._waiters.clear()
            self._sequence = 0
            self._condition.notify_all()

    def _snapshot_locked(self, key: str, *, job_id: str | None = None) -> dict[str, int]:
        queue_position: int | None = None
        if job_id is not None and job_id in self._waiters:
            waiter_key, sequence = self._waiters[job_id]
            queue_position = 1 + sum(
                1
                for current_key, current_sequence in self._waiters.values()
                if current_key == waiter_key and current_sequence < sequence
            )
        return {
            "output_waiting_count": sum(1 for current_key, _ in self._waiters.values() if current_key == key),
            "output_queue_position": queue_position or 0,
        }


_collector_resources = _CollectorResourceManager()
_output_locks = _OutputLockManager()


class DownloadRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict, description="Downloader request parameters.")
    fields: str | list[str] | None = Field(default=None, description="Selected fields to persist.")
    output_root: str | None = Field(default=None, description="Directory used as the downloader output root.")
    output_dir: str | None = Field(default=None, description="Final directory where output files are written.")
    formats: str | list[str] | None = Field(default=None, description="Output file formats.")
    collect_mode: str | None = Field(default=None, description="Collection mode.")
    connection_mode: str | None = Field(default=None, description="Downloader connection mode.")
    concurrency_mode: str | None = Field(default=None, description="Downloader concurrency preset mode.")
    connection_count: int | None = Field(default=None, description="Number of source connections/workers.")
    source_server_count: int | None = Field(default=None, description="Number of source servers to use.")
    connections_per_server: int | None = Field(default=None, description="Long connections per source server.")
    max_concurrent_tasks: int | None = Field(default=None, description="Maximum concurrent downloader tasks.")
    batch_size: int | None = Field(default=None, description="Downloader task batch size.")
    request_interval_ms: int | None = Field(default=None, description="Interval between source requests in milliseconds.")
    retry_count: int | None = Field(default=None, description="Retry count for source requests.")
    timeout_ms: int | None = Field(default=None, description="Per-request timeout in milliseconds.")
    async_job: bool = Field(default=False, description="Run as a background collection job.")


class DownloadScheduleRequest(DownloadRequest):
    frequency: str = Field(default="trade_day", description="daily, trade_day, or weekly.")
    time: str = Field(default="18:00", description="Local trigger time, HH:MM.")
    weekday: str = Field(default="1", description="Weekday for weekly schedules, 1-7.")
    enabled: bool = Field(default=True, description="Whether the schedule is enabled.")


@router.get("/v1/downloaders")
def list_downloaders() -> dict[str, Any]:
    from axdata_core import list_downloader_profiles

    profiles = list(list_downloader_profiles(data_root=data_root()))
    return response_payload(profiles, count=len(profiles))


@router.get("/v1/downloaders/{interface_name}")
def get_downloader(interface_name: str) -> JSONResponse:
    try:
        from axdata_core import DownloaderError, get_downloader_profile

        profile = get_downloader_profile(interface_name, data_root=data_root())
    except DownloaderError as exc:
        payload = error_payload(
            "DOWNLOADER_NOT_CONFIGURED",
            str(exc),
            interface_name=interface_name,
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))

    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(profile.to_dict())))


@router.post("/v1/download/{interface_name}")
def run_download(interface_name: str, request: DownloadRequest) -> JSONResponse:
    requested_fields = parse_fields(request.fields)
    try:
        from axdata_core import (
            DownloaderError,
            SourceAdapterError,
            SourceAdapterNotFound,
            SourceInterfaceNotFound,
            SourceRequestValidationError,
            SourceUnavailableError,
            run_downloader,
        )
    except ImportError:
        payload = error_payload(
            "DOWNLOADER_GATEWAY_UNAVAILABLE",
            "axdata_core downloader gateway is not available.",
            interface_name=interface_name,
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))

    kwargs = {
        "params": request.params,
        "fields": requested_fields,
        "data_root": data_root(),
        "output_root": request.output_root,
        "output_dir": request.output_dir,
        "formats": request.formats,
        "collect_mode": request.collect_mode,
        "connection_mode": request.connection_mode,
        "concurrency_mode": request.concurrency_mode,
        "connection_count": request.connection_count,
        "source_server_count": request.source_server_count,
        "connections_per_server": request.connections_per_server,
        "max_concurrent_tasks": request.max_concurrent_tasks,
        "batch_size": request.batch_size,
        "request_interval_ms": request.request_interval_ms,
        "retry_count": request.retry_count,
        "timeout_ms": request.timeout_ms,
    }

    if request.async_job:
        try:
            resource_request = _resolve_resource_request(interface_name, kwargs)
        except DownloaderError as exc:
            payload = error_payload(
                "DOWNLOADER_NOT_CONFIGURED",
                str(exc),
                interface_name=interface_name,
            )
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
        job = _create_job(
            interface_name,
            kwargs=kwargs,
            resource_request=resource_request,
            output_lock_key=_output_lock_key(interface_name, kwargs=kwargs),
            trigger_type="manual",
            skip_active_duplicates=True,
        )
        if job["status"] != "skipped":
            _executor.submit(_run_download_job, job["job_id"], interface_name, kwargs)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=to_jsonable(response_payload(job)))

    try:
        result = run_downloader(interface_name, **kwargs)
    except DownloaderError as exc:
        payload = error_payload(
            "DOWNLOADER_NOT_CONFIGURED",
            str(exc),
            interface_name=interface_name,
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except SourceInterfaceNotFound as exc:
        payload = error_payload("SOURCE_INTERFACE_NOT_FOUND", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except SourceRequestValidationError as exc:
        payload = error_payload("SOURCE_REQUEST_VALIDATION_ERROR", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=to_jsonable(payload))
    except SourceAdapterNotFound as exc:
        payload = error_payload("SOURCE_ADAPTER_NOT_FOUND", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content=to_jsonable(payload))
    except SourceUnavailableError as exc:
        payload = error_payload("SOURCE_UNAVAILABLE", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))
    except SourceAdapterError as exc:
        payload = error_payload("SOURCE_ADAPTER_ERROR", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=to_jsonable(payload))

    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(result)))


@router.get("/v1/download/jobs/{job_id}")
def get_download_job(job_id: str) -> JSONResponse:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            payload = error_payload("DOWNLOAD_JOB_NOT_FOUND", f"Download job {job_id!r} was not found.", job_id=job_id)
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
        started_at = _parse_datetime(job.get("started_at"))
        if started_at is not None and job.get("status") in {"queued", "waiting_resource", "waiting_output", "running"}:
            job["duration_ms"] = max(int((_utc_now() - started_at).total_seconds() * 1000), 0)
        return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(dict(job))))


@router.get("/v1/download/schedules/{interface_name}")
def get_download_schedule(interface_name: str) -> JSONResponse:
    _load_schedules_from_disk()
    with _schedules_lock:
        schedule = _schedules.get(interface_name)
    if schedule is None:
        payload = error_payload(
            "DOWNLOAD_SCHEDULE_NOT_FOUND",
            f"Download schedule {interface_name!r} was not found.",
            interface_name=interface_name,
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(schedule)))


@router.post("/v1/download/schedules/{interface_name}")
def enable_download_schedule(interface_name: str, request: DownloadScheduleRequest) -> JSONResponse:
    try:
        from axdata_core import DownloaderError, get_downloader_profile

        get_downloader_profile(interface_name, data_root=data_root())
    except DownloaderError as exc:
        payload = error_payload("DOWNLOADER_NOT_CONFIGURED", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))

    try:
        schedule = _build_schedule(interface_name, request)
        if schedule["frequency"] == "trade_day":
            _ensure_calendar_for_today()
    except ValueError as exc:
        payload = error_payload("DOWNLOAD_SCHEDULE_INVALID", str(exc), interface_name=interface_name)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=to_jsonable(payload))
    except Exception as exc:
        payload = error_payload(
            "DOWNLOAD_SCHEDULE_CALENDAR_ERROR",
            str(exc),
            interface_name=interface_name,
            error_type=type(exc).__name__,
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))

    with _schedules_lock:
        previous = _schedules.get(interface_name, {})
        schedule["last_run_key"] = previous.get("last_run_key")
        schedule["last_job_id"] = previous.get("last_job_id")
        schedule["last_checked_at"] = previous.get("last_checked_at")
        _schedules[interface_name] = schedule
        snapshot = dict(_schedules)
    _write_schedules_to_disk(snapshot)
    start_download_scheduler_loop()
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(schedule)))


@router.delete("/v1/download/schedules/{interface_name}")
def disable_download_schedule(interface_name: str) -> JSONResponse:
    _load_schedules_from_disk()
    with _schedules_lock:
        schedule = _schedules.get(interface_name)
        if schedule is None:
            payload = error_payload(
                "DOWNLOAD_SCHEDULE_NOT_FOUND",
                f"Download schedule {interface_name!r} was not found.",
                interface_name=interface_name,
            )
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
        schedule = {**schedule, "enabled": False, "updated_at": _utc_now().isoformat()}
        _schedules[interface_name] = schedule
        snapshot = dict(_schedules)
    _write_schedules_to_disk(snapshot)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(schedule)))


def start_download_scheduler_loop() -> None:
    if _scheduler_started.is_set():
        return
    _scheduler_started.set()
    _load_schedules_from_disk()
    Thread(target=_run_download_scheduler_loop, name="axdata-download-scheduler", daemon=True).start()


def _create_job(
    interface_name: str,
    *,
    kwargs: dict[str, Any] | None = None,
    resource_request: _ResourceRequest | None = None,
    output_lock_key: str | None = None,
    job_kind: str = "download",
    collector_name: str | None = None,
    trigger_type: str = "manual",
    schedule_run_key: str | None = None,
    duplicate_reference_time: datetime | None = None,
    skip_active_duplicates: bool = False,
    skip_success_same_day: bool = False,
    enforce_failure_backoff: bool = False,
) -> dict[str, Any]:
    now = _utc_now()
    duplicate_now = duplicate_reference_time or now
    job_kwargs = kwargs or {}
    resource = resource_request or _ResourceRequest(
        resource_group="default",
        requested_connections=1,
        limit_connections=1,
    )
    lock_key = output_lock_key or _output_lock_key(interface_name, kwargs=job_kwargs)
    run_signature = _run_signature(
        interface_name,
        kwargs=job_kwargs,
        output_lock_key=lock_key,
        collector_name=collector_name,
    )
    job = {
        "job_id": f"job_{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}",
        "job_kind": job_kind,
        "collector_name": collector_name,
        "interface_name": interface_name,
        "status": "queued",
        "progress_pct": 0,
        "message": "等待采集",
        "trigger_type": trigger_type,
        "provider_id": resource.provider_id,
        "resource_group": resource.resource_group,
        "resource_requested": resource.requested_connections,
        "resource_granted": 0,
        "resource_used": 0,
        "resource_limit": resource.limit_connections,
        "resource_wait_reason": None,
        "queue_position": 0,
        "output_lock_key": lock_key,
        "output_wait_reason": None,
        "output_queue_position": 0,
        "run_signature": run_signature,
        "schedule_run_key": schedule_run_key,
        "duplicate_job_id": None,
        "skip_reason": None,
        "backoff_until": None,
        "started_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "finished_at": None,
        "duration_ms": 0,
        "eta_ms": None,
        "progress_current": None,
        "progress_total": None,
        "progress_unit": None,
        "progress_label": None,
        "result": None,
        "error": None,
    }
    with _jobs_lock:
        if enforce_failure_backoff:
            backoff_until = _active_failure_backoff_locked(run_signature, now)
            if backoff_until is not None:
                skipped = _skipped_job(
                    job,
                    now,
                    reason="failure_backoff",
                    message=f"上次失败后退避中，{backoff_until.astimezone(_LOCAL_TIMEZONE).strftime('%H:%M:%S')} 后再试",
                    backoff_until=backoff_until,
                )
                _jobs[skipped["job_id"]] = skipped
                return dict(skipped)
        if skip_active_duplicates:
            duplicate = _find_active_duplicate_locked(run_signature)
            if duplicate is not None:
                skipped = _skipped_job(
                    job,
                    now,
                    reason="active_duplicate",
                    message="已有相同采集任务正在运行，本次跳过",
                    duplicate_job_id=str(duplicate.get("job_id")),
                )
                _jobs[skipped["job_id"]] = skipped
                return dict(skipped)
        if skip_success_same_day:
            duplicate = _find_success_same_day_locked(run_signature, duplicate_now, schedule_run_key=schedule_run_key)
            if duplicate is not None:
                skipped = _skipped_job(
                    job,
                    now,
                    reason="duplicate_success",
                    message="今天已有相同采集结果，本次自动任务跳过",
                    duplicate_job_id=str(duplicate.get("job_id")),
                )
                _jobs[skipped["job_id"]] = skipped
                return dict(skipped)
        _jobs[job["job_id"]] = job
    return dict(job)


def _run_download_job(job_id: str, interface_name: str, kwargs: dict[str, Any]) -> None:
    def progress(percent: int, message: str, **details: Any) -> None:
        allowed_details = {
            key: details[key]
            for key in ("progress_current", "progress_total", "progress_unit", "progress_label", "eta_ms")
            if key in details
        }
        _update_job(job_id, progress_pct=percent, message=message, status="running", **allowed_details)

    resource_request = _job_resource_request(job_id, interface_name, kwargs)
    output_key = _output_lock_key(interface_name, kwargs=kwargs)
    lease: _ResourceLease | None = None
    output_lease: _OutputLease | None = None
    try:
        lease = _collector_resources.acquire(
            job_id=job_id,
            resource_group=resource_request.resource_group,
            requested_connections=resource_request.requested_connections,
            limit_connections=resource_request.limit_connections,
            on_wait=lambda usage: _mark_job_waiting_for_resource(
                job_id,
                resource_request,
                usage,
            ),
        )
        usage = _collector_resources.usage(lease.resource_group)
        _update_job(
            job_id,
            status="running",
            progress_pct=1,
            message="开始采集",
            resource_group=lease.resource_group,
            resource_requested=resource_request.requested_connections,
            resource_granted=lease.granted_connections,
            resource_used=usage["resource_used"],
            resource_limit=usage["resource_limit"],
            resource_wait_reason=None,
            queue_position=0,
            output_lock_key=output_key,
        )
        output_lease = _output_locks.acquire(
            job_id=job_id,
            key=output_key,
            on_wait=lambda usage: _mark_job_waiting_for_output(
                job_id,
                output_key,
                usage,
            ),
        )
        _update_job(
            job_id,
            status="running",
            output_wait_reason=None,
            output_queue_position=0,
        )
        from axdata_core import run_downloader

        result = run_downloader(interface_name, progress_callback=progress, **kwargs)
    except Exception as exc:  # background job must keep errors queryable
        finished_at = _utc_now()
        backoff_until = None
        if _should_apply_failure_backoff(exc):
            signature = _job_run_signature(job_id) or _run_signature(
                interface_name,
                kwargs=kwargs,
                output_lock_key=output_key,
            )
            backoff_until = _record_failure_backoff(signature, finished_at)
        _update_job(
            job_id,
            status="failed",
            progress_pct=100,
            message="采集失败",
            error={"message": str(exc), "type": type(exc).__name__},
            finished_at=finished_at.isoformat(),
            backoff_until=backoff_until.isoformat() if backoff_until is not None else None,
        )
        return
    finally:
        if output_lease is not None:
            output_lease.release()
        if lease is not None:
            lease.release()

    _update_job(
        job_id,
        status="success",
        progress_pct=100,
        message="采集完成",
        result=result,
        finished_at=_utc_now().isoformat(),
    )
    signature = _job_run_signature(job_id)
    if signature:
        _clear_failure_backoff(signature)


def _run_collector_job(
    job_id: str,
    collector_name: str,
    interface_name: str,
    kwargs: dict[str, Any],
) -> None:
    def progress(percent: int, message: str, **details: Any) -> None:
        allowed_details = {
            key: details[key]
            for key in ("progress_current", "progress_total", "progress_unit", "progress_label", "eta_ms")
            if key in details
        }
        _update_job(job_id, progress_pct=percent, message=message, status="running", **allowed_details)

    resource_request = _job_resource_request(job_id, interface_name, kwargs)
    output_key = _output_lock_key(interface_name, kwargs=kwargs)
    lease: _ResourceLease | None = None
    output_lease: _OutputLease | None = None
    try:
        lease = _collector_resources.acquire(
            job_id=job_id,
            resource_group=resource_request.resource_group,
            requested_connections=resource_request.requested_connections,
            limit_connections=resource_request.limit_connections,
            on_wait=lambda usage: _mark_job_waiting_for_resource(
                job_id,
                resource_request,
                usage,
            ),
        )
        usage = _collector_resources.usage(lease.resource_group)
        _update_job(
            job_id,
            status="running",
            progress_pct=1,
            message="开始运行采集器",
            resource_group=lease.resource_group,
            resource_requested=resource_request.requested_connections,
            resource_granted=lease.granted_connections,
            resource_used=usage["resource_used"],
            resource_limit=usage["resource_limit"],
            resource_wait_reason=None,
            queue_position=0,
            output_lock_key=output_key,
        )
        output_lease = _output_locks.acquire(
            job_id=job_id,
            key=output_key,
            on_wait=lambda usage: _mark_job_waiting_for_output(
                job_id,
                output_key,
                usage,
            ),
        )
        _update_job(
            job_id,
            status="running",
            output_wait_reason=None,
            output_queue_position=0,
        )
        from axdata_core import run_collector

        result = run_collector(collector_name, progress_callback=progress, **kwargs)
    except Exception as exc:  # background job must keep errors queryable
        finished_at = _utc_now()
        backoff_until = None
        if _should_apply_failure_backoff(exc):
            signature = _job_run_signature(job_id) or _run_signature(
                interface_name,
                kwargs=kwargs,
                output_lock_key=output_key,
                collector_name=collector_name,
            )
            backoff_until = _record_failure_backoff(signature, finished_at)
        _update_job(
            job_id,
            status="failed",
            progress_pct=100,
            message="采集器运行失败",
            error={"message": str(exc), "type": type(exc).__name__},
            finished_at=finished_at.isoformat(),
            backoff_until=backoff_until.isoformat() if backoff_until is not None else None,
        )
        return
    finally:
        if output_lease is not None:
            output_lease.release()
        if lease is not None:
            lease.release()

    _update_job(
        job_id,
        status="success",
        progress_pct=100,
        message="采集器运行完成",
        result=result,
        finished_at=_utc_now().isoformat(),
    )
    signature = _job_run_signature(job_id)
    if signature:
        _clear_failure_backoff(signature)


def _update_job(job_id: str, **updates: Any) -> None:
    now = _utc_now()
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        job.update(updates)
        job["updated_at"] = now.isoformat()
        started_at = _parse_datetime(job.get("started_at"))
        if started_at is not None:
            elapsed_ms = int((now - started_at).total_seconds() * 1000)
            job["duration_ms"] = max(elapsed_ms, 0)
            if "eta_ms" not in updates:
                job["eta_ms"] = None


def _skipped_job(
    job: dict[str, Any],
    now: datetime,
    *,
    reason: str,
    message: str,
    duplicate_job_id: str | None = None,
    backoff_until: datetime | None = None,
) -> dict[str, Any]:
    skipped = dict(job)
    skipped.update(
        {
            "status": "skipped",
            "progress_pct": 100,
            "message": message,
            "duplicate_job_id": duplicate_job_id,
            "skip_reason": reason,
            "backoff_until": backoff_until.isoformat() if backoff_until is not None else None,
            "finished_at": now.isoformat(),
            "duration_ms": 0,
            "eta_ms": None,
        }
    )
    return skipped


def _find_active_duplicate_locked(run_signature: str) -> dict[str, Any] | None:
    for job in _jobs.values():
        if job.get("run_signature") == run_signature and job.get("status") in _ACTIVE_JOB_STATUSES:
            return job
    return None


def _find_success_same_day_locked(
    run_signature: str,
    now: datetime,
    *,
    schedule_run_key: str | None = None,
) -> dict[str, Any] | None:
    current_date = now.astimezone(_LOCAL_TIMEZONE).date()
    for job in _jobs.values():
        if job.get("run_signature") != run_signature or job.get("status") != "success":
            continue
        if schedule_run_key and job.get("schedule_run_key") == schedule_run_key:
            return job
        finished_at = _parse_datetime(job.get("finished_at")) or _parse_datetime(job.get("updated_at"))
        if finished_at is not None and finished_at.astimezone(_LOCAL_TIMEZONE).date() == current_date:
            return job
    return None


def _active_failure_backoff_locked(run_signature: str, now: datetime) -> datetime | None:
    backoff_until = _failure_backoff.get(run_signature)
    if backoff_until is None:
        return None
    if backoff_until <= now:
        _failure_backoff.pop(run_signature, None)
        return None
    return backoff_until


def _record_failure_backoff(run_signature: str, now: datetime) -> datetime:
    backoff_until = now + timedelta(seconds=_FAILURE_BACKOFF_SECONDS)
    with _jobs_lock:
        _failure_backoff[run_signature] = backoff_until
    return backoff_until


def _clear_failure_backoff(run_signature: str) -> None:
    with _jobs_lock:
        _failure_backoff.pop(run_signature, None)


def _job_run_signature(job_id: str) -> str | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None
        signature = job.get("run_signature")
    return str(signature) if signature else None


def _should_apply_failure_backoff(exc: Exception) -> bool:
    non_backoff_errors = {
        "CollectorError",
        "DownloaderError",
        "SourceInterfaceNotFound",
        "SourceRequestValidationError",
        "ValueError",
    }
    return type(exc).__name__ not in non_backoff_errors


def _mark_job_waiting_for_resource(
    job_id: str,
    resource_request: _ResourceRequest,
    usage: dict[str, int],
) -> None:
    used = usage["resource_used"]
    limit = usage["resource_limit"] or resource_request.limit_connections
    queue_position = usage["queue_position"]
    reason = (
        f"{resource_request.resource_group} 资源组已占用 "
        f"{used}/{limit} 连接，等待 {resource_request.requested_connections} 条连接"
    )
    if queue_position > 0:
        reason = f"{reason}，前面还有 {queue_position - 1} 个任务"
    _update_job(
        job_id,
        status="waiting_resource",
        progress_pct=0,
        message=f"等待资源：{reason}",
        resource_group=resource_request.resource_group,
        resource_requested=resource_request.requested_connections,
        resource_granted=0,
        resource_used=used,
        resource_limit=limit,
        resource_wait_reason=reason,
        queue_position=queue_position,
    )


def _mark_job_waiting_for_output(
    job_id: str,
    output_key: str,
    usage: dict[str, int],
) -> None:
    queue_position = usage["output_queue_position"]
    reason = f"输出目标正在写入，等待 {output_key}"
    if queue_position > 0:
        reason = f"{reason}，前面还有 {queue_position - 1} 个任务"
    _update_job(
        job_id,
        status="waiting_output",
        message=f"等待写入：{reason}",
        output_lock_key=output_key,
        output_wait_reason=reason,
        output_queue_position=queue_position,
    )


def _job_resource_request(job_id: str, interface_name: str, kwargs: dict[str, Any]) -> _ResourceRequest:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None and job.get("resource_group"):
            return _ResourceRequest(
                resource_group=str(job.get("resource_group")),
                requested_connections=_safe_int(job.get("resource_requested"), default=1),
                limit_connections=_safe_int(job.get("resource_limit"), default=1),
                provider_id=str(job["provider_id"]) if job.get("provider_id") else None,
            )
    return _resolve_resource_request(interface_name, kwargs)


def _resolve_resource_request(interface_name: str, kwargs: dict[str, Any]) -> _ResourceRequest:
    from axdata_core import get_downloader_profile

    profile = get_downloader_profile(interface_name, data_root=data_root())
    provider_id = profile.provider_id
    resource_group = str(profile.resource_group or "default")
    limit_connections = _safe_int(
        profile.manifest_default_limits.get("max_connections_total"),
        default=profile.max_connection_count,
    )
    requested_connections = _requested_connection_count(interface_name, kwargs, profile=profile)
    limit_connections = max(limit_connections, requested_connections, 1)
    return _ResourceRequest(
        resource_group=resource_group,
        requested_connections=requested_connections,
        limit_connections=limit_connections,
        provider_id=provider_id,
    )


def _requested_connection_count(
    interface_name: str,
    kwargs: dict[str, Any],
    *,
    profile: Any | None = None,
) -> int:
    try:
        if profile is None:
            from axdata_core import get_downloader_profile

            profile = get_downloader_profile(interface_name, data_root=data_root())
        concurrency = profile.concurrency
        if concurrency.mode_editable and kwargs.get("concurrency_mode") in {"low", "medium", "high"}:
            preset = {
                "low": (1, 2, 2),
                "medium": (2, 2, 4),
                "high": (4, 2, 8),
            }[str(kwargs.get("concurrency_mode"))]
            source_server_count = min(concurrency.max_source_server_count, preset[0])
            connections_per_server = min(concurrency.max_connections_per_server, preset[1])
            max_concurrent_tasks = min(concurrency.max_max_concurrent_tasks, preset[2])
            return max(min(source_server_count * connections_per_server, max_concurrent_tasks), 1)
        source_server_count = _safe_int(
            kwargs.get("source_server_count") if concurrency.source_server_count_editable else None,
            default=concurrency.default_source_server_count,
        )
        connections_per_server = _safe_int(
            kwargs.get("connections_per_server") if concurrency.connections_per_server_editable else None,
            default=concurrency.default_connections_per_server,
        )
        default_tasks = concurrency.default_max_concurrent_tasks
        if not concurrency.max_concurrent_tasks_editable:
            default_tasks = min(
                concurrency.max_max_concurrent_tasks,
                source_server_count * connections_per_server,
            )
        max_concurrent_tasks = _safe_int(
            kwargs.get("max_concurrent_tasks") if concurrency.max_concurrent_tasks_editable else None,
            default=default_tasks,
        )
        connection_count = kwargs.get("connection_count")
        if (
            connection_count is not None
            and concurrency.max_concurrent_tasks_editable
            and kwargs.get("source_server_count") is None
            and kwargs.get("connections_per_server") is None
        ):
            max_concurrent_tasks = _safe_int(connection_count, default=max_concurrent_tasks)
        return max(min(source_server_count * connections_per_server, max_concurrent_tasks), 1)
    except Exception:
        return 1


def _safe_int(value: Any, *, default: int) -> int:
    try:
        if value is None:
            return max(int(default), 1)
        return max(int(value), 1)
    except (TypeError, ValueError):
        return max(int(default), 1)


def _output_lock_key(interface_name: str, *, kwargs: dict[str, Any]) -> str:
    output_dir = kwargs.get("output_dir")
    output_root = kwargs.get("output_root")
    data_root_value = kwargs.get("data_root")
    if output_dir:
        root = Path(str(output_dir)).expanduser().resolve()
    elif output_root:
        root = Path(str(output_root)).expanduser().resolve()
    elif data_root_value:
        root = Path(str(data_root_value)).expanduser().resolve()
    else:
        root = data_root().resolve()

    formats = kwargs.get("formats")
    if isinstance(formats, str):
        format_key = ",".join(sorted(item.strip().lower() for item in formats.split(",") if item.strip()))
    elif isinstance(formats, (list, tuple, set)):
        format_key = ",".join(sorted(str(item).strip().lower() for item in formats if str(item).strip()))
    else:
        format_key = "default"
    return f"{interface_name}|{root}|{format_key or 'default'}"


def _run_signature(
    interface_name: str,
    *,
    kwargs: dict[str, Any],
    output_lock_key: str,
    collector_name: str | None = None,
) -> str:
    payload = {
        "interface_name": interface_name,
        "kwargs": _normalize_signature_value(kwargs),
        "output_lock_key": output_lock_key,
    }
    if collector_name:
        payload["collector_name"] = collector_name
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_signature_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_signature_value(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalize_signature_value(item) for item in value]
    if isinstance(value, set):
        return [_normalize_signature_value(item) for item in sorted(value, key=str)]
    if isinstance(value, Path):
        return str(value.expanduser().resolve())
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _run_download_scheduler_loop() -> None:
    while True:
        try:
            _tick_download_schedules()
        except Exception:
            pass
        sleep(30)


def _tick_download_schedules(*, now: datetime | None = None) -> list[dict[str, Any]]:
    current = (now or datetime.now(_LOCAL_TIMEZONE)).astimezone(_LOCAL_TIMEZONE)
    _load_schedules_from_disk()
    triggered: list[dict[str, Any]] = []
    with _schedules_lock:
        schedules = [dict(item) for item in _schedules.values()]
    for schedule in schedules:
        if not _schedule_due(schedule, current):
            continue
        if schedule.get("frequency") == "trade_day" and not _today_is_trade_day(current.date()):
            _mark_schedule_checked(schedule["interface_name"], current)
            continue
        kwargs = dict(schedule.get("download_kwargs") or {})
        try:
            resource_request = _resolve_resource_request(schedule["interface_name"], kwargs)
        except Exception:
            _mark_schedule_checked(schedule["interface_name"], current)
            continue
        run_key = _schedule_run_key(current)
        job = _create_job(
            schedule["interface_name"],
            kwargs=kwargs,
            resource_request=resource_request,
            output_lock_key=_output_lock_key(schedule["interface_name"], kwargs=kwargs),
            trigger_type="schedule",
            schedule_run_key=run_key,
            duplicate_reference_time=current,
            skip_active_duplicates=True,
            skip_success_same_day=True,
            enforce_failure_backoff=True,
        )
        if job["status"] != "skipped":
            _executor.submit(_run_download_job, job["job_id"], schedule["interface_name"], kwargs)
        _mark_schedule_triggered(schedule["interface_name"], current, job["job_id"])
        triggered.append(job)
    return triggered


def _schedule_due(schedule: dict[str, Any], now: datetime) -> bool:
    if not schedule.get("enabled", True):
        return False
    trigger_time = str(schedule.get("time") or "")
    if trigger_time != now.strftime("%H:%M"):
        return False
    frequency = schedule.get("frequency")
    if frequency == "weekly" and str(schedule.get("weekday") or "1") != str(now.isoweekday()):
        return False
    if frequency not in {"daily", "trade_day", "weekly"}:
        return False
    return schedule.get("last_run_key") != _schedule_run_key(now)


def _mark_schedule_checked(interface_name: str, now: datetime) -> None:
    with _schedules_lock:
        schedule = _schedules.get(interface_name)
        if schedule is None:
            return
        schedule["last_checked_at"] = now.isoformat()
        snapshot = dict(_schedules)
    _write_schedules_to_disk(snapshot)


def _mark_schedule_triggered(interface_name: str, now: datetime, job_id: str) -> None:
    with _schedules_lock:
        schedule = _schedules.get(interface_name)
        if schedule is None:
            return
        schedule["last_run_key"] = _schedule_run_key(now)
        schedule["last_job_id"] = job_id
        schedule["last_checked_at"] = now.isoformat()
        schedule["updated_at"] = _utc_now().isoformat()
        snapshot = dict(_schedules)
    _write_schedules_to_disk(snapshot)


def _build_schedule(interface_name: str, request: DownloadScheduleRequest) -> dict[str, Any]:
    frequency = _normalize_frequency(request.frequency)
    trigger_time = _normalize_schedule_time(request.time)
    weekday = _normalize_weekday(request.weekday)
    requested_fields = parse_fields(request.fields)
    created_at = _utc_now().isoformat()
    return {
        "interface_name": interface_name,
        "enabled": bool(request.enabled),
        "frequency": frequency,
        "time": trigger_time,
        "weekday": weekday,
        "timezone": "Asia/Shanghai",
        "download_kwargs": _download_kwargs(request, requested_fields),
        "created_at": created_at,
        "updated_at": created_at,
    }


def _download_kwargs(request: DownloadRequest, requested_fields: list[str] | None) -> dict[str, Any]:
    return {
        "params": request.params,
        "fields": requested_fields,
        "data_root": str(data_root()),
        "output_root": request.output_root,
        "output_dir": request.output_dir,
        "formats": request.formats,
        "collect_mode": request.collect_mode,
        "connection_mode": request.connection_mode,
        "concurrency_mode": request.concurrency_mode,
        "connection_count": request.connection_count,
        "source_server_count": request.source_server_count,
        "connections_per_server": request.connections_per_server,
        "max_concurrent_tasks": request.max_concurrent_tasks,
        "batch_size": request.batch_size,
        "request_interval_ms": request.request_interval_ms,
        "retry_count": request.retry_count,
        "timeout_ms": request.timeout_ms,
    }


def _normalize_frequency(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in {"daily", "trade_day", "weekly"}:
        raise ValueError("frequency must be daily, trade_day, or weekly.")
    return normalized


def _normalize_schedule_time(value: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.strptime(text, "%H:%M")
    except ValueError as exc:
        raise ValueError("time must be HH:MM.") from exc
    return parsed.strftime("%H:%M")


def _normalize_weekday(value: str) -> str:
    text = str(value or "1").strip()
    if text not in {"1", "2", "3", "4", "5", "6", "7"}:
        raise ValueError("weekday must be 1-7.")
    return text


def _schedule_run_key(value: datetime) -> str:
    return value.astimezone(_LOCAL_TIMEZONE).strftime("%Y%m%d_%H%M")


def _today_is_trade_day(today: date) -> bool:
    status_data = _ensure_calendar_for_today(today=today)
    return bool(status_data.get("today_is_open"))


def _ensure_calendar_for_today(*, today: date | None = None) -> dict[str, Any]:
    from axdata_core import ensure_trade_calendar_cache, get_trade_calendar_cache_status

    root = data_root()
    status_data = get_trade_calendar_cache_status(root, today=today)
    if status_data.get("covers_today"):
        return status_data
    return ensure_trade_calendar_cache(root, today=today)


def _schedule_store_path() -> Path:
    return data_root() / "cache" / "schedules" / "download_schedules.json"


def _load_schedules_from_disk() -> None:
    path = _schedule_store_path()
    if not path.exists():
        with _schedules_lock:
            _schedules.clear()
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict):
        return
    schedules = {str(key): value for key, value in raw.items() if isinstance(value, dict)}
    with _schedules_lock:
        _schedules.clear()
        _schedules.update(schedules)


def _write_schedules_to_disk(schedules: dict[str, dict[str, Any]]) -> None:
    path = _schedule_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schedules, ensure_ascii=False, indent=2), encoding="utf-8")
