"""Compatibility shim for ``axdata_core._tdx_wire.protocol.commands.security``.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight classification helpers are exposed without loading the full security
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.security"
_PROVIDER_CLASSIFICATION_MODULE = "axdata_source_tdx._tdx_wire._security_classification"
_PROVIDER_LAYOUTS_MODULE = "axdata_source_tdx._tdx_wire._command_layouts"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_CLASSIFICATION_EXPORTS = {"classify_board", "classify_security"}
_LAYOUT_EXPORTS = {
    "CODE_RECORD_SIZE",
    "ETF_PREFIXES",
    "FUND_PREFIXES",
    "INDEX_PREFIXES",
    "SSE_A_SHARE_PREFIXES",
    "SZSE_A_SHARE_PREFIXES",
}
_COMMAND_CODE_EXPORTS = {
    "TYPE_SECURITY_COUNT": "security_count",
    "TYPE_SECURITY_LIST": "security_list",
}


_classification_impl = None
_layout_impl = None
_codes_impl = None
_command_impl = None


def _load_classification_impl():
    return load_provider_first_cached(
        globals(),
        "_classification_impl",
        _PROVIDER_CLASSIFICATION_MODULE,
    )


def _load_layout_impl():
    return load_provider_first_cached(
        globals(),
        "_layout_impl",
        _PROVIDER_LAYOUTS_MODULE,
    )


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _command_code(name: str) -> int:
    return _load_codes_impl().command_code(name)

__all__ = [
    "CODE_RECORD_SIZE",
    "ETF_PREFIXES",
    "FUND_PREFIXES",
    "INDEX_PREFIXES",
    "SSE_A_SHARE_PREFIXES",
    "SZSE_A_SHARE_PREFIXES",
    "TYPE_SECURITY_COUNT",
    "TYPE_SECURITY_LIST",
    "build_security_count_frame",
    "build_security_list_frame",
    "classify_board",
    "classify_security",
    "parse_security_count_payload",
    "parse_security_list_payload",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str):
    if name in _CLASSIFICATION_EXPORTS:
        value = getattr(_load_classification_impl(), name)
    elif name in _LAYOUT_EXPORTS:
        value = getattr(_load_layout_impl(), name)
    elif name in _COMMAND_CODE_EXPORTS:
        value = _command_code(_COMMAND_CODE_EXPORTS[name])
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
