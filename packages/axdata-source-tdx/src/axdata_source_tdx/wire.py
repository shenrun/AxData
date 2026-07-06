"""Provider-owned seam for the bundled TDX wire runtime."""

from __future__ import annotations

from typing import Any

from axdata_core.source_errors import SourceUnavailableError

from ._tdx_wire._host_defaults import DEFAULT_QUOTE_HOSTS
from ._tdx_wire._host_resource import DEFAULT_HOSTS


def tdx_client_class() -> Any:
    """Return the provider-owned TDX wire client class lazily."""

    try:
        from axdata_source_tdx._tdx_wire.client import TdxClient
    except ImportError as exc:
        raise SourceUnavailableError("TDX provider wire client is not available.") from exc
    return TdxClient


def default_tdx_hosts() -> list[str]:
    """Return provider-packaged quote hosts with static fallback."""

    return list(DEFAULT_HOSTS or DEFAULT_QUOTE_HOSTS)


def fallback_tdx_hosts() -> list[str]:
    """Return the static quote host list used when packaged resources are absent."""

    return list(DEFAULT_QUOTE_HOSTS)
