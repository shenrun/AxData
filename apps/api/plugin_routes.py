from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from .config import data_root
from .models import PluginCollectorRunRequest, ProviderOverrideRequest
from .serialization import error_payload, parse_fields, response_payload, to_jsonable


router = APIRouter()


def load_provider_status_catalog() -> tuple[list[dict[str, Any]], str]:
    """Load Provider registry status for API/Web display."""

    try:
        from axdata_core import build_builtin_provider_registry
        from axdata_core import expected_provider_statuses, managed_provider_ids, provider_status_row
    except ImportError:
        return [], "unavailable"

    registry = build_builtin_provider_registry(data_root=data_root())
    config = _load_plugin_config()
    provider_overrides = getattr(config, "provider_overrides", {})
    removed_provider_ids = getattr(config, "removed_provider_ids", ())
    managed_ids = managed_provider_ids(data_root=data_root())
    snapshot = registry.snapshot()
    providers = [
        provider_status_row(
            provider,
            provider_overrides=provider_overrides,
            snapshot=snapshot,
            managed_provider_ids=managed_ids,
            removed_provider_ids=removed_provider_ids,
        )
        for provider in registry.list_providers()
    ]
    providers.extend(expected_provider_statuses(provider["provider_id"] for provider in providers))
    return sorted(providers, key=lambda item: item["provider_id"]), "axdata_core.provider_registry"


def load_collector_catalog() -> tuple[list[dict[str, Any]], str]:
    """Load enabled collector capabilities for API/Web display."""

    try:
        from axdata_core import list_registry_collector_dicts
    except ImportError:
        return [], "unavailable"

    collectors = list(list_registry_collector_dicts(data_root=data_root()))
    return sorted(collectors, key=lambda item: item["name"]), "axdata_core.collector_registry"


@router.get("/v1/plugins/providers")
def list_plugin_providers() -> dict[str, Any]:
    providers, catalog_source = load_provider_status_catalog()
    return response_payload(
        providers,
        count=len(providers),
        catalog_source=catalog_source,
    )


@router.get("/v1/plugins/collectors")
def list_plugin_collectors() -> dict[str, Any]:
    collectors, catalog_source = load_collector_catalog()
    return response_payload(
        collectors,
        count=len(collectors),
        catalog_source=catalog_source,
    )


@router.get("/v1/plugins/installed")
def list_installed_plugins() -> dict[str, Any]:
    try:
        from axdata_core import list_installed_axp_plugins
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXP plugin management is unavailable.",
        ) from exc

    plugins = [plugin.to_dict() for plugin in list_installed_axp_plugins(data_root=data_root())]
    return response_payload(
        plugins,
        count=len(plugins),
        catalog_source="axdata_core.axp",
    )


@router.get("/v1/plugins/collectors/{collector_name:path}")
def get_plugin_collector(collector_name: str) -> dict[str, Any]:
    collectors, catalog_source = load_collector_catalog()
    for collector in collectors:
        if collector["name"] == collector_name:
            return response_payload(collector, catalog_source=catalog_source)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown collector {collector_name!r}.",
    )


