from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import data_root
from .serialization import error_payload, parse_fields, response_payload, to_jsonable


router = APIRouter()
_collector_service_cache: dict[str, Any] = {}
DEFAULT_RUN_LIST_LIMIT = 100
MAX_RUN_LIST_LIMIT = 500


class CollectorTaskRequest(BaseModel):
    collector_name: str = Field(description="CollectorSpec name to schedule.")
    task_id: str | None = Field(default=None, description="Optional stable task id.")
    name: str | None = Field(default=None, description="Display name.")
    enabled: bool = Field(default=True, description="Whether this task should run when scheduled.")
    trigger_type: str = Field(default="manual", description="manual, interval, daily, or startup.")
    interval_seconds: int | None = Field(default=None, description="Interval trigger seconds.")
    daily_time: str | None = Field(default=None, description="Daily local trigger time, HH:MM.")
    params: dict[str, Any] = Field(default_factory=dict, description="Collector params.")
    fields: str | list[str] | None = Field(default=None, description="Selected fields.")
    output_root: str | None = Field(default=None, description="Output root.")
    output_dir: str | None = Field(default=None, description="Final output directory.")
    formats: str | list[str] | None = Field(default=None, description="Output formats.")
    collect_mode: str | None = None
    connection_mode: str | None = None
    concurrency_mode: str | None = None
    connection_count: int | None = None
    source_server_count: int | None = None
    connections_per_server: int | None = None
    max_concurrent_tasks: int | None = None
    batch_size: int | None = None
    request_interval_ms: int | None = None
    retry_count: int | None = None
    max_retries: int | None = Field(default=None, description="Collector run-level retry attempts after the first failure.")
    backoff_seconds: int | None = Field(default=None, description="Seconds to wait between Collector run-level retry attempts.")
    timeout_ms: int | None = None


class CollectorTaskPatchRequest(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    trigger_type: str | None = None
    interval_seconds: int | None = None
    daily_time: str | None = None
    params: dict[str, Any] | None = None
    fields: str | list[str] | None = None
    output_root: str | None = None
    output_dir: str | None = None
    formats: str | list[str] | None = None
    collect_mode: str | None = None
    connection_mode: str | None = None
    concurrency_mode: str | None = None
    connection_count: int | None = None
    source_server_count: int | None = None
    connections_per_server: int | None = None
    max_concurrent_tasks: int | None = None
    batch_size: int | None = None
    request_interval_ms: int | None = None
    retry_count: int | None = None
    max_retries: int | None = None
    backoff_seconds: int | None = None
    timeout_ms: int | None = None


class CollectorTaskRunRequest(BaseModel):
    trigger_type: str = Field(default="manual", description="manual, interval, daily, or startup.")
    params: dict[str, Any] = Field(default_factory=dict, description="Params merged only into this run.")
    start: str | None = Field(default=None, description="Optional start date override.")
    end: str | None = Field(default=None, description="Optional end date override.")
    symbol: str | None = Field(default=None, description="Optional code/symbol override.")
    limit: int | None = Field(default=None, description="Optional limit/count override.")


class CollectorTaskBackfillRequest(BaseModel):
    start: str = Field(description="Start date, YYYYMMDD or YYYY-MM-DD.")
    end: str = Field(description="End date, YYYYMMDD or YYYY-MM-DD.")
    params: dict[str, Any] = Field(default_factory=dict, description="Params merged only into this backfill run.")
    symbol: str | None = Field(default=None, description="Optional code/symbol override.")
    limit: int | None = Field(default=None, description="Optional limit/count override.")


class CollectorTaskTemplateRequest(BaseModel):
    template_id: str = Field(description="Built-in task template id.")
    task_id: str | None = Field(default=None, description="Optional stable task id.")
    name: str | None = Field(default=None, description="Display name.")
    enabled: bool | None = Field(default=None, description="Whether this task should run when scheduled.")
    trigger_type: str | None = Field(default=None, description="manual, interval, daily, or startup.")
    interval_seconds: int | None = Field(default=None, description="Interval trigger seconds.")
    daily_time: str | None = Field(default=None, description="Daily local trigger time, HH:MM.")
    params: dict[str, Any] = Field(default_factory=dict, description="Params merged over template defaults.")
    fields: str | list[str] | None = Field(default=None, description="Selected fields.")
    formats: str | list[str] | None = Field(default=None, description="Output formats.")


@router.get("/v1/collector/tasks/templates")
@router.get("/v1/tasks/templates")
def list_collector_task_templates() -> dict[str, Any]:
    from axdata_core import list_task_templates

    templates = [template.to_dict() for template in list_task_templates(data_root=data_root())]
    return response_payload(templates, count=len(templates))


@router.get("/v1/collector/tasks/templates/{template_id}")
@router.get("/v1/tasks/templates/{template_id}")
def get_collector_task_template(template_id: str) -> JSONResponse:
    from axdata_core import get_task_template

    try:
        template = get_task_template(template_id, data_root=data_root())
    except Exception as exc:
        return _collector_error_response(exc, template_id=template_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(template.to_dict())))


