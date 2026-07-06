"""Shared API helpers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from axdata_source_tdx._tdx_wire.transport.base import Transport

__all__ = ["Any", "ApiBase", "COMMAND_CODES", "TYPE_CHECKING"]


class ApiBase:
    """Base class for capability-specific APIs."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _execute(self, command_name: str, **payload: Any) -> Any:
        return self._transport.execute(_command_code(command_name), payload)


def _command_codes() -> dict[str, int]:
    module = import_module("axdata_source_tdx._tdx_wire._command_codes")
    command_codes = module.COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def _command_code(name: str) -> int:
    module = import_module("axdata_source_tdx._tdx_wire._command_codes")
    return module.command_code(name)


def __getattr__(name: str) -> Any:
    if name == "COMMAND_CODES":
        return _command_codes()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
