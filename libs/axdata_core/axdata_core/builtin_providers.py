"""Built-in Provider wrappers for the current source request catalog.

The existing AxData source catalog remains the behavioral source of truth in
this phase. This module only projects it into the new Provider protocol so the
registry can represent today's built-in sources before routing is migrated.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Mapping, Sequence

from .plugins import (
    AssetClass,
    CollectorSpec,
    DownloaderMode,
    DownloaderProfile as PluginDownloaderProfile,
    FieldSpec,
    FieldType,
    InterfaceCollectionSpec,
    InterfaceSpec,
    ParameterSpec,
    ParameterType,
    RequestExample as PluginRequestExample,
    RequestMode,
    SourceResult,
)
from .sources import SourceRequestInterface
from .sources.display_docs import display_doc_for_interface


BUILTIN_SOURCE_CATALOG_MODULES: tuple[tuple[str, str], ...] = (
    ("exchange", "axdata_core.sources.exchange.catalog"),
    ("cninfo", "axdata_core.sources.cninfo.catalog"),
    ("tencent", "axdata_core.sources.tencent.catalog"),
    ("eastmoney", "axdata_core.sources.eastmoney.catalog"),
    ("cls", "axdata_core.sources.cls.catalog"),
    ("kph", "axdata_core.sources.kph.catalog"),
    ("sina", "axdata_core.sources.sina.catalog"),
)

BUILTIN_PROVIDER_PREFIX = "axdata.source"
BUILTIN_SOURCE_NAMES_ZH: Mapping[str, str] = {}
_PROJECTION_DOWNLOADER_PROFILES_CACHE: tuple[Any, ...] | None = None

_BUILTIN_INTERFACE_DOWNLOADER_CONFIG: Mapping[str, Mapping[str, Any]] = {
    "stock_trade_calendar_exchange": {
        "primary_key": ("cal_date",),
        "params": {"year": "2026"},
        "fields": ("cal_date", "is_open", "pretrade_date"),
        "output_layer": "core",
        "required_columns": ("cal_date", "is_open"),
        "date_field": "cal_date",
    },
    "stock_historical_list_exchange": {
        "primary_key": ("trade_date", "instrument_id"),
        "params": {"trade_date": "20260102"},
        "output_layer": "snapshot",
        "required_columns": ("trade_date", "instrument_id"),
        "date_field": "trade_date",
    },
    "stock_basic_info_exchange": {
        "primary_key": ("instrument_id",),
        "params": {},
        "output_layer": "core",
        "required_columns": ("instrument_id", "symbol", "exchange", "asset_type", "name"),
        "date_field": "list_date",
        "numeric_positive_columns": ("total_share", "float_share"),
    },
}


@dataclass(frozen=True)
class BuiltinSourceProvider:
    """Provider wrapper for one current built-in source catalog group."""

    source_code: str
    source_name_zh: str
    interfaces_: tuple[InterfaceSpec, ...]
    version: str = "0.1.0"
    plugin_api_version: str = "1.0"

    @property
    def provider_id(self) -> str:
        return f"{BUILTIN_PROVIDER_PREFIX}.{self.source_code}"

    def interfaces(self) -> Sequence[InterfaceSpec]:
        return self.interfaces_

    def create_adapter(self, options: Mapping[str, object] | None = None) -> "BuiltinSourceAdapter":
        return BuiltinSourceAdapter(
            source_code=self.source_code,
            provider_id=self.provider_id,
            options=options,
        )

    def downloader_profiles(self) -> Sequence[PluginDownloaderProfile]:
        if self.source_code != "tdx":
            return tuple(
                _generic_builtin_downloader_profile(interface)
                for interface in self.interfaces_
                if interface.name in _BUILTIN_INTERFACE_DOWNLOADER_CONFIG
            )
        interface_names = {interface.name for interface in self.interfaces_}
        return tuple(
            _convert_downloader_profile(profile)
            for profile in _current_downloader_profiles()
            if profile.interface_name in interface_names
        )

    def collectors(self) -> Sequence[CollectorSpec]:
        return ()


@dataclass(frozen=True)
class BuiltinSourceAdapter:
    """Adapter shim that delegates to the existing source request adapters."""

    source_code: str
    provider_id: str | None = None
    options: Mapping[str, object] | None = None

    def call(
        self,
        interface_name: str,
        params: Mapping[str, object] | None = None,
        fields: Sequence[str] | None = None,
        options: Mapping[str, object] | None = None,
    ) -> SourceResult:
        # Import lazily to keep provider catalog projection side-effect free.
        from .source_projection import select_fields

        request_options = {**dict(self.options or {}), **dict(options or {})}
        adapter = _adapter_for_builtin_source(
            provider_id=self.provider_id,
            source_code=self.source_code,
            options=request_options,
        )
        records = adapter.request(interface_name, dict(params or {}))
        if fields:
            records = select_fields(records, fields)
        meta = {
            "interface_name": interface_name,
            "source": adapter.source,
            "requested_fields": list(fields or []),
        }
        adapter_meta = getattr(adapter, "last_meta", None)
        if isinstance(adapter_meta, Mapping):
            meta.update(adapter_meta)
        return SourceResult(
            data=tuple(records),
            meta=meta,
        )


class _ProjectionObject:
    """Small shape-compatible object for Provider metadata projection."""

    def __init__(self, **values: Any) -> None:
        for name, value in values.items():
            setattr(self, name, value)


class _ProjectionConcurrencyProfile(_ProjectionObject):
    """Downloader concurrency shape without importing the runtime downloader."""

    def __init__(self, **values: Any) -> None:
        defaults = {
            "mode": "fixed",
            "mode_editable": False,
            "default_source_server_count": 1,
            "source_server_count_editable": False,
            "max_source_server_count": 1,
            "default_connections_per_server": 1,
            "connections_per_server_editable": False,
            "max_connections_per_server": 1,
            "default_max_concurrent_tasks": 1,
            "max_concurrent_tasks_editable": False,
            "max_max_concurrent_tasks": 1,
            "default_batch_size": 1,
            "batch_size_editable": False,
            "max_batch_size": 1,
            "default_request_interval_ms": 0,
            "request_interval_ms_editable": False,
            "min_request_interval_ms": 0,
            "max_request_interval_ms": 0,
            "default_retry_count": 0,
            "retry_count_editable": False,
            "max_retry_count": 0,
            "default_timeout_ms": 30000,
            "timeout_ms_editable": False,
            "min_timeout_ms": 30000,
            "max_timeout_ms": 30000,
            "description": "",
        }
        defaults.update(values)
        super().__init__(**defaults)

    @property
    def default_connection_count(self) -> int:
        return min(
            self.default_source_server_count * self.default_connections_per_server,
            self.default_max_concurrent_tasks,
        )

    @property
    def max_connection_count(self) -> int:
        return min(
            self.max_source_server_count * self.max_connections_per_server,
            self.max_max_concurrent_tasks,
        )


class _ProjectionDownloaderProfile(_ProjectionObject):
    """Downloader profile shape used only for built-in Provider manifests."""

    pass


def list_builtin_providers() -> tuple[BuiltinSourceProvider, ...]:
    """Return built-in providers projected from the current catalog."""

    return tuple(
        _builtin_provider_from_interfaces(source_code, _source_interfaces(source_code))
        for source_code, _module_name in BUILTIN_SOURCE_CATALOG_MODULES
    )


def get_builtin_provider(source_code: str) -> BuiltinSourceProvider:
    """Return one built-in provider by source code."""

    normalized = source_code.strip()
    known_source_codes = [known_source_code for known_source_code, _module_name in BUILTIN_SOURCE_CATALOG_MODULES]
    if normalized in known_source_codes:
        return _builtin_provider_from_interfaces(normalized, _source_interfaces(normalized))
    known = ", ".join(known_source_codes)
    raise KeyError(f"Unknown built-in provider {source_code!r}. Known providers: {known}.")


def _source_interfaces(source_code: str) -> tuple[SourceRequestInterface, ...]:
    module_name = dict(BUILTIN_SOURCE_CATALOG_MODULES)[source_code]
    module = import_module(module_name)
    interfaces = getattr(module, "INTERFACES")
    return tuple(interfaces.values())


def _builtin_provider_from_interfaces(
    source_code: str,
    interfaces: tuple[SourceRequestInterface, ...],
) -> BuiltinSourceProvider:
    if not interfaces:
        raise KeyError(f"Built-in provider {source_code!r} has no interfaces.")
    source_name_zh = _builtin_source_name_zh(source_code, interfaces[0].source_name_zh)
    return BuiltinSourceProvider(
        source_code=source_code,
        source_name_zh=source_name_zh,
        interfaces_=tuple(_convert_interface(interface) for interface in interfaces),
    )


def _adapter_for_builtin_source(
    source_code: str,
    *,
    provider_id: str | None = None,
    options: Mapping[str, object] | None = None,
) -> Any:
    """Create the adapter for one known built-in Provider/source."""

    from .source_adapter_factory import adapter_for_source_identity

    return adapter_for_source_identity(
        provider_id=provider_id,
        source_code=source_code,
        options=options,
    )


def _convert_interface(interface: SourceRequestInterface) -> InterfaceSpec:
    source_name_zh = _builtin_source_name_zh(interface.source_code, interface.source_name_zh)
    display_doc = display_doc_for_interface(interface.name)
    summary_zh = display_doc.summary_zh or interface.summary_zh or _default_summary_zh(interface, source_name_zh)
    description_zh = (
        display_doc.description_zh
        or interface.description_zh
        or _default_description_zh(interface, summary_zh)
    )
    downloader_profile_name = (
        _downloader_profile_name(interface.name)
        if interface.source_code == "tdx"
        else _generic_builtin_downloader_name(interface.name)
    )
    return InterfaceSpec(
        name=interface.name,
        display_name_zh=interface.display_name_zh,
        source_code=interface.source_code,
        source_name_zh=source_name_zh,
        category=interface.category,
        menu_path=(source_name_zh, interface.category),
        asset_class=_infer_asset_class(interface),
        request_mode=_convert_request_mode(interface.request_mode),
        collection=InterfaceCollectionSpec(
            supported=downloader_profile_name is not None,
            default_profile=downloader_profile_name,
        ),
        parameters=tuple(_convert_parameter(parameter) for parameter in interface.parameters),
        fields=tuple(_convert_field(field) for field in interface.fields),
        examples=(_convert_example(interface),),
        summary_zh=summary_zh,
        description_zh=description_zh,
        params_note_zh=display_doc.params_note_zh or interface.params_note_zh,
        params_example_zh=display_doc.params_example_zh or interface.params_example_zh,
        notes=interface.description,
    )


def _builtin_source_name_zh(source_code: str, fallback: str) -> str:
    return BUILTIN_SOURCE_NAMES_ZH.get(source_code, fallback)


def _default_summary_zh(interface: SourceRequestInterface, source_name_zh: str) -> str:
    title = interface.display_name_zh or interface.name
    return f"临时获取{source_name_zh}{title}数据，默认不入库。"


def _default_description_zh(interface: SourceRequestInterface, summary_zh: str) -> str:
    if _contains_cjk(interface.first_stage_strategy):
        return interface.first_stage_strategy
    return summary_zh


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def _current_downloader_profiles() -> tuple[Any, ...]:
    """Return current built-in downloader profiles without making them catalog truth."""

    global _PROJECTION_DOWNLOADER_PROFILES_CACHE
    if _PROJECTION_DOWNLOADER_PROFILES_CACHE is not None:
        return _PROJECTION_DOWNLOADER_PROFILES_CACHE

    from .downloader_registry import load_builtin_downloader_profiles

    _PROJECTION_DOWNLOADER_PROFILES_CACHE = tuple(
        load_builtin_downloader_profiles(
            _ProjectionConcurrencyProfile,
            _ProjectionDownloaderProfile,
        ).values()
    )
    return _PROJECTION_DOWNLOADER_PROFILES_CACHE


def _downloader_profile_name(interface_name: str) -> str | None:
    for profile in _current_downloader_profiles():
        if profile.interface_name == interface_name:
            return _plugin_downloader_name(profile)
    return None


def _convert_downloader_profile(profile: Any) -> PluginDownloaderProfile:
    concurrency = profile.concurrency
    return PluginDownloaderProfile(
        name=_plugin_downloader_name(profile),
        interface_name=profile.interface_name,
        display_name_zh=profile.display_name,
        resource_group=str(getattr(profile, "resource_group", None) or f"{profile.interface_name}.source"),
        mode=DownloaderMode.SNAPSHOT.value,
        default_options={
            "params": dict(profile.default_params),
            "fields": list(profile.default_fields) if profile.default_fields is not None else None,
            "formats": [profile.output_format],
            "connection_mode": profile.default_connection_mode,
            "source_server_count": concurrency.default_source_server_count,
            "connections_per_server": concurrency.default_connections_per_server,
            "max_concurrent_tasks": concurrency.default_max_concurrent_tasks,
            "batch_size": concurrency.default_batch_size,
            "request_interval_ms": concurrency.default_request_interval_ms,
            "retry_count": concurrency.default_retry_count,
            "timeout_ms": concurrency.default_timeout_ms,
        },
        default_limits={
            "max_active_jobs": 1,
            "max_connections_total": concurrency.max_connection_count,
            "request_interval_ms": concurrency.default_request_interval_ms,
            "max_retries": concurrency.max_retry_count,
        },
        output={
            "default_dir_name": profile.interface_name,
            "file_name_template": "{interface_name}_{data_date}_{run_time}",
            "supported_formats": list(profile.supported_formats),
            "output_layer": profile.output_layer,
            "write_mode": getattr(profile, "write_mode", "snapshot"),
            "primary_key": list(profile.primary_key) if isinstance(profile.primary_key, tuple) else profile.primary_key,
            "partition_by": list(getattr(profile, "partition_by", ()) or ()),
            "required_columns": list(getattr(profile, "required_columns", ()) or ()),
            "expected_columns": list(getattr(profile, "expected_columns", ()) or ()),
            "date_field": getattr(profile, "date_field", None),
            "datetime_field": getattr(profile, "datetime_field", None),
            "numeric_positive_columns": list(getattr(profile, "numeric_positive_columns", ()) or ()),
            "field_mappings": dict(getattr(profile, "field_mappings", {}) or {}),
        },
    )


def _generic_builtin_downloader_name(interface_name: str) -> str | None:
    if interface_name not in _BUILTIN_INTERFACE_DOWNLOADER_CONFIG:
        return None
    return f"{interface_name}.snapshot"


def _generic_builtin_downloader_profile(interface: InterfaceSpec) -> PluginDownloaderProfile:
    config = dict(_BUILTIN_INTERFACE_DOWNLOADER_CONFIG[interface.name])
    default_fields = config.get("fields")
    if default_fields is None:
        default_fields = tuple(field.name for field in interface.fields)
    return PluginDownloaderProfile(
        name=f"{interface.name}.snapshot",
        interface_name=interface.name,
        display_name_zh=f"{interface.display_name_zh}采集",
        resource_group=f"{interface.source_code}.http",
        mode=DownloaderMode.SNAPSHOT.value,
        default_options={
            "params": dict(config.get("params") or {}),
            "fields": list(default_fields),
            "formats": ["parquet"],
            "source_server_count": 1,
            "connections_per_server": 1,
            "max_concurrent_tasks": 1,
            "batch_size": 1,
            "request_interval_ms": 0,
            "retry_count": 0,
            "timeout_ms": 30000,
        },
        default_limits={
            "max_active_jobs": 1,
            "max_connections_total": 1,
            "request_interval_ms": 0,
            "max_retries": 0,
        },
        output={
            "default_dir_name": interface.name,
            "file_name_template": "{interface_name}_{data_date}_{run_time}",
            "supported_formats": ["parquet", "csv", "jsonl"],
            "output_layer": str(config.get("output_layer") or "snapshot"),
            "write_mode": str(config.get("write_mode") or "snapshot"),
            "primary_key": list(config.get("primary_key") or ()),
            "partition_by": list(config.get("partition_by") or ()),
            "required_columns": list(config.get("required_columns") or config.get("primary_key") or ()),
            "expected_columns": list(default_fields),
            "date_field": config.get("date_field"),
            "datetime_field": config.get("datetime_field"),
            "numeric_positive_columns": list(config.get("numeric_positive_columns") or ()),
        },
    )


def _generic_builtin_collector_spec(interface: InterfaceSpec) -> CollectorSpec:
    config = dict(_BUILTIN_INTERFACE_DOWNLOADER_CONFIG[interface.name])
    output_layer = str(config.get("output_layer") or "snapshot")
    return CollectorSpec(
        name=f"{interface.source_code}.{interface.name}.snapshot",
        display_name_zh=f"{interface.display_name_zh}采集",
        description=f"通过 {interface.source_name_zh} 源端接口 {interface.name} 采集小批量快照。",
        interfaces=(interface.name,),
        downloader_profile=f"{interface.name}.snapshot",
        resource_group=f"{interface.source_code}.http",
        default_params=dict(config.get("params") or {}),
        required_interfaces=(interface.name,),
        output={"layer": output_layer, "formats": ["parquet", "csv", "jsonl"]},
    )


def _plugin_downloader_name(profile: Any) -> str:
    return f"{profile.interface_name}.snapshot"


def _convert_parameter(parameter: Any) -> ParameterSpec:
    return ParameterSpec(
        name=parameter.name,
        display_name_zh=parameter.description_zh or parameter.name,
        type=_convert_parameter_type(parameter.dtype),
        required=parameter.required,
        multiple="list" in parameter.dtype,
        default=parameter.default,
        description=parameter.description_zh or parameter.description,
    )


def _convert_field(field: Any) -> FieldSpec:
    return FieldSpec(
        name=field.name,
        display_name_zh=field.description_zh or field.name,
        type=_convert_field_type(field.dtype),
        required=False,
        description=field.description_zh or field.description,
    )


def _convert_example(interface: SourceRequestInterface) -> PluginRequestExample:
    return PluginRequestExample(
        title=interface.display_name_zh,
        request={
            "interface_name": interface.name,
            "params": dict(interface.example.request.get("params", interface.example.request)),
        },
        response={
            "data": [dict(row) for row in interface.example.response],
            "schema": [{"name": field.name, "type": _convert_field_type(field.dtype)} for field in interface.fields],
            "meta": {"count": len(interface.example.response)},
        },
    )


def _convert_request_mode(value: str) -> str:
    if value in {mode.value for mode in RequestMode}:
        return value
    return RequestMode.SOURCE_REQUEST.value


def _convert_parameter_type(dtype: str) -> str:
    normalized = dtype.lower()
    if "boolean" in normalized:
        return ParameterType.BOOLEAN.value
    if "date" in normalized and "datetime" not in normalized:
        return ParameterType.DATE.value
    if "datetime" in normalized:
        return ParameterType.DATETIME.value
    if "integer" in normalized and "string" not in normalized and "list" not in normalized:
        return ParameterType.INTEGER.value
    if ("number" in normalized or "float" in normalized) and "string" not in normalized:
        return ParameterType.NUMBER.value
    return ParameterType.STRING.value


def _convert_field_type(dtype: str) -> str:
    normalized = dtype.lower()
    if "boolean" in normalized:
        return FieldType.BOOLEAN.value
    if "datetime" in normalized:
        return FieldType.DATETIME.value
    if normalized.startswith("date"):
        return FieldType.DATE.value
    if normalized.startswith("time"):
        return FieldType.STRING.value
    if "integer" in normalized:
        return FieldType.INTEGER.value
    if "number" in normalized or "float" in normalized:
        return FieldType.NUMBER.value
    return FieldType.STRING.value


def _infer_asset_class(interface: SourceRequestInterface) -> str:
    name = interface.name
    category = interface.category
    if name.startswith("index_"):
        return AssetClass.INDEX.value
    if name.startswith("etf_"):
        return AssetClass.ETF.value
    if name.startswith("fund_"):
        return AssetClass.FUND.value
    if name.startswith("bond_"):
        return AssetClass.BOND.value
    if name.startswith("futures_"):
        return AssetClass.FUTURE.value
    if name.startswith("option_"):
        return AssetClass.OPTION.value
    if name.startswith("fx_"):
        return AssetClass.FX.value
    if name.startswith("macro_"):
        return AssetClass.MACRO.value
    if category in {"指数数据"}:
        return AssetClass.INDEX.value
    if category in {"基金数据"}:
        return AssetClass.FUND.value
    if category in {"债券数据"}:
        return AssetClass.BOND.value
    if category in {"期货数据"}:
        return AssetClass.FUTURE.value
    if category in {"期权数据"}:
        return AssetClass.OPTION.value
    if category in {"外汇数据"}:
        return AssetClass.FX.value
    if category in {"宏观数据"}:
        return AssetClass.MACRO.value
    return AssetClass.STOCK.value
