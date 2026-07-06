"""Source-side request gateway for AxData interfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .source_adapter_factory import adapter_for_source_code
from .source_errors import (
    SourceAdapterError,
    SourceAdapterNotFound,
    SourceInterfaceNotFound,
    SourceRequestError,
    SourceRequestValidationError,
    SourceUnavailableError,
)
from .source_execution_options import execution_options_for_source
from .source_projection import select_fields
from .sources import RequestExample, RequestField, RequestParameter, SourceRequestInterface, get_request_interface
from .tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE


@dataclass(frozen=True)
class SourceRequestResult:
    """Normalized AxData source request result."""

    records: list[dict[str, Any]]
    meta: dict[str, Any] = field(default_factory=dict)


class SourceRequestAdapter(Protocol):
    """Protocol implemented by source adapters."""

    source: str

    def supports(self, interface_name: str) -> bool:
        """Return whether the adapter supports one interface."""

    def request(self, interface_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return AxData-normalized records for one request."""


def request_interface(
    interface: str,
    *,
    params: Mapping[str, Any] | None = None,
    fields: str | Sequence[str] | None = None,
    persist: bool = False,
    adapter: SourceRequestAdapter | None = None,
    options: Mapping[str, Any] | None = None,
    data_root: str | Path | None = None,
) -> SourceRequestResult:
    """Request a source interface and return normalized AxData records.

    This is the single gateway used by the local SDK and HTTP API. It is
    intentionally separate from ordinary table queries: source requests may hit
    an upstream source, but they do not write raw/staging/core/factor data.
    """

    interface_name = str(interface or "").strip()
    if not interface_name:
        raise SourceRequestValidationError("interface is required")

    contract = _contract_for_interface(interface_name, data_root=data_root)

    requested_fields = normalize_fields(fields) or list(contract.field_names)
    validate_fields(contract.field_names, requested_fields)
    request_params = normalize_params(params)
    request_options = normalize_options(options)
    execution_options = execution_options_for_source(
        request_options,
        data_root=data_root,
        provider_id=getattr(contract, "_axdata_provider_id", None),
        source_code=contract.source_code,
    )
    validate_params(contract, request_params)
    validate_required_params(contract, request_params)

    if persist:
        raise SourceRequestValidationError(
            "persist=true is reserved for explicit collection jobs; source requests are read-only."
        )

    resolved_adapter = adapter or registry_adapter_for_interface(
        interface_name,
        options=execution_options,
        data_root=data_root,
    )
    if not resolved_adapter.supports(interface_name):
        raise SourceAdapterNotFound(
            f"Source adapter {resolved_adapter.source!r} does not support interface {interface_name!r} yet."
        )

    try:
        records = resolved_adapter.request(interface_name, request_params)
    except SourceRequestError:
        raise
    except (TimeoutError, OSError) as exc:
        raise SourceUnavailableError(f"Source request {interface_name!r} is unavailable: {exc}") from exc
    except ValueError as exc:
        raise SourceRequestValidationError(str(exc)) from exc
    except Exception as exc:
        raise SourceAdapterError(f"Source adapter failed for {interface_name!r}: {exc}") from exc

    filtered_records = select_fields(records, requested_fields)
    adapter_meta = getattr(resolved_adapter, "last_meta", None)
    meta = {
        "interface_name": interface_name,
        "source": resolved_adapter.source,
        "requested_fields": requested_fields,
        "persisted": False,
    }
    if request_options:
        meta["options"] = request_options
    if isinstance(adapter_meta, Mapping):
        _merge_adapter_meta(meta, adapter_meta)
    return SourceRequestResult(
        records=filtered_records,
        meta=meta,
    )


def adapter_for_interface(
    interface_name: str,
    *,
    options: Mapping[str, Any] | None = None,
) -> SourceRequestAdapter:
    """Resolve the source adapter for an interface name."""

    try:
        contract = get_request_interface(interface_name)
    except KeyError as exc:
        if _is_tdx_interface_name(interface_name):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise SourceAdapterNotFound(f"No source adapter is registered for interface {interface_name!r}.") from exc
    try:
        return adapter_for_source_code(contract.source_code, options=options)
    except KeyError as exc:
        if _is_tdx_interface_name(interface_name) or contract.source_code in {"tdx", "tdx_ext"}:
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise SourceAdapterNotFound(f"No source adapter is registered for interface {interface_name!r}.") from exc


