"""TDX source adapter package."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS: dict[str, tuple[str, str]] = {
    "TdxRequestAdapter": (".request", "TdxRequestAdapter"),
    "create_tdx_client": (".client_factory", "create_tdx_client"),
    "instrument_id_to_tdx_code": (".codes", "instrument_id_to_tdx_code"),
    "tdx_code_to_instrument_id": (".codes", "tdx_code_to_instrument_id"),
}

__all__ = [
    "TdxRequestAdapter",
    "create_tdx_client",
    "instrument_id_to_tdx_code",
    "tdx_code_to_instrument_id",
]


def __getattr__(name: str) -> Any:
    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = export
    module = import_module(module_name, __name__)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
