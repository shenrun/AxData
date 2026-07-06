"""Source request adapter for TDX extended-asset local catalog interfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from axdata_core.source_errors import SourceAdapterNotFound, SourceRequestValidationError

from .interface_sets import (
    EXT_ASSET_INTERFACE_TO_TYPE,
    FUND_NAV_INTERFACE,
    INTRADAY_INTERFACE_TO_TYPE,
    KLINE_INTERFACE_TO_TYPE,
    OPTION_CHAIN_INTERFACE,
    QUOTE_INTERFACE_TO_TYPE,
    SUPPORTED_INTERFACES,
    TRADES_HISTORY_INTERFACE_TO_TYPE,
    TRADES_TODAY_INTERFACE_TO_TYPE,
)
from .options import normalize_tdx_ext_request_options
from .request_params import (
    EXT_KLINE_PERIODS as _EXT_KLINE_PERIODS,
    asset_types_param as _asset_types_param,
    bool_param as _bool_param,
    code_filter as _code_filter,
    contains_filter as _contains_filter,
    exchange_filter as _exchange_filter,
    float_param as _float_param,
    limit_param as _limit_param,
    normalize_code as _normalize_code,
    optional_text as _optional_text,
    period_param as _period_param,
    required_text as _required_text,
    string_values as _string_values,
)
from .request_series import (
    request_intraday_rows_for_item as _tdx_ext_request_intraday_rows_for_item,
    request_kline_rows_for_item as _tdx_ext_request_kline_rows_for_item,
    request_trade_rows_for_item as _tdx_ext_request_trade_rows_for_item,
)
from .request_execution import request_items as _tdx_ext_request_items
from .request_execution import request_quotes as _tdx_ext_request_quotes
from .request_normalize import (
    bar_to_row as _bar_to_row,
    empty_option_chain_row as _empty_option_chain_row,
    instrument_to_row as _instrument_to_row,
    intraday_to_row as _intraday_to_row,
    macro_bar_to_row as _macro_bar_to_row,
    macro_indicator_category_from_symbol as _macro_indicator_category_from_symbol,
    macro_metadata as _macro_metadata,
    macro_snapshot_row as _macro_snapshot_row,
    normalize_trade_price as _normalize_trade_price,
    open_close_type as _open_close_type,
    option_chain_rows as _option_chain_rows,
    price_tick as _price_tick,
    quote_snapshot_rows as _quote_snapshot_rows,
    quote_to_row as _quote_to_row,
    tick_decimals as _tick_decimals,
    trade_price_scale as _trade_price_scale,
    trade_to_row as _trade_to_row,
)
from .request_instruments import (
    find_instrument as _tdx_ext_find_instrument,
    fund_nav_rows as _tdx_ext_fund_nav_rows,
    instrument_code_matches as _tdx_ext_instrument_code_matches,
    request_market_rows as _tdx_ext_request_market_rows,
    request_instrument_rows as _tdx_ext_request_instrument_rows,
    resolve_option_chain_contracts as _tdx_ext_resolve_option_chain_contracts,
    resolve_requested_instruments as _tdx_ext_resolve_requested_instruments,
    text_matches_any as _tdx_ext_text_matches_any,
)


_LOCAL_CACHE_EXPORTS = {
    "TdxExtLocalInstrument",
    "load_tdx_ext_local_instruments",
    "load_tdx_ext_local_markets",
}
_POOL_EXPORTS = {"TdxExtClientPool", "flatten_results", "resolve_tdx_ext_pool_config"}


def __getattr__(name: str) -> Any:
    if name == "TdxExtClient":
        from .client import TdxExtClient as value
    elif name in _POOL_EXPORTS:
        from . import pool as pool_module

        value = getattr(pool_module, name)
    elif name in _LOCAL_CACHE_EXPORTS:
        from . import local_cache as local_cache_module

        value = getattr(local_cache_module, name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def _tdx_ext_client_class() -> Any:
    client = globals().get("TdxExtClient")
    if client is not None:
        return client
    return __getattr__("TdxExtClient")


def _tdx_ext_pool_tools() -> tuple[Any, Any, Any]:
    pool_class = globals().get("TdxExtClientPool")
    flatten = globals().get("flatten_results")
    resolver = globals().get("resolve_tdx_ext_pool_config")
    if pool_class is None or flatten is None or resolver is None:
        pool_class = __getattr__("TdxExtClientPool")
        flatten = __getattr__("flatten_results")
        resolver = __getattr__("resolve_tdx_ext_pool_config")
    return pool_class, flatten, resolver


def _load_tdx_ext_local_markets(root: str | None) -> Any:
    loader = globals().get("load_tdx_ext_local_markets")
    if loader is None:
        loader = __getattr__("load_tdx_ext_local_markets")
    return loader(root)


def _load_tdx_ext_local_instruments(root: str | None) -> Any:
    loader = globals().get("load_tdx_ext_local_instruments")
    if loader is None:
        loader = __getattr__("load_tdx_ext_local_instruments")
    return loader(root)


class TdxExtRequestAdapter:
    """Adapter that exposes verified extended-asset catalog data."""

    source = "tdx_ext"

    def __init__(
        self,
        options: Mapping[str, Any] | None = None,
        *,
        client_pool: Any | None = None,
        client_pool_config: Any | None = None,
    ) -> None:
        self._options = normalize_tdx_ext_request_options(dict(options or {}))
        self._client_pool = client_pool
        self._client_pool_config = client_pool_config
        self.last_meta: dict[str, Any] = {}

    def supports(self, interface_name: str) -> bool:
        return interface_name in SUPPORTED_INTERFACES

    def request(self, interface_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        if not self.supports(interface_name):
            raise SourceAdapterNotFound(
                f"TDX extended source adapter does not support interface {interface_name!r}."
            )

        root = _optional_text(params.get("tdx_root"))
        if interface_name == "tdx_ext_markets_tdx":
            rows = self._request_markets(params, root=root)
            origin = "local_tdx_extended_cache"
        elif interface_name in QUOTE_INTERFACE_TO_TYPE:
            rows = self._request_realtime_snapshot(interface_name, params, root=root)
            origin = "tdx_extended_source"
        elif interface_name in KLINE_INTERFACE_TO_TYPE:
            rows = self._request_kline(interface_name, params, root=root)
            origin = "tdx_extended_source"
        elif interface_name in INTRADAY_INTERFACE_TO_TYPE:
            rows = self._request_intraday(interface_name, params, root=root)
            origin = "tdx_extended_source"
        elif interface_name in TRADES_HISTORY_INTERFACE_TO_TYPE:
            rows = self._request_trades(interface_name, params, root=root, is_history=True)
            origin = "tdx_extended_source"
        elif interface_name in TRADES_TODAY_INTERFACE_TO_TYPE:
            rows = self._request_trades(interface_name, params, root=root, is_history=False)
            origin = "tdx_extended_source"
        elif interface_name == OPTION_CHAIN_INTERFACE:
            rows = self._request_option_chain(params, root=root)
            origin = "tdx_extended_source"
        elif interface_name == FUND_NAV_INTERFACE:
            rows = self._request_fund_nav(params, root=root)
            origin = "local_tdx_extended_cache"
        else:
            rows = self._request_instruments(interface_name, params, root=root)
            origin = "local_tdx_extended_cache"

        self.last_meta = {
            "source": self.source,
            "persisted": False,
            "count": len(rows),
            "data_origin": origin,
        }
        self.last_meta.update(self._execution_meta())
        return rows

    def _request_markets(self, params: Mapping[str, Any], *, root: str | None) -> list[dict[str, Any]]:
        return _tdx_ext_request_market_rows(
            params,
            root=root,
            load_markets=_load_tdx_ext_local_markets,
            asset_types_param=_asset_types_param,
            contains_filter=_contains_filter,
            limit_param=_limit_param,
        )

    def _request_realtime_snapshot(
        self,
        interface_name: str,
        params: Mapping[str, Any],
        *,
        root: str | None,
    ) -> list[dict[str, Any]]:
        asset_type = QUOTE_INTERFACE_TO_TYPE[interface_name]
        instruments = _resolve_requested_instruments(params, asset_type=asset_type, root=root)
        code_list = [(item.market_id, item.symbol) for item in instruments]
        timeout = _float_param(params.get("timeout"), default=6.0)
        quotes, pool_config, task_count = _tdx_ext_request_quotes(
            code_list,
            options=self._options,
            root=root,
            server_cache_root=self._server_cache_root(),
            timeout=timeout,
            client_factory=_tdx_ext_client_class(),
            pool_tools=_tdx_ext_pool_tools(),
            client_pool=self._client_pool,
            client_pool_config=self._client_pool_config,
        )
        if pool_config:
            self._set_parallel_meta(pool_config, task_count=task_count or 0)

        return _quote_snapshot_rows(
            instruments,
            quotes,
            macro_snapshot=interface_name == "macro_indicator_snapshot_tdx",
            find_instrument=lambda code: _find_instrument(code, asset_type=asset_type, root=root),
        )

    def _request_option_chain(
        self,
        params: Mapping[str, Any],
        *,
        root: str | None,
    ) -> list[dict[str, Any]]:
        contracts = _resolve_option_chain_contracts(params, root=root)
        if not contracts:
            return []

        code_list = [(item.market_id, item.symbol) for item in contracts]
        timeout = _float_param(params.get("timeout"), default=6.0)
        quotes, pool_config, task_count = _tdx_ext_request_quotes(
            code_list,
            options=self._options,
            root=root,
            server_cache_root=self._server_cache_root(),
            timeout=timeout,
            client_factory=_tdx_ext_client_class(),
            pool_tools=_tdx_ext_pool_tools(),
            client_pool=self._client_pool,
            client_pool_config=self._client_pool_config,
        )
        if pool_config:
            self._set_parallel_meta(pool_config, task_count=task_count or 0)

        return _option_chain_rows(contracts, quotes)

    def _request_fund_nav(
        self,
        params: Mapping[str, Any],
        *,
        root: str | None,
    ) -> list[dict[str, Any]]:
        instruments = _resolve_requested_instruments(params, asset_type="fund", root=root)
        return _tdx_ext_fund_nav_rows(instruments)

    def _request_trades(
        self,
        interface_name: str,
        params: Mapping[str, Any],
        *,
        root: str | None,
        is_history: bool,
    ) -> list[dict[str, Any]]:
        asset_type = (
            TRADES_HISTORY_INTERFACE_TO_TYPE[interface_name]
            if is_history
            else TRADES_TODAY_INTERFACE_TO_TYPE[interface_name]
        )
        instruments = _resolve_requested_instruments(params, asset_type=asset_type, root=root)
        trade_date = _required_text(params.get("trade_date"), "trade_date") if is_history else None
        all_rows = _bool_param(params.get("all"), default=False)
        limit = _limit_param(params, default=100000 if all_rows else 120, maximum=100000)
        page_size = _limit_param({"limit": params.get("page_size", 1800)}, default=1800, maximum=1800)
        timeout = _float_param(params.get("timeout"), default=6.0)
        pool_tools = _tdx_ext_pool_tools()
        flatten_results = pool_tools[1]

        def request_item_trades(client: Any, item: TdxExtLocalInstrument) -> list[dict[str, Any]]:
            return _tdx_ext_request_trade_rows_for_item(
                client,
                item,
                is_history=is_history,
                trade_date=trade_date,
                all_rows=all_rows,
                limit=limit,
                page_size=page_size,
                flatten_results=flatten_results,
            )

        rows, pool_config, task_count = _tdx_ext_request_items(
            instruments,
            options=self._options,
            root=root,
            server_cache_root=self._server_cache_root(),
            timeout=timeout,
            client_factory=_tdx_ext_client_class(),
            pool_tools=pool_tools,
            request_item=request_item_trades,
            client_pool=self._client_pool,
            client_pool_config=self._client_pool_config,
        )
        if pool_config:
            self._set_parallel_meta(pool_config, task_count=task_count or 0)
        return rows

    def _request_kline(
        self,
        interface_name: str,
        params: Mapping[str, Any],
        *,
        root: str | None,
    ) -> list[dict[str, Any]]:
        asset_type = KLINE_INTERFACE_TO_TYPE[interface_name]
        instruments = _resolve_requested_instruments(params, asset_type=asset_type, root=root)
        period_name = _period_param(params.get("period"), default="day")
        period_raw = _EXT_KLINE_PERIODS[period_name]
        count = _limit_param(params, default=30, maximum=800)
        timeout = _float_param(params.get("timeout"), default=6.0)

        def request_item_kline(client: Any, item: TdxExtLocalInstrument) -> list[dict[str, Any]]:
            return _tdx_ext_request_kline_rows_for_item(
                client,
                item,
                interface_name=interface_name,
                period_raw=period_raw,
                period_name=period_name,
                count=count,
            )

        rows, pool_config, task_count = _tdx_ext_request_items(
            instruments,
            options=self._options,
            root=root,
            server_cache_root=self._server_cache_root(),
            timeout=timeout,
            client_factory=_tdx_ext_client_class(),
            pool_tools=_tdx_ext_pool_tools(),
            request_item=request_item_kline,
            client_pool=self._client_pool,
            client_pool_config=self._client_pool_config,
        )
        if pool_config:
            self._set_parallel_meta(pool_config, task_count=task_count or 0)
        return rows

    def _request_intraday(
        self,
        interface_name: str,
        params: Mapping[str, Any],
        *,
        root: str | None,
    ) -> list[dict[str, Any]]:
        asset_type = INTRADAY_INTERFACE_TO_TYPE[interface_name]
        instruments = _resolve_requested_instruments(params, asset_type=asset_type, root=root)
        is_history = interface_name.endswith("_history_tdx")
        trade_date = _required_text(params.get("trade_date"), "trade_date") if is_history else None
        timeout = _float_param(params.get("timeout"), default=6.0)

        def request_item_intraday(client: Any, item: TdxExtLocalInstrument) -> list[dict[str, Any]]:
            return _tdx_ext_request_intraday_rows_for_item(
                client,
                item,
                is_history=is_history,
                trade_date=trade_date,
            )

        rows, pool_config, task_count = _tdx_ext_request_items(
            instruments,
            options=self._options,
            root=root,
            server_cache_root=self._server_cache_root(),
            timeout=timeout,
            client_factory=_tdx_ext_client_class(),
            pool_tools=_tdx_ext_pool_tools(),
            request_item=request_item_intraday,
            client_pool=self._client_pool,
            client_pool_config=self._client_pool_config,
        )
        if pool_config:
            self._set_parallel_meta(pool_config, task_count=task_count or 0)
        return rows

    def _server_cache_root(self) -> str | None:
        value = self._options.get("server_cache_root")
        return str(value) if value not in (None, "") else None

    def _set_parallel_meta(self, pool_config: Any, *, task_count: int) -> None:
        self._parallel_meta = {
            "tdx_ext_parallel": True,
            "tdx_ext_source_server_count": pool_config.source_server_count,
            "tdx_ext_connections_per_server": pool_config.requested_connections_per_server,
            "tdx_ext_connection_count": pool_config.connection_count,
            "tdx_ext_task_count": task_count,
        }

    def _execution_meta(self) -> dict[str, Any]:
        meta = getattr(self, "_parallel_meta", None)
        if isinstance(meta, dict):
            self._parallel_meta = None
            return dict(meta)
        return {"tdx_ext_parallel": False}

    def _request_instruments(
        self,
        interface_name: str,
        params: Mapping[str, Any],
        *,
        root: str | None,
    ) -> list[dict[str, Any]]:
        return _tdx_ext_request_instrument_rows(
            interface_name,
            params,
            root=root,
            asset_type_map=EXT_ASSET_INTERFACE_TO_TYPE,
            load_instruments=_load_tdx_ext_local_instruments,
            asset_types_param=_asset_types_param,
            code_filter=_code_filter,
            exchange_filter=_exchange_filter,
            contains_filter=_contains_filter,
            limit_param=_limit_param,
            normalize_code=_normalize_code,
            instrument_to_row=_instrument_to_row,
        )


def _resolve_requested_instruments(
    params: Mapping[str, Any],
    *,
    asset_type: str,
    root: str | None,
) -> list[TdxExtLocalInstrument]:
    return _tdx_ext_resolve_requested_instruments(
        params,
        asset_type=asset_type,
        root=root,
        load_instruments=_load_tdx_ext_local_instruments,
        code_filter=_code_filter,
        normalize_code=_normalize_code,
        validation_error=SourceRequestValidationError,
    )


def _find_instrument(
    code: str,
    *,
    asset_type: str,
    root: str | None,
) -> TdxExtLocalInstrument | None:
    return _tdx_ext_find_instrument(
        code,
        asset_type=asset_type,
        root=root,
        load_instruments=_load_tdx_ext_local_instruments,
        normalize_code=_normalize_code,
    )


def _resolve_option_chain_contracts(
    params: Mapping[str, Any],
    *,
    root: str | None,
) -> list[TdxExtLocalInstrument]:
    return _tdx_ext_resolve_option_chain_contracts(
        params,
        root=root,
        load_instruments=_load_tdx_ext_local_instruments,
        contains_filter=_contains_filter,
        string_values=_string_values,
        exchange_filter=_exchange_filter,
        limit_param=_limit_param,
    )


def _instrument_code_matches(item: TdxExtLocalInstrument, codes: set[str]) -> bool:
    return _tdx_ext_instrument_code_matches(item, codes, normalize_code=_normalize_code)


def _text_matches_any(values: Sequence[Any], filters: Sequence[str]) -> bool:
    return _tdx_ext_text_matches_any(values, filters)