@router.post("/v1/plugins/collectors/{collector_name:path}/run")
def run_plugin_collector(
    collector_name: str,
    request: PluginCollectorRunRequest,
) -> JSONResponse:
    requested_fields = parse_fields(request.fields)
    try:
        from axdata_core import (
            CollectorError,
            DownloaderError,
            SourceAdapterError,
            SourceAdapterNotFound,
            SourceInterfaceNotFound,
            SourceRequestValidationError,
            SourceUnavailableError,
            build_collector_run_plan,
            run_collector,
        )
    except ImportError:
        payload = error_payload(
            "COLLECTOR_RUNNER_UNAVAILABLE",
            "axdata_core collector runner is not available.",
            collector_name=collector_name,
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))

    kwargs = _collector_run_kwargs(request, requested_fields)
    try:
        plan = build_collector_run_plan(
            collector_name,
            params=request.params,
            fields=requested_fields,
            data_root=data_root(),
            formats=request.formats,
        )
    except CollectorError as exc:
        payload = error_payload("COLLECTOR_NOT_CONFIGURED", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except DownloaderError as exc:
        payload = error_payload("DOWNLOADER_NOT_CONFIGURED", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    kwargs["params"] = plan.params
    kwargs["fields"] = plan.fields
    kwargs["formats"] = plan.formats

    if request.async_job:
        try:
            from . import downloader_routes as collector_queue

            resource_request = collector_queue._resolve_resource_request(plan.target_interface, kwargs)
            output_lock_key = collector_queue._output_lock_key(plan.target_interface, kwargs=kwargs)
            job = collector_queue._create_job(
                plan.target_interface,
                kwargs=kwargs,
                resource_request=resource_request,
                output_lock_key=output_lock_key,
                job_kind="collector",
                collector_name=collector_name,
                trigger_type="manual",
                skip_active_duplicates=True,
            )
            if job["status"] != "skipped":
                collector_queue._executor.submit(
                    collector_queue._run_collector_job,
                    job["job_id"],
                    collector_name,
                    plan.target_interface,
                    kwargs,
                )
        except DownloaderError as exc:
            payload = error_payload("DOWNLOADER_NOT_CONFIGURED", str(exc), collector_name=collector_name)
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=to_jsonable(response_payload(job)))

    try:
        result = run_collector(collector_name, **kwargs)
    except CollectorError as exc:
        payload = error_payload("COLLECTOR_NOT_CONFIGURED", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except DownloaderError as exc:
        payload = error_payload("DOWNLOADER_NOT_CONFIGURED", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except SourceInterfaceNotFound as exc:
        payload = error_payload("SOURCE_INTERFACE_NOT_FOUND", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except SourceRequestValidationError as exc:
        payload = error_payload("SOURCE_REQUEST_VALIDATION_ERROR", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=to_jsonable(payload))
    except SourceAdapterNotFound as exc:
        payload = error_payload("SOURCE_ADAPTER_NOT_FOUND", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content=to_jsonable(payload))
    except SourceUnavailableError as exc:
        payload = error_payload("SOURCE_UNAVAILABLE", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))
    except SourceAdapterError as exc:
        payload = error_payload("SOURCE_ADAPTER_ERROR", str(exc), collector_name=collector_name)
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=to_jsonable(payload))

    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(response_payload(result)))


@router.get("/v1/plugins/providers/{provider_id:path}")
def get_plugin_provider(provider_id: str) -> dict[str, Any]:
    providers, catalog_source = load_provider_status_catalog()
    for provider in providers:
        if provider["provider_id"] == provider_id:
            return response_payload(provider, catalog_source=catalog_source)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown Provider {provider_id!r}.",
    )


@router.post("/v1/plugins/providers/{provider_id:path}/enable")
def enable_plugin_provider(provider_id: str) -> dict[str, Any]:
    try:
        from axdata_core import enable_provider
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider configuration is unavailable.",
        ) from exc

    enable_provider(provider_id, data_root=data_root())
    provider = _provider_status_or_404(provider_id)
    return response_payload(provider, catalog_source="axdata_core.provider_registry")


@router.post("/v1/plugins/providers/{provider_id:path}/disable")
def disable_plugin_provider(provider_id: str) -> dict[str, Any]:
    try:
        from axdata_core import disable_provider
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider configuration is unavailable.",
        ) from exc

    disable_provider(provider_id, data_root=data_root())
    provider = _provider_status_or_404(provider_id)
    return response_payload(provider, catalog_source="axdata_core.provider_registry")


@router.post("/v1/plugins/overrides/{interface_name}")
def set_plugin_provider_override(
    interface_name: str,
    request: ProviderOverrideRequest,
) -> dict[str, Any]:
    try:
        from axdata_core import set_provider_override
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider configuration is unavailable.",
        ) from exc

    provider_id = request.provider_id.strip()
    _validate_override_target(interface_name, provider_id)
    set_provider_override(interface_name, provider_id, data_root=data_root())
    providers, catalog_source = load_provider_status_catalog()
    return response_payload(
        {
            "interface_name": interface_name,
            "provider_id": provider_id,
            "providers": providers,
        },
        catalog_source=catalog_source,
    )


@router.delete("/v1/plugins/overrides/{interface_name}")
def clear_plugin_provider_override(interface_name: str) -> dict[str, Any]:
    try:
        from axdata_core import set_provider_override
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider configuration is unavailable.",
        ) from exc

    set_provider_override(interface_name, None, data_root=data_root())
    providers, catalog_source = load_provider_status_catalog()
    return response_payload(
        {
            "interface_name": interface_name,
            "provider_id": None,
            "providers": providers,
        },
        catalog_source=catalog_source,
    )


@router.delete("/v1/plugins/installed/{provider_id:path}")
def uninstall_installed_plugin(provider_id: str, disable_first: bool = False) -> dict[str, Any]:
    try:
        from axdata_core import AxpUninstallError, uninstall_axp_plugin
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXP plugin management is unavailable.",
        ) from exc

    try:
        result = uninstall_axp_plugin(provider_id, data_root=data_root(), disable_first=disable_first)
    except AxpUninstallError as exc:
        message = str(exc)
        if "not installed" in message:
            http_status = status.HTTP_404_NOT_FOUND
        elif "enabled" in message or "Built-in" in message or "Core" in message or "不能卸载" in message:
            http_status = status.HTTP_409_CONFLICT
        else:
            http_status = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=http_status, detail=message) from exc
    return response_payload(result.to_dict(), catalog_source="axdata_core.axp")


