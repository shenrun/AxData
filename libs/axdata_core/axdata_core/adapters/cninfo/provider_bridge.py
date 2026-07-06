"""Provider/legacy adapter bridge helpers for Cninfo requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import CninfoRequestAdapter


def create_cninfo_request_adapter(
    options: Mapping[str, object] | None = None,
) -> CninfoRequestAdapter:
    """Create a Cninfo request adapter from execution options."""

    from .request import CninfoRequestAdapter

    resolved_options = dict(options or {})
    return CninfoRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=20.0),
    )
