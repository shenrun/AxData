"""Shared provider-only shim helpers for legacy core TDX wire imports."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

from axdata_core.tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE
from axdata_core.source_errors import SourceUnavailableError


def _is_missing_tdx_provider(exc: ModuleNotFoundError, provider_module: str) -> bool:
    missing_name = str(exc.name)
    return exc.name in {"axdata_source_tdx", provider_module} or missing_name.startswith("axdata_source_tdx.")


def load_provider_module(provider_module: str) -> ModuleType:
    """Load the provider-owned wire module or raise a clear plugin error."""

    try:
        return import_module(provider_module)
    except ModuleNotFoundError as exc:
        if _is_missing_tdx_provider(exc, provider_module):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        raise


def load_provider_module_cached(
    module_globals: dict[str, Any],
    cache_name: str,
    provider_module: str,
) -> ModuleType:
    """Load and cache a provider-owned implementation inside a shim module."""

    implementation = module_globals.get(cache_name)
    if implementation is None:
        implementation = load_provider_module(provider_module)
        module_globals[cache_name] = implementation
    return implementation


def install_provider_module(
    module_globals: dict[str, Any],
    *,
    provider_module: str,
) -> ModuleType:
    """Populate a legacy shim module from its provider-owned implementation."""

    implementation = load_provider_module(provider_module)
    exports = list(getattr(implementation, "__all__", [name for name in dir(implementation) if not name.startswith("_")]))

    module_globals["_impl"] = implementation
    module_globals["__all__"] = exports
    for name in exports:
        module_globals[name] = getattr(implementation, name)

    def __getattr__(name: str) -> Any:
        return getattr(implementation, name)

    def __dir__() -> list[str]:
        return sorted(set(module_globals) | set(dir(implementation)))

    module_globals["__getattr__"] = __getattr__
    module_globals["__dir__"] = __dir__
    return implementation


def install_lazy_provider_module(
    module_globals: dict[str, Any],
    *,
    provider_module: str,
    exports: list[str],
) -> None:
    """Install a provider-owned shim that loads the implementation on demand."""

    export_names = list(exports)
    module_globals["_impl"] = None
    module_globals["__all__"] = export_names

    def _load_impl() -> ModuleType:
        implementation = module_globals.get("_impl")
        if implementation is None:
            implementation = load_provider_module(provider_module)
            module_globals["_impl"] = implementation
        return implementation

    def __getattr__(name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"module {module_globals.get('__name__')!r} has no attribute {name!r}")
        value = getattr(_load_impl(), name)
        if name in export_names:
            module_globals[name] = value
        return value

    def __dir__() -> list[str]:
        implementation = module_globals.get("_impl")
        names = set(module_globals) | set(export_names)
        if implementation is not None:
            names |= set(dir(implementation))
        return sorted(names)

    module_globals["_load_impl"] = _load_impl
    module_globals["__getattr__"] = __getattr__
    module_globals["__dir__"] = __dir__


# Backward-compatible helper names for existing shim modules. The fallback
# argument is accepted but ignored; core no longer contains a runnable TDX wire
# fallback.
def load_provider_first(provider_module: str, fallback_module: str | None = None) -> ModuleType:
    return load_provider_module(provider_module)


def load_provider_first_cached(
    module_globals: dict[str, Any],
    cache_name: str,
    provider_module: str,
    fallback_module: str | None = None,
) -> ModuleType:
    return load_provider_module_cached(module_globals, cache_name, provider_module)


def install_provider_first(
    module_globals: dict[str, Any],
    *,
    provider_module: str,
    fallback_module: str | None = None,
) -> ModuleType:
    return install_provider_module(module_globals, provider_module=provider_module)


def install_lazy_provider_first(
    module_globals: dict[str, Any],
    *,
    provider_module: str,
    fallback_module: str | None = None,
    exports: list[str],
) -> None:
    install_lazy_provider_module(module_globals, provider_module=provider_module, exports=exports)
