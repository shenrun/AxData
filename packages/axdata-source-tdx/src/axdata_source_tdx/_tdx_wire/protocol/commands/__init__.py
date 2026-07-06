"""Protocol command registry."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MODULES = {
    "build_command_frame": "..._command_codec",
    "parse_command_response": "..._command_codec",
    "COMMANDS": "..._command_registry",
    "CommandSpec": "..._command_registry",
    "command_code": "..._command_lookup",
    "required_commands": "..._command_registry",
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
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
