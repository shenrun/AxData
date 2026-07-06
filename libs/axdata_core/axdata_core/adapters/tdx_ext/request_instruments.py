"""Instrument selection helpers for TDX extended market requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .local_cache import TdxExtLocalInstrument


InstrumentLoader = Callable[[str | None], Sequence["TdxExtLocalInstrument"]]
MarketLoader = Callable[[str | None], Sequence[Any]]


def request_market_rows(
    params: Mapping[str, Any],
    *,
    root: str | None,
    load_markets: MarketLoader,
    asset_types_param: Callable[[Any], set[str] | None],
    contains_filter: Callable[[Any], Sequence[str]],
    limit_param: Callable[..., int],
) -> list[dict[str, Any]]:
    asset_types = asset_types_param(params.get("asset_type"))
    name_filter = contains_filter(params.get("name"))
    limit = limit_param(params, default=500, maximum=5000)
    rows: list[dict[str, Any]] = []
    for market in load_markets(root):
        if asset_types and market.asset_type not in asset_types:
            continue
        if name_filter and not text_matches_any((market.name, market.short_name, market.group_name), name_filter):
            continue
        rows.append(
            {
                "market_name": market.name,
                "short_name": market.short_name,
                "market_group": market.group_name,
                "asset_type": market.asset_type,
                "asset_type_zh": market.asset_type_zh,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def fund_nav_rows(instruments: Sequence[TdxExtLocalInstrument]) -> list[dict[str, Any]]:
    return [
        {
            "fund_id": item.instrument_id,
            "symbol": item.symbol,
            "fund_type": item.fund_type,
            "name": item.product_name,
            "update_date": item.update_date,
            "nav": item.nav,
            "accumulated_nav": item.accumulated_nav,
        }
        for item in instruments
    ]


def request_instrument_rows(
    interface_name: str,
    params: Mapping[str, Any],
    *,
    root: str | None,
    asset_type_map: Mapping[str, str],
    load_instruments: InstrumentLoader,
    asset_types_param: Callable[[Any], set[str] | None],
    code_filter: Callable[[Any], set[str] | None],
    exchange_filter: Callable[[Any], set[str] | None],
    contains_filter: Callable[[Any], Sequence[str]],
    limit_param: Callable[..., int],
    normalize_code: Callable[[Any], str],
    instrument_to_row: Callable[[Any, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    target_asset_type = asset_type_map.get(interface_name)
    asset_types = {target_asset_type} if target_asset_type else asset_types_param(params.get("asset_type"))
    codes = code_filter(params.get("code"))
    exchanges = exchange_filter(params.get("exchange"))
    name_filter = contains_filter(params.get("name"))
    limit = limit_param(params, default=1000, maximum=100000)
    rows: list[dict[str, Any]] = []
    for item in load_instruments(root):
        if asset_types and item.asset_type not in asset_types:
            continue
        if exchanges and str(item.exchange or "").upper() not in exchanges:
            continue
        if codes and not instrument_code_matches(item, codes, normalize_code=normalize_code):
            continue
        if name_filter and not text_matches_any(
            (item.symbol, item.product_name, item.market_name, item.fund_type, item.bond_type),
            name_filter,
        ):
            continue
        rows.append(instrument_to_row(item, interface_name))
        if len(rows) >= limit:
            break
    return rows


def resolve_requested_instruments(
    params: Mapping[str, Any],
    *,
    asset_type: str,
    root: str | None,
    load_instruments: InstrumentLoader,
    code_filter: Callable[[Any], set[str] | None],
    normalize_code: Callable[[Any], str],
    validation_error: type[Exception],
) -> list[TdxExtLocalInstrument]:
    codes = code_filter(params.get("code"))
    if not codes:
        raise validation_error("code is required")
    result: list[TdxExtLocalInstrument] = []
    for item in load_instruments(root):
        if item.asset_type != asset_type:
            continue
        if instrument_code_matches(item, codes, normalize_code=normalize_code):
            result.append(item)
    missing = sorted(
        codes
        - {normalize_code(item.symbol) for item in result}
        - {normalize_code(item.instrument_id) for item in result}
    )
    if missing:
        raise validation_error(f"unknown {asset_type} code(s): {', '.join(missing)}")
    return result


def find_instrument(
    code: str,
    *,
    asset_type: str,
    root: str | None,
    load_instruments: InstrumentLoader,
    normalize_code: Callable[[Any], str],
) -> TdxExtLocalInstrument | None:
    normalized = normalize_code(code)
    for item in load_instruments(root):
        if item.asset_type == asset_type and normalized in {
            normalize_code(item.symbol),
            normalize_code(item.instrument_id),
        }:
            return item
    return None


def resolve_option_chain_contracts(
    params: Mapping[str, Any],
    *,
    root: str | None,
    load_instruments: InstrumentLoader,
    contains_filter: Callable[[Any], Sequence[str]],
    string_values: Callable[[Any], Sequence[str]],
    exchange_filter: Callable[[Any], set[str] | None],
    limit_param: Callable[..., int],
) -> list[TdxExtLocalInstrument]:
    product_filter = contains_filter(params.get("product_code"))
    month_filter = (
        {str(item).strip() for item in string_values(params.get("contract_month")) if str(item).strip()}
        if params.get("contract_month") not in (None, "")
        else None
    )
    exchanges = exchange_filter(params.get("exchange"))
    limit = limit_param(params, default=50, maximum=100)
    candidates: list[TdxExtLocalInstrument] = []
    for item in load_instruments(root):
        if item.asset_type != "option":
            continue
        if exchanges and str(item.exchange or "").upper() not in exchanges:
            continue
        if product_filter and not text_matches_any((item.product_code, item.product_name), product_filter):
            continue
        if month_filter and str(item.contract_month or "") not in month_filter:
            continue
        if item.option_type not in {"call", "put"} or item.strike_price is None:
            continue
        candidates.append(item)
    candidates.sort(
        key=lambda item: (
            str(item.product_code or ""),
            str(item.contract_month or ""),
            float(item.strike_price or 0),
            0 if item.option_type == "call" else 1,
        )
    )
    selected_keys = []
    selected_key_set = set()
    for item in candidates:
        key = (item.product_code, item.contract_month, item.strike_price)
        if key in selected_key_set:
            continue
        selected_keys.append(key)
        selected_key_set.add(key)
        if len(selected_keys) >= limit:
            break
    return [
        item
        for item in candidates
        if (item.product_code, item.contract_month, item.strike_price) in selected_key_set
    ]


def instrument_code_matches(
    item: TdxExtLocalInstrument,
    codes: set[str],
    *,
    normalize_code: Callable[[Any], str],
) -> bool:
    candidates = {
        normalize_code(item.symbol),
        normalize_code(item.instrument_id),
    }
    return any(code in candidates for code in codes)


def text_matches_any(values: Sequence[Any], filters: Sequence[str]) -> bool:
    haystack = " ".join(str(value or "").lower() for value in values)
    return any(filter_text in haystack for filter_text in filters)
