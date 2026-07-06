"""Compatibility shim for axdata_core._tdx_wire.protocol.commands.session.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
Lightweight session command codes are exposed without loading the full session
command parser; other legacy names still load provider-first on demand.
"""

from __future__ import annotations

from datetime import datetime

from ..._shim import load_provider_first, load_provider_first_cached


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.protocol.commands.session"
_PROVIDER_CODES_MODULE = "axdata_source_tdx._tdx_wire._command_codes"


_codes_impl = None
_command_impl = None


def _load_codes_impl():
    return load_provider_first_cached(globals(), "_codes_impl", _PROVIDER_CODES_MODULE)


def _command_codes() -> dict[str, int]:
    command_codes = _load_codes_impl().COMMAND_CODES
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def _command_code(name: str) -> int:
    return _load_codes_impl().command_code(name)

__all__ = [
    "COMMAND_CODES",
    "HandshakeInfo",
    "HeartbeatAck",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "TYPE_HANDSHAKE",
    "TYPE_HEARTBEAT",
    "annotations",
    "build_handshake_frame",
    "build_heartbeat_frame",
    "date_from_yyyymmdd",
    "datetime",
    "decode_gbk_text",
    "little_u16",
    "little_u32",
    "parse_handshake_payload",
    "parse_heartbeat_payload",
]


def _load_command_impl():
    global _command_impl
    if _command_impl is None:
        _command_impl = load_provider_first(_PROVIDER_MODULE)
    return _command_impl


def __getattr__(name: str):
    if name == "COMMAND_CODES":
        return _command_codes()
    if name == "TYPE_HANDSHAKE":
        value = _command_code("handshake")
    elif name == "TYPE_HEARTBEAT":
        value = _command_code("heartbeat")
    else:
        if name.startswith("_"):
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        implementation = _load_command_impl()
        value = getattr(implementation, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
