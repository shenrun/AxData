"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.resources.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight command/default facts are exposed without loading the full resource
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from typing import Any

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.resources"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"
_PROVIDER_COMMAND_DEFAULTS_MODULE = "axdata_source_tdx._tdx_wire._command_defaults"
_PROVIDER_REQUEST_DEFAULTS_MODULE = "axdata_source_tdx._tdx_wire._request_defaults"


_codes_impl = None
_command_defaults_impl = None
_request_defaults_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _load_command_defaults_impl():
    return load_provider_first_cached(
        globals(),
        "_command_defaults_impl",
        _PROVIDER_COMMAND_DEFAULTS_MODULE,
    )


def _load_request_defaults_impl():
    return load_provider_first_cached(
        globals(),
        "_request_defaults_impl",
        _PROVIDER_REQUEST_DEFAULTS_MODULE,
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
    "DEFAULT_FILE_CHUNK_SIZE",
    "FILE_PATH_FIELD_SIZE",
    "FileContentChunk",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "TYPE_FILE_CONTENT",
    "annotations",
    "build_file_content_frame",
    "little_u32",
    "parse_file_content_payload",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str) -> Any:
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "DEFAULT_FILE_CHUNK_SIZE":
        value = _load_request_defaults_impl().DEFAULT_FILE_CHUNK_SIZE
    elif name == "FILE_PATH_FIELD_SIZE":
        value = _load_command_defaults_impl().FILE_PATH_FIELD_SIZE
    elif name == "TYPE_FILE_CONTENT":
        value = _command_code("file_content")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