@router.post("/v1/collector/tasks/from-template")
@router.post("/v1/tasks/from-template")
def create_collector_task_from_template(request: CollectorTaskTemplateRequest) -> JSONResponse:
    service = _collector_service()
    try:
        from axdata_core import task_template_to_create_kwargs

        kwargs = task_template_to_create_kwargs(
            request.template_id,
            data_root=data_root(),
            task_id=request.task_id,
            name=request.name,
            enabled=request.enabled,
            params=request.params,
            fields=parse_fields(request.fields),
            formats=parse_fields(request.formats),
            trigger_type=request.trigger_type,
            interval_seconds=request.interval_seconds,
            daily_time=request.daily_time,
        )
        collector_name = kwargs.pop("collector_name")
        task = service.create_task(collector_name, **kwargs)
    except Exception as exc:
        return _collector_error_response(exc, template_id=request.template_id)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=to_jsonable(response_payload(task.to_dict())))


@router.get("/v1/collector/tasks")
@router.get("/v1/tasks")
def list_collector_tasks() -> dict[str, Any]:
    service = _collector_service()
    tasks = [task.to_dict() for task in service.list_tasks()]
    return response_payload(tasks, count=len(tasks))


@router.post("/v1/collector/tasks")
@router.post("/v1/tasks")
def create_collector_task(request: CollectorTaskRequest) -> JSONResponse:
    service = _collector_service()
    try:
        task = service.create_task(
            request.collector_name,
            task_id=request.task_id,
            name=request.name,
            enabled=request.enabled,
            trigger_type=request.trigger_type,
            interval_seconds=request.interval_seconds,
            daily_time=request.daily_time,
            params=request.params,
            fields=parse_fields(request.fields),
            output_root=request.output_root,
            output_dir=request.output_dir,
            formats=parse_fields(request.formats),
            collect_mode=request.collect_mode,
            connection_mode=request.connection_mode,
            concurrency_mode=request.concurrency_mode,
            connection_count=request.connection_count,
            source_server_count=request.source_server_count,
            connections_per_server=request.connections_per_server,
            max_concurrent_tasks=request.max_concurrent_tasks,
            batch_size=request.batch_size,
            request_interval_ms=request.request_interval_ms,
            retry_count=request.retry_count,
            max_retries=request.max_retries,
            backoff_seconds=request.backoff_seconds,
            timeout_ms=request.timeout_ms,
        )
    except Exception as exc:
        return _collector_error_response(exc)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=to_jsonable(response_payload(task.to_dict())))


@router.get("/v1/collector/tasks/{task_id}")
@router.get("/v1/tasks/{task_id}")
def get_collector_task(task_id: str) -> JSONResponse:
    service = _collector_service()
    task = service.store.get_task(task_id)
    if task is None:
        return _not_found("COLLECTOR_TASK_NOT_FOUND", f"Collector task {task_id!r} was not found.", task_id=task_id)
    task = service.refresh_task(task)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(task.to_dict())))


@router.patch("/v1/collector/tasks/{task_id}")
@router.patch("/v1/tasks/{task_id}")
def patch_collector_task(task_id: str, request: CollectorTaskPatchRequest) -> JSONResponse:
    service = _collector_service()
    updates = request.model_dump(exclude_unset=True)
    if "fields" in updates:
        updates["fields"] = parse_fields(updates["fields"])
    if "formats" in updates:
        updates["formats"] = parse_fields(updates["formats"])
    try:
        task = service.store.update_task(task_id, **updates)
    except Exception as exc:
        return _collector_error_response(exc, task_id=task_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(task.to_dict())))


