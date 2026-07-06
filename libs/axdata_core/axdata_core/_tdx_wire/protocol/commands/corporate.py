"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.corporate.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command/layout facts are exposed without loading the full corporate
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.corporate"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_PROVIDER_LAYOUTS_MODULE = "axdata_source_tdx._tdx_wire._command_layouts"


_codes_impl = None
_layout_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _load_layout_impl():
    return load_provider_first_cached(
        globals(),
        "_layout_impl",
        _PROVIDER_LAYOUTS_MODULE,
    )


def _command_codes() -> dict[str, int]:
    command_codes = _load_codes_impl().COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def _command_code(name: str) -> int:
    return _load_codes_impl().command_code(name)

__all__ = [
    "Any",
    "CAPITAL_CHANGE_CATEGORY_NAMES",
    "CAPITAL_CHANGE_RECORD_SIZE",
    "COMMAND_CODES",
    "CapitalChangeBlock",
    "CapitalChangeRecord",
    "ID_TO_MARKET",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "TYPE_CAPITAL_CHANGES",
    "annotations",
    "build_capital_changes_frame",
    "date_from_yyyymmdd",
    "little_f32",
    "little_u16",
    "little_u32",
    "market_to_id",
    "normalize_code",
    "parse_capital_changes_payload",
    "split_code",
    "tdx_quantity_u32",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str) -> Any:
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "CAPITAL_CHANGE_CATEGORY_NAMES":
        value = _load_layout_impl().CAPITAL_CHANGE_CATEGORY_NAMES
    elif name == "CAPITAL_CHANGE_RECORD_SIZE":
        value = _load_layout_impl().CAPITAL_CHANGE_RECORD_SIZE
    elif name == "TYPE_CAPITAL_CHANGES":
        value = _command_code("capital_changes")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