@dataclass
class RegistrySourceRequestAdapter:
    """SourceRequestAdapter wrapper around a Provider protocol adapter."""

    source: str
    interface_name: str
    provider_adapter: Any
    last_meta: dict[str, Any] = field(default_factory=dict)

    def supports(self, interface_name: str) -> bool:
        return interface_name == self.interface_name

    def request(self, interface_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        result = self.provider_adapter.call(interface_name, params=params)
        from .plugins import SourceResult

        if isinstance(result, SourceResult):
            self.last_meta = dict(result.meta)
            return [dict(row) for row in result.data]
        if isinstance(result, Mapping):
            meta = result.get("meta")
            if isinstance(meta, Mapping):
                self.last_meta = dict(meta)
            data = result.get("data", [])
            if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
                return [dict(row) for row in data]
            return [dict(result)]
        self.last_meta = {}
        return [dict(row) for row in result]


def registry_adapter_for_interface(
    interface_name: str,
    *,
    options: Mapping[str, Any] | None = None,
    data_root: str | Path | None = None,
) -> SourceRequestAdapter:
    """Resolve an adapter through ProviderRegistry, falling back to legacy routing."""

    try:
        from .provider_catalog import build_builtin_provider_registry
    except ImportError:
        return adapter_for_interface(interface_name, options=options)

    registry = build_builtin_provider_registry(data_root=data_root)
    try:
        route = registry.get_interface(interface_name)
        provider = registry.snapshot().providers[route.provider_id]
    except KeyError:
        unavailable_provider = _provider_for_unavailable_interface(registry, interface_name)
        if unavailable_provider is not None:
            if _is_tdx_provider(unavailable_provider):
                raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE)
            status = unavailable_provider.status
            detail = f" {unavailable_provider.error}" if unavailable_provider.error else ""
            raise SourceAdapterNotFound(
                f"Provider {unavailable_provider.provider_id!r} is {status} "
                f"for interface {interface_name!r}.{detail}"
            )
        return adapter_for_interface(interface_name, options=options)

    try:
        provider_object = _load_registered_provider(provider)
    except SourceRequestError:
        raise
    except Exception as exc:
        provider_id = getattr(provider, "provider_id", route.provider_id)
        raise SourceAdapterError(
            f"Failed to load provider {provider_id!r} for interface {interface_name!r}: {exc}"
        ) from exc
    if provider_object is None:
        provider_id = getattr(provider, "provider_id", route.provider_id)
        raise SourceAdapterError(
            f"Provider {provider_id!r} could not be loaded for interface {interface_name!r}."
        )

    try:
        provider_adapter = provider_object.create_adapter(options=options)
    except SourceRequestError:
        raise
    except Exception as exc:
        provider_id = getattr(provider, "provider_id", route.provider_id)
        raise SourceAdapterError(
            f"Provider {provider_id!r} failed to create adapter for interface {interface_name!r}: {exc}"
        ) from exc
    return RegistrySourceRequestAdapter(
        source=provider.source_code,
        interface_name=interface_name,
        provider_adapter=provider_adapter,
    )


def _contract_for_interface(
    interface_name: str,
    *,
    data_root: str | Path | None = None,
) -> SourceRequestInterface:
    registry_error: Exception | None = None
    try:
        from .provider_catalog import build_builtin_provider_registry

        registry = build_builtin_provider_registry(data_root=data_root)
        try:
            route = registry.get_interface(interface_name)
            route_interface = getattr(route, "interface", None)
            if route_interface is not None:
                return _contract_from_registry_interface(
                    route_interface,
                    provider_id=getattr(route, "provider_id", None),
                )
        except KeyError as exc:
            registry_error = exc
            unavailable_provider = _provider_for_unavailable_interface(registry, interface_name)
            if unavailable_provider is not None:
                for interface in unavailable_provider.manifest.interfaces:
                    if interface.name == interface_name:
                        return _contract_from_registry_interface(interface)
    except Exception as exc:
        registry_error = exc

    try:
        return get_request_interface(interface_name)
    except KeyError as exc:
        if _is_tdx_interface_name(interface_name):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        if registry_error is not None:
            raise SourceInterfaceNotFound(str(registry_error)) from registry_error
        raise SourceInterfaceNotFound(str(exc)) from exc


