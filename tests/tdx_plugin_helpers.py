from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from axdata_core.sources.base import RequestExample, RequestField, RequestParameter, SourceRequestInterface


REPO_ROOT = Path(__file__).resolve().parents[1]
TDX_PACKAGE_ROOT = REPO_ROOT / "packages" / "axdata-source-tdx"
TDX_EXT_PACKAGE_ROOT = REPO_ROOT / "packages" / "axdata-source-tdx-ext"
TDX_PROVIDER_ID = "axdata.source.tdx_external"
TDX_EXT_PROVIDER_ID = "axdata.source.tdx_ext_external"
TDX_COLLECTOR_PLUGIN_ID = "axdata.collector.tdx"
TDX_COLLECTOR_RUNNER_ENTRY = "axdata_source_tdx.collectors:run_tdx_collector"
TDX_BASE_COLLECTOR_DATASET_IDS = {
    "tdx.stock_codes_tdx.snapshot": "tdx.stock_codes",
    "tdx.stock_suspensions_tdx.snapshot": "tdx.stock_suspensions",
    "tdx.stock_st_list_tdx.snapshot": "tdx.stock_st_list",
    "tdx.stock_daily_share_tdx.snapshot": "tdx.stock_daily_share",
    "tdx.stock_daily_price_limit_tdx.snapshot": "tdx.stock_daily_price_limit",
    "tdx.stock_kline_daily_tdx.snapshot": "tdx.stock_daily",
    "tdx.stock_limit_ladder_tdx.snapshot": "tdx.stock_limit_ladder",
    "tdx.stock_theme_strength_rank_tdx.snapshot": "tdx.stock_theme_strength_rank",
}
TDX_LEGACY_COLLECTOR_NAMES: set[str] = set()


def ensure_local_tdx_plugin_paths() -> None:
    for package_root in (TDX_PACKAGE_ROOT, TDX_EXT_PACKAGE_ROOT):
        path = str(package_root / "src")
        if path not in sys.path:
            sys.path.insert(0, path)


def build_registry_with_local_tdx_plugins(*, base_builder: Any | None = None, **kwargs: Any):
    ensure_local_tdx_plugin_paths()

    from axdata_core.plugin_config import load_plugin_config
    from axdata_core.plugins import manifest_from_provider
    if base_builder is None:
        from axdata_core.provider_catalog import build_builtin_provider_registry as base_builder
    from axdata_source_tdx.provider import provider as tdx_provider
    from axdata_source_tdx_ext.provider import provider as tdx_ext_provider

    plugin_config = kwargs.get("plugin_config")
    data_root = kwargs.get("data_root")
    config = plugin_config or load_plugin_config(data_root=data_root)
    enabled_provider_ids = set(config.enabled_provider_ids)
    enabled_provider_ids.update({TDX_PROVIDER_ID, TDX_EXT_PROVIDER_ID})

    registry = base_builder(
        plugin_config=config,
        data_root=data_root,
        discover_entry_points=kwargs.get("discover_entry_points", True),
    )
    registry.enabled_provider_ids = enabled_provider_ids
    registry.register_manifest(
        manifest_from_provider(tdx_provider),
        provider=tdx_provider,
        enabled=TDX_PROVIDER_ID not in set(config.disabled_provider_ids),
        built_in=True,
    )
    registry.register_manifest(
        manifest_from_provider(tdx_ext_provider),
        provider=tdx_ext_provider,
        enabled=TDX_EXT_PROVIDER_ID not in set(config.disabled_provider_ids),
        built_in=True,
    )
    return registry


def local_tdx_plugin_interfaces() -> tuple[SourceRequestInterface, ...]:
    ensure_local_tdx_plugin_paths()

    from axdata_source_tdx.provider import provider as tdx_provider
    from axdata_source_tdx_ext.provider import provider as tdx_ext_provider

    return tuple(
        _legacy_interface_from_plugin(interface)
        for provider in (tdx_provider, tdx_ext_provider)
        for interface in provider.interfaces()
    )


def local_tdx_plugin_interface_map() -> dict[str, SourceRequestInterface]:
    return {interface.name: interface for interface in local_tdx_plugin_interfaces()}


def local_request_interface_catalog() -> dict[str, SourceRequestInterface]:
    from axdata_core.sources import list_request_interfaces

    return {
        interface.name: interface
        for interface in (*local_tdx_plugin_interfaces(), *list_request_interfaces())
    }


def local_request_interfaces() -> tuple[SourceRequestInterface, ...]:
    return tuple(local_request_interface_catalog().values())


def local_request_interface_names() -> tuple[str, ...]:
    return tuple(local_request_interface_catalog())


def local_request_interface_dicts() -> tuple[dict[str, Any], ...]:
    return tuple(interface.to_dict() for interface in local_request_interfaces())


def local_tdx_plugin_interface_dicts() -> tuple[dict[str, Any], ...]:
    return tuple(interface.to_dict() for interface in local_tdx_plugin_interfaces())


def _legacy_interface_from_plugin(interface: Any) -> SourceRequestInterface:
    example = interface.examples[0] if interface.examples else None
    request = dict(getattr(example, "request", {}) or {}) if example is not None else {}
    response_payload = dict(getattr(example, "response", {}) or {}) if example is not None else {}
    response_rows = response_payload.get("data", response_payload)
    if not isinstance(response_rows, list):
        response_rows = []

    return SourceRequestInterface(
        name=interface.name,
        display_name_zh=interface.display_name_zh,
        source_code=interface.source_code,
        source_name_zh=interface.source_name_zh,
        category=interface.category or (interface.menu_path[-1] if interface.menu_path else ""),
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
        example=RequestExample(
            request=request,
            response=tuple(dict(row) for row in response_rows),
        ),
        source_ability=_source_ability_from_plugin(interface),
        description=interface.notes,
    )


def _source_ability_from_plugin(interface: Any) -> str:
    if str(getattr(interface, "source_code", "") or "") == "tdx_ext":
        return "TDX extended asset cache/provider"
    name = str(getattr(interface, "name", "") or "")
    marker_by_name = {
        "stock_realtime_rank_tdx": "0x054b",
        "stock_limit_ladder_tdx": "0x054b tdxstat",
        "stock_theme_strength_rank_tdx": "0x054b tdxstat",
        "stock_auction_result_tdx": "0x0fc5",
        "stock_auction_result_history_tdx": "0x0fc6",
        "stock_shortline_indicators_tdx": "tdxstat",
        "stock_intraday_recent_history_tdx": "0x0feb",
        "stock_intraday_today_tdx": "0x0537",
    }
    ability = "TDX 7709 provider"
    if name in marker_by_name:
        ability += f" {marker_by_name[name]}"
    return ability
