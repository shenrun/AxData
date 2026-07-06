"""Provider/legacy adapter bridge helpers for Sina requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import SinaRequestAdapter


def create_sina_request_adapter(
    options: Mapping[str, object] | None = None,
) -> SinaRequestAdapter:
    """Create a Sina request adapter from execution options."""

    from .request import SinaRequestAdapter

    resolved_options = dict(options or {})
    return SinaRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=20.0),
    )
