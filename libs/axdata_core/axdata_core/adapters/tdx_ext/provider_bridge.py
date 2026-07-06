"""Provider/legacy adapter bridge helpers for TDX extended-market requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .request import TdxExtRequestAdapter


def create_tdx_ext_request_adapter(
    options: Mapping[str, object] | None = None,
) -> TdxExtRequestAdapter:
    """Create a TDX extended-market request adapter from execution options."""

    from .request import TdxExtRequestAdapter

    client_pool, client_pool_config, adapter_options = split_tdx_ext_provider_options(options)
    return TdxExtRequestAdapter(
        options=adapter_options,
        client_pool=client_pool,
        client_pool_config=client_pool_config,
    )


def split_tdx_ext_provider_options(
    options: Mapping[str, object] | None = None,
) -> tuple[Any | None, Any | None, dict[str, object]]:
    """Return injected pool resources and remaining TDX Ext execution options."""

    resolved_options = dict(options or {})
    client_pool = resolved_options.pop("client_pool", None)
    client_pool_config = resolved_options.pop("client_pool_config", None)
    return client_pool, client_pool_config, resolved_options
