"""Legacy request-module entry points owned by the TDX provider."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _loaded_request_attr(name: str) -> Any | None:
    import sys

    request_module = sys.modules.get("axdata_core.adapters.tdx.request")
    if request_module is None:
        return None
    return request_module.__dict__.get(name)


def _loaded_request_callable(name: str, default: Any) -> Any:
    loaded = _loaded_request_attr(name)
    if loaded is None:
        return default
    if (
        getattr(loaded, "__module__", None) == getattr(default, "__module__", None)
        and getattr(loaded, "__name__", None) == getattr(default, "__name__", None)
    ):
        return default
    return loaded


def __getattr__(name: str) -> Any:
    if name == "TdxRequestAdapter":
        adapter_cls = _request_adapter_class()
        globals()[name] = adapter_cls
        return adapter_cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _request_adapter_class() -> type[Any]:
    from .request_adapter import TdxRequestAdapter as provider_adapter_cls

    class TdxRequestAdapter(provider_adapter_cls):
        """Provider-owned compatibility wrapper for the legacy core request adapter."""

        def _create_request_client(self, interface_name: str, params: Mapping[str, Any]) -> Any:
            from . import request_adapter_runtime

            return request_adapter_runtime.create_tdx_request_client(
                interface_name,
                params,
                self._options,
                create_client=_loaded_request_callable("create_tdx_client", create_tdx_client),
                configured_hosts_from_options=_loaded_request_callable(
                    "_configured_tdx_hosts_from_options",
                    _configured_tdx_hosts_from_options,
                ),
            )

        def _request_hosts(self) -> list[str]:
            from . import request_adapter_runtime

            return request_adapter_runtime.tdx_request_hosts(
                self._options,
                configured_hosts_from_options=_loaded_request_callable(
                    "_configured_tdx_hosts_from_options",
                    _configured_tdx_hosts_from_options,
                ),
            )

        def _configured_hosts(self) -> list[str]:
            from . import request_adapter_runtime

            return request_adapter_runtime.configured_hosts(
                self._options,
                configured_hosts_from_options=_loaded_request_callable(
                    "_configured_tdx_hosts_from_options",
                    _configured_tdx_hosts_from_options,
                ),
            )

        def _request_stock_finance_info(
            self,
            client: Any,
            interface_name: str,
            params: Mapping[str, Any],
        ) -> list[dict[str, Any]]:
            from . import request_methods
            from .finance_maps import load_finance_local_maps_from_root, lookup_finance_profile_maps

            return request_methods.request_stock_finance_info(
                self,
                client,
                interface_name,
                params,
                load_finance_maps=_loaded_request_callable(
                    "load_finance_local_maps_from_root",
                    load_finance_local_maps_from_root,
                ),
                lookup_finance_profile=_loaded_request_callable(
                    "lookup_finance_profile_maps",
                    lookup_finance_profile_maps,
                ),
            )

    TdxRequestAdapter.__module__ = __name__
    TdxRequestAdapter.__qualname__ = "TdxRequestAdapter"
    return TdxRequestAdapter


def _configured_tdx_hosts_from_options(options: Mapping[str, Any]) -> list[str]:
    from .request_host_config import _configured_tdx_hosts_from_options as configured

    return configured(options)


def create_tdx_client(**kwargs: Any) -> Any:
    from .client_factory import create_tdx_client as current_create_tdx_client

    return current_create_tdx_client(**kwargs)


def _tdx_env_int(name: str, default: int, *, minimum: int) -> int:
    from .client_factory import tdx_env_int

    return tdx_env_int(name, default, minimum=minimum)


def request_realtime_refresh_rows(
    *,
    code: Any,
    fields: Sequence[str] | None = None,
    cursors: Mapping[str, int] | None = None,
    include_internal: bool = False,
    client: Any | None = None,
) -> list[dict[str, Any]]:
    """Request TDX 0x0547 quote refresh rows for realtime WebSocket streams."""

    from .realtime_refresh import request_realtime_refresh_rows as current_request_realtime_refresh_rows

    return current_request_realtime_refresh_rows(
        code=code,
        fields=fields,
        cursors=cursors,
        include_internal=include_internal,
        client=client,
        create_client=_loaded_request_callable("create_tdx_client", create_tdx_client),
    )
