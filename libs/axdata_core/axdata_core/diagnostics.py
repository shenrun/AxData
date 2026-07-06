"""Local AxData setup and diagnostics helpers."""

from __future__ import annotations

import importlib
import os
import platform
import socket
import sys
import uuid
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping

from .paths import DATA_LAYERS, AxDataPaths
from .plugin_config import load_plugin_config, plugin_config_path, save_plugin_config
from .plugin_status import (
    TDX_EXT_PROVIDER_ID,
    TDX_PROVIDER_ID,
    expected_provider_statuses,
    managed_provider_ids,
    provider_status_row,
)

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8666
DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = 8667
TDX_PROVIDER_IDS = (TDX_PROVIDER_ID, TDX_EXT_PROVIDER_ID)


def resolve_data_root(data_root: str | Path | None = None) -> Path:
    """Resolve AxData's local data root."""

    return Path(data_root or os.getenv("AXDATA_DATA_DIR", "data")).expanduser().resolve()


def metadata_root(data_root: str | Path | None = None) -> Path:
    """Return the metadata directory paired with the data root."""

    return resolve_data_root(data_root).parent / "metadata"


def cache_root(data_root: str | Path | None = None) -> Path:
    """Return the cache directory paired with the data root."""

    return resolve_data_root(data_root).parent / "cache"


def logs_root(data_root: str | Path | None = None) -> Path:
    """Return the logs directory paired with the data root."""

    return resolve_data_root(data_root).parent / "logs"


def initialize_local_environment(data_root: str | Path | None = None) -> dict[str, Any]:
    """Create the local directory skeleton and default plugin config if missing."""

    root = resolve_data_root(data_root)
    paths = AxDataPaths(root)
    created: list[str] = []
    existing: list[str] = []

    for path in [
        *[getattr(paths, layer) for layer in DATA_LAYERS],
        metadata_root(root),
        metadata_root(root) / "collector",
        cache_root(root),
        logs_root(root),
        plugin_directory(root),
        plugin_site_packages(root),
    ]:
        path = path.resolve()
        if path.exists():
            existing.append(str(path))
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))

    config_path = plugin_config_path(data_root=root)
    config_created = False
    if not config_path.exists():
        save_plugin_config(load_plugin_config(data_root=root), data_root=root)
        config_created = True
        created.append(str(config_path))
    else:
        existing.append(str(config_path))

    return {
        "data_root": str(root),
        "metadata_root": str(metadata_root(root)),
        "plugin_config_path": str(config_path),
        "plugin_site_packages": str(plugin_site_packages(root)),
        "created": sorted(created),
        "existing": sorted(existing),
        "config_created": config_created,
    }


def local_config(data_root: str | Path | None = None) -> dict[str, Any]:
    """Return resolved local configuration paths and startup defaults."""

    root = resolve_data_root(data_root)
    api_host = os.getenv("AXDATA_API_HOST", DEFAULT_API_HOST)
    api_port = _int_env("AXDATA_API_PORT", DEFAULT_API_PORT)
    web_port = _int_env("AXDATA_WEB_PORT", DEFAULT_WEB_PORT)
    local_api_host = "127.0.0.1" if api_host == "0.0.0.0" else api_host
    local_api_base = f"http://{local_api_host}:{api_port}"
    return {
        "data_root": str(root),
        "raw_dir": str(AxDataPaths(root).raw),
        "staging_dir": str(AxDataPaths(root).staging),
        "core_dir": str(AxDataPaths(root).core),
        "factor_dir": str(AxDataPaths(root).factor),
        "metadata_root": str(metadata_root(root)),
        "cache_root": str(cache_root(root)),
        "logs_root": str(logs_root(root)),
        "plugin_config_path": str(plugin_config_path(data_root=root)),
        "plugin_dir": str(plugin_directory(root)),
        "plugin_site_packages": str(plugin_site_packages(root)),
        "collector_store_path": str(collector_store_path(root)),
        "api_host": api_host,
        "api_port": api_port,
        "api_base": local_api_base,
        "local_api_base": local_api_base,
        "listen_api_base": f"http://{api_host}:{api_port}",
        "web_host": DEFAULT_WEB_HOST,
        "web_port": web_port,
        "web_base": f"http://{DEFAULT_WEB_HOST}:{web_port}",
        "auth_enabled": bool(os.getenv("AXDATA_API_TOKEN")),
        "env": {
            "AXDATA_DATA_DIR": os.getenv("AXDATA_DATA_DIR"),
            "AXDATA_PLUGIN_CONFIG_PATH": os.getenv("AXDATA_PLUGIN_CONFIG_PATH"),
            "AXDATA_PLUGIN_INSTALL_ROOT": os.getenv("AXDATA_PLUGIN_INSTALL_ROOT"),
        },
    }


