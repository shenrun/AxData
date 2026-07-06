"""Runtime glue for the ordinary TDX request adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from axdata_core.source_errors import SourceAdapterNotFound


def normalize_adapter_options(
    options: Mapping[str, Any] | None,
    *,
    normalize_options: Callable[[Mapping[str, Any] | None], Mapping[str, Any]],
) -> Mapping[str, Any]:
    return normalize_options(options)


def normalize_tdx_adapter_options(options: Mapping[str, Any] | None) -> Mapping[str, Any]:
    from .options import normalize_tdx_request_options

    return normalize_adapter_options(options, normalize_options=normalize_tdx_request_options)


def supports_interface(
    interface_name: str,
    *,
    supported_interfaces: Sequence[str] | Mapping[str, Any],
) -> bool:
    from .request_dispatch import supports_tdx_interface

    return supports_tdx_interface(interface_name, supported_interfaces)


def supports_tdx_request_interface(interface_name: str) -> bool:
    from .interface_sets import SUPPORTED_INTERFACES

    return supports_interface(interface_name, supported_interfaces=SUPPORTED_INTERFACES)


def request(
    adapter: Any,
    interface_name: str,
    params: Mapping[str, Any],
    *,
    existing_client: Any | None,
    f10_interfaces: Sequence[str] | Mapping[str, Any],
    kline_interface_specs: Sequence[str] | Mapping[str, Any],
    requested_kline_codes: Callable[[Any], Sequence[str]],
    create_client: Callable[[str, Mapping[str, Any]], Any],
    dispatch_with_client: Callable[..., list[dict[str, Any]]],
    supports: Callable[[str], bool],
) -> list[dict[str, Any]]:
    from .request_dispatch import dispatch_adapter_request

    return dispatch_adapter_request(
        adapter,
        interface_name,
        params,
        existing_client=existing_client,
        f10_interfaces=f10_interfaces,
        kline_interface_specs=kline_interface_specs,
        requested_kline_codes=requested_kline_codes,
        create_client=create_client,
        dispatch_with_client=dispatch_with_client,
        supports=supports,
        not_found_error=unsupported_interface_error,
    )


def request_tdx_adapter(
    adapter: Any,
    interface_name: str,
    params: Mapping[str, Any],
    *,
    existing_client: Any | None,
    create_client: Callable[[str, Mapping[str, Any]], Any],
    dispatch_with_client: Callable[..., list[dict[str, Any]]],
    supports: Callable[[str], bool],
) -> list[dict[str, Any]]:
    from .request_filters import requested_kline_codes
    from .request_params import KLINE_INTERFACE_SPECS
    from .tdx_f10_names import F10_INTERFACE_NAMES

    return request(
        adapter,
        interface_name,
        params,
        existing_client=existing_client,
        f10_interfaces=F10_INTERFACE_NAMES,
        kline_interface_specs=KLINE_INTERFACE_SPECS,
        requested_kline_codes=requested_kline_codes,
        create_client=create_client,
        dispatch_with_client=dispatch_with_client,
        supports=supports,
    )


def dispatch_with_client(
    adapter: Any,
    interface_name: str,
    params: Mapping[str, Any],
    client: Any,
    *,
    should_close: bool,
    use_parallel_suspension_quotes: bool | None,
    intraday_subchart_interfaces: Sequence[str] | Mapping[str, Any],
    finance_interface_fields: Sequence[str] | Mapping[str, Any],
    kline_interface_specs: Sequence[str] | Mapping[str, Any],
    exact_request_methods: Mapping[str, str],
    client_meta: Callable[[Any], dict[str, Any]],
) -> list[dict[str, Any]]:
    from .request_dispatch import dispatch_request_with_client

    return dispatch_request_with_client(
        adapter,
        interface_name,
        params,
        client,
        should_close=should_close,
        use_parallel_suspension_quotes=use_parallel_suspension_quotes,
        intraday_subchart_interfaces=intraday_subchart_interfaces,
        finance_interface_fields=finance_interface_fields,
        kline_interface_specs=kline_interface_specs,
        exact_request_methods=exact_request_methods,
        client_meta=client_meta,
        not_found_error=unsupported_interface_error,
    )


def dispatch_tdx_request_with_client(
    adapter: Any,
    interface_name: str,
    params: Mapping[str, Any],
    client: Any,
    *,
    should_close: bool,
    use_parallel_suspension_quotes: bool | None,
) -> list[dict[str, Any]]:
    from .execution_utils import tdx_client_meta
    from .interface_sets import (
        FINANCE_INTERFACE_FIELDS,
        INTRADAY_SUBCHART_INTERFACE_SPECS,
    )
    from .request_dispatch import TDX_EXACT_REQUEST_METHODS
    from .request_params import KLINE_INTERFACE_SPECS

    return dispatch_with_client(
        adapter,
        interface_name,
        params,
        client,
        should_close=should_close,
        use_parallel_suspension_quotes=use_parallel_suspension_quotes,
        intraday_subchart_interfaces=INTRADAY_SUBCHART_INTERFACE_SPECS,
        finance_interface_fields=FINANCE_INTERFACE_FIELDS,
        kline_interface_specs=KLINE_INTERFACE_SPECS,
        exact_request_methods=TDX_EXACT_REQUEST_METHODS,
        client_meta=tdx_client_meta,
    )


def create_request_client(
    interface_name: str,
    params: Mapping[str, Any],
    options: Mapping[str, Any],
    *,
    has_connection_options: Callable[[Mapping[str, Any]], bool],
    create_client: Callable[..., Any],
    option_pool_size: Callable[[Mapping[str, Any]], int | None],
    option_hosts: Callable[..., list[str] | None],
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
    should_parallelize_stock_codes: Callable[[Mapping[str, Any]], bool],
    stock_code_pool_size: Callable[[Mapping[str, Any]], int],
) -> Any:
    from .request_client import create_request_client as create_client_for_request

    return create_client_for_request(
        interface_name,
        params,
        options,
        has_connection_options=has_connection_options,
        create_client=create_client,
        option_pool_size=option_pool_size,
        option_hosts=option_hosts,
        configured_hosts_from_options=configured_hosts_from_options,
        should_parallelize_stock_codes=should_parallelize_stock_codes,
        stock_code_pool_size=stock_code_pool_size,
    )


def create_tdx_request_client(
    interface_name: str,
    params: Mapping[str, Any],
    options: Mapping[str, Any],
    *,
    create_client: Callable[..., Any],
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> Any:
    from .options import (
        has_tdx_connection_options,
        tdx_request_option_hosts,
        tdx_request_option_pool_size,
    )

    return create_request_client(
        interface_name,
        params,
        options,
        has_connection_options=has_tdx_connection_options,
        create_client=create_client,
        option_pool_size=tdx_request_option_pool_size,
        option_hosts=tdx_request_option_hosts,
        configured_hosts_from_options=configured_hosts_from_options,
        should_parallelize_stock_codes=should_parallelize_tdx_stock_code_request,
        stock_code_pool_size=tdx_stock_code_request_pool_size,
    )


def request_hosts(
    options: Mapping[str, Any],
    *,
    option_hosts: Callable[..., list[str] | None],
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    from .request_client import request_hosts as resolve_hosts

    return resolve_hosts(
        options,
        option_hosts=option_hosts,
        configured_hosts_from_options=configured_hosts_from_options,
    )


def tdx_request_hosts(
    options: Mapping[str, Any],
    *,
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    from .options import tdx_request_option_hosts

    return request_hosts(
        options,
        option_hosts=tdx_request_option_hosts,
        configured_hosts_from_options=configured_hosts_from_options,
    )


def configured_hosts(
    options: Mapping[str, Any],
    *,
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    from .request_client import configured_hosts as resolve_hosts

    return resolve_hosts(
        options,
        configured_hosts_from_options=configured_hosts_from_options,
    )


def finish_tdx_request_result(adapter: Any, client: Any, result: Any) -> list[dict[str, Any]]:
    from .execution_utils import finish_request_result

    rows, adapter.last_meta = finish_request_result(client=client, result=result)
    return rows


def should_parallelize_tdx_stock_code_request(params: Mapping[str, Any]) -> bool:
    from .code_fetch import should_parallelize_stock_code_request as should_parallelize
    from .request_client import should_parallelize_stock_code_request
    from .request_filters import exchanges_for_boards, requested_boards, requested_exchanges
    from .request_params import int_param

    return should_parallelize_stock_code_request(
        params,
        should_parallelize=should_parallelize,
        int_param=int_param,
        requested_boards=requested_boards,
        requested_exchanges=requested_exchanges,
        exchanges_for_boards=exchanges_for_boards,
    )


def tdx_stock_code_request_pool_size(params: Mapping[str, Any]) -> int:
    from .code_fetch import stock_code_request_pool_size
    from .request_client import stock_code_request_pool_size as resolve_pool_size
    from .request_filters import exchanges_for_boards, requested_boards, requested_exchanges

    return resolve_pool_size(
        params,
        pool_size=stock_code_request_pool_size,
        requested_boards=requested_boards,
        requested_exchanges=requested_exchanges,
        exchanges_for_boards=exchanges_for_boards,
    )


def unsupported_interface_error(interface_name: str) -> SourceAdapterNotFound:
    return SourceAdapterNotFound(
        f"TDX source adapter does not support interface {interface_name!r}."
    )
