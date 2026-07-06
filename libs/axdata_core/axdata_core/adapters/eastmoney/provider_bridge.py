"""Provider/legacy adapter bridge helpers for Eastmoney requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import EastmoneyRequestAdapter


def create_eastmoney_request_adapter(
    options: Mapping[str, object] | None = None,
) -> EastmoneyRequestAdapter:
    """Create an Eastmoney request adapter from execution options."""

    from .request import EastmoneyRequestAdapter

    resolved_options = dict(options or {})
    return EastmoneyRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=15.0),
    )
