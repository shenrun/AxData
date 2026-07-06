"""Compatibility wrapper for TDX limit-ladder style fetch helpers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any as _Any


_EXPORTS = (
    "LimitLadderSourceRowsResult",
    "LimitLadderTopicLookupResult",
    "LimitLadderRequestResult",
    "ThemeStrengthRequestResult",
    "limit_ladder_request_result",
    "theme_strength_request_result",
    "limit_ladder_meta",
    "theme_strength_meta",
    "prepare_limit_ladder_source_rows",
    "lookup_limit_ladder_topics",
    "limit_ladder_candidate_tdx_codes",
    "limit_ladder_rows_from_rank_rows",
    "security_names_by_tdx_code",
    "request_limit_ladder_rank_rows",
)
__all__ = list(_EXPORTS)
_IMPLEMENTATION: ModuleType | None = None


def _provider_package_limit_ladder_fetch() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.limit_ladder_fetch")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.limit_ladder_fetch"}:
            return None
        raise


def _fallback_limit_ladder_fetch() -> ModuleType:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _implementation() -> ModuleType:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_limit_ladder_fetch()
        _IMPLEMENTATION = implementation if implementation is not None else _fallback_limit_ladder_fetch()
    return _IMPLEMENTATION


def __getattr__(name: str) -> _Any:
    try:
        value = getattr(_implementation(), name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name in _EXPORTS:
        globals()[name] = value
    return value
