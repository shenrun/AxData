"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.finance.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command/layout facts are exposed without loading the full finance
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.finance"
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
    "COMMAND_CODES",
    "FINANCE_INFO_BODY_SIZE",
    "FINANCE_INFO_RECORD_SIZE",
    "FinanceInfoBlock",
    "FinanceInfoRecord",
    "ID_TO_MARKET",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "TYPE_FINANCE_INFO",
    "annotations",
    "build_finance_info_frame",
    "date_from_yyyymmdd",
    "little_f32",
    "little_u16",
    "little_u32",
    "parse_finance_info_payload",
    "parse_finance_info_record",
    "split_code",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str) -> Any:
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "FINANCE_INFO_BODY_SIZE":
        value = _load_layout_impl().FINANCE_INFO_BODY_SIZE
    elif name == "FINANCE_INFO_RECORD_SIZE":
        value = _load_layout_impl().FINANCE_INFO_RECORD_SIZE
    elif name == "TYPE_FINANCE_INFO":
        value = _command_code("finance_info")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
