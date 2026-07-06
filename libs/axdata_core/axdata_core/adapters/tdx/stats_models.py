"""Compatibility wrapper for TDX statistics resource row models and parsers."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Iterable


_NO_PROVIDER = object()
_IMPLEMENTATION: ModuleType | object | None = None


def stats_resource_from_lines(
    stat_lines: Iterable[str],
    stat2_lines: Iterable[str],
    *,
    source_path: str,
    metadata: dict[str, object] | None = None,
):
    implementation = _implementation()
    if implementation is not None:
        return implementation.stats_resource_from_lines(
            stat_lines,
            stat2_lines,
            source_path=source_path,
            metadata=metadata,
        )
    return _fallback_stats_resource_from_lines(
        stat_lines,
        stat2_lines,
        source_path=source_path,
        metadata=metadata,
    )


def decode_lines(payload: bytes) -> list[str]:
    implementation = _implementation()
    if implementation is not None:
        return implementation.decode_lines(payload)
    return payload.decode("gbk", errors="ignore").splitlines()


def parse_stat_rows(lines: Iterable[str]):
    implementation = _implementation()
    if implementation is not None:
        return implementation.parse_stat_rows(lines)
    return _fallback_parse_stat_rows(lines)


def parse_stat2_rows(lines: Iterable[str]):
    implementation = _implementation()
    if implementation is not None:
        return implementation.parse_stat2_rows(lines)
    return _fallback_parse_stat2_rows(lines)


def text_value(value: str) -> str | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.text_value(value)
    text = value.strip()
    return text or None


def float_value(value: str) -> float | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.float_value(value)
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def int_value(value: str) -> int | None:
    implementation = _implementation()
    if implementation is not None:
        return implementation.int_value(value)
    number = _fallback_float_value(value)
    if number is None:
        return None
    return int(number)


def _fallback_stats_resource_from_lines(
    stat_lines: Iterable[str],
    stat2_lines: Iterable[str],
    *,
    source_path: str,
    metadata: dict[str, object] | None = None,
):
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_parse_stat_rows(lines: Iterable[str]):
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_parse_stat2_rows(lines: Iterable[str]):
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_text_value(value: str) -> str | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_float_value(value: str) -> float | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _fallback_int_value(value: str) -> int | None:
    from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

    raise_tdx_plugin_required()


def _provider_package_stats_models() -> ModuleType | None:
    try:
        return import_module("axdata_source_tdx.stats_models")
    except ModuleNotFoundError as exc:
        if exc.name in {"axdata_source_tdx", "axdata_source_tdx.stats_models"}:
            return None
        raise


def _implementation() -> ModuleType | None:
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        implementation = _provider_package_stats_models()
        _IMPLEMENTATION = implementation if implementation is not None else _NO_PROVIDER
    return None if _IMPLEMENTATION is _NO_PROVIDER else _IMPLEMENTATION  # type: ignore[return-value]


def __getattr__(name: str):
    if name in {"TdxStatRow", "TdxStat2Row", "TdxStatsResource"}:
        implementation = _implementation()
        if implementation is not None:
            value = getattr(implementation, name)
        else:
            from axdata_core.tdx_plugin_required import raise_tdx_plugin_required

            raise_tdx_plugin_required()
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
