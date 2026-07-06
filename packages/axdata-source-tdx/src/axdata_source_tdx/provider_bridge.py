"""Provider/legacy adapter bridge helpers for ordinary TDX requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .request_adapter import TdxRequestAdapter


def create_tdx_request_adapter(options: Mapping[str, object] | None = None) -> TdxRequestAdapter:
    """Create a TDX request adapter from Provider/legacy execution options."""

    client, adapter_options = split_tdx_provider_options(options)
    adapter_cls = _tdx_request_adapter_class()
    return adapter_cls(client=client, options=adapter_options)


def split_tdx_provider_options(
    options: Mapping[str, object] | None = None,
) -> tuple[Any | None, dict[str, object]]:
    """Return injected client and remaining TDX execution options."""

    resolved_options = dict(options or {})
    client = resolved_options.pop("client", None)
    return client, resolved_options


def _tdx_request_adapter_class() -> Any:
    adapter_cls = globals().get("TdxRequestAdapter")
    if adapter_cls is not None:
        return adapter_cls
    from .request_adapter import TdxRequestAdapter as loaded_adapter_cls

    globals()["TdxRequestAdapter"] = loaded_adapter_cls
    return loaded_adapter_cls


def __getattr__(name: str) -> Any:
    if name == "TdxRequestAdapter":
        return _tdx_request_adapter_class()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