@router.post("/v1/plugins/installed/{provider_id:path}/uninstall")
def uninstall_installed_plugin_post(provider_id: str, disable_first: bool = False) -> dict[str, Any]:
    return uninstall_installed_plugin(provider_id, disable_first=disable_first)


@router.get("/v1/plugins/axp/export/{provider_id:path}")
def export_axp_plugin_archive(provider_id: str) -> FileResponse:
    export_dir = Path(tempfile.mkdtemp(prefix="axdata-axp-export-api-"))
    try:
        from axdata_core import AxpError, export_axp_plugin
    except ImportError as exc:
        shutil.rmtree(export_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXP plugin export is unavailable.",
        ) from exc

    try:
        result = export_axp_plugin(provider_id, data_root=data_root(), output_dir=export_dir)
    except AxpError as exc:
        shutil.rmtree(export_dir, ignore_errors=True)
        message = str(exc)
        http_status = (
            status.HTTP_404_NOT_FOUND
            if "not installed or discoverable" in message
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=http_status, detail=message) from exc
    except Exception:
        shutil.rmtree(export_dir, ignore_errors=True)
        raise

    return FileResponse(
        result.path,
        media_type="application/octet-stream",
        filename=result.file_name,
        background=BackgroundTask(shutil.rmtree, export_dir, ignore_errors=True),
    )


@router.post("/v1/plugins/axp/preview")
async def preview_axp_plugin(request: Request) -> dict[str, Any]:
    file, _enable, _replace_install, _allow_online_deps = await _uploaded_axp_file(request)
    archive_path = await _save_upload_to_temp(file)
    try:
        from axdata_core import AxpError, preview_axp

        preview = preview_axp(archive_path, data_root=data_root())
        return response_payload(preview.to_dict(), catalog_source="axdata_core.axp")
    except AxpError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        archive_path.unlink(missing_ok=True)


@router.post("/v1/plugins/axp/install")
async def install_axp_plugin(request: Request) -> dict[str, Any]:
    file, enable, replace_install, allow_online_deps = await _uploaded_axp_file(request)
    archive_path = await _save_upload_to_temp(file)
    try:
        from axdata_core import AxpAlreadyInstalledError, AxpError, install_axp

        result = install_axp(
            archive_path,
            data_root=data_root(),
            enable=enable,
            replace=replace_install,
            allow_online_deps=allow_online_deps,
        )
        provider = _provider_status_or_none(result.preview.provider_id)
        return response_payload(
            {
                **result.to_dict(),
                "provider": provider,
            },
            catalog_source="axdata_core.axp",
        )
    except AxpAlreadyInstalledError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AxpError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        archive_path.unlink(missing_ok=True)


def _provider_status_or_404(provider_id: str) -> dict[str, Any]:
    provider = _provider_status_or_none(provider_id)
    if provider is not None:
        return provider
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown Provider {provider_id!r}.",
    )


def _collector_run_kwargs(
    request: PluginCollectorRunRequest,
    requested_fields: list[str] | None,
) -> dict[str, Any]:
    return {
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


def _provider_status_or_none(provider_id: str) -> dict[str, Any] | None:
    providers, _catalog_source = load_provider_status_catalog()
    for provider in providers:
        if provider["provider_id"] == provider_id:
            return provider
    return None


async def _save_upload_to_temp(file: UploadFile) -> Path:
    suffix = Path(file.filename or "plugin.axp").suffix or ".axp"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    path = Path(handle.name)
    try:
        with handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


async def _uploaded_axp_file(request: Request) -> tuple[UploadFile, bool, bool, bool]:
    try:
        form = await request.form()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXP upload requires python-multipart to parse multipart/form-data.",
        ) from exc
    file = form.get("file")
    if not hasattr(file, "read") or not hasattr(file, "filename"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload field 'file' is required.",
        )
    enable = _truthy_form_value(form.get("enable"))
    replace_install = _truthy_form_value(form.get("replace"))
    allow_online_deps = _truthy_form_value(form.get("allow_online_deps"))
    return file, enable, replace_install, allow_online_deps


def _truthy_form_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_plugin_config() -> Any:
    try:
        from axdata_core import load_plugin_config
    except ImportError:
        return None
    return load_plugin_config(data_root=data_root())


def _validate_override_target(interface_name: str, provider_id: str) -> None:
    if not interface_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="interface_name is required.")
    if not provider_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="provider_id is required.")

    try:
        from axdata_core import build_builtin_provider_registry
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider registry is unavailable.",
        ) from exc

    registry = build_builtin_provider_registry(data_root=data_root())
    provider = registry.snapshot().providers.get(provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown Provider {provider_id!r}.",
        )
    if not provider.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider {provider_id!r} is not enabled.",
        )
    if interface_name not in {interface.name for interface in provider.manifest.interfaces}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider {provider_id!r} does not expose interface {interface_name!r}.",
        )
