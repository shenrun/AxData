"""Provider-owned command registry compatibility facts."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

_COMMAND_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_COMMAND_METADATA_MODULE = "axdata_source_tdx._tdx_wire._command_metadata"


@dataclass(frozen=True, slots=True)
class CommandSpec:
    code: int
    name: str
    module: str
    method: str
    required_for_1_0: bool
    document: str

    @property
    def hex(self) -> str:
        return f"0x{self.code:04x}"


def command_code(name: str) -> int:
    module = import_module(_COMMAND_CODES_MODULE)
    return module.command_code(name)


def required_commands() -> list[CommandSpec]:
    command_codes_module = import_module(_COMMAND_CODES_MODULE)
    metadata_items = import_module(_COMMAND_METADATA_MODULE).COMMAND_METADATA_ITEMS
    return [
        CommandSpec(command_codes_module.command_code(name), name, module, method, required_for_1_0, document)
        for name, module, method, required_for_1_0, document in metadata_items
        if required_for_1_0
    ]


def _commands() -> dict[str, CommandSpec]:
    cached = globals().get("COMMANDS")
    if cached is not None:
        return cached
    command_codes_module = import_module(_COMMAND_CODES_MODULE)
    metadata_items = import_module(_COMMAND_METADATA_MODULE).COMMAND_METADATA_ITEMS
    commands = {
        name: CommandSpec(command_codes_module.command_code(name), name, module, method, required_for_1_0, document)
        for name, module, method, required_for_1_0, document in metadata_items
    }
    globals()["COMMANDS"] = commands
    return commands


def __getattr__(name: str):
    if name == "COMMANDS":
        return _commands()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["COMMANDS", "CommandSpec", "command_code", "required_commands"]
