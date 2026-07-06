"""Provider-owned lightweight command-code lookup."""

from __future__ import annotations

from importlib import import_module

def command_code(name: str) -> int:
    module = import_module("axdata_source_tdx._tdx_wire._command_codes")
    return module.command_code(name)


def _command_codes() -> dict[str, int]:
    module = import_module("axdata_source_tdx._tdx_wire._command_codes")
    command_codes = module.COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def __getattr__(name: str):
    if name == "COMMAND_CODES":
        return _command_codes()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["command_code"]
