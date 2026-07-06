"""TDX Provider adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.legacy_provider_adapter import LegacyProviderAdapter

from .metadata import PROVIDER_ID, SOURCE_CODE

if TYPE_CHECKING:
    from .request_adapter import TdxRequestAdapter


class TdxProviderAdapter(LegacyProviderAdapter):
    """Adapter that exposes ordinary TDX quote interfaces through Provider API."""

    def __init__(self, options: Mapping[str, object] | None = None) -> None:
        super().__init__(
            source=SOURCE_CODE,
            provider_id=PROVIDER_ID,
            create_adapter=lambda call_options: _create_legacy_adapter(call_options),
            options=options,
        )


def _create_legacy_adapter(options: Mapping[str, object]) -> TdxRequestAdapter:
    from .provider_bridge import create_tdx_request_adapter

    return create_tdx_request_adapter(options)
