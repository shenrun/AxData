"""Provider/legacy adapter bridge helpers for KPH requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import KphRequestAdapter


def create_kph_request_adapter(options: Mapping[str, object] | None = None) -> KphRequestAdapter:
    """Create a KPH request adapter from execution options."""

    from .request import KphRequestAdapter

    resolved_options = dict(options or {})
    return KphRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=15.0),
    )