def build_local_diagnostics(data_root: str | Path | None = None) -> dict[str, Any]:
    """Build a local, offline diagnostic report for CLI/API users."""

    root = resolve_data_root(data_root)
    config = local_config(root)
    dependency_checks = _dependency_checks()
    registry_report = _registry_report(root)
    collector_report = _collector_report(root)
    smoke_report = _real_source_smoke_report(registry_report)
    checks = [
        *_path_checks(root),
        *dependency_checks,
        registry_report["check"],
        *_port_checks(),
        smoke_report["check"],
    ]
    if collector_report.get("check"):
        checks.append(collector_report["check"])

    summary = _summary(checks)
    return {
        "summary": summary,
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "axdata": {
            "version": _package_version("axdata-core") or _package_version("axdata-workspace") or "0.1.0",
            "package": "axdata-core",
        },
        "config": config,
        "checks": checks,
        "dependencies": dependency_checks,
        "registry": registry_report["registry"],
        "plugins": registry_report["plugins"],
        "tdx": registry_report["tdx"],
        "ports": [check for check in checks if check["category"] == "ports"],
        "collector": collector_report["collector"],
        "real_source_smoke": smoke_report["smoke"],
        "next_actions": _next_actions(checks, registry_report, collector_report),
    }


def provider_guidance(
    *,
    provider_id: str,
    source_code: str,
    status: str,
    enabled: bool,
    built_in: bool,
    error: str = "",
) -> dict[str, str | None]:
    """Return user-facing status guidance for a Provider registry row."""

    is_tdx = provider_id == TDX_PROVIDER_ID or source_code == "tdx"
    is_tdx_ext = provider_id == TDX_EXT_PROVIDER_ID or source_code == "tdx_ext"
    if status == "enabled" and enabled:
        return {
            "status_message": (
                "Provider 已启用，并参与接口路由。"
                if not built_in
                else "预装插件已启用，并参与接口路由。"
            ),
            "next_action": None,
            "action_command": None,
        }
    if status == "uninstalled":
        return {
            "status_message": "预装插件已从当前 AxData 管理状态移除；相关接口、下载器、采集器和任务模板不会参与路由。",
            "next_action": "需要恢复该数据源时，重新启用预装插件；已采集数据和 run history 不会被删除。",
            "action_command": f"axdata plugin enable {provider_id}",
        }
    if status == "failed":
        lower_error = error.lower()
        if "manifest" in lower_error or "axdata-provider" in lower_error or "axdata-plugin" in lower_error:
            message = f"插件 manifest 不可发现或不可读取：{error}"
            next_action = "重新安装插件包，或检查 wheel/AXP 是否包含 axdata-provider.json 或 axdata-plugin.json。"
        else:
            message = f"插件发现失败：{error}"
            next_action = "检查插件包安装、entry point 和本地 Python 环境。"
        return {
            "status_message": message,
            "next_action": next_action,
            "action_command": None,
        }
    if status == "incompatible":
        return {
            "status_message": f"插件协议版本不兼容：{error}",
            "next_action": "升级 AxData 或安装兼容当前 plugin_api_version 的插件版本。",
            "action_command": None,
        }
    if status == "conflict":
        return {
            "status_message": f"插件接口或采集器冲突：{error}",
            "next_action": "禁用冲突 Provider，或为冲突接口设置本地 override。",
            "action_command": None,
        }
    if status == "disabled" or not enabled:
        if is_tdx_ext:
            return {
                "status_message": "TDX Ext 扩展行情插件已安装但未启用；扩展行情接口不会参与路由。",
                "next_action": "需要期货、期权、基金、债券、外汇、宏观等扩展行情接口时，显式启用 TDX Ext 扩展行情插件。",
                "action_command": f"axdata plugin enable {provider_id}",
            }
        if is_tdx:
            return {
                "status_message": "TDX 插件已安装但未启用；TDX 接口不会参与路由。",
                "next_action": "需要 TDX 接口时，显式启用 TDX 插件。",
                "action_command": f"axdata plugin enable {provider_id}",
            }
        return {
            "status_message": "插件已禁用；不会参与接口路由或 Collector 能力列表。",
            "next_action": "确认来源和依赖后，可显式启用该 Provider。",
            "action_command": f"axdata plugin enable {provider_id}",
        }
    return {
        "status_message": error or f"Provider 状态为 {status}。",
        "next_action": "运行 `axdata doctor` 或 `axdata plugin info <provider_id> --json` 查看详情。",
        "action_command": None,
    }


