"""Lightweight TDX realtime quote refresh entry points."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .quote_fetch import (
    request_realtime_refresh_rows as _request_realtime_refresh_rows,
)
from .codes import tdx_code_to_instrument_id
from .normalize_utils import as_list, get_value, optional_int
from .quote_identity import quote_security_from_tdx_code
from .request_filters import requested_kline_codes
from .snapshot_normalize import normalize_realtime_snapshot_row
from .wire_requests import tdx_refresh_quotes


def request_realtime_refresh_rows(
    *,
    code: Any,
    fields: Sequence[str] | None = None,
    cursors: Mapping[str, int] | None = None,
    include_internal: bool = False,
    client: Any | None = None,
    create_client: Any | None = None,
) -> list[dict[str, Any]]:
    """Request TDX 0x0547 quote refresh rows for realtime WebSocket streams."""

    return _request_realtime_refresh_rows(
        code=code,
        fields=fields,
        cursors=cursors,
        include_internal=include_internal,
        client=client,
        requested_codes=requested_kline_codes,
        quote_security_from_tdx_code=quote_security_from_tdx_code,
        tdx_code_to_instrument_id=tdx_code_to_instrument_id,
        create_client=create_tdx_client if create_client is None else create_client,
        tdx_refresh_quotes=tdx_refresh_quotes,
        normalize_snapshot_row=normalize_realtime_snapshot_row,
        as_list=as_list,
        get_value=get_value,
        optional_int=optional_int,
    )


def create_tdx_client(**kwargs: Any) -> Any:
    from .client_factory import create_tdx_client as current_create_tdx_client

    return current_create_tdx_client(**kwargs)
