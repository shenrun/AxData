"""Provider/legacy adapter bridge helpers for exchange requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import ExchangeRequestAdapter


def create_exchange_request_adapter(
    options: Mapping[str, object] | None = None,
) -> ExchangeRequestAdapter:
    """Create an exchange request adapter from execution options."""

    from .request import ExchangeRequestAdapter

    resolved_options = dict(options or {})
    return ExchangeRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=20.0),
    )
