"""Compatibility frame helpers for ``axdata_core._tdx_wire.protocol.frame``.

The provider-owned TDX wire stack is the primary implementation. This legacy
module keeps old frame imports working while reading stable frame constants from
lightweight provider facts directly, falling back only when the provider package
is absent.
"""

from __future__ import annotations

from types import ModuleType as _ModuleType

from .._shim import load_provider_first as _load_provider_first
from .._shim import load_provider_first_cached as _load_provider_first_cached


_PROVIDER_CONSTANTS_MODULE = "axdata_source_tdx._tdx_wire.protocol._frame_constants"
_PROVIDER_RUNTIME_MODULE = "axdata_source_tdx._tdx_wire.protocol.frame"
_CONSTANT_EXPORTS = {"CONTROL_DEFAULT", "PREFIX", "PREFIX_RESP"}
_RUNTIME_EXPORTS = {
    "ConnectionClosedError",
    "ProtocolError",
    "RequestFrame",
    "ResponseFrame",
    "dataclass",
    "decode_response",
    "read_exact",
    "read_response_frame",
    "socket",
    "struct",
    "zlib",
}


_FRAME_CONSTANTS = None


def _load_frame_constants() -> _ModuleType:
    return _load_provider_first_cached(
        globals(),
        "_FRAME_CONSTANTS",
        _PROVIDER_CONSTANTS_MODULE,
    )


def _load_runtime_module() -> _ModuleType:
    return _load_provider_first(_PROVIDER_RUNTIME_MODULE)


def __getattr__(name: str):
    if name in _CONSTANT_EXPORTS:
        value = getattr(_load_frame_constants(), name)
        globals()[name] = value
        return value
    runtime = _load_runtime_module()
    try:
        value = getattr(runtime, name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__) | _RUNTIME_EXPORTS)


__all__ = sorted(_CONSTANT_EXPORTS | _RUNTIME_EXPORTS)