def plugin_directory(data_root: str | Path | None = None) -> Path:
    try:
        from .axp import AXP_PLUGINS_DIR_NAME
    except Exception:
        name = "plugins"
    else:
        name = AXP_PLUGINS_DIR_NAME
    root = resolve_data_root(data_root)
    env_root = os.getenv("AXDATA_PLUGIN_INSTALL_ROOT", "").strip()
    return Path(env_root).expanduser().resolve() if env_root else root.parent / name


def plugin_site_packages(data_root: str | Path | None = None) -> Path:
    try:
        from .axp import axp_plugin_site_packages

        return axp_plugin_site_packages(data_root=resolve_data_root(data_root))
    except Exception:
        return plugin_directory(data_root) / "site-packages"


def collector_store_path(data_root: str | Path | None = None) -> Path:
    from .collector_scheduler import collector_scheduler_store_path

    return collector_scheduler_store_path(data_root=resolve_data_root(data_root))


def _path_checks(data_root: Path) -> list[dict[str, Any]]:
    paths = AxDataPaths(data_root)
    targets = [
        ("data_root", paths.root),
        ("raw_dir", paths.raw),
        ("staging_dir", paths.staging),
        ("core_dir", paths.core),
        ("factor_dir", paths.factor),
        ("metadata_root", metadata_root(data_root)),
        ("collector_metadata_dir", collector_store_path(data_root).parent),
        ("plugin_dir", plugin_directory(data_root)),
        ("plugin_site_packages", plugin_site_packages(data_root)),
        ("cache_root", cache_root(data_root)),
        ("logs_root", logs_root(data_root)),
    ]
    return [_path_check(name, path) for name, path in targets]


