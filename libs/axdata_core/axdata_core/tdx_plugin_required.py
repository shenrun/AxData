"""Shared TDX plugin availability helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

from .source_errors import SourceUnavailableError

TDX_PLUGIN_REQUIRED_MESSAGE = "TDX 插件未安装或不可用，请安装并启用 TDX 插件。"


def raise_tdx_plugin_required() -> None:
    raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE)


def missing_tdx_provider_module(exc: ModuleNotFoundError, module_name: str) -> bool:
    """Return whether a ModuleNotFoundError means the TDX plugin is missing."""

    missing = str(exc.name or "")
    root = module_name.split(".", 1)[0]
    return missing == root or missing == module_name or missing.startswith(f"{root}.")


def load_tdx_provider_module(module_name: str) -> ModuleType:
    """Load one module from the TDX plugin or raise the shared availability error."""

    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        if missing_tdx_provider_module(exc, module_name):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise


def empty_downloader_profile_declarations(
    concurrency_profile_cls: type[Any],
    downloader_profile_cls: type[Any],
) -> dict[str, Any]:
    """Downloader declarations shape used when the TDX plugin is absent."""

    return {}
