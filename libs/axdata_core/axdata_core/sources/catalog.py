"""Aggregated source request interface catalog."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from axdata_core.source_errors import SourceUnavailableError
from axdata_core.tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE

from .base import RequestExample, RequestField, RequestParameter, SourceRequestInterface
from .cninfo import INTERFACES as CNINFO_INTERFACES
from .cls import INTERFACES as CLS_INTERFACES
from .eastmoney import INTERFACES as EASTMONEY_INTERFACES
from .exchange import INTERFACES as EXCHANGE_INTERFACES
from .kph import INTERFACES as KPH_INTERFACES
from .sina import INTERFACES as SINA_INTERFACES
from .tencent import INTERFACES as TENCENT_INTERFACES

INTERFACES: Dict[str, SourceRequestInterface] = {
    **EXCHANGE_INTERFACES,
    **CNINFO_INTERFACES,
    **TENCENT_INTERFACES,
    **EASTMONEY_INTERFACES,
    **CLS_INTERFACES,
    **KPH_INTERFACES,
    **SINA_INTERFACES,
}


def list_request_interfaces() -> Tuple[SourceRequestInterface, ...]:
    """Return all registered source request interfaces in catalog order."""

    return tuple(INTERFACES.values())


def list_request_interface_names() -> Tuple[str, ...]:
    """Return all registered source request interface names in catalog order."""

    return tuple(INTERFACES)


def list_request_interface_dicts() -> Tuple[Dict[str, Any], ...]:
    """Return all registered source request interfaces as serializable dicts."""

    return tuple(interface.to_dict() for interface in list_request_interfaces())


def get_request_interface(name: str) -> SourceRequestInterface:
    """Return one registered source request interface by AxData interface name."""

    normalized = name.strip()
    try:
        return INTERFACES[normalized]
    except KeyError as exc:
        if normalized.endswith("_tdx"):
            raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc
        known = ", ".join(list_request_interface_names()) or "<empty>"
        raise KeyError(
            f"Unknown AxData request interface {name!r}. Known interfaces: {known}."
        ) from exc
