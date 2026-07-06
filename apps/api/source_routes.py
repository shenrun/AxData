from __future__ import annotations

import sys
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from .models import SourceRequest
from .serialization import error_payload, parse_fields, response_payload, to_jsonable


router = APIRouter()


def normalize_interface_entry(name: str, entry: Any) -> dict[str, Any]:
    normalized = to_jsonable(entry)
    if isinstance(normalized, str):
        normalized = {"name": normalized}
    elif not isinstance(normalized, dict):
        normalized = {"name": name, "value": normalized}

    normalized.setdefault("name", normalized.get("interface_name", name))
    normalized.setdefault("interface_name", normalized["name"])
    normalized.setdefault("request_mode", "source_request")
    normalized.setdefault("persisted", False)
    return normalized


def load_source_interface_catalog() -> tuple[dict[str, dict[str, Any]], str]:
    """Load source-request interfaces from core.

    Core owns source request contracts. The API only serializes and exposes the
    catalog over HTTP.
    """

    catalog: dict[str, dict[str, Any]] = {}
    catalog_source = "unavailable"

    try:
        from axdata_core import list_registry_interface_dicts
    except ImportError:
        list_registry_interface_dicts = None

    if list_registry_interface_dicts is not None:
        from .config import data_root

        for entry in list_registry_interface_dicts(data_root=data_root()):
            normalized = normalize_interface_entry("", entry)
            catalog[str(normalized["name"])] = normalized
        catalog_source = "axdata_core.provider_registry"

    return dict(sorted(catalog.items())), catalog_source


def get_source_interface(interface_name: str) -> tuple[dict[str, Any], str]:
    catalog, catalog_source = load_source_interface_catalog()
    try:
        return catalog[interface_name], catalog_source
    except KeyError as exc:
        unavailable = unavailable_source_interface(interface_name)
        if unavailable is not None:
            return unavailable, catalog_source
        known = ", ".join(catalog) or "<empty>"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown source request interface {interface_name!r}. Known interfaces: {known}.",
        ) from exc


def unavailable_source_interface(interface_name: str) -> dict[str, Any] | None:
    try:
        from axdata_core.provider_catalog import build_builtin_provider_registry
    except ImportError:
        return None

    try:
        from .config import data_root

        registry = build_builtin_provider_registry(data_root=data_root())
        for provider in registry.snapshot().providers.values():
            if provider.status not in {"disabled", "failed", "incompatible", "conflict"}:
                continue
            for interface in provider.manifest.interfaces:
                if interface.name != interface_name:
                    continue
                normalized = normalize_interface_entry(interface_name, interface.to_dict())
                normalized.update(
                    {
                        "provider_id": provider.provider_id,
                        "plugin_status": provider.status,
                        "enabled": provider.enabled,
                        "source_code": interface.source_code,
                        "source_name_zh": interface.source_name_zh,
                    }
                )
                return normalized
    except Exception:
        return None
    return None


def core_request_interface(interface_name: str, **kwargs: Any) -> Any:
    """Call the core source request gateway.

    This stays as a named wrapper so tests and local debugging can replace the
    gateway without touching the real source adapter.
    """

    main_module = sys.modules.get("apps.api.main")
    override = getattr(main_module, "core_request_interface", None) if main_module else None
    if override is not None and override is not core_request_interface:
        return override(interface_name, **kwargs)

    from axdata_core import request_interface

    return request_interface(interface_name, **kwargs)


@router.get("/v1/request/interfaces")
def list_request_interfaces() -> dict[str, Any]:
    catalog, catalog_source = load_source_interface_catalog()
    return response_payload(
        list(catalog.values()),
        count=len(catalog),
        catalog_source=catalog_source,
        request_mode="source_request",
        persisted=False,
    )


