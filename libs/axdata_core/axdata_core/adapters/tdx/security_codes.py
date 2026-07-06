"""Compatibility wrapper for TDX security code-list helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "ASSET_TYPE_MAP",
    "BOARD_MAP",
    "SCOPE_TO_BOARDS",
    "normalize_security",
    "board_from_tdx_code",
    "index_type_from_tdx_code",
    "etf_type_from_tdx_code",
    "normalize_index_code_row",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_security_codes() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.security_codes")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.security_codes"}:
            return None
        raise


def _fallback_security_codes() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_security_codes()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_security_codes()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
