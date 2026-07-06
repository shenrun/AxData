"""Thin compatibility wrappers for TDX 7709 wire requests."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from axdata_core.source_errors import SourceUnavailableError

from .request_limits import DEFAULT_QUOTE_BATCH_SIZE


def tdx_legacy_quotes(client: Any, securities: Sequence[tuple[str, str]]) -> Any:
    if hasattr(client, "get_legacy_quotes"):
        return client.get_legacy_quotes(securities, batch_size=DEFAULT_QUOTE_BATCH_SIZE)
    if hasattr(client, "quotes") and hasattr(client.quotes, "legacy_all"):
        return client.quotes.legacy_all(securities, batch_size=DEFAULT_QUOTE_BATCH_SIZE)
    raise SourceUnavailableError("TDX client does not expose 0x053e legacy quote requests.")


def tdx_explicit_quotes(client: Any, securities: Sequence[tuple[str, str]]) -> Any:
    if hasattr(client, "get_explicit_quotes"):
        return client.get_explicit_quotes(securities, batch_size=DEFAULT_QUOTE_BATCH_SIZE)
    if hasattr(client, "quotes") and hasattr(client.quotes, "explicit_all"):
        return client.quotes.explicit_all(securities, batch_size=DEFAULT_QUOTE_BATCH_SIZE)
    raise SourceUnavailableError("TDX client does not expose 0x054c explicit quote requests.")


def tdx_refresh_quotes(client: Any, cursors: Sequence[tuple[str, str, int]]) -> Any:
    if hasattr(client, "get_quote_refresh"):
        return client.get_quote_refresh(cursors)
    if hasattr(client, "quotes") and hasattr(client.quotes, "refresh"):
        return client.quotes.refresh(cursors)
    raise SourceUnavailableError("TDX client does not expose 0x0547 quote refresh requests.")


def tdx_category_quotes(
    client: Any,
    *,
    category: int,
    sort_type: int,
    start: int,
    count: int,
    ascending: bool,
    filter_raw: int,
) -> Any:
    if hasattr(client, "get_category_quotes"):
        return client.get_category_quotes(
            category=category,
            sort_type=sort_type,
            start=start,
            count=count,
            ascending=ascending,
            filter_raw=filter_raw,
        )
    if hasattr(client, "quotes") and hasattr(client.quotes, "category"):
        return client.quotes.category(
            category=category,
            sort_type=sort_type,
            start=start,
            count=count,
            ascending=ascending,
            filter_raw=filter_raw,
        )
    raise SourceUnavailableError("TDX client does not expose 0x054b category quote requests.")


def tdx_auction_process(client: Any, tdx_code: str) -> Any:
    if hasattr(client, "get_auction_process"):
        return client.get_auction_process(tdx_code)
    if hasattr(client, "auction") and hasattr(client.auction, "process"):
        return client.auction.process(tdx_code)
    raise SourceUnavailableError("TDX client does not expose 0x056a auction process requests.")


def tdx_kline(
    client: Any,
    code: str,
    *,
    period: str,
    start: int,
    count: int,
    adjust: str,
    anchor_date: Any,
    kind: str = "stock",
) -> Any:
    if hasattr(client, "get_kline"):
        try:
            return client.get_kline(
                code,
                period=period,
                start=start,
                count=count,
                adjust=adjust,
                anchor_date=anchor_date,
                kind=kind,
            )
        except TypeError:
            if kind != "stock":
                raise
            return client.get_kline(
                code,
                period=period,
                start=start,
                count=count,
                adjust=adjust,
                anchor_date=anchor_date,
            )
    if hasattr(client, "bars") and hasattr(client.bars, "get"):
        return client.bars.get(
            code,
            period=period,
            start=start,
            count=count,
            adjust=adjust,
            anchor_date=anchor_date,
            kind=kind,
        )
    raise SourceUnavailableError("TDX client does not expose 0x052d kline requests.")


def tdx_capital_changes(client: Any, code: str) -> Any:
    if hasattr(client, "get_capital_changes"):
        return client.get_capital_changes(code)
    if hasattr(client, "corporate") and hasattr(client.corporate, "capital_changes"):
        return client.corporate.capital_changes(code)
    raise SourceUnavailableError("TDX client does not expose 0x000f capital-change requests.")


def tdx_historical_intraday(client: Any, code: str, *, trade_date: str) -> Any:
    if hasattr(client, "get_historical_intraday"):
        return client.get_historical_intraday(code, trade_date=trade_date)
    if hasattr(client, "intraday") and hasattr(client.intraday, "historical"):
        return client.intraday.historical(code, trade_date=trade_date)
    raise SourceUnavailableError("TDX client does not expose 0x0fb4 historical intraday requests.")


def tdx_recent_historical_intraday(client: Any, code: str, *, trade_date: str) -> Any:
    if hasattr(client, "get_recent_historical_intraday"):
        return client.get_recent_historical_intraday(code, trade_date=trade_date)
    if hasattr(client, "intraday") and hasattr(client.intraday, "recent_historical"):
        return client.intraday.recent_historical(code, trade_date=trade_date)
    raise SourceUnavailableError("TDX client does not expose 0x0feb recent historical intraday requests.")


def tdx_today_intraday(client: Any, code: str) -> Any:
    if hasattr(client, "get_today_intraday"):
        return client.get_today_intraday(code)
    if hasattr(client, "intraday") and hasattr(client.intraday, "today"):
        return client.intraday.today(code)
    raise SourceUnavailableError("TDX client does not expose 0x0537 today intraday requests.")


def tdx_intraday_subchart(client: Any, code: str, *, selector: int) -> Any:
    if hasattr(client, "get_intraday_subchart"):
        return client.get_intraday_subchart(code, selector=selector)
    if hasattr(client, "intraday") and hasattr(client.intraday, "subchart"):
        return client.intraday.subchart(code, selector=selector)
    raise SourceUnavailableError("TDX client does not expose 0x051b intraday subchart requests.")


def tdx_today_trades(client: Any, code: str, *, start: int, count: int) -> Any:
    if hasattr(client, "get_today_trades"):
        return client.get_today_trades(code, start=start, count=count)
    if hasattr(client, "trades") and hasattr(client.trades, "today"):
        return client.trades.today(code, start=start, count=count)
    raise SourceUnavailableError("TDX client does not expose 0x0fc5 today trade-detail requests.")


def tdx_historical_trades(
    client: Any,
    code: str,
    *,
    trade_date: str,
    start: int,
    count: int,
) -> Any:
    if hasattr(client, "get_historical_trades"):
        return client.get_historical_trades(code, trade_date=trade_date, start=start, count=count)
    if hasattr(client, "trades") and hasattr(client.trades, "historical"):
        return client.trades.historical(code, trade_date=trade_date, start=start, count=count)
    raise SourceUnavailableError("TDX client does not expose 0x0fc6 historical trade-detail requests.")


def tdx_finance_info(client: Any, codes: Sequence[str]) -> list[Any]:
    if hasattr(client, "get_finance_info"):
        return [client.get_finance_info(list(codes))]
    if hasattr(client, "finance") and hasattr(client.finance, "info"):
        return [client.finance.info(list(codes))]
    raise SourceUnavailableError("TDX client does not expose 0x0010 finance info requests.")
