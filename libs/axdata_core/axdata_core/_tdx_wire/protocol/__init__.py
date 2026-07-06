"""Compatibility shim for ``axdata_core._tdx_wire.protocol``.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from .._shim import load_provider_first


_EXPORT_MODULES = {
    "COMMANDS": "axdata_source_tdx._tdx_wire._command_registry",
    "CommandSpec": "axdata_source_tdx._tdx_wire._command_registry",
    "build_command_frame": "axdata_source_tdx._tdx_wire._command_codec",
    "command_code": "axdata_source_tdx._tdx_wire._command_lookup",
    "parse_command_response": "axdata_source_tdx._tdx_wire._command_codec",
    "required_commands": "axdata_source_tdx._tdx_wire._command_registry",
    "RequestFrame": "axdata_source_tdx._tdx_wire.protocol.frame",
    "ResponseFrame": "axdata_source_tdx._tdx_wire.protocol.frame",
    "decode_response": "axdata_source_tdx._tdx_wire.protocol.frame",
}

__all__ = [
    "COMMANDS",
    "CommandSpec",
    "RequestFrame",
    "ResponseFrame",
    "build_command_frame",
    "command_code",
    "decode_response",
    "parse_command_response",
    "required_commands",
]


def __getattr__(name: str):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    implementation = load_provider_first(module_name)
    value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
