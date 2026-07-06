"""TDX interface dispatch declarations for simple adapter request paths."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .request_params import INDEX_KLINE_INTERFACE


TDX_EXACT_REQUEST_METHODS: dict[str, str] = {
    "index_codes_tdx": "_request_index_codes",
    "stock_st_list_tdx": "_request_stock_st_list",
    "stock_daily_share_tdx": "_request_stock_daily_share",
    "stock_daily_price_limit_tdx": "_request_stock_daily_price_limit",
    "stock_order_book_tdx": "_request_stock_order_book",
    "stock_realtime_snapshot_tdx": "_request_stock_realtime_snapshot",
    "index_realtime_snapshot_tdx": "_request_index_realtime_snapshot",
    "stock_realtime_rank_tdx": "_request_stock_realtime_rank",
    "index_realtime_rank_tdx": "_request_index_realtime_rank",
    "index_quote_refresh_tdx": "_request_index_quote_refresh",
    "stock_limit_ladder_tdx": "_request_stock_limit_ladder",
    "stock_theme_strength_rank_tdx": "_request_stock_theme_strength_rank",
    "stock_auction_process_tdx": "_request_stock_auction_process",
    "stock_auction_result_tdx": "_request_stock_auction_result_today",
    "stock_auction_result_history_tdx": "_request_stock_auction_result_history",
    "stock_shortline_indicators_tdx": "_request_stock_auction_indicators",
    "stock_capital_changes_tdx": "_request_stock_capital_changes",
    "stock_adj_factor_tdx": "_request_stock_adj_factor",
    "stock_intraday_today_tdx": "_request_stock_intraday_today",
    "stock_intraday_history_tdx": "_request_stock_intraday_history",
    "index_intraday_today_tdx": "_request_index_intraday_today",
    "index_intraday_history_tdx": "_request_index_intraday_history",
    "etf_codes_tdx": "_request_etf_codes",
    "etf_realtime_snapshot_tdx": "_request_etf_realtime_snapshot",
    "etf_realtime_rank_tdx": "_request_etf_realtime_rank",
    "etf_kline_tdx": "_request_etf_kline",
    "etf_intraday_today_tdx": "_request_etf_intraday_today",
    "etf_intraday_history_tdx": "_request_etf_intraday_history",
    "etf_trades_today_tdx": "_request_etf_trades_today",
    "etf_trades_history_tdx": "_request_etf_trades_history",
    "etf_auction_process_tdx": "_request_etf_auction_process",
    "etf_auction_result_tdx": "_request_etf_auction_result_today",
    INDEX_KLINE_INTERFACE: "_request_index_kline",
    "stock_intraday_recent_history_tdx": "_request_stock_intraday_recent_history",
    "stock_trades_today_tdx": "_request_stock_trades_today",
    "stock_trades_history_tdx": "_request_stock_trades_history",
}


def supports_tdx_interface(interface_name: str, supported_interfaces: Sequence[str] | Mapping[str, Any]) -> bool:
    """Return whether the TDX adapter declares support for an interface."""

    return interface_name in supported_interfaces


def dispatch_adapter_request(
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
    not_found_error: Callable[[str], Exception],
) -> list[dict[str, Any]]:
    if not supports(interface_name):
        raise not_found_error(interface_name)

    if interface_name in f10_interfaces:
        return adapter._request_stock_f10(interface_name, params)

    if interface_name in kline_interface_specs and existing_client is None:
        kline_codes = requested_kline_codes(params.get("code"))
        if len(kline_codes) > 1:
            return adapter._request_stock_kline_parallel(interface_name, params, kline_codes)

    client = existing_client or create_client(interface_name, params)
    return dispatch_with_client(
        adapter,
        interface_name,
        params,
        client,
        should_close=existing_client is None,
    )


def dispatch_request_with_client(
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
    not_found_error: Callable[[str], Exception],
) -> list[dict[str, Any]]:
    try:
        if hasattr(client, "connect"):
            client.connect()
        if interface_name == "stock_codes_tdx":
            rows = adapter._request_stock_codes(client, params)
            request_meta = dict(adapter.last_meta)
            adapter.last_meta = client_meta(client) | request_meta
            return rows
        if interface_name == "stock_suspensions_tdx":
            return adapter._request_stock_suspensions(
                client,
                params,
                use_parallel_quote_clients=(
                    should_close
                    if use_parallel_suspension_quotes is None
                    else use_parallel_suspension_quotes
                ),
            )
        if interface_name in intraday_subchart_interfaces:
            return adapter._request_stock_intraday_subchart(client, interface_name, params)
        if interface_name in finance_interface_fields:
            return adapter._request_stock_finance_info(client, interface_name, params)
        if interface_name in kline_interface_specs:
            return adapter._request_stock_kline(client, interface_name, params)
        request_method_name = exact_request_methods.get(interface_name)
        if request_method_name:
            return getattr(adapter, request_method_name)(client, params)
    finally:
        if should_close and hasattr(client, "close"):
            client.close()

    raise not_found_error(interface_name)