@router.post("/v1/request/{interface_name}")
def request_source_interface(interface_name: str, request: SourceRequest) -> JSONResponse:
    interface, catalog_source = get_source_interface(interface_name)
    requested_fields = parse_fields(request.fields)

    try:
        from axdata_core import (
            SourceAdapterError,
            SourceAdapterNotFound,
            SourceInterfaceNotFound,
            SourceRequestValidationError,
            SourceUnavailableError,
        )
    except ImportError:
        payload = error_payload(
            "SOURCE_REQUEST_GATEWAY_UNAVAILABLE",
            "axdata_core source request gateway is not available.",
            interface_name=interface_name,
            request_mode="source_request",
            persisted=False,
            catalog_source=catalog_source,
            interface=interface,
            requested_fields=requested_fields,
            params=to_jsonable(request.params),
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))

    try:
        from .config import data_root

        request_kwargs = {
            "params": request.params,
            "fields": requested_fields,
            "persist": request.persist,
            "data_root": data_root(),
        }
        if request.options:
            request_kwargs["options"] = request.options
        result = core_request_interface(interface_name, **request_kwargs)
    except SourceInterfaceNotFound as exc:
        payload = error_payload(
            "SOURCE_INTERFACE_NOT_FOUND",
            str(exc),
            interface_name=interface_name,
            request_mode="source_request",
            persisted=False,
            catalog_source=catalog_source,
            interface=interface,
            requested_fields=requested_fields,
            params=to_jsonable(request.params),
            **source_request_error_guidance("SOURCE_INTERFACE_NOT_FOUND", interface_name),
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=to_jsonable(payload))
    except SourceRequestValidationError as exc:
        payload = error_payload(
            "SOURCE_REQUEST_VALIDATION_ERROR",
            str(exc),
            interface_name=interface_name,
            request_mode="source_request",
            persisted=False,
            catalog_source=catalog_source,
            interface=interface,
            requested_fields=requested_fields,
            params=to_jsonable(request.params),
            **source_request_error_guidance("SOURCE_REQUEST_VALIDATION_ERROR", interface_name),
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=to_jsonable(payload))
    except SourceAdapterNotFound as exc:
        payload = error_payload(
            "SOURCE_ADAPTER_NOT_FOUND",
            str(exc),
            interface_name=interface_name,
            request_mode="source_request",
            persisted=False,
            catalog_source=catalog_source,
            interface=interface,
            requested_fields=requested_fields,
            params=to_jsonable(request.params),
            **source_request_error_guidance("SOURCE_ADAPTER_NOT_FOUND", interface_name),
        )
        return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content=to_jsonable(payload))
    except SourceUnavailableError as exc:
        payload = error_payload(
            "SOURCE_UNAVAILABLE",
            str(exc),
            interface_name=interface_name,
            request_mode="source_request",
            persisted=False,
            catalog_source=catalog_source,
            interface=interface,
            requested_fields=requested_fields,
            params=to_jsonable(request.params),
            **source_request_error_guidance("SOURCE_UNAVAILABLE", interface_name),
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=to_jsonable(payload))
    except SourceAdapterError as exc:
        payload = error_payload(
            "SOURCE_ADAPTER_ERROR",
            str(exc),
            interface_name=interface_name,
            request_mode="source_request",
            persisted=False,
            catalog_source=catalog_source,
            interface=interface,
            requested_fields=requested_fields,
            params=to_jsonable(request.params),
            **source_request_error_guidance("SOURCE_ADAPTER_ERROR", interface_name),
        )
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=to_jsonable(payload))

    meta = dict(result.meta)
    effective_fields = meta.get("requested_fields", requested_fields)
    meta.update(
        {
            "interface_name": interface_name,
            "request_mode": "source_request",
            "persisted": False,
            "catalog_source": catalog_source,
            "interface": interface,
            "requested_fields": effective_fields,
            "params": to_jsonable(request.params),
            "options": to_jsonable(request.options or {}),
            "count": len(result.records),
        }
    )
    payload = response_payload(result.records, **meta)
    return JSONResponse(status_code=status.HTTP_200_OK, content=to_jsonable(payload))


def source_request_error_guidance(code: str, interface_name: str) -> dict[str, str | None]:
    if code == "SOURCE_UNAVAILABLE" and interface_name.endswith("_tdx"):
        return {
            "next_action": "安装并启用 TDX Provider 后重试该源端直取接口。",
            "action_command": "axdata plugin enable axdata.source.tdx_external",
        }
    if code == "SOURCE_REQUEST_VALIDATION_ERROR":
        return {
            "next_action": "检查接口参数名、必填参数和字段选择；可先查看 /v1/request/interfaces 的参数示例。",
            "action_command": None,
        }
    if code == "SOURCE_ADAPTER_NOT_FOUND":
        return {
            "next_action": "检查对应 Provider 是否已安装、启用，或是否存在接口冲突。",
            "action_command": "axdata plugin list --json",
        }
    return {"next_action": None, "action_command": None}
