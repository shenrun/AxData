"""Provider plugin protocol and manifest models for AxData.

The classes in this module are intentionally source-neutral. They describe
metadata and call contracts that can be used by built-in providers today and
entry-point based external plugins later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Mapping, Protocol, Sequence, Tuple, runtime_checkable

MANIFEST_FILE_NAME = "axdata-provider.json"
PLUGIN_MANIFEST_FILE_NAME = "axdata-plugin.json"
MANIFEST_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:[._-][a-z0-9_]+)*$")
_SNAKE_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class ManifestError(ValueError):
    """Raised when a provider manifest cannot be parsed or validated."""


class AssetClass(str, Enum):
    """Standard AxData asset classes."""

    STOCK = "stock"
    INDEX = "index"
    ETF = "etf"
    FUND = "fund"
    BOND = "bond"
    FUTURE = "future"
    OPTION = "option"
    FX = "fx"
    MACRO = "macro"


class PluginTrustLevel(str, Enum):
    """Trust value declared by plugin authors or computed by the registry."""

    OFFICIAL = "official"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class PluginStatus(str, Enum):
    """Provider registry status."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"
    INCOMPATIBLE = "incompatible"
    CONFLICT = "conflict"


class RequestMode(str, Enum):
    """Interface request mode."""

    SOURCE_REQUEST = "source_request"
    QUERY = "query"
    STREAM = "stream"
    COLLECT = "collect"


class ParameterType(str, Enum):
    """Supported manifest parameter types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    ARRAY = "array"
    OBJECT = "object"


class FieldType(str, Enum):
    """Supported manifest field types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"


class DownloaderMode(str, Enum):
    """Supported downloader profile modes."""

    SNAPSHOT = "snapshot"
    INCREMENTAL = "incremental"
    HISTORY = "history"
    STREAM_RECORDING = "stream_recording"


def _enum_value(value: Any, enum_type: type[Enum], field_name: str) -> str:
    if isinstance(value, enum_type):
        return str(value.value)
    if isinstance(value, str):
        try:
            return str(enum_type(value).value)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in enum_type)
            raise ManifestError(f"{field_name} must be one of: {allowed}") from exc
    raise ManifestError(f"{field_name} must be a string")


def _ensure_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{field_name} must be an object")
    return value


def _optional_mapping(value: Any, field_name: str) -> Mapping[str, Any] | None:
    if value is None:
        return None
    return _ensure_mapping(value, field_name)