def _path_check(name: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    writable = _path_writable(path)
    if exists and writable:
        status = "ok"
        message = "exists and is writable"
    elif exists:
        status = "error"
        message = "exists but is not writable"
    else:
        status = "warning"
        message = "missing; run `axdata init` to create it"
    return {
        "category": "paths",
        "name": name,
        "status": status,
        "path": str(path),
        "exists": exists,
        "writable": writable,
        "message": message,
    }


def _path_writable(path: Path) -> bool:
    target_dir = path if path.exists() and path.is_dir() else path.parent
    if not target_dir.exists():
        return False
    probe = target_dir / f".axdata_write_probe_{os.getpid()}_{uuid.uuid4().hex}"
    try:
        probe.write_text("ok", encoding="utf-8")
        return True
    except OSError:
        return False
    finally:
        probe.unlink(missing_ok=True)


def _dependency_checks() -> list[dict[str, Any]]:
    checks = []
    for module_name, package_name, purpose in (
        ("duckdb", "duckdb", "DuckDB local query engine"),
        ("pyarrow", "pyarrow", "Parquet read/write support"),
        ("pandas", "pandas", "DataFrame and Parquet helpers"),
        ("fastapi", "fastapi", "HTTP API server"),
        ("uvicorn", "uvicorn", "local API startup"),
    ):
        checks.append(_module_check(module_name, package_name, purpose))
    return checks


def _module_check(module_name: str, package_name: str, purpose: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {
            "category": "dependencies",
            "name": package_name,
            "status": "error",
            "available": False,
            "message": f"{purpose} is unavailable: {exc}",
        }
    version = getattr(module, "__version__", None) or _package_version(package_name)
    return {
        "category": "dependencies",
        "name": package_name,
        "status": "ok",
        "available": True,
        "version": version,
        "message": f"{purpose} is available",
    }


def _registry_report(data_root: Path) -> dict[str, Any]:
    try:
        from .provider_catalog import build_builtin_provider_registry

        config = load_plugin_config(data_root=data_root)
        registry = build_builtin_provider_registry(data_root=data_root)
        snapshot = registry.snapshot()
    except Exception as exc:
        return {
            "check": {
                "category": "registry",
                "name": "provider_registry",
                "status": "error",
                "message": f"ProviderRegistry failed to load: {exc}",
            },
            "registry": {"loaded": False, "error": str(exc)},
            "plugins": {"providers": [], "installed": []},
            "tdx": _tdx_missing_report(),
        }

    managed_ids = managed_provider_ids(data_root=data_root)
    providers = [
        provider_status_row(
            provider,
            snapshot=snapshot,
            provider_overrides=getattr(registry, "provider_overrides", {}),
            managed_provider_ids=managed_ids,
            removed_provider_ids=getattr(config, "removed_provider_ids", ()),
        )
        for provider in registry.list_providers()
    ]
    providers.extend(expected_provider_statuses(provider["provider_id"] for provider in providers))
    ignored_candidates = [candidate.to_dict() for candidate in snapshot.ignored_candidates]
    installed = _installed_plugins(data_root)
    status_counts = _count_by(providers, "status")
    tdx = _tdx_report(providers)
    return {
        "check": {
            "category": "registry",
            "name": "provider_registry",
            "status": "ok",
            "message": (
                f"loaded {len(providers)} providers, "
                f"{len(snapshot.interfaces)} interfaces, {len(snapshot.collectors)} collectors"
            ),
        },
        "registry": {
            "loaded": True,
            "provider_count": len(providers),
            "enabled_provider_count": status_counts.get("enabled", 0),
            "interface_count": len(snapshot.interfaces),
            "collector_count": len(snapshot.collectors),
            "ignored_candidate_count": len(ignored_candidates),
            "status_counts": status_counts,
        },
        "plugins": {
            "providers": providers,
            "ignored_candidates": ignored_candidates,
            "installed": installed,
            "installed_count": len(installed),
            "enabled_provider_ids": sorted(
                provider["provider_id"] for provider in providers if provider["enabled"]
            ),
            "disabled_provider_ids": sorted(
                provider["provider_id"] for provider in providers if provider["status"] == "disabled"
            ),
            "failed_provider_ids": sorted(
                provider["provider_id"]
                for provider in providers
                if provider["status"] in {"failed", "incompatible", "conflict"}
            ),
        },
        "tdx": tdx,
    }


def _installed_plugins(data_root: Path) -> list[dict[str, Any]]:
    try:
        from .axp import list_installed_axp_plugins

        return [plugin.to_dict() for plugin in list_installed_axp_plugins(data_root=data_root)]
    except Exception as exc:
        return [{"provider_id": "axdata.plugins", "status": "failed", "error": str(exc)}]


def _tdx_report(providers: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        provider
        for provider in providers
        if provider["provider_id"] in TDX_PROVIDER_IDS
        or provider["source_code"] in {"tdx", "tdx_ext"}
        or any(str(name).endswith("_tdx") for name in provider.get("interfaces", []))
    ]
    if not matches:
        return _tdx_missing_report()

    quote_matches = [
        provider
        for provider in matches
        if provider["provider_id"] == TDX_PROVIDER_ID or provider["source_code"] == "tdx"
    ]
    ext_matches = [
        provider
        for provider in matches
        if provider["provider_id"] == TDX_EXT_PROVIDER_ID or provider["source_code"] == "tdx_ext"
    ]
    quote_enabled = any(provider["enabled"] and provider["status"] == "enabled" for provider in quote_matches)
    ext_enabled = any(provider["enabled"] and provider["status"] == "enabled" for provider in ext_matches)
    quote_problem = next((provider for provider in quote_matches if provider["status"] != "enabled"), None)
    ext_problem = next((provider for provider in ext_matches if provider["status"] != "enabled"), None)
    enabled = [provider for provider in matches if provider["enabled"] and provider["status"] == "enabled"]
    failed = [
        provider
        for provider in matches
        if provider["status"] in {"failed", "incompatible", "conflict"}
    ]
    missing = [provider for provider in matches if provider["status"] == "missing"]
    if quote_enabled and ext_enabled:
        status_value = "enabled"
        message = "TDX 普通行情和 TDX Ext 扩展行情插件均已安装并启用。"
    elif quote_enabled and ext_problem is not None:
        status_value = "partial"
        message = "TDX 普通行情已启用；TDX Ext 扩展行情未安装或未启用，扩展行情接口不会出现在运行目录。"
    elif ext_enabled and quote_problem is not None:
        status_value = "partial"
        message = "TDX Ext 扩展行情已启用；TDX 普通行情未安装或未启用，普通 TDX 接口不可用。"
    elif enabled:
        status_value = "partial"
        message = "部分 TDX Provider 已启用；请检查普通 TDX 与 TDX Ext 扩展行情是否都符合预期。"
    elif failed:
        status_value = "failed"
        message = "TDX plugin is installed but not usable; inspect provider error."
    elif missing and len(missing) == len(matches):
        status_value = "missing"
        message = "TDX 普通行情和 TDX Ext 扩展行情插件未安装或当前 Python 环境不可发现。"
    elif missing:
        status_value = "partial"
        message = "部分 TDX Provider 未安装或当前 Python 环境不可发现；请检查普通 TDX 与 TDX Ext 扩展行情。"
    else:
        status_value = "disabled"
        message = "TDX plugin is installed but not enabled."
    return {
        "status": status_value,
        "installed": len(missing) < len(matches),
        "enabled": bool(enabled),
        "quote_enabled": quote_enabled,
        "extended_enabled": ext_enabled,
        "manifest_discoverable": True,
        "providers": matches,
        "message": message,
    }


def _tdx_missing_report() -> dict[str, Any]:
    return {
        "status": "missing",
        "installed": False,
        "enabled": False,
        "manifest_discoverable": False,
        "providers": [],
        "message": "TDX 插件未安装或不可用，请安装并启用 TDX 插件。",
    }


def _port_checks() -> list[dict[str, Any]]:
    api_host = os.getenv("AXDATA_API_HOST", DEFAULT_API_HOST)
    api_port = _int_env("AXDATA_API_PORT", DEFAULT_API_PORT)
    web_port = _int_env("AXDATA_WEB_PORT", DEFAULT_WEB_PORT)
    return [
        _port_check("api", api_host, api_port),
        _port_check("web", DEFAULT_WEB_HOST, web_port),
    ]


def _port_check(name: str, host: str, port: int) -> dict[str, Any]:
    occupied = _port_is_occupied(host, port)
    return {
        "category": "ports",
        "name": name,
        "status": "warning" if occupied else "ok",
        "host": host,
        "port": port,
        "occupied": occupied,
        "message": (
            f"{host}:{port} appears occupied; choose another port with AXDATA_{name.upper()}_PORT"
            if occupied
            else f"{host}:{port} appears available"
        ),
    }


def _port_is_occupied(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, int(port))) == 0


def _collector_report(data_root: Path) -> dict[str, Any]:
    from .collector_scheduler import CollectorSchedulerStore

    store = CollectorSchedulerStore(data_root=data_root)
    try:
        tasks = [task.to_dict() for task in store.list_tasks()]
        runs = [run.to_dict() for run in store.list_runs(limit=20)]
        active_runs = [run.to_dict() for run in store.active_runs()]
    except Exception as exc:
        return {
            "check": {
                "category": "collector",
                "name": "collector_store",
                "status": "error",
                "path": str(store.path),
                "message": f"collector metadata cannot be read: {exc}",
            },
            "collector": {"store_path": str(store.path), "error": str(exc)},
        }

    failed_runs = [run for run in runs if run["status"] == "failed"]
    check_status = "ok" if not failed_runs else "warning"
    check_message = (
        "collector metadata is readable"
        if not failed_runs
        else f"{len(failed_runs)} recent collector run(s) failed"
    )
    return {
        "check": {
            "category": "collector",
            "name": "collector_store",
            "status": check_status,
            "path": str(store.path),
            "message": check_message,
        },
        "collector": {
            "store_path": str(store.path),
            "task_count": len(tasks),
            "enabled_task_count": sum(1 for task in tasks if task["enabled"]),
            "run_count_recent": len(runs),
            "active_run_count": len(active_runs),
            "tasks": tasks,
            "active_runs": active_runs,
            "recent_runs": runs,
            "recent_failed_runs": failed_runs[:5],
        },
    }


def _real_source_smoke_report(registry_report: Mapping[str, Any]) -> dict[str, Any]:
    tdx = registry_report.get("tdx", {})
    can_run_tdx = bool(tdx.get("enabled"))
    smoke = {
        "script": "scripts/smoke_real_sources.py",
        "default_mode": "dry-skip/offline",
        "requires_explicit_run": True,
        "can_run_builtin_exchange_smoke": True,
        "can_run_tdx_smoke": can_run_tdx,
        "tdx_requirement": "install and enable TDX plugin before running daily smoke",
        "example": (
            ".venv\\Scripts\\python scripts\\smoke_real_sources.py --run "
            "--interfaces stock_basic_exchange trade_cal daily --json "
            "--output-dir %TEMP%\\axdata-real-source-smoke"
        ),
    }
    return {
        "check": {
            "category": "smoke",
            "name": "real_source_smoke",
            "status": "ok" if can_run_tdx else "warning",
            "message": (
                "real source smoke can include TDX interfaces"
                if can_run_tdx
                else "real source smoke is optional; TDX items require an installed and enabled TDX plugin"
            ),
        },
        "smoke": smoke,
    }


def _summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _count_by(checks, "status")
    status = "ok"
    if counts.get("error", 0):
        status = "error"
    elif counts.get("warning", 0):
        status = "warning"
    return {
        "status": status,
        "ok": counts.get("ok", 0),
        "warning": counts.get("warning", 0),
        "error": counts.get("error", 0),
    }


def _next_actions(
    checks: list[dict[str, Any]],
    registry_report: Mapping[str, Any],
    collector_report: Mapping[str, Any],
) -> list[str]:
    actions: list[str] = []
    if any(check["category"] == "paths" and check["status"] != "ok" for check in checks):
        actions.append("Run `axdata init` to create missing local directories and default config.")
    if any(check["category"] == "dependencies" and check["status"] == "error" for check in checks):
        actions.append("Install missing Python dependencies, for example `pip install -e .[dev]`.")
    tdx = registry_report.get("tdx", {})
    if tdx.get("status") == "missing":
        actions.append("Install and enable the TDX plugin before using TDX interfaces.")
    elif tdx.get("status") == "partial" and not tdx.get("extended_enabled"):
        actions.append("Install and enable the TDX Ext plugin before using extended-market interfaces.")
    elif tdx.get("status") == "partial" and not tdx.get("quote_enabled"):
        actions.append("Install and enable the TDX plugin before using ordinary TDX quote interfaces.")
    elif tdx.get("status") == "disabled":
        provider_id = tdx.get("providers", [{}])[0].get("provider_id", "axdata.source.tdx_external")
        actions.append(f"Enable TDX with `axdata plugin enable {provider_id}` when you need TDX interfaces.")
    if collector_report.get("collector", {}).get("recent_failed_runs"):
        actions.append("Inspect `axdata collector run list --status failed --json` for recent collector failures.")
    if not actions:
        actions.append("Start the API with `npm run dev:api` or uvicorn, then start Web with `npm run dev:web`.")
    return actions


def _manifest_display_name(manifest: Any) -> str:
    if getattr(manifest, "provider", None) is not None:
        return manifest.provider.source_name_zh
    if getattr(manifest, "plugin", None) is not None:
        return manifest.plugin.name_zh
    return "未知插件"


def _manifest_version(manifest: Any) -> str:
    if getattr(manifest, "provider", None) is not None:
        return manifest.provider.version
    if getattr(manifest, "plugin", None) is not None:
        return manifest.plugin.version
    return "0.0.0"


def _package_version(package_name: str) -> str | None:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _count_by(rows: list[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field) or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts
