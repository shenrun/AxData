"""Provider/legacy adapter bridge helpers for Tencent Finance requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import TencentRequestAdapter


def create_tencent_request_adapter(
    options: Mapping[str, object] | None = None,
) -> TencentRequestAdapter:
    """Create a Tencent Finance request adapter from execution options."""

    from .request import TencentRequestAdapter

    resolved_options = dict(options or {})
    return TencentRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=15.0),
    )