@router.delete("/v1/collector/tasks/{task_id}")
@router.delete("/v1/tasks/{task_id}")
def delete_collector_task(task_id: str) -> JSONResponse:
    service = _collector_service()
    try:
        task = service.delete_task(task_id)
    except Exception as exc:
        return _collector_error_response(exc, task_id=task_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(task.to_dict())))


@router.post("/v1/collector/tasks/{task_id}/run")
@router.post("/v1/tasks/{task_id}/run")
def run_collector_task(task_id: str, request: CollectorTaskRunRequest) -> JSONResponse:
    service = _collector_service()
    try:
        overrides = _collector_run_overrides(request)
        run = service.submit_task(
            task_id,
            trigger_type=request.trigger_type,
            allow_disabled_manual_run=request.trigger_type == "manual",
            params_override=overrides or None,
            metadata={"run_mode": "manual", "params_override": overrides} if overrides else None,
        )
    except Exception as exc:
        return _collector_error_response(exc, task_id=task_id)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=to_jsonable(response_payload(run.to_dict())))


@router.post("/v1/collector/tasks/{task_id}/backfill")
@router.post("/v1/tasks/{task_id}/backfill")
def backfill_collector_task(task_id: str, request: CollectorTaskBackfillRequest) -> JSONResponse:
    service = _collector_service()
    try:
        overrides = _collector_run_overrides(request, include_dates=False)
        run = service.backfill_task(
            task_id,
            start=request.start,
            end=request.end,
            params_override=overrides or None,
        )
    except Exception as exc:
        return _collector_error_response(exc, task_id=task_id)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=to_jsonable(response_payload(run.to_dict())))


@router.post("/v1/collector/tasks/{task_id}/enable")
@router.post("/v1/tasks/{task_id}/enable")
def enable_collector_task(task_id: str) -> JSONResponse:
    service = _collector_service()
    try:
        task = service.refresh_task(service.store.set_task_enabled(task_id, True))
    except Exception as exc:
        return _collector_error_response(exc, task_id=task_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(task.to_dict())))


@router.post("/v1/collector/tasks/{task_id}/disable")
@router.post("/v1/tasks/{task_id}/disable")
def disable_collector_task(task_id: str) -> JSONResponse:
    service = _collector_service()
    try:
        task = service.refresh_task(service.store.set_task_enabled(task_id, False))
    except Exception as exc:
        return _collector_error_response(exc, task_id=task_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(task.to_dict())))


@router.get("/v1/collector/runs")
@router.get("/v1/runs")
def list_collector_runs(
    task_id: str | None = None,
    status_filter: str | None = None,
    limit: int | None = DEFAULT_RUN_LIST_LIMIT,
) -> dict[str, Any]:
    service = _collector_service()
    normalized_limit = _run_list_limit(limit)
    runs = [run.to_dict() for run in service.store.list_runs(task_id=task_id, status=status_filter, limit=normalized_limit)]
    return response_payload(runs, count=len(runs))


@router.get("/v1/tasks/{task_id}/runs")
@router.get("/v1/collector/tasks/{task_id}/runs")
def list_collector_task_runs(
    task_id: str,
    status_filter: str | None = None,
    limit: int | None = DEFAULT_RUN_LIST_LIMIT,
) -> JSONResponse:
    service = _collector_service()
    if service.store.get_task(task_id) is None:
        return _not_found("COLLECTOR_TASK_NOT_FOUND", f"Collector task {task_id!r} was not found.", task_id=task_id)
    normalized_limit = _run_list_limit(limit)
    runs = [run.to_dict() for run in service.store.list_runs(task_id=task_id, status=status_filter, limit=normalized_limit)]
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(runs, count=len(runs))))


@router.get("/v1/collector/runs/{run_id}")
@router.get("/v1/runs/{run_id}")
def get_collector_run(run_id: str) -> JSONResponse:
    service = _collector_service()
    run = service.store.get_run(run_id)
    if run is None:
        return _not_found("COLLECTOR_RUN_NOT_FOUND", f"Collector run {run_id!r} was not found.", run_id=run_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(run.to_dict())))


