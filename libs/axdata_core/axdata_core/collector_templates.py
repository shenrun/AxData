"""Built-in Collector task templates.

Templates are product shortcuts over existing CollectorSpec declarations. They
do not add new provider behavior and they intentionally keep default params
small so creating a task never implies a full-market backfill.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping


class CollectorTemplateError(ValueError):
    """Raised when a Collector task template cannot be used."""


@dataclass(frozen=True)
class TaskTemplate:
    """Serializable built-in task template."""

    template_id: str
    title: str
    description: str
    collector_name: str
    interface_name: str
    provider: str
    default_params: dict[str, Any] = field(default_factory=dict)
    fields: list[str] | None = None
    formats: list[str] | None = None
    trigger_type: str = "manual"
    interval_seconds: int | None = None
    daily_time: str | None = None
    schedule_hint: str = "manual"
    resource_group: str = "default"
    expected_layer: str = "snapshot"
    write_mode: str = "snapshot"
    partition_by: list[str] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    date_field: str | None = None
    required_datasets: list[str] = field(default_factory=list)
    dependency: dict[str, Any] = field(default_factory=dict)
    safety_limits: dict[str, Any] = field(default_factory=dict)
    required_plugin: str | None = None
    enabled_by_default: bool = True
    system_default: bool = False
    category: str = "core"
    tags: list[str] = field(default_factory=list)
    task_id: str | None = None
    next_action: str | None = None
    action_command: str | None = None
    available: bool = False
    unavailable_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "collector_name": self.collector_name,
            "interface_name": self.interface_name,
            "provider": self.provider,
            "default_params": dict(self.default_params),
            "fields": list(self.fields) if self.fields is not None else None,
            "formats": list(self.formats) if self.formats is not None else None,
            "trigger_type": self.trigger_type,
            "interval_seconds": self.interval_seconds,
            "daily_time": self.daily_time,
            "schedule_hint": self.schedule_hint,
            "resource_group": self.resource_group,
            "expected_layer": self.expected_layer,
            "write_mode": self.write_mode,
            "partition_by": list(self.partition_by),
            "primary_key": list(self.primary_key),
            "date_field": self.date_field,
            "required_datasets": list(self.required_datasets),
            "dependency": dict(self.dependency),
            "safety_limits": dict(self.safety_limits),
            "required_plugin": self.required_plugin,
            "enabled_by_default": bool(self.enabled_by_default),
            "system_default": bool(self.system_default),
            "category": self.category,
            "tags": list(self.tags),
            "task_id": self.task_id,
            "available": bool(self.available),
            "unavailable_reason": self.unavailable_reason,
            "next_action": self.next_action,
            "action_command": self.action_command,
        }


_CORE_TASK_TEMPLATES: tuple[TaskTemplate, ...] = (
    TaskTemplate(
        template_id="daily",
        title="股票日线小样本",
        description="使用 TDX 日 K 线插件接口创建小样本任务；默认只采 000001.SZ 最近 800 条。",
        collector_name="tdx.stock_kline_daily_tdx.snapshot",
        interface_name="stock_kline_daily_tdx",
        provider="axdata.collector.tdx",
        default_params={"code": "000001.SZ", "count": 800, "adjust": "none"},
        fields=[
            "instrument_id",
            "symbol",
            "tdx_code",
            "exchange",
            "trade_time",
            "period",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
        ],
        formats=["parquet"],
        schedule_hint="manual; 默认单只 000001.SZ 小样本",
        resource_group="tdx.quote",
        expected_layer="core",
        write_mode="snapshot",
        partition_by=["trade_date"],
        primary_key=["instrument_id", "trade_time", "period"],
        date_field="trade_time",
        required_datasets=["trade_cal"],
        dependency={
            "provider_id": "axdata.collector.tdx",
            "required": True,
            "missing_message": "请安装/启用 TDX 插件",
        },
        safety_limits={"code": "000001.SZ", "count": 800, "full_market_by_default": False},
        required_plugin="axdata.collector.tdx",
        category="daily",
        tags=["core-loop", "tdx", "sample"],
        task_id="daily_sample_tdx",
    ),
    TaskTemplate(
        template_id="stock_kline_daily_tdx",
        title="TDX 日 K 线",
        description="直接创建 TDX 日 K 线小样本任务；默认不展开全市场。",
        collector_name="tdx.stock_kline_daily_tdx.snapshot",
        interface_name="stock_kline_daily_tdx",
        provider="axdata.collector.tdx",
        default_params={"code": "000001.SZ", "count": 800, "adjust": "none"},
        formats=["parquet"],
        schedule_hint="manual; 默认单只 000001.SZ 小样本",
        resource_group="tdx.quote",
        expected_layer="core",
        write_mode="snapshot",
        partition_by=["trade_date"],
        primary_key=["instrument_id", "trade_time", "period"],
        date_field="trade_time",
        required_datasets=["trade_cal"],
        dependency={
            "provider_id": "axdata.collector.tdx",
            "required": True,
            "missing_message": "请安装/启用 TDX 插件",
        },
        safety_limits={"code": "000001.SZ", "count": 800, "full_market_by_default": False},
        required_plugin="axdata.collector.tdx",
        system_default=True,
        category="daily",
        tags=["default", "core-loop", "tdx", "daily"],
        task_id="stock_kline_daily_tdx_sample",
    ),
)

DEFAULT_TASK_TEMPLATE_IDS: tuple[str, ...] = (
    "stock_kline_daily_tdx",
)


def list_task_templates(*, data_root: str | Path | None = None) -> tuple[TaskTemplate, ...]:
    """Return built-in task templates with current registry availability."""

    snapshot = _registry_snapshot(data_root=data_root)
    return tuple(_with_availability(template, snapshot=snapshot) for template in _CORE_TASK_TEMPLATES)


def get_task_template(template_id: str, *, data_root: str | Path | None = None) -> TaskTemplate:
    """Return one built-in task template."""

    normalized = str(template_id or "").strip()
    for template in list_task_templates(data_root=data_root):
        if template.template_id == normalized:
            return template
    known = ", ".join(template.template_id for template in _CORE_TASK_TEMPLATES)
    raise CollectorTemplateError(f"Unknown task template {template_id!r}. Known templates: {known}.")


def task_template_to_create_kwargs(
    template_id: str,
    *,
    data_root: str | Path | None = None,
    task_id: str | None = None,
    name: str | None = None,
    enabled: bool | None = None,
    params: Mapping[str, Any] | None = None,
    fields: list[str] | None = None,
    formats: list[str] | None = None,
    trigger_type: str | None = None,
    interval_seconds: int | None = None,
    daily_time: str | None = None,
) -> dict[str, Any]:
    """Build CollectorSchedulerService.create_task kwargs from a template."""

    template = get_task_template(template_id, data_root=data_root)
    if not template.available:
        message = template.unavailable_reason or f"Task template {template.template_id!r} is not available."
        raise CollectorTemplateError(message)
    merged_params = dict(template.default_params)
    merged_params.update(dict(params or {}))
    return {
        "collector_name": template.collector_name,
        "task_id": task_id or template.task_id or template.template_id,
        "name": name or template.title,
        "enabled": template.enabled_by_default if enabled is None else bool(enabled),
        "trigger_type": trigger_type or template.trigger_type,
        "interval_seconds": interval_seconds if interval_seconds is not None else template.interval_seconds,
        "daily_time": daily_time if daily_time is not None else template.daily_time,
        "params": merged_params,
        "fields": fields if fields is not None else template.fields,
        "formats": formats if formats is not None else template.formats,
        "template_id": template.template_id,
        "created_by": "template",
        "interface_name": template.interface_name,
        "expected_layer": template.expected_layer,
        "schedule_hint": template.schedule_hint,
        "write_mode": template.write_mode,
        "partition_by": template.partition_by,
        "primary_key": template.primary_key,
        "date_field": template.date_field,
        "required_datasets": list(template.required_datasets),
        "required_plugin": template.required_plugin,
        "dependency": template.dependency,
        "category": template.category,
        "tags": template.tags,
    }


def default_task_templates(*, data_root: str | Path | None = None) -> tuple[TaskTemplate, ...]:
    """Return product-default tasks that should be visible in an empty store."""

    templates = {template.template_id: template for template in list_task_templates(data_root=data_root)}
    return tuple(templates[template_id] for template_id in DEFAULT_TASK_TEMPLATE_IDS)


def default_task_to_create_kwargs(template: TaskTemplate) -> dict[str, Any]:
    """Build create kwargs for seeding a default task even if dependencies are missing."""

    return {
        "collector_name": template.collector_name,
        "task_id": template.task_id or template.template_id,
        "name": template.title,
        "enabled": False,
        "trigger_type": template.trigger_type,
        "interval_seconds": template.interval_seconds,
        "daily_time": template.daily_time,
        "params": dict(template.default_params),
        "fields": list(template.fields) if template.fields is not None else None,
        "formats": list(template.formats) if template.formats is not None else None,
        "template_id": template.template_id,
        "created_by": "system",
        "interface_name": template.interface_name,
        "expected_layer": template.expected_layer,
        "schedule_hint": template.schedule_hint,
        "resource_group": template.resource_group,
        "provider_id": template.provider,
        "write_mode": template.write_mode,
        "partition_by": list(template.partition_by),
        "primary_key": list(template.primary_key),
        "date_field": template.date_field,
        "required_datasets": list(template.required_datasets),
        "required_plugin": template.required_plugin,
        "dependency": dict(template.dependency),
        "category": template.category,
        "tags": list(template.tags),
        "dependency_status": "ok" if template.available else "missing",
        "dependency_message": None if template.available else _template_unavailable_message(template),
    }


def _with_availability(template: TaskTemplate, *, snapshot: Any) -> TaskTemplate:
    collector_available = template.collector_name in snapshot.collectors
    if collector_available:
        return replace(template, available=True, unavailable_reason=None, next_action=None, action_command=None)
    if template.required_plugin:
        return replace(
            template,
            available=False,
            unavailable_reason=_tdx_unavailable_reason(template.required_plugin),
            next_action=_tdx_next_action(template.required_plugin),
            action_command=f"axdata plugin enable {template.required_plugin}",
        )
    return replace(
        template,
        available=False,
        unavailable_reason=f"Collector {template.collector_name!r} is not available in the current registry.",
        next_action="检查 Provider registry 和插件状态。",
        action_command="axdata plugin collectors --json",
    )


def _registry_snapshot(*, data_root: str | Path | None = None) -> Any:
    from .provider_catalog import build_builtin_provider_registry
    from .collector_registry import build_collector_registry

    provider_registry = build_builtin_provider_registry(data_root=data_root)
    collector_snapshot = build_collector_registry(
        provider_registry=provider_registry,
        data_root=data_root,
    ).snapshot()

    class Snapshot:
        providers = provider_registry.snapshot().providers
        collectors = collector_snapshot.collectors

    return Snapshot()


def _template_unavailable_message(template: TaskTemplate) -> str:
    if template.required_plugin in {"axdata.source.tdx_external", "axdata.collector.tdx"}:
        return "请安装/启用 TDX 插件 (axdata.collector.tdx)"
    return template.unavailable_reason or "Collector dependency is not available."


def _tdx_unavailable_reason(provider_id: str) -> str:
    if provider_id == "axdata.source.tdx_external":
        return "请安装/启用 TDX 插件 (axdata.source.tdx_external)"
    if provider_id == "axdata.collector.tdx":
        return "请安装/启用 TDX 采集器插件 (axdata.collector.tdx)"
    return f"Provider {provider_id!r} is not enabled or not installed."


def _tdx_next_action(provider_id: str) -> str:
    if provider_id == "axdata.source.tdx_external":
        return "请安装/启用 TDX 插件 (axdata.source.tdx_external) 后再运行该任务。"
    if provider_id == "axdata.collector.tdx":
        return "请安装/启用 TDX 采集器插件 (axdata.collector.tdx) 后再运行该任务。"
    return "安装并启用对应 Provider 后再从模板创建任务。"
