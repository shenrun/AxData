"""TDX request adapter client selection helpers."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import Any


def configured_hosts(
    options: Mapping[str, Any],
    *,
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    return configured_hosts_from_options(options)


def request_hosts(
    options: Mapping[str, Any],
    *,
    option_hosts: Callable[..., list[str] | None],
    configured_hosts_from_options: Callable[[Mapping[str, Any]], list[str]],
) -> list[str]:
    return (
        option_hosts(
            options,
            configured_hosts=configured_hosts_from_options,
        )
        or configured_hosts(options, configured_hosts_from_options=configured_hosts_from_options)
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
    if has_connection_options(options):
        return create_client(
            hosts=request_hosts(
                options,
                option_hosts=option_hosts,
                configured_hosts_from_options=configured_hosts_from_options,
            ),
            pool_size=option_pool_size(options),
        )
    if interface_name == "stock_codes_tdx" and should_parallelize_stock_codes(params):
        return create_client(
            hosts=configured_hosts(options, configured_hosts_from_options=configured_hosts_from_options),
            pool_size=stock_code_pool_size(params),
        )
    return create_client(
        hosts=configured_hosts(options, configured_hosts_from_options=configured_hosts_from_options),
    )


def should_parallelize_stock_code_request(
    params: Mapping[str, Any],
    *,
    should_parallelize: Callable[..., bool],
    int_param: Callable[..., int],
    requested_boards: Callable[[Any], set[str] | None],
    requested_exchanges: Callable[[Any], list[str]],
    exchanges_for_boards: Callable[[set[str] | None], str],
    pool_size_env_name: str = "AXDATA_TDX_POOL_SIZE",
) -> bool:
    return should_parallelize(
        params,
        pool_size_env_set=pool_size_env_name in os.environ,
        int_param=int_param,
        requested_boards=requested_boards,
        requested_exchanges=requested_exchanges,
        exchanges_for_boards=exchanges_for_boards,
    )


def stock_code_request_pool_size(
    params: Mapping[str, Any],
    *,
    pool_size: Callable[..., int],
    requested_boards: Callable[[Any], set[str] | None],
    requested_exchanges: Callable[[Any], list[str]],
    exchanges_for_boards: Callable[[set[str] | None], str],
) -> int:
    return pool_size(
        params,
        requested_boards=requested_boards,
        requested_exchanges=requested_exchanges,
        exchanges_for_boards=exchanges_for_boards,
    )
