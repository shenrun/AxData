"""Provider/legacy adapter bridge helpers for CLS requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from axdata_core.source_adapter_options import timeout_seconds

if TYPE_CHECKING:
    from .request import ClsRequestAdapter


def create_cls_request_adapter(options: Mapping[str, object] | None = None) -> ClsRequestAdapter:
    """Create a CLS request adapter from execution options."""

    from .request import ClsRequestAdapter

    resolved_options = dict(options or {})
    return ClsRequestAdapter(
        opener=resolved_options.get("opener"),
        timeout=timeout_seconds(resolved_options, default=15.0),
    )
