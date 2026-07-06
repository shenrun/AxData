"""Derived TDX request row builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from .codes import MARKET_TO_EXCHANGE, MARKET_TO_ID, tdx_code_to_instrument_id
from .normalize_utils import (
    auction_open_volume_hand,
    bar_trade_date,
    get_value,
    limit_board_text,
    market_value,
    open_volume_ratio,
    optional_int,
    round_optional_float,
    safe_ratio,
    safe_ratio_pct,
    tenk_shares_to_lots,
    tenk_to_unit,
    tenk_yuan,
)
from .price_limits import (
    limit_ladder_status,
    positive_number,
    price_limit_name_flag,
    price_limit_ratio_from_rule,
    price_limit_rule,
    rule_price_limits,
    st_type_from_name,
)
from .request_filters import board_matches
from .security_codes import board_from_tdx_code
from .snapshot_normalize import (
    normalize_realtime_snapshot_row,
    quote_level_at,
    quote_tdx_code,
)
from axdata_core.source_errors import SourceRequestValidationError


def normalize_auction_indicator_row(
    quote: Any,
    *,
    stat_row: Any | None,
    stat2_row: Any | None,
    recent_daily_bars: Sequence[Any],
    finance_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    snapshot = normalize_realtime_snapshot_row(quote)
    open_price = snapshot.get("open")
    last_price = snapshot.get("last_price")
    open_amount = snapshot.get("open_amount")
    amount = snapshot.get("amount")
    locked_amount = snapshot.get("locked_amount")
    open_volume_hand_value = auction_open_volume_hand(open_amount, open_price)
    free_float_shares = tenk_to_unit(get_value(stat_row, "free_float_shares_10k"))
    free_float_market_value = market_value(free_float_shares, last_price)
    float_shares = get_value(finance_row, "float_share") if finance_row else None
    float_market_value = market_value(float_shares, last_price)
    prev_amount = tenk_yuan(get_value(stat2_row, "prev_amount_10k"))
    prev_seal_amount = tenk_yuan(get_value(stat2_row, "prev_seal_amount_10k"))
    prev2_seal_amount = tenk_yuan(get_value(stat2_row, "prev2_seal_amount_10k"))
    prev_open_amount = tenk_yuan(get_value(stat2_row, "prev_open_amount_10k"))
    prev_open_volume_hand = round_optional_float(get_value(stat2_row, "prev_open_volume_hand"))
    limit_stat_days = optional_int(get_value(stat_row, "limit_stat_days"))
    limit_up_count = optional_int(get_value(stat_row, "limit_up_count_in_stat_days"))
    return {
        "instrument_id": snapshot.get("instrument_id"),
        "symbol": snapshot.get("symbol"),
        "tdx_code": str(snapshot.get("tdx_code") or "").lower(),
        "exchange": snapshot.get("exchange"),
        "stats_date": get_value(stat2_row, "stats_date") or get_value(stat_row, "stats_date"),
        "open_price": open_price,
        "pre_close": snapshot.get("pre_close"),
        "open_change_pct": snapshot.get("open_change_pct"),
        "open_amount": open_amount,
        "open_volume_hand": open_volume_hand_value,
        "open_volume_ratio": open_volume_ratio(open_volume_hand_value, recent_daily_bars),
        "open_turnover_z": safe_ratio_pct(open_volume_hand_value, tenk_shares_to_lots(get_value(stat_row, "free_float_shares_10k"))),
        "open_prev_amount_ratio": safe_ratio_pct(open_amount, prev_amount),
        "auction_prev_volume_ratio": safe_ratio(open_volume_hand_value, prev_open_volume_hand),
        "opening_rush": snapshot.get("opening_rush"),
        "open_prev_seal_ratio": safe_ratio_pct(open_amount, prev_seal_amount),
        "prev_amount": prev_amount,
        "prev_seal_amount": prev_seal_amount,
        "prev2_seal_amount": prev2_seal_amount,
        "prev_open_volume_hand": prev_open_volume_hand,
        "prev_open_amount": prev_open_amount,
        "float_shares": round_optional_float(float_shares),
        "float_market_value": float_market_value,
        "free_float_shares": free_float_shares,
        "free_float_market_value": free_float_market_value,
        "seal_amount": locked_amount,
        "seal_to_amount_ratio": safe_ratio(locked_amount, amount),
        "seal_to_float_ratio": safe_ratio_pct(locked_amount, free_float_market_value),
        "seal_prev_ratio": safe_ratio(locked_amount, prev_seal_amount),
        "limit_stat_days": limit_stat_days,
        "limit_up_count_in_stat_days": limit_up_count,
        "limit_board_text": limit_board_text(limit_stat_days, limit_up_count),
        "limit_up_streak_days": optional_int(get_value(stat_row, "limit_up_streak_days")),
        "year_limit_up_days": optional_int(get_value(stat_row, "year_limit_up_days")),
    }


def normalize_daily_share_row(
    tdx_code: str,
    *,
    stats_date: Any,
    stat_row: Any | None,
    finance_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    symbol = instrument_id.split(".", 1)[0]
    total_share = get_value(finance_row, "total_share") if finance_row else None
    float_share = get_value(finance_row, "float_share") if finance_row else None
    free_float_share = tenk_to_unit(get_value(stat_row, "free_float_shares_10k"))
    row_stats_date = get_value(stat_row, "stats_date") or stats_date
    row_stats_date = str(row_stats_date) if row_stats_date not in (None, "") else None
    return {
        "trade_date": row_stats_date,
        "instrument_id": instrument_id,
        "symbol": symbol,
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], tdx_code[:2].upper()),
        "total_share": round_optional_float(total_share),
        "float_share": round_optional_float(float_share),
        "free_float_share_z": free_float_share,
        "finance_updated_date": get_value(finance_row, "updated_date") if finance_row else None,
        "share_source": daily_share_source(total_share, float_share, free_float_share),
    }


def normalize_daily_price_limit_row(
    tdx_code: str,
    *,
    target_trade_date: Any,
    base: Any,
    name: str | None,
) -> dict[str, Any]:
    base_bar = getattr(base, "bar", None)
    pre_close = round_optional_float(get_value(base_bar, "close")) if base_bar is not None else None
    pre_close_trade_date = bar_trade_date(base_bar) if base_bar is not None else None
    return normalize_daily_price_limit_from_pre_close(
        tdx_code,
        target_trade_date=target_trade_date,
        pre_close_trade_date=pre_close_trade_date,
        pre_close=pre_close,
        pre_close_source="tdx_daily_kline" if pre_close_trade_date else None,
        name=name,
    )


def normalize_daily_price_limit_snapshot_row(
    tdx_code: str,
    *,
    target_trade_date: Any,
    pre_close_trade_date: Any,
    snapshot: Mapping[str, Any] | None,
    snapshot_base_field: str,
    name: str | None,
) -> dict[str, Any]:
    if snapshot_base_field == "last_price":
        pre_close = snapshot.get("last_price") if snapshot is not None else None
    else:
        pre_close = snapshot.get("pre_close") if snapshot is not None else None
    return normalize_daily_price_limit_from_pre_close(
        tdx_code,
        target_trade_date=target_trade_date,
        pre_close_trade_date=pre_close_trade_date,
        pre_close=pre_close,
        pre_close_source="tdx_realtime_snapshot" if snapshot is not None else None,
        name=name,
    )


def normalize_daily_price_limit_from_pre_close(
    tdx_code: str,
    *,
    target_trade_date: Any,
    pre_close_trade_date: Any,
    pre_close: Any,
    pre_close_source: str | None,
    name: str | None,
) -> dict[str, Any]:
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    symbol = instrument_id.split(".", 1)[0]
    exchange = MARKET_TO_EXCHANGE.get(tdx_code[:2], tdx_code[:2].upper())
    normalized_pre_close = round_optional_float(pre_close)
    normalized_pre_close_trade_date = str(pre_close_trade_date) if pre_close_trade_date not in (None, "") else None
    name_flag = price_limit_name_flag(name)
    limit_ratio = price_limit_ratio_from_rule(tdx_code, name_flag)
    limit_rule = price_limit_rule(tdx_code, name_flag)
    limit_status = "normal"
    if limit_ratio is None:
        limit_up_price = None
        limit_down_price = None
        limit_status = "no_price_limit"
    elif normalized_pre_close in (None, ""):
        limit_up_price = None
        limit_down_price = None
        limit_status = "missing_pre_close"
    else:
        limit_up_price, limit_down_price = rule_price_limits(normalized_pre_close, limit_ratio)

    return {
        "trade_date": str(target_trade_date) if target_trade_date not in (None, "") else None,
        "instrument_id": instrument_id,
        "symbol": symbol,
        "tdx_code": tdx_code,
        "exchange": exchange,
        "name": name,
        "name_flag": name_flag,
        "pre_close_trade_date": normalized_pre_close_trade_date,
        "pre_close": normalized_pre_close,
        "pre_close_source": pre_close_source if normalized_pre_close not in (None, "") else None,
        "limit_up_price": limit_up_price,
        "limit_down_price": limit_down_price,
        "limit_ratio_pct": limit_ratio,
        "limit_rule": limit_rule,
        "limit_status": limit_status,
    }


def normalize_limit_ladder_row(
    snapshot: Mapping[str, Any],
    *,
    stats: Any,
    name: str | None,
    boards: set[str] | None,
    include_touched: bool,
) -> dict[str, Any] | None:
    tdx_code = str(snapshot.get("tdx_code") or "").lower()
    if not tdx_code:
        return None
    board = board_from_tdx_code(tdx_code)
    if not board_matches(board, boards):
        return None
    name_flag = price_limit_name_flag(name)
    if name_flag in {"ST", "*ST"} or st_type_from_name(name):
        return None
    limit_ratio = price_limit_ratio_from_rule(tdx_code, name_flag)
    if limit_ratio is None:
        return None
    limit_up_price, _limit_down_price = rule_price_limits(snapshot.get("pre_close"), limit_ratio)
    last_price = snapshot.get("last_price")
    pre_close = snapshot.get("pre_close")
    if not positive_number(last_price) or not positive_number(pre_close) or not positive_number(limit_up_price):
        return None
    status = limit_ladder_status(snapshot, limit_up_price)
    if status == "none" or (status == "touched" and not include_touched):
        return None
    market_id = MARKET_TO_ID.get(tdx_code[:2], 0)
    stat_row, _stat2_row = stats.row(market_id, tdx_code[2:])
    ladder_level = limit_ladder_level(stat_row, stats.stats_date)
    recent_days = optional_int(get_value(stat_row, "limit_stat_days"))
    recent_count = optional_int(get_value(stat_row, "limit_up_count_in_stat_days"))
    if status == "sealed":
        recent_days, recent_count = today_limit_board_window(recent_days, recent_count, stats.stats_date)
    amount = snapshot.get("amount")
    seal_amount = snapshot.get("locked_amount") if status == "sealed" else None
    free_float_shares = tenk_to_unit(get_value(stat_row, "free_float_shares_10k"))
    free_float_market_value = market_value(free_float_shares, last_price)
    return {
        "ladder_level": ladder_level if status == "sealed" else None,
        "limit_board_text": limit_board_text(recent_days, recent_count),
        "trade_date": limit_ladder_trade_date(stats.stats_date),
        "stats_date": stats.stats_date,
        "rank": snapshot.get("rank"),
        "limit_status": status,
        "instrument_id": snapshot.get("instrument_id"),
        "symbol": snapshot.get("symbol"),
        "tdx_code": tdx_code,
        "exchange": snapshot.get("exchange"),
        "name": name,
        "last_price": last_price,
        "pre_close": snapshot.get("pre_close"),
        "limit_up_price": limit_up_price,
        "change_pct": snapshot.get("change_pct"),
        "high": snapshot.get("high"),
        "amount": amount,
        "seal_amount": seal_amount,
        "free_float_market_value": free_float_market_value,
        "seal_to_amount_ratio": safe_ratio(seal_amount, amount),
        "limit_stat_days": recent_days,
        "limit_up_count_in_stat_days": recent_count,
        "limit_up_streak_days": optional_int(get_value(stat_row, "limit_up_streak_days")),
        "year_limit_up_days": limit_ladder_year_limit_up_days(stat_row, status, stats.stats_date),
        "primary_theme": None,
        "secondary_themes": None,
        "top_theme_names": None,
        "top_themes": [],
        "themes": [],
        "theme_count": 0,
        "theme_strength_score": None,
        "same_theme_limit_up_count": None,
        "same_theme_highest_board": None,
        "same_theme_lianban_count": None,
    }


def daily_share_source(total_share: Any, float_share: Any, free_float_share: Any) -> str:
    sources = []
    if total_share not in (None, "") or float_share not in (None, ""):
        sources.append("finance_snapshot")
    if free_float_share not in (None, ""):
        sources.append("tdxstat")
    return "+".join(sources) if sources else "empty"


def limit_ladder_rank_page_below_threshold(rows: Sequence[Mapping[str, Any]], threshold: float) -> bool:
    if not rows:
        return True
    return all(not numeric_at_or_above(row.get("change_pct"), threshold) for row in rows)


def limit_ladder_candidate(row: Mapping[str, Any], *, include_touched: bool) -> bool:
    change_pct = row.get("change_pct")
    high_change_pct = row.get("high_change_pct")
    threshold = 4.5 if include_touched else 8.5
    for value in (change_pct, high_change_pct):
        try:
            if value is not None and float(value) >= threshold:
                return True
        except (TypeError, ValueError):
            continue
    return False


def limit_ladder_needs_name_lookup(
    snapshot: Mapping[str, Any],
    *,
    boards: set[str] | None,
    include_touched: bool,
) -> bool:
    tdx_code = str(snapshot.get("tdx_code") or "").lower()
    if not tdx_code:
        return False
    if not board_matches(board_from_tdx_code(tdx_code), boards):
        return False
    if not limit_ladder_candidate(snapshot, include_touched=include_touched):
        return False
    limit_ratio = price_limit_ratio_from_rule(tdx_code, None)
    if limit_ratio is None:
        return False
    limit_up_price, _limit_down_price = rule_price_limits(snapshot.get("pre_close"), limit_ratio)
    if not positive_number(snapshot.get("last_price")) or not positive_number(snapshot.get("pre_close")):
        return False
    if not positive_number(limit_up_price):
        return False
    status = limit_ladder_status(snapshot, limit_up_price)
    return status != "none" and (include_touched or status != "touched")


def numeric_at_or_above(value: Any, threshold: float) -> bool:
    try:
        return value is not None and float(value) >= threshold
    except (TypeError, ValueError):
        return False


_LIMIT_LADDER_PUBLIC_FIELDS = (
    "trade_date",
    "ladder_level",
    "limit_board_text",
    "instrument_id",
    "name",
    "last_price",
    "change_pct",
    "limit_status",
    "amount",
    "seal_amount",
    "seal_to_amount_ratio",
    "free_float_market_value",
    "primary_theme",
    "secondary_themes",
    "year_limit_up_days",
    "symbol",
    "exchange",
    "pre_close",
    "limit_up_price",
)


def limit_ladder_public_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in _LIMIT_LADDER_PUBLIC_FIELDS}


def limit_ladder_trade_date(stats_date: Any) -> str:
    return default_daily_price_limit_trade_date(stats_date)


def stats_date_is_today(stats_date: Any) -> bool:
    stats_text = str(stats_date or "").strip()
    return bool(stats_text) and stats_text == datetime.now().strftime("%Y%m%d")


def limit_ladder_level(stat_row: Any | None, stats_date: Any) -> int:
    prior_streak = optional_int(get_value(stat_row, "limit_up_streak_days")) or 0
    if stats_date_is_today(stats_date):
        return max(1, prior_streak)
    return max(1, prior_streak + 1)


def today_limit_board_window(days: int | None, count: int | None, stats_date: Any) -> tuple[int | None, int | None]:
    if stats_date_is_today(stats_date):
        return days, count
    next_days = (days or 0) + 1
    next_count = (count or 0) + 1
    return next_days if next_days > 0 else None, next_count if next_count > 0 else None


def limit_ladder_year_limit_up_days(stat_row: Any | None, status: str, stats_date: Any) -> int | None:
    value = optional_int(get_value(stat_row, "year_limit_up_days"))
    if value is None:
        return None
    if status == "sealed" and not stats_date_is_today(stats_date):
        return value + 1
    return value


def limit_ladder_topic_type(value: Any) -> str:
    text = str(value or "theme").strip().lower()
    if text in {"theme", "主题", "题材"}:
        return "theme"
    if text in {"sector", "板块"}:
        return "sector"
    raise SourceRequestValidationError("topic_type must be theme or sector")


def limit_ladder_count_param(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, str) and value.strip().lower() == "all":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise SourceRequestValidationError("count must be an integer or 'all'") from exc
    if parsed < 1:
        raise SourceRequestValidationError("count must be >= 1")
    if parsed > 500:
        raise SourceRequestValidationError("count must be <= 500")
    return parsed


def normalize_order_book_rows(quote: Any) -> list[dict[str, Any]]:
    tdx_code = quote_tdx_code(quote)
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    symbol = instrument_id.split(".", 1)[0]
    exchange = MARKET_TO_EXCHANGE.get(tdx_code[:2], str(get_value(quote, "exchange") or "").upper())
    bid_levels = list(get_value(quote, "bid_levels", ()) or ())
    ask_levels = list(get_value(quote, "ask_levels", ()) or ())

    rows: list[dict[str, Any]] = []
    for index in range(5):
        bid_level = quote_level_at(bid_levels, index)
        ask_level = quote_level_at(ask_levels, index)
        rows.append(
            {
                "instrument_id": instrument_id,
                "symbol": symbol,
                "tdx_code": tdx_code,
                "exchange": exchange,
                "level": index + 1,
                "bid_price": round_optional_float(get_value(bid_level, "price")) if bid_level is not None else None,
                "bid_volume": optional_int(get_value(bid_level, "volume")) if bid_level is not None else None,
                "ask_price": round_optional_float(get_value(ask_level, "price")) if ask_level is not None else None,
                "ask_volume": optional_int(get_value(ask_level, "volume")) if ask_level is not None else None,
            }
        )
    return rows


def normalize_adj_factor_row(tdx_code: str, trade_date: str, adj_factor: float) -> dict[str, Any]:
    instrument_id = tdx_code_to_instrument_id(tdx_code)
    return {
        "instrument_id": instrument_id,
        "ts_code": instrument_id,
        "symbol": instrument_id.split(".", 1)[0],
        "tdx_code": tdx_code,
        "exchange": MARKET_TO_EXCHANGE.get(tdx_code[:2], tdx_code[:2].upper()),
        "trade_date": trade_date,
        "adj_factor": round(float(adj_factor), 10),
    }


def default_daily_price_limit_trade_date(stats_date: Any) -> str | None:
    stats_text = str(stats_date or "").strip()
    today_text = datetime.now().strftime("%Y%m%d")
    weekday = datetime.now().weekday()
    if weekday < 5 and (not stats_text or today_text > stats_text):
        return today_text
    return stats_text or today_text


def before_daily_close_buffer(value: datetime) -> bool:
    return value.hour < 15 or (value.hour == 15 and value.minute < 30)