def _contract_from_registry_interface(
    interface: Any,
    *,
    provider_id: str | None = None,
) -> SourceRequestInterface:
    contract = SourceRequestInterface(
        name=interface.name,
        display_name_zh=interface.display_name_zh,
        source_code=interface.source_code,
        source_name_zh=interface.source_name_zh,
        category=interface.category,
        request_mode=interface.request_mode,
        first_stage_strategy="provider_registry",
        parameters=tuple(
            RequestParameter(
                name=parameter.name,
                dtype=parameter.type,
                required=parameter.required,
                description=parameter.description,
                description_zh=parameter.display_name_zh,
                default=parameter.default,
            )
            for parameter in interface.parameters
        ),
        fields=tuple(
            RequestField(
                name=field.name,
                dtype=field.type,
                description=field.description,
                description_zh=field.display_name_zh,
            )
            for field in interface.fields
        ),
        example=RequestExample(request={}, response=()),
        source_ability="provider_registry",
        description=interface.notes,
    )
    if provider_id:
        object.__setattr__(contract, "_axdata_provider_id", provider_id)
    return contract


def _load_registered_provider(provider: Any) -> Any | None:
    load_provider = getattr(provider, "load_provider", None)
    if callable(load_provider):
        return load_provider()
    return getattr(provider, "provider", None)


def _provider_for_unavailable_interface(registry: Any, interface_name: str) -> Any | None:
    unavailable_statuses = {
        "conflict",
        "disabled",
        "failed",
        "incompatible",
    }
    for candidate in registry.snapshot().providers.values():
        if candidate.status not in unavailable_statuses:
            continue
        if interface_name in {interface.name for interface in candidate.manifest.interfaces}:
            return candidate
    return None


def _is_tdx_provider(provider: Any) -> bool:
    provider_id = str(getattr(provider, "provider_id", "") or "")
    source_code = str(getattr(provider, "source_code", "") or "")
    manifest = getattr(provider, "manifest", None)
    manifest_provider = getattr(manifest, "provider", None)
    if manifest_provider is not None:
        provider_id = provider_id or str(getattr(manifest_provider, "provider_id", "") or "")
        source_code = source_code or str(getattr(manifest_provider, "source_code", "") or "")
    return provider_id.startswith("axdata.source.tdx") or source_code in {"tdx", "tdx_ext"}


def _is_tdx_interface_name(interface_name: str) -> bool:
    normalized = str(interface_name or "").strip()
    return normalized.endswith("_tdx")


def _merge_adapter_meta(meta: dict[str, Any], adapter_meta: Mapping[str, Any]) -> None:
    reserved_keys = {
        "interface_name",
        "source",
        "requested_fields",
        "persisted",
        "options",
    }
    for key, value in adapter_meta.items():
        if key in reserved_keys:
            continue
        meta[key] = value


def normalize_fields(fields: str | Sequence[str] | None) -> list[str] | None:
    """Normalize comma-separated or sequence field input."""

    if fields in (None, ""):
        return None
    if isinstance(fields, str):
        normalized = [field.strip() for field in fields.split(",") if field.strip()]
    else:
        normalized = [str(field).strip() for field in fields if str(field).strip()]
    return normalized or None


def normalize_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize params to a plain dict and drop explicit nulls."""

    return {str(key): value for key, value in dict(params or {}).items() if value is not None}


def normalize_options(options: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize execution options to a plain dict and drop explicit nulls."""

    return {str(key): value for key, value in dict(options or {}).items() if value is not None}


def validate_fields(known_fields: Sequence[str], requested_fields: Sequence[str] | None) -> None:
    """Validate selected fields against the interface contract."""

    if not requested_fields:
        return
    known = set(known_fields)
    unknown = [field for field in requested_fields if field not in known]
    if unknown:
        raise SourceRequestValidationError(
            f"Unknown field(s): {', '.join(unknown)}. Known fields: {', '.join(known_fields)}."
        )


def validate_required_params(contract: Any, params: Mapping[str, Any]) -> None:
    """Validate catalog-declared required params."""

    missing = [
        parameter.name
        for parameter in contract.parameters
        if parameter.required and _missing_required_param(parameter.name, params)
    ]
    if missing:
        raise SourceRequestValidationError(
            f"Missing required param(s) for {contract.name}: {', '.join(missing)}."
        )


def validate_params(contract: Any, params: Mapping[str, Any]) -> None:
    """Validate request params against the interface contract."""

    known = set(contract.parameter_names)
    unknown = [name for name in params if name not in known]
    if unknown:
        raise SourceRequestValidationError(
            f"Unknown param(s) for {contract.name}: {', '.join(unknown)}. "
            f"Known params: {', '.join(contract.parameter_names)}."
        )


def _missing_required_param(name: str, params: Mapping[str, Any]) -> bool:
    value = params.get(name)
    if value in (None, ""):
        if name == "instrument_ids" and params.get("instrument_id") not in (None, ""):
            return False
        return True
    if isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 0:
        return True
    return False
