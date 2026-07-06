"""Provider-owned command codec dispatch for TDX 7709 protocol commands."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

_COMMAND_PACKAGE = "axdata_source_tdx._tdx_wire.protocol.commands"
_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_DISPATCH_MODULE = "axdata_source_tdx._tdx_wire._command_dispatch"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"

Builder = Callable[[dict[str, Any], int], Any]
Parser = Callable[[Any, dict[str, Any] | None], Any]
_BUILDER_CACHE: dict[int, Builder] = {}
_PARSER_CACHE: dict[int, Parser] = {}


def _load_callable(module_name: str, function_name: str) -> Callable[..., Any]:
    module = import_module(f"{_COMMAND_PACKAGE}.{module_name}")
    return getattr(module, function_name)


def _lazy_builder(module_name: str, function_name: str) -> Builder:
    def builder(payload: dict[str, Any], msg_id: int) -> Any:
        return _load_callable(module_name, function_name)(payload, msg_id)

    builder.__name__ = function_name
    builder.__qualname__ = function_name
    builder.__module__ = f"{_COMMAND_PACKAGE}.{module_name}"
    return builder


def _lazy_parser(module_name: str, function_name: str, *, pass_request_payload: bool = True) -> Parser:
    def parser(response: Any, request_payload: dict[str, Any] | None = None) -> Any:
        target = _load_callable(module_name, function_name)
        if pass_request_payload:
            return target(response, request_payload)
        return target(response)

    parser.__name__ = function_name
    parser.__qualname__ = function_name
    parser.__module__ = f"{_COMMAND_PACKAGE}.{module_name}"
    return parser


def build_command_frame(command: int, payload: dict[str, Any] | None, msg_id: int) -> Any:
    try:
        builder = _builder(command)
    except KeyError as exc:
        raise _unsupported_command_error()(f"7709 command 0x{command:04x} is not enabled yet") from exc
    return builder(dict(payload or {}), msg_id)


def parse_command_response(command: int, response: Any, request_payload: dict[str, Any] | None = None) -> Any:
    try:
        parser = _parser(command)
    except KeyError as exc:
        raise _unsupported_command_error()(f"7709 command 0x{command:04x} is not enabled yet") from exc
    return parser(response, request_payload)


def _command_codes() -> dict[str, int]:
    return import_module(_CODES_MODULE).COMMAND_CODES


def _command_code(name: str) -> int:
    return import_module(_CODES_MODULE).command_code(name)


def _command_name(command: int) -> str:
    return import_module(_CODES_MODULE).command_name(command)


def _builder_targets() -> dict[str, tuple[str, str]]:
    return import_module(_DISPATCH_MODULE).BUILDER_TARGETS


def _parser_targets() -> dict[str, tuple[str, str, bool]]:
    return import_module(_DISPATCH_MODULE).PARSER_TARGETS


def _builder_target_items() -> tuple[tuple[str, tuple[str, str]], ...]:
    return import_module(_DISPATCH_MODULE).BUILDER_TARGET_ITEMS


def _parser_target_items() -> tuple[tuple[str, tuple[str, str, bool]], ...]:
    return import_module(_DISPATCH_MODULE).PARSER_TARGET_ITEMS


def _builder_target(name: str) -> tuple[str, str]:
    return import_module(_DISPATCH_MODULE).builder_target(name)


def _parser_target(name: str) -> tuple[str, str, bool]:
    return import_module(_DISPATCH_MODULE).parser_target(name)


def _builder(command: int) -> Builder:
    builders = globals().get("BUILDERS")
    if builders is not None:
        return builders[command]
    cached = _BUILDER_CACHE.get(command)
    if cached is not None:
        return cached
    command_name = _command_name(command)
    module_name, function_name = _builder_target(command_name)
    builder = _lazy_builder(module_name, function_name)
    _BUILDER_CACHE[command] = builder
    return builder


def _parser(command: int) -> Parser:
    parsers = globals().get("PARSERS")
    if parsers is not None:
        return parsers[command]
    cached = _PARSER_CACHE.get(command)
    if cached is not None:
        return cached
    command_name = _command_name(command)
    module_name, function_name, pass_request_payload = _parser_target(command_name)
    parser = _lazy_parser(module_name, function_name, pass_request_payload=pass_request_payload)
    _PARSER_CACHE[command] = parser
    return parser


def _builders() -> dict[int, Builder]:
    cached = globals().get("BUILDERS")
    if cached is not None:
        return cached
    builders = {}
    for name, (module_name, function_name) in _builder_target_items():
        command = _command_code(name)
        builder = _BUILDER_CACHE.get(command)
        if builder is None:
            builder = _lazy_builder(module_name, function_name)
            _BUILDER_CACHE[command] = builder
        builders[command] = builder
    globals()["BUILDERS"] = builders
    return builders


def _parsers() -> dict[int, Parser]:
    cached = globals().get("PARSERS")
    if cached is not None:
        return cached
    parsers = {}
    for name, (module_name, function_name, pass_request_payload) in _parser_target_items():
        command = _command_code(name)
        parser = _PARSER_CACHE.get(command)
        if parser is None:
            parser = _lazy_parser(module_name, function_name, pass_request_payload=pass_request_payload)
            _PARSER_CACHE[command] = parser
        parsers[command] = parser
    globals()["PARSERS"] = parsers
    return parsers


def _unsupported_command_error() -> type[Exception]:
    return import_module(_EXCEPTIONS_MODULE).UnsupportedCommandError


def __getattr__(name: str) -> Any:
    if name == "BUILDERS":
        return _builders()
    if name == "PARSERS":
        return _parsers()
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "BUILDER_TARGETS":
        return _builder_targets()
    if name == "PARSER_TARGETS":
        return _parser_targets()
    if name == "UnsupportedCommandError":
        return _unsupported_command_error()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BUILDERS",
    "Builder",
    "PARSERS",
    "Parser",
    "build_command_frame",
    "parse_command_response",
]
