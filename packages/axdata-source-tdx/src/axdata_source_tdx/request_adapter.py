"""Provider-owned ordinary TDX request adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .tdx_f10_models import F10InterfaceSpec


class TdxRequestAdapter:
    """Adapter that requests ordinary TDX data and returns AxData field names."""

    source = "tdx"

    def __init__(
        self,
        client: Any | None = None,
        progress_callback: Callable[..., None] | None = None,
        use_parallel_suspension_quotes: bool | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._progress_callback = progress_callback
        self._use_parallel_suspension_quotes = use_parallel_suspension_quotes
        from . import request_adapter_runtime

        self._options = request_adapter_runtime.normalize_tdx_adapter_options(options)
        self.last_meta: dict[str, Any] = {}
        self._last_topic_lookup_meta: dict[str, Any] = {}

    def supports(self, interface_name: str) -> bool:
        from . import request_adapter_runtime

        return request_adapter_runtime.supports_tdx_request_interface(interface_name)

    def request(self, interface_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_adapter_runtime

        return request_adapter_runtime.request_tdx_adapter(
            self,
            interface_name,
            params,
            existing_client=self._client,
            create_client=self._create_request_client,
            dispatch_with_client=self._dispatch_with_client,
            supports=self.supports,
        )

    def _dispatch_with_client(
        self,
        adapter: Any,
        interface_name: str,
        params: Mapping[str, Any],
        client: Any,
        *,
        should_close: bool,
    ) -> list[dict[str, Any]]:
        from . import request_adapter_runtime

        return request_adapter_runtime.dispatch_tdx_request_with_client(
            adapter,
            interface_name,
            params,
            client,
            should_close=should_close,
            use_parallel_suspension_quotes=self._use_parallel_suspension_quotes,
        )

    def _create_request_client(self, interface_name: str, params: Mapping[str, Any]) -> Any:
        from . import request_adapter_runtime

        return request_adapter_runtime.create_tdx_request_client(
            interface_name,
            params,
            self._options,
            create_client=create_tdx_client,
            configured_hosts_from_options=configured_tdx_hosts_from_options,
        )

    def _request_hosts(self) -> list[str]:
        from . import request_adapter_runtime

        return request_adapter_runtime.tdx_request_hosts(
            self._options,
            configured_hosts_from_options=configured_tdx_hosts_from_options,
        )

    def _configured_hosts(self) -> list[str]:
        from . import request_adapter_runtime

        return request_adapter_runtime.configured_hosts(
            self._options,
            configured_hosts_from_options=configured_tdx_hosts_from_options,
        )

    def _request_stock_codes(
        self,
        client: Any,
        params: Mapping[str, Any],
        *,
        progress_start: int = 20,
        progress_span: int = 40,
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_codes(
            self,
            client,
            params,
            progress_start=progress_start,
            progress_span=progress_span,
        )

    def _request_stock_codes_exchange(
        self,
        client: Any,
        exchange: str,
        *,
        boards: set[str] | None,
        requested_codes: set[str] | None,
        requested_names: set[str] | None,
        start: int,
    ) -> tuple[list[dict[str, Any]], int]:
        from . import request_methods

        return request_methods.request_stock_codes_exchange(
            client,
            exchange,
            boards=boards,
            requested_codes=requested_codes,
            requested_names=requested_names,
            start=start,
        )

    def _request_index_codes(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_codes(self, client, params)

    def _request_etf_codes(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_codes(self, client, params)

    def _request_stock_st_list(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_st_list(self, client, params)

    def _request_stock_suspensions(
        self,
        client: Any,
        params: Mapping[str, Any],
        *,
        use_parallel_quote_clients: bool = False,
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_suspensions(
            self,
            client,
            params,
            use_parallel_quote_clients=use_parallel_quote_clients,
        )

    def _request_stock_order_book(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_order_book(self, client, params)

    def _request_stock_realtime_snapshot(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_realtime_snapshot(self, client, params)

    def _request_index_realtime_snapshot(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_realtime_snapshot(self, client, params)

    def _request_stock_kline(
        self,
        client: Any,
        interface_name: str,
        params: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_kline(self, client, interface_name, params)

    def _request_stock_kline_parallel(
        self,
        interface_name: str,
        params: Mapping[str, Any],
        tdx_codes: Sequence[str],
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_kline_parallel(
            self,
            interface_name,
            params,
            tdx_codes,
        )

    def _request_index_kline(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_kline(self, client, params)

    def _request_stock_realtime_rank(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_realtime_rank(self, client, params)

    def _request_index_realtime_rank(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_realtime_rank(self, client, params)

    def _request_index_quote_refresh(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_quote_refresh(self, client, params)

    def _request_stock_limit_ladder(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_limit_ladder(self, client, params)

    def _request_stock_theme_strength_rank(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_theme_strength_rank(self, client, params)

    def _topic_rows_by_instrument_id(
        self,
        instrument_ids: Sequence[str],
        *,
        topic_type: str,
        progress_start: int | None = None,
        progress_span: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        from . import request_methods

        return request_methods.topic_rows_by_instrument_id(
            self,
            instrument_ids,
            topic_type=topic_type,
            progress_start=progress_start,
            progress_span=progress_span,
        )

    def _request_stock_capital_changes(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_capital_changes(self, client, params)

    def _request_stock_adj_factor(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_adj_factor(self, client, params)

    def _request_stock_auction_process(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_auction_process(self, client, params)

    def _request_stock_intraday_subchart(
        self,
        client: Any,
        interface_name: str,
        params: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_intraday_subchart(
            self,
            client,
            interface_name,
            params,
        )

    def _request_stock_intraday_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_intraday_history(self, client, params)

    def _request_index_intraday_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_intraday_history(self, client, params)

    def _request_stock_intraday_recent_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_intraday_recent_history(self, client, params)

    def _request_stock_intraday_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_intraday_today(self, client, params)

    def _request_index_intraday_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_index_intraday_today(self, client, params)

    def _request_etf_realtime_snapshot(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_realtime_snapshot(self, client, params)

    def _request_etf_realtime_rank(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_realtime_rank(self, client, params)

    def _request_etf_kline(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_kline(self, client, params)

    def _request_etf_intraday_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_intraday_today(self, client, params)

    def _request_etf_intraday_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_intraday_history(self, client, params)

    def _request_etf_trades_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_trades_today(self, client, params)

    def _request_etf_trades_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_trades_history(self, client, params)

    def _request_etf_auction_process(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_auction_process(self, client, params)

    def _request_etf_auction_result_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_etf_auction_result_today(self, client, params)

    def _request_stock_trades_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_trades_today(self, client, params)

    def _request_stock_trades_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_trades_history(self, client, params)

    def _request_stock_auction_result_today(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_auction_result_today(self, client, params)

    def _request_stock_auction_result_history(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_auction_result_history(self, client, params)

    def _request_stock_auction_indicators(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_auction_indicators(self, client, params)

    def _request_stock_daily_share(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_daily_share(self, client, params)

    def _daily_share_tdx_codes(
        self,
        client: Any,
        params: Mapping[str, Any],
        *,
        progress_start: int = 20,
        progress_span: int = 8,
    ) -> tuple[list[str], str | None, dict[str, str]]:
        from . import request_methods

        return request_methods.daily_share_tdx_codes(
            self,
            client,
            params,
            progress_start=progress_start,
            progress_span=progress_span,
        )

    def _request_stock_daily_price_limit(self, client: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_daily_price_limit(self, client, params)

    def _request_stock_finance_info(
        self,
        client: Any,
        interface_name: str,
        params: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_finance_info(self, client, interface_name, params)

    def _request_stock_f10(self, interface_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_f10(self, interface_name, params)

    def _request_stock_f10_many(
        self,
        client: Any,
        spec: F10InterfaceSpec,
        params: Mapping[str, Any],
        requested_codes: Sequence[str],
        *,
        worker_count: int,
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_stock_f10_many(
            client,
            spec,
            params,
            requested_codes,
            worker_count=worker_count,
        )

    def _request_with_asset_type(
        self,
        client: Any,
        params: Mapping[str, Any],
        request_func: Callable[[Any, Mapping[str, Any]], list[dict[str, Any]]],
        *,
        asset_type: str,
    ) -> list[dict[str, Any]]:
        from . import request_methods

        return request_methods.request_with_asset_type(
            self,
            client,
            params,
            request_func,
            asset_type=asset_type,
        )

    def _finish_request_result(self, client: Any, result: Any) -> list[dict[str, Any]]:
        from . import request_adapter_runtime

        return request_adapter_runtime.finish_tdx_request_result(self, client, result)

    def _stats_resource_params(self, params: Mapping[str, Any]) -> dict[str, Any]:
        from . import request_methods

        return request_methods.stats_resource_params(self, params)


def create_tdx_client(**kwargs: Any) -> Any:
    from .client_factory import create_tdx_client as current_create_tdx_client

    return current_create_tdx_client(**kwargs)


def configured_tdx_hosts_from_options(options: Mapping[str, Any]) -> list[str]:
    from .request_host_config import configured_tdx_hosts_from_options as configured

    return configured(options, effective_host_strings_func=effective_host_strings)


def effective_host_strings(kind: str, *, cache_root: str | None = None) -> Sequence[str]:
    from .request_host_config import effective_host_strings as current_effective_host_strings

    return current_effective_host_strings(kind, cache_root=cache_root)


def _should_parallelize_stock_code_request(params: Mapping[str, Any]) -> bool:
    from . import request_adapter_runtime

    return request_adapter_runtime.should_parallelize_tdx_stock_code_request(params)


def _stock_code_request_pool_size(params: Mapping[str, Any]) -> int:
    from . import request_adapter_runtime

    return request_adapter_runtime.tdx_stock_code_request_pool_size(params)


def request_realtime_refresh_rows(
    *,
    code: Any,
    fields: Sequence[str] | None = None,
    cursors: Mapping[str, int] | None = None,
    include_internal: bool = False,
    client: Any | None = None,
) -> list[dict[str, Any]]:
    from .realtime_refresh import request_realtime_refresh_rows as current_request_realtime_refresh_rows

    return current_request_realtime_refresh_rows(
        code=code,
        fields=fields,
        cursors=cursors,
        include_internal=include_internal,
        client=client,
        create_client=create_tdx_client,
    )


def _latest_daily_price_limit_calendar_dates(
    today: date | None = None,
    *,
    request_interface: Callable[..., Any] | None = None,
) -> Any:
    from . import request_methods

    return request_methods._latest_daily_price_limit_calendar_dates(
        today=today,
        request_interface=request_interface,
    )