def _ensure_sequence(value: Any, field_name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ManifestError(f"{field_name} must be an array")
    return value


def _string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ManifestError(f"{field_name} must be a string")
    return value


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ManifestError(f"{field_name} must be a boolean")
    return value


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _string(value, field_name)


def _identifier(value: str, field_name: str, *, allow_dot: bool = True) -> str:
    pattern = _IDENTIFIER_PATTERN if allow_dot else _SNAKE_IDENTIFIER_PATTERN
    if not pattern.fullmatch(value):
        allowed = "lowercase letters, numbers and underscores"
        if allow_dot:
            allowed += ", dots and dashes"
        raise ManifestError(
            f"{field_name} must use {allowed} and start with a lowercase letter"
        )
    return value


@dataclass(frozen=True)
class RequiredConfig:
    """Display-only configuration requirement declared by a provider."""

    name: str
    kind: str
    required: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "required": self.required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RequiredConfig":
        return cls(
            name=_string(data.get("name"), "required_config.name"),
            kind=_string(data.get("kind"), "required_config.kind"),
            required=_bool(data.get("required", False), "required_config.required"),
            description=_string(data.get("description", ""), "required_config.description"),
        )


@dataclass(frozen=True)
class PluginInfo:
    """V2 plugin-level manifest metadata."""

    plugin_id: str
    name_zh: str
    version: str
    description: str = ""

    def __post_init__(self) -> None:
        _identifier(self.plugin_id, "plugin.plugin_id")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name_zh": self.name_zh,
            "version": self.version,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PluginInfo":
        return cls(
            plugin_id=_string(data.get("plugin_id"), "plugin.plugin_id"),
            name_zh=_string(data.get("name_zh"), "plugin.name_zh"),
            version=_string(data.get("version"), "plugin.version"),
            description=_string(data.get("description", ""), "plugin.description"),
        )


@dataclass(frozen=True)
class ProviderInfo:
    """Provider-level manifest metadata."""

    provider_id: str
    source_code: str
    source_name_zh: str
    version: str
    declared_trust_level: str = PluginTrustLevel.COMMUNITY.value
    homepage: str | None = None
    license: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        _identifier(self.provider_id, "provider.provider_id")
        _identifier(self.source_code, "provider.source_code", allow_dot=False)
        _enum_value(
            self.declared_trust_level,
            PluginTrustLevel,
            "provider.declared_trust_level",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "source_code": self.source_code,
            "source_name_zh": self.source_name_zh,
            "version": self.version,
            "declared_trust_level": _enum_value(
                self.declared_trust_level,
                PluginTrustLevel,
                "declared_trust_level",
            ),
            "homepage": self.homepage,
            "license": self.license,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProviderInfo":
        return cls(
            provider_id=_string(data.get("provider_id"), "provider.provider_id"),
            source_code=_string(data.get("source_code"), "provider.source_code"),
            source_name_zh=_string(data.get("source_name_zh"), "provider.source_name_zh"),
            version=_string(data.get("version"), "provider.version"),
            declared_trust_level=_enum_value(
                data.get("declared_trust_level", PluginTrustLevel.COMMUNITY.value),
                PluginTrustLevel,
                "provider.declared_trust_level",
            ),
            homepage=_optional_string(data.get("homepage"), "provider.homepage"),
            license=_optional_string(data.get("license"), "provider.license"),
            description=_string(data.get("description", ""), "provider.description"),
        )


@dataclass(frozen=True)
class ParameterSpec:
    """Interface parameter manifest entry."""

    name: str
    display_name_zh: str
    type: str
    required: bool = False
    multiple: bool = False
    default: Any = None
    enum: Tuple[Any, ...] = ()
    control: str | None = None
    placeholder: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        _identifier(self.name, f"parameter.{self.name}.name", allow_dot=False)
        _enum_value(self.type, ParameterType, f"parameter.{self.name}.type")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name_zh": self.display_name_zh,
            "type": _enum_value(self.type, ParameterType, f"parameter.{self.name}.type"),
            "required": self.required,
            "multiple": self.multiple,
            "default": self.default,
            "enum": list(self.enum),
            "control": self.control,
            "placeholder": self.placeholder,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ParameterSpec":
        name = _string(data.get("name"), "parameter.name")
        return cls(
            name=name,
            display_name_zh=_string(
                data.get("display_name_zh"),
                f"parameter.{name}.display_name_zh",
            ),
            type=_enum_value(data.get("type"), ParameterType, f"parameter.{name}.type"),
            required=_bool(data.get("required", False), f"parameter.{name}.required"),
            multiple=_bool(data.get("multiple", False), f"parameter.{name}.multiple"),
            default=data.get("default"),
            enum=tuple(_ensure_sequence(data.get("enum", ()), f"parameter.{name}.enum")),
            control=_optional_string(data.get("control"), f"parameter.{name}.control"),
            placeholder=_optional_string(data.get("placeholder"), f"parameter.{name}.placeholder"),
            description=_string(data.get("description", ""), f"parameter.{name}.description"),
        )


@dataclass(frozen=True)
class FieldSpec:
    """Interface response field manifest entry."""

    name: str
    display_name_zh: str
    type: str
    required: bool = False
    unit: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        _identifier(self.name, f"field.{self.name}.name", allow_dot=False)
        _enum_value(self.type, FieldType, f"field.{self.name}.type")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name_zh": self.display_name_zh,
            "type": _enum_value(self.type, FieldType, f"field.{self.name}.type"),
            "required": self.required,
            "unit": self.unit,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FieldSpec":
        name = _string(data.get("name"), "field.name")
        return cls(
            name=name,
            display_name_zh=_string(data.get("display_name_zh"), f"field.{name}.display_name_zh"),
            type=_enum_value(data.get("type"), FieldType, f"field.{name}.type"),
            required=_bool(data.get("required", False), f"field.{name}.required"),
            unit=_optional_string(data.get("unit"), f"field.{name}.unit"),
            description=_string(data.get("description", ""), f"field.{name}.description"),
        )


@dataclass(frozen=True)
class RequestExample:
    """Request and response example for an interface."""

    title: str
    request: Mapping[str, Any]
    response: Mapping[str, Any]
    request_time: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "request": dict(self.request),
            "response": dict(self.response),
            "request_time": self.request_time,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RequestExample":
        return cls(
            title=_string(data.get("title"), "example.title"),
            request=dict(_ensure_mapping(data.get("request"), "example.request")),
            response=dict(_ensure_mapping(data.get("response"), "example.response")),
            request_time=_optional_string(data.get("request_time"), "example.request_time"),
        )


@dataclass(frozen=True)
class ReferenceSectionSpec:
    """Static interface reference table supplied by a plugin manifest."""

    id: str
    title: str
    columns: Tuple[str, ...]
    rows: Tuple[Tuple[str, ...], ...]
    note: str = ""

    def __post_init__(self) -> None:
        _identifier(self.id, f"reference_section.{self.id}.id", allow_dot=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "note": self.note,
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReferenceSectionSpec":
        section_id = _string(data.get("id"), "reference_section.id")
        return cls(
            id=section_id,
            title=_string(data.get("title"), f"reference_section.{section_id}.title"),
            note=_string(data.get("note", ""), f"reference_section.{section_id}.note"),
            columns=tuple(
                _string(item, f"reference_section.{section_id}.columns")
                for item in _ensure_sequence(
                    data.get("columns", ()),
                    f"reference_section.{section_id}.columns",
                )
            ),
            rows=tuple(
                tuple(
                    _string(cell, f"reference_section.{section_id}.rows")
                    for cell in _ensure_sequence(row, f"reference_section.{section_id}.rows[]")
                )
                for row in _ensure_sequence(
                    data.get("rows", ()),
                    f"reference_section.{section_id}.rows",
                )
            ),
        )


@dataclass(frozen=True)
class InterfaceCollectionSpec:
    """Collection capability metadata for one interface."""

    supported: bool = False
    default_profile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported": self.supported,
            "default_profile": self.default_profile,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "InterfaceCollectionSpec":
        if data is None:
            return cls()
        return cls(
            supported=_bool(data.get("supported", False), "collection.supported"),
            default_profile=_optional_string(
                data.get("default_profile"),
                "collection.default_profile",
            ),
        )


@dataclass(frozen=True)
class InterfaceSpec:
    """Manifest entry for one public AxData interface."""

    name: str
    display_name_zh: str
    source_code: str
    source_name_zh: str
    asset_class: str
    request_mode: str = RequestMode.SOURCE_REQUEST.value
    category: str | None = None
    menu_path: Tuple[str, ...] = ()
    collection: InterfaceCollectionSpec = field(default_factory=InterfaceCollectionSpec)
    parameters: Tuple[ParameterSpec, ...] = ()
    fields: Tuple[FieldSpec, ...] = ()
    examples: Tuple[RequestExample, ...] = ()
    reference_sections: Tuple[ReferenceSectionSpec, ...] = ()
    summary_zh: str = ""
    description_zh: str = ""
    params_note_zh: str = ""
    params_example_zh: str = ""
    limits: Mapping[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        _identifier(self.name, f"interface.{self.name}.name", allow_dot=False)
        _identifier(self.source_code, f"interface.{self.name}.source_code", allow_dot=False)
        _enum_value(self.asset_class, AssetClass, f"interface.{self.name}.asset_class")
        _enum_value(self.request_mode, RequestMode, f"interface.{self.name}.request_mode")

    def to_dict(self) -> dict[str, Any]:
        data = {
            "name": self.name,
            "display_name_zh": self.display_name_zh,
            "source_code": self.source_code,
            "source_name_zh": self.source_name_zh,
            "category": self.category,
            "menu_path": list(self.menu_path),
            "asset_class": _enum_value(
                self.asset_class,
                AssetClass,
                f"interface.{self.name}.asset_class",
            ),
            "request_mode": _enum_value(
                self.request_mode,
                RequestMode,
                f"interface.{self.name}.request_mode",
            ),
            "collection": self.collection.to_dict(),
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "fields": [field_spec.to_dict() for field_spec in self.fields],
            "examples": [example.to_dict() for example in self.examples],
            "reference_sections": [section.to_dict() for section in self.reference_sections],
            "limits": dict(self.limits),
            "notes": self.notes,
        }
        if self.summary_zh:
            data["summary_zh"] = self.summary_zh
        if self.description_zh:
            data["description_zh"] = self.description_zh
        if self.params_note_zh:
            data["params_note_zh"] = self.params_note_zh
        if self.params_example_zh:
            data["params_example_zh"] = self.params_example_zh
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InterfaceSpec":
        name = _string(data.get("name"), "interface.name")
        return cls(
            name=name,
            display_name_zh=_string(
                data.get("display_name_zh"),
                f"interface.{name}.display_name_zh",
            ),
            source_code=_string(data.get("source_code"), f"interface.{name}.source_code"),
            source_name_zh=_string(data.get("source_name_zh"), f"interface.{name}.source_name_zh"),
            category=_optional_string(data.get("category"), f"interface.{name}.category"),
            menu_path=tuple(
                _string(item, f"interface.{name}.menu_path")
                for item in _ensure_sequence(
                    data.get("menu_path", ()),
                    f"interface.{name}.menu_path",
                )
            ),
            asset_class=_enum_value(
                data.get("asset_class"),
                AssetClass,
                f"interface.{name}.asset_class",
            ),
            request_mode=_enum_value(
                data.get("request_mode"),
                RequestMode,
                f"interface.{name}.request_mode",
            ),
            collection=InterfaceCollectionSpec.from_dict(data.get("collection")),
            parameters=tuple(
                ParameterSpec.from_dict(_ensure_mapping(item, f"interface.{name}.parameters"))
                for item in _ensure_sequence(
                    data.get("parameters", ()),
                    f"interface.{name}.parameters",
                )
            ),
            fields=tuple(
                FieldSpec.from_dict(_ensure_mapping(item, f"interface.{name}.fields"))
                for item in _ensure_sequence(data.get("fields", ()), f"interface.{name}.fields")
            ),
            examples=tuple(
                RequestExample.from_dict(_ensure_mapping(item, f"interface.{name}.examples"))
                for item in _ensure_sequence(data.get("examples", ()), f"interface.{name}.examples")
            ),
            reference_sections=tuple(
                ReferenceSectionSpec.from_dict(
                    _ensure_mapping(item, f"interface.{name}.reference_sections")
                )
                for item in _ensure_sequence(
                    data.get("reference_sections", ()),
                    f"interface.{name}.reference_sections",
                )
            ),
            summary_zh=_string(data.get("summary_zh", ""), f"interface.{name}.summary_zh"),
            description_zh=_string(data.get("description_zh", ""), f"interface.{name}.description_zh"),
            params_note_zh=_string(data.get("params_note_zh", ""), f"interface.{name}.params_note_zh"),
            params_example_zh=_string(data.get("params_example_zh", ""), f"interface.{name}.params_example_zh"),
            limits=dict(_ensure_mapping(data.get("limits", {}), f"interface.{name}.limits")),
            notes=_string(data.get("notes", ""), f"interface.{name}.notes"),
        )


@dataclass(frozen=True)
class DownloaderProfile:
    """Manifest entry for one collection profile."""

    name: str
    interface_name: str
    display_name_zh: str
    resource_group: str
    mode: str
    default_options: Mapping[str, Any] = field(default_factory=dict)
    default_limits: Mapping[str, Any] = field(default_factory=dict)
    output: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.name, f"downloader.{self.name}.name")
        _identifier(self.interface_name, f"downloader.{self.name}.interface_name", allow_dot=False)
        _identifier(self.resource_group, f"downloader.{self.name}.resource_group")
        _enum_value(self.mode, DownloaderMode, f"downloader.{self.name}.mode")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "interface_name": self.interface_name,
            "display_name_zh": self.display_name_zh,
            "resource_group": self.resource_group,
            "mode": _enum_value(self.mode, DownloaderMode, f"downloader.{self.name}.mode"),
            "default_options": dict(self.default_options),
            "default_limits": dict(self.default_limits),
            "output": dict(self.output),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DownloaderProfile":
        name = _string(data.get("name"), "downloader.name")
        return cls(
            name=name,
            interface_name=_string(data.get("interface_name"), f"downloader.{name}.interface_name"),
            display_name_zh=_string(
                data.get("display_name_zh"),
                f"downloader.{name}.display_name_zh",
            ),
            resource_group=_string(data.get("resource_group"), f"downloader.{name}.resource_group"),
            mode=_enum_value(data.get("mode"), DownloaderMode, f"downloader.{name}.mode"),
            default_options=dict(
                _ensure_mapping(
                    data.get("default_options", {}),
                    f"downloader.{name}.default_options",
                )
            ),
            default_limits=dict(
                _ensure_mapping(
                    data.get("default_limits", {}),
                    f"downloader.{name}.default_limits",
                )
            ),
            output=dict(_ensure_mapping(data.get("output", {}), f"downloader.{name}.output")),
        )


@dataclass(frozen=True)
class CollectorSpec:
    """Manifest entry for one collector capability."""

    name: str
    display_name_zh: str
    resource_group: str
    interfaces: Tuple[str, ...] = ()
    downloader_profile: str | None = None
    description: str = ""
    default_schedule: Mapping[str, Any] = field(default_factory=dict)
    default_params: Mapping[str, Any] = field(default_factory=dict)
    required_interfaces: Tuple[str, ...] = ()
    output: Mapping[str, Any] = field(default_factory=dict)
    collector_plugin_id: str | None = None
    dataset_id: str | None = None
    asset_class: str | None = None
    category: str | None = None
    config_schema: Mapping[str, Any] = field(default_factory=dict)
    quality: Mapping[str, Any] = field(default_factory=dict)
    required_datasets: Tuple[str, ...] = ()
    runner_entry: str | None = None
    lifecycle_status: str | None = None
    legacy_source: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.name, f"collector.{self.name}.name")
        _identifier(self.resource_group, f"collector.{self.name}.resource_group")
        if self.collector_plugin_id is not None:
            _identifier(self.collector_plugin_id, f"collector.{self.name}.collector_plugin_id")
        if self.dataset_id is not None:
            _identifier(self.dataset_id, f"collector.{self.name}.dataset_id")
        if self.asset_class is not None:
            _enum_value(self.asset_class, AssetClass, f"collector.{self.name}.asset_class")
        if self.category is not None:
            _string(self.category, f"collector.{self.name}.category")
        if self.runner_entry is not None:
            _string(self.runner_entry, f"collector.{self.name}.runner_entry")
        if self.lifecycle_status is not None:
            _identifier(
                self.lifecycle_status,
                f"collector.{self.name}.lifecycle_status",
                allow_dot=False,
            )
        if self.legacy_source is not None:
            _identifier(self.legacy_source, f"collector.{self.name}.legacy_source")
        for interface_name in self.interfaces:
            _identifier(interface_name, f"collector.{self.name}.interfaces", allow_dot=False)
        for interface_name in self.required_interfaces:
            _identifier(interface_name, f"collector.{self.name}.required_interfaces", allow_dot=False)
        for dataset in self.required_datasets:
            _identifier(dataset, f"collector.{self.name}.required_datasets")
        if self.downloader_profile is not None:
            _identifier(self.downloader_profile, f"collector.{self.name}.downloader_profile")

    @property
    def collector_id(self) -> str:
        return self.name

    @property
    def is_independent(self) -> bool:
        return self.runner_entry is not None

    @property
    def is_legacy(self) -> bool:
        return not self.is_independent

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "display_name_zh": self.display_name_zh,
            "description": self.description,
            "resource_group": self.resource_group,
            "default_schedule": dict(self.default_schedule),
            "default_params": dict(self.default_params),
            "output": dict(self.output),
        }
        if self.collector_plugin_id is not None:
            payload["collector_plugin_id"] = self.collector_plugin_id
        if self.dataset_id is not None:
            payload["dataset_id"] = self.dataset_id
        if self.asset_class is not None:
            payload["asset_class"] = self.asset_class
        if self.category is not None:
            payload["category"] = self.category
        if self.config_schema:
            payload["config_schema"] = dict(self.config_schema)
        if self.quality:
            payload["quality"] = dict(self.quality)
        if self.runner_entry is not None:
            payload["collector_id"] = self.name
            payload["runner_entry"] = self.runner_entry
        if self.lifecycle_status is not None:
            payload["lifecycle_status"] = self.lifecycle_status
        if self.legacy_source is not None:
            payload["legacy_source"] = self.legacy_source
        if self.interfaces:
            payload["interfaces"] = list(self.interfaces)
        if self.downloader_profile is not None:
            payload["downloader_profile"] = self.downloader_profile
        if self.required_interfaces:
            payload["required_interfaces"] = list(self.required_interfaces)
        if self.required_datasets:
            payload["required_datasets"] = list(self.required_datasets)
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CollectorSpec":
        raw_collector_id = data.get("collector_id")
        raw_legacy_name = data.get("name")
        if (
            raw_collector_id is not None
            and raw_legacy_name is not None
            and raw_collector_id != raw_legacy_name
        ):
            raise ManifestError("collector.collector_id and collector.name must match when both are set")
        raw_name = raw_collector_id if raw_collector_id is not None else raw_legacy_name
        name = _string(raw_name, "collector.collector_id")
        return cls(
            name=name,
            display_name_zh=_string(
                data.get("display_name_zh"),
                f"collector.{name}.display_name_zh",
            ),
            description=_string(data.get("description", ""), f"collector.{name}.description"),
            collector_plugin_id=_optional_string(
                data.get("collector_plugin_id"),
                f"collector.{name}.collector_plugin_id",
            ),
            dataset_id=_optional_string(data.get("dataset_id"), f"collector.{name}.dataset_id"),
            asset_class=(
                _enum_value(data.get("asset_class"), AssetClass, f"collector.{name}.asset_class")
                if data.get("asset_class") is not None
                else None
            ),
            category=_optional_string(data.get("category"), f"collector.{name}.category"),
            config_schema=dict(
                _ensure_mapping(
                    data.get("config_schema", {}),
                    f"collector.{name}.config_schema",
                )
            ),
            quality=dict(
                _ensure_mapping(
                    data.get("quality", {}),
                    f"collector.{name}.quality",
                )
            ),
            runner_entry=_optional_string(
                data.get("runner_entry"),
                f"collector.{name}.runner_entry",
            ),
            lifecycle_status=_optional_string(
                data.get("lifecycle_status"),
                f"collector.{name}.lifecycle_status",
            ),
            legacy_source=_optional_string(
                data.get("legacy_source"),
                f"collector.{name}.legacy_source",
            ),
            interfaces=tuple(
                _string(item, f"collector.{name}.interfaces")
                for item in _ensure_sequence(
                    data.get("interfaces", ()),
                    f"collector.{name}.interfaces",
                )
            ),
            downloader_profile=_optional_string(
                data.get("downloader_profile"),
                f"collector.{name}.downloader_profile",
            ),
            resource_group=_string(data.get("resource_group"), f"collector.{name}.resource_group"),
            default_schedule=dict(
                _ensure_mapping(
                    data.get("default_schedule", {}),
                    f"collector.{name}.default_schedule",
                )
            ),
            default_params=dict(
                _ensure_mapping(
                    data.get("default_params", {}),
                    f"collector.{name}.default_params",
                )
            ),
            required_interfaces=tuple(
                _string(item, f"collector.{name}.required_interfaces")
                for item in _ensure_sequence(
                    data.get("required_interfaces", ()),
                    f"collector.{name}.required_interfaces",
                )
            ),
            required_datasets=tuple(
                _string(item, f"collector.{name}.required_datasets")
                for item in _ensure_sequence(
                    data.get("required_datasets", ()),
                    f"collector.{name}.required_datasets",
                )
            ),
            output=dict(_ensure_mapping(data.get("output", {}), f"collector.{name}.output")),
        )


@dataclass(frozen=True)
class DependencySpec:
    """Display/install-time Python dependency declaration for a plugin."""

    name: str
    version_spec: str | None = None
    optional: bool = False
    source: str | None = None
    wheel: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        _identifier(self.name, f"dependency.{self.name}.name")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version_spec": self.version_spec,
            "optional": self.optional,
            "source": self.source,
            "wheel": self.wheel,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DependencySpec":
        name = _string(data.get("name"), "dependency.name")
        return cls(
            name=name,
            version_spec=_optional_string(data.get("version_spec"), f"dependency.{name}.version_spec"),
            optional=_bool(data.get("optional", False), f"dependency.{name}.optional"),
            source=_optional_string(data.get("source"), f"dependency.{name}.source"),
            wheel=_optional_string(data.get("wheel"), f"dependency.{name}.wheel"),
            description=_string(data.get("description", ""), f"dependency.{name}.description"),
        )


@dataclass(frozen=True)
class ConfigSchema:
    """V2 display-only configuration schema."""

    required_config: Tuple[RequiredConfig, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_config": [config.to_dict() for config in self.required_config],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "ConfigSchema":
        if data is None:
            return cls()
        mapping = _ensure_mapping(data, "config_schema")
        return cls(
            required_config=tuple(
                RequiredConfig.from_dict(_ensure_mapping(item, "config_schema.required_config[]"))
                for item in _ensure_sequence(
                    mapping.get("required_config", ()),
                    "config_schema.required_config",
                )
            )
        )


@dataclass(frozen=True)
class ProviderManifest:
    """Serializable provider manifest."""

    provider: ProviderInfo | None
    interfaces: Tuple[InterfaceSpec, ...]
    manifest_version: str = MANIFEST_VERSION
    plugin_api_version: str = PLUGIN_API_VERSION
    plugin: PluginInfo | None = None
    downloaders: Tuple[DownloaderProfile, ...] = ()
    collectors: Tuple[CollectorSpec, ...] = ()
    dependencies: Tuple[DependencySpec, ...] = ()
    config_schema: ConfigSchema = field(default_factory=ConfigSchema)
    required_config: Tuple[RequiredConfig, ...] = ()
    resources: Mapping[str, Any] = field(default_factory=dict)
    build: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.required_config and self.config_schema.required_config:
            object.__setattr__(self, "required_config", self.config_schema.required_config)
        elif self.required_config and not self.config_schema.required_config:
            object.__setattr__(self, "config_schema", ConfigSchema(self.required_config))

    @property
    def identity(self) -> str:
        if self.provider is not None:
            return self.provider.provider_id
        if self.plugin is not None:
            return self.plugin.plugin_id
        return "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "plugin_api_version": self.plugin_api_version,
            "plugin": self.plugin.to_dict() if self.plugin is not None else None,
            "provider": self.provider.to_dict() if self.provider is not None else None,
            "interfaces": [interface.to_dict() for interface in self.interfaces],
            "downloaders": [downloader.to_dict() for downloader in self.downloaders],
            "collectors": [collector.to_dict() for collector in self.collectors],
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
            "config_schema": self.config_schema.to_dict(),
            "required_config": [config.to_dict() for config in self.required_config],
            "resources": dict(self.resources),
            "build": dict(self.build),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProviderManifest":
        manifest_version = _string(data.get("manifest_version"), "manifest_version")
        plugin_api_version = _string(data.get("plugin_api_version"), "plugin_api_version")
        return cls(
            manifest_version=manifest_version,
            plugin_api_version=plugin_api_version,
            plugin=(
                PluginInfo.from_dict(_ensure_mapping(data.get("plugin"), "plugin"))
                if data.get("plugin") is not None
                else None
            ),
            provider=(
                ProviderInfo.from_dict(_ensure_mapping(data.get("provider"), "provider"))
                if data.get("provider") is not None
                else None
            ),
            interfaces=tuple(
                InterfaceSpec.from_dict(_ensure_mapping(item, "interfaces[]"))
                for item in _ensure_sequence(data.get("interfaces", ()), "interfaces")
            ),
            downloaders=tuple(
                DownloaderProfile.from_dict(_ensure_mapping(item, "downloaders[]"))
                for item in _ensure_sequence(data.get("downloaders", ()), "downloaders")
            ),
            collectors=tuple(
                CollectorSpec.from_dict(_ensure_mapping(item, "collectors[]"))
                for item in _ensure_sequence(data.get("collectors", ()), "collectors")
            ),
            dependencies=tuple(
                DependencySpec.from_dict(_ensure_mapping(item, "dependencies[]"))
                for item in _ensure_sequence(data.get("dependencies", ()), "dependencies")
            ),
            config_schema=ConfigSchema.from_dict(_optional_mapping(data.get("config_schema"), "config_schema")),
            required_config=tuple(
                RequiredConfig.from_dict(_ensure_mapping(item, "required_config[]"))
                for item in _ensure_sequence(data.get("required_config", ()), "required_config")
            ),
            resources=dict(_ensure_mapping(data.get("resources", {}), "resources")),
            build=dict(_ensure_mapping(data.get("build", {}), "build")),
        )


@dataclass(frozen=True)
class SourceResult:
    """Normalized source adapter result."""

    data: Tuple[Mapping[str, Any], ...]
    schema: Tuple[Mapping[str, Any], ...] = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": [dict(row) for row in self.data],
            "schema": [dict(field_spec) for field_spec in self.schema],
            "meta": dict(self.meta),
        }


@runtime_checkable
class SourceAdapter(Protocol):
    """Runtime source adapter protocol."""

    def call(
        self,
        interface_name: str,
        params: Mapping[str, object] | None = None,
        fields: Sequence[str] | None = None,
        options: Mapping[str, object] | None = None,
    ) -> SourceResult | Mapping[str, Any] | Sequence[Mapping[str, Any]]:
        """Call one source interface and return normalized data."""


@runtime_checkable
class SourceProvider(Protocol):
    """Runtime provider protocol."""

    provider_id: str
    source_code: str
    source_name_zh: str
    version: str
    plugin_api_version: str

    def interfaces(self) -> Sequence[InterfaceSpec]:
        """Return public interface specifications."""

    def create_adapter(self, options: Mapping[str, object] | None = None) -> SourceAdapter:
        """Create a source adapter."""

    def downloader_profiles(self) -> Sequence[DownloaderProfile]:
        """Return collection downloader profiles."""


def _provider_collectors(provider: Any) -> tuple[CollectorSpec, ...]:
    collectors = getattr(provider, "collectors", None)
    if collectors is None:
        return ()
    if callable(collectors):
        collectors = collectors()
    return tuple(collectors)


def _provider_dependencies(provider: Any) -> tuple[DependencySpec, ...]:
    dependencies = getattr(provider, "dependencies", None)
    if dependencies is None:
        return ()
    if callable(dependencies):
        dependencies = dependencies()
    return tuple(dependencies)


def _required_config_from_provider(provider: SourceProvider) -> tuple[RequiredConfig, ...]:
    required_config = getattr(provider, "required_config", None)
    if required_config is None:
        return ()
    if callable(required_config):
        required_config = required_config()
    return tuple(required_config)


def _provider_attr_string(provider: SourceProvider, name: str, default: str | None = None) -> str | None:
    value = getattr(provider, name, default)
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def manifest_from_provider(provider: SourceProvider) -> ProviderManifest:
    """Build a manifest from a provider object."""

    required_config = _required_config_from_provider(provider)
    return ProviderManifest(
        manifest_version=MANIFEST_VERSION,
        plugin_api_version=provider.plugin_api_version,
        provider=ProviderInfo(
            provider_id=provider.provider_id,
            source_code=provider.source_code,
            source_name_zh=provider.source_name_zh,
            version=provider.version,
            declared_trust_level=_provider_attr_string(
                provider,
                "declared_trust_level",
                PluginTrustLevel.COMMUNITY.value,
            )
            or PluginTrustLevel.COMMUNITY.value,
            homepage=_provider_attr_string(provider, "homepage"),
            license=_provider_attr_string(provider, "license"),
            description=_provider_attr_string(provider, "description", "") or "",
        ),
        interfaces=tuple(provider.interfaces()),
        downloaders=tuple(provider.downloader_profiles()),
        collectors=_provider_collectors(provider),
        dependencies=_provider_dependencies(provider),
        config_schema=ConfigSchema(required_config),
        required_config=required_config,
    )


def validate_manifest(manifest: ProviderManifest) -> None:
    """Run basic manifest integrity checks."""

    if manifest.provider is None and manifest.interfaces:
        raise ManifestError("provider is required when interfaces are declared")
    if manifest.provider is None and manifest.downloaders:
        raise ManifestError("provider is required when downloader profiles are declared")
    if manifest.provider is None and manifest.plugin is None:
        raise ManifestError("provider or plugin metadata is required")

    _validate_named_specs(
        [config.name for config in manifest.required_config],
        "Duplicate required_config name",
    )
    _validate_named_specs(
        [config.name for config in manifest.config_schema.required_config],
        "Duplicate config_schema.required_config name",
    )

    interface_names: set[str] = set()
    for interface in manifest.interfaces:
        if manifest.provider is None:
            raise ManifestError("provider is required when interfaces are declared")
        if interface.source_code != manifest.provider.source_code:
            raise ManifestError(
                f"Interface {interface.name!r} source_code {interface.source_code!r} "
                f"does not match provider source_code {manifest.provider.source_code!r}"
            )
        if interface.name in interface_names:
            raise ManifestError(f"Duplicate interface name: {interface.name}")
        interface_names.add(interface.name)
        parameter_name_list = [parameter.name for parameter in interface.parameters]
        field_name_list = [field_spec.name for field_spec in interface.fields]
        _validate_named_specs(
            parameter_name_list,
            f"Duplicate parameter name in {interface.name}",
        )
        _validate_named_specs(
            field_name_list,
            f"Duplicate field name in {interface.name}",
        )
        parameter_names = set(parameter_name_list)
        field_names = set(field_name_list)
        for example in interface.examples:
            _validate_example(example, interface.name, parameter_names, field_names)

    downloader_names: set[str] = set()
    downloader_interfaces_by_name: dict[str, str] = {}
    downloader_names_by_interface: dict[str, set[str]] = {}
    for downloader in manifest.downloaders:
        if downloader.name in downloader_names:
            raise ManifestError(f"Duplicate downloader profile name: {downloader.name}")
        downloader_names.add(downloader.name)
        downloader_interfaces_by_name[downloader.name] = downloader.interface_name
        downloader_names_by_interface.setdefault(downloader.interface_name, set()).add(downloader.name)
        if downloader.interface_name not in interface_names:
            raise ManifestError(
                f"DownloaderProfile {downloader.name!r} references unknown interface "
                f"{downloader.interface_name!r}"
            )

    for interface in manifest.interfaces:
        interface_downloader_names = downloader_names_by_interface.get(interface.name, set())
        if interface_downloader_names and not interface.collection.supported:
            raise ManifestError(
                f"Interface {interface.name!r} has downloader profiles but "
                "collection.supported is false"
            )
        default_profile = interface.collection.default_profile
        if default_profile and not interface.collection.supported:
            raise ManifestError(
                f"Interface {interface.name!r} collection.default_profile is set but "
                "collection.supported is false"
            )
        if default_profile and default_profile not in downloader_names:
            raise ManifestError(
                f"Interface {interface.name!r} collection.default_profile references "
                f"unknown downloader profile {default_profile!r}"
            )
        if (
            default_profile
            and downloader_interfaces_by_name.get(default_profile) != interface.name
        ):
            raise ManifestError(
                f"Interface {interface.name!r} collection.default_profile references "
                f"downloader profile {default_profile!r} for another interface"
            )

    collector_names: set[str] = set()
    local_interface_names = set(interface_names)
    for collector in manifest.collectors:
        if collector.name in collector_names:
            raise ManifestError(f"Duplicate collector name: {collector.name}")
        collector_names.add(collector.name)
        _validate_collector_contract(collector, manifest)
        if (
            collector.downloader_profile
            and manifest.downloaders
            and collector.downloader_profile not in downloader_names
        ):
            raise ManifestError(
                f"CollectorSpec {collector.name!r} references unknown downloader profile "
                f"{collector.downloader_profile!r}"
            )
        for interface_name in collector.interfaces:
            if manifest.interfaces and interface_name not in local_interface_names:
                raise ManifestError(
                    f"CollectorSpec {collector.name!r} references unknown interface "
                    f"{interface_name!r}"
                )

    _validate_named_specs(
        [dependency.name for dependency in manifest.dependencies],
        "Duplicate dependency name",
    )


def _validate_collector_contract(collector: CollectorSpec, manifest: ProviderManifest) -> None:
    independent_fields = {
        "collector_plugin_id": collector.collector_plugin_id,
        "dataset_id": collector.dataset_id,
        "runner_entry": collector.runner_entry,
        "asset_class": collector.asset_class,
        "category": collector.category,
        "lifecycle_status": collector.lifecycle_status,
    }
    has_independent_metadata = any(value is not None for value in independent_fields.values()) or bool(
        collector.config_schema or collector.quality
    )
    has_legacy_runtime = bool(
        collector.interfaces or collector.required_interfaces or collector.downloader_profile
    )
    if not has_independent_metadata and has_legacy_runtime:
        return
    if not has_independent_metadata and manifest.provider is not None:
        return

    required: tuple[tuple[str, Any], ...] = (
        ("collector_plugin_id", collector.collector_plugin_id),
        ("dataset_id", collector.dataset_id),
        ("runner_entry", collector.runner_entry),
    )
    for field_name, value in required:
        if not isinstance(value, str) or not value.strip():
            raise ManifestError(
                f"Independent CollectorSpec {collector.name!r} requires {field_name}"
            )
    if not collector.output:
        raise ManifestError(f"Independent CollectorSpec {collector.name!r} requires output")
    if not collector.quality:
        raise ManifestError(f"Independent CollectorSpec {collector.name!r} requires quality")
    if manifest.plugin is None:
        raise ManifestError(
            f"Independent CollectorSpec {collector.name!r} requires plugin metadata"
        )
    if collector.collector_plugin_id != manifest.plugin.plugin_id:
        raise ManifestError(
            f"Independent CollectorSpec {collector.name!r} collector_plugin_id "
            f"{collector.collector_plugin_id!r} does not match plugin_id "
            f"{manifest.plugin.plugin_id!r}"
        )


def _validate_named_specs(names: Sequence[str], message: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ManifestError(f"{message}: {name}")
        seen.add(name)


def _validate_example(
    example: RequestExample,
    interface_name: str,
    parameter_names: set[str],
    field_names: set[str],
) -> None:
    request = dict(example.request or {})
    response = dict(example.response or {})
    requested_interface = request.get("interface_name")
    if requested_interface is not None and requested_interface != interface_name:
        raise ManifestError(
            f"Example {example.title!r} for {interface_name} references interface "
            f"{requested_interface!r}"
        )

    params = request.get("params")
    if isinstance(params, Mapping):
        _validate_subset(
            set(str(name) for name in params),
            parameter_names,
            f"Example {example.title!r} for {interface_name} uses unknown params",
        )

    requested_fields = request.get("fields")
    if isinstance(requested_fields, Sequence) and not isinstance(
        requested_fields,
        (str, bytes, bytearray),
    ):
        _validate_subset(
            {str(name) for name in requested_fields},
            field_names,
            f"Example {example.title!r} for {interface_name} requests unknown fields",
        )

    schema = response.get("schema")
    if isinstance(schema, Sequence) and not isinstance(schema, (str, bytes, bytearray)):
        schema_names = {
            str(item.get("name"))
            for item in schema
            if isinstance(item, Mapping) and item.get("name") is not None
        }
        _validate_subset(
            schema_names,
            field_names,
            f"Example {example.title!r} for {interface_name} returns unknown schema fields",
        )

    data = response.get("data")
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        for row in data:
            if isinstance(row, Mapping):
                _validate_subset(
                    {str(name) for name in row},
                    field_names,
                    f"Example {example.title!r} for {interface_name} returns unknown data fields",
                )


def _validate_subset(values: set[str], allowed: set[str], message: str) -> None:
    unknown = sorted(value for value in values if value not in allowed)
    if unknown:
        raise ManifestError(f"{message}: {', '.join(unknown)}")