@router.delete("/v1/collector/runs/{run_id}")
@router.delete("/v1/runs/{run_id}")
def delete_collector_run(run_id: str) -> JSONResponse:
    service = _collector_service()
    run = service.store.get_run(run_id)
    if run is None:
        return _not_found("COLLECTOR_RUN_NOT_FOUND", f"Collector run {run_id!r} was not found.", run_id=run_id)
    if run.status in {"pending", "queued", "running"}:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=to_jsonable(
                error_payload(
                    "COLLECTOR_RUN_ACTIVE",
                    "Active collector runs cannot be deleted. Cancel or wait for the run to finish first.",
                    run_id=run_id,
                    status=run.status,
                )
            ),
        )
    removed = service.store.delete_runs([run_id])
    if not removed:
        return _not_found("COLLECTOR_RUN_NOT_FOUND", f"Collector run {run_id!r} was not found.", run_id=run_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(removed[0].to_dict())))


@router.get("/v1/collector/status")
def get_collector_status() -> dict[str, Any]:
    service = _collector_service()
    tasks = service.list_tasks()
    run_summary = service.store.run_summary(recent_limit=DEFAULT_RUN_LIST_LIMIT)
    recent_runs = run_summary["recent_runs"]
    active_runs = run_summary["active_runs"]
    latest_by_task = {
        task.task_id: latest.to_dict()
        for task in tasks
        if (latest := run_summary["latest_by_task"].get(task.task_id)) is not None
    }
    return response_payload(
        {
            "task_count": len(tasks),
            "enabled_task_count": sum(1 for task in tasks if task.enabled),
            "run_count": len(recent_runs),
            "total_run_count": run_summary["total_run_count"],
            "recent_run_count": len(recent_runs),
            "recent_run_limit": DEFAULT_RUN_LIST_LIMIT,
            "status_counts": run_summary["status_counts"],
            "active_run_count": len(active_runs),
            "active_runs": [run.to_dict() for run in active_runs],
            "latest_runs": latest_by_task,
        }
    )


def start_collector_scheduler_loop() -> None:
    _collector_service().start_loop()


def _collector_service() -> Any:
    root = str(data_root())
    service = _collector_service_cache.get(root)
    if service is not None:
        return service
    from axdata_core import CollectorSchedulerService

    service = CollectorSchedulerService(data_root=data_root())
    _collector_service_cache[root] = service
    return service


def _run_list_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_RUN_LIST_LIMIT
    return min(max(int(limit), 0), MAX_RUN_LIST_LIMIT)


def _collector_error_response(exc: Exception, **details: Any) -> JSONResponse:
    message = str(exc)
    if "does not exist" in message or "was not found" in message:
        http_status = status.HTTP_404_NOT_FOUND
        code = "COLLECTOR_TASK_NOT_FOUND"
    elif "Unknown task template" in message:
        http_status = status.HTTP_404_NOT_FOUND
        code = "COLLECTOR_TASK_TEMPLATE_NOT_FOUND"
    elif "already exists" in message:
        http_status = status.HTTP_409_CONFLICT
        code = "COLLECTOR_TASK_CONFLICT"
    elif type(exc).__name__ in {"CollectorError", "DownloaderError"}:
        http_status = status.HTTP_404_NOT_FOUND
        code = "COLLECTOR_NOT_CONFIGURED"
    else:
        http_status = status.HTTP_400_BAD_REQUEST
        code = "COLLECTOR_TASK_INVALID"
    payload = error_payload(code, message, **details)
    return JSONResponse(status_code=http_status, content=to_jsonable(payload))


def _not_found(code: str, message: str, **details: Any) -> JSONResponse:
    payload = error_payload(code, message, **details)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))


def _collector_run_overrides(request: Any, *, include_dates: bool = True) -> dict[str, Any]:
    overrides = dict(getattr(request, "params", {}) or {})
    if include_dates:
        start = getattr(request, "start", None)
        end = getattr(request, "end", None)
        if start or end:
            if not start or not end:
                raise ValueError("start and end must be provided together.")
            from axdata_core import normalize_date_range

            start_date, end_date = normalize_date_range(start, end)
            overrides.setdefault("start_date", start_date)
            overrides.setdefault("end_date", end_date)
    symbol = getattr(request, "symbol", None)
    if symbol:
        overrides.setdefault("code", symbol)
    limit = getattr(request, "limit", None)
    if limit is not None:
        if int(limit) < 0:
            raise ValueError("limit must be non-negative.")
        overrides.setdefault("limit", int(limit))
        overrides.setdefault("count", int(limit))
    return overrides
