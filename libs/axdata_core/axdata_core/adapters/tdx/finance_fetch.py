"""Compatibility wrapper for TDX finance fetch helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "CapitalChangeResult",
    "CapitalChangeRequestResult",
    "FinanceInfoResult",
    "finance_info_request_result",
    "capital_change_request_result",
    "DailyShareRequestResult",
    "daily_share_request_result",
    "capital_change_meta",
    "finance_info_result",
    "finance_info_rows",
    "daily_share_rows",
    "daily_share_meta",
    "capital_change_rows_by_tdx_code",
    "capital_change_result",
    "finance_rows_by_tdx_code",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_finance_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.finance_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.finance_fetch"}:
            return None
        raise


def _fallback_finance_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_finance_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_finance_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
