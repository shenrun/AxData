"""Compatibility shim for ``axdata_core._tdx_wire.protocol.commands``.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from ..._shim import load_provider_first


_EXPORT_MODULES = {
    "build_command_frame": "axdata_source_tdx._tdx_wire._command_codec",
    "parse_command_response": "axdata_source_tdx._tdx_wire._command_codec",
    "COMMANDS": "axdata_source_tdx._tdx_wire._command_registry",
    "CommandSpec": "axdata_source_tdx._tdx_wire._command_registry",
    "command_code": "axdata_source_tdx._tdx_wire._command_lookup",
    "required_commands": "axdata_source_tdx._tdx_wire._command_registry",
}

__all__ = [
    "COMMANDS",
    "CommandSpec",
    "build_command_frame",
    "command_code",
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
