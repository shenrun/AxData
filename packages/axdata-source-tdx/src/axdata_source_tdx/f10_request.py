"""TDX 7615 F10 request orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from axdata_core.source_errors import SourceUnavailableError

from .codes import (
    MARKET_TO_EXCHANGE,
    tdx_code_to_instrument_id,
)
from .f10_normalize import (
    f10_date_text,
    f10_first_text,
    f10_market_from_market_code,
    f10_number,
    normalize_f10_plain_text,
)
from .f10_params import (
    analyst_target_stats,
    bool_param,
    control_ranking_item,
    f10_business_period_candidates,
    f10_context,
    f10_unfiltered_page_params,
    int_param,
)
from .f10_postprocess import (
    filter_f10_rows,
    normalize_dividend_metrics_summary_rows,
    normalize_equity_financing_rows,
    normalize_f10_row,
    postprocess_f10_rows,
)
from .f10_render import render_f10_body
from .tdx_f10_models import F10InterfaceSpec


def f10_interface_specs() -> Mapping[str, F10InterfaceSpec]:
    from .tdx_f10_specs import F10_INTERFACE_SPECS

    return F10_INTERFACE_SPECS


_f10_interface_specs = f10_interface_specs


def __getattr__(name: str) -> Any:
    if name == "parse_tqlex_tables":
        from .tqlex import parse_tqlex_tables as value

        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _parse_tqlex_tables(payload: dict[str, Any]) -> tuple[Any, ...]:
    parser = globals().get("parse_tqlex_tables")
    if parser is None:
        parser = __getattr__("parse_tqlex_tables")
    return parser(payload)


def request_f10_interface(client: Any, spec: F10InterfaceSpec, params: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Request one TDX 7615 F10 interface and normalize rows."""

    params = prepare_f10_params(client, spec, params)
    if spec.name == "stock_business_composition_tdx" and params.get("period") in (None, ""):
        rows: list[dict[str, Any]] = []
        for period in f10_business_composition_periods(client, params):
            period_params = dict(params)
            period_params["period"] = period
            rows.extend(request_f10_interface_once(client, spec, period_params))
        return rows
    if spec.name == "stock_private_placement_allocations_tdx" and params.get("event_date") in (None, ""):
        rows = []
        for event_date in f10_private_placement_dates(client, params):
            event_params = dict(params)
            event_params["event_date"] = event_date
            rows.extend(request_f10_interface_once(client, spec, event_params))
        return rows
    if spec.name == "stock_shareholder_change_plans_tdx":
        rows = request_f10_all_pages(
            client,
            spec,
            params,
            key_fields=("announcement_date", "direction", "shareholder_name", "start_date", "end_date", "detail_id"),
        )
        return filter_f10_rows(spec, rows, params)
    if spec.name == "stock_northbound_holding_tdx":
        rows = request_f10_all_pages(
            client,
            spec,
            params,
            key_fields=("date", "channel_type", "holding_volume", "change_volume"),
        )
        return filter_f10_rows(spec, rows, params)
    if spec.name == "stock_analyst_rating_tdx":
        rows = request_analyst_rating_rows(client, spec, params)
        return filter_f10_rows(spec, rows, params)
    return request_f10_interface_once(client, spec, params)


def request_analyst_rating_rows(
    client: Any,
    spec: F10InterfaceSpec,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    context = f10_context(spec, params)
    rating_tables = request_f10_tables(client, spec.entry, {"Params": ["jgpj", context["code"], "", ""]})
    if not rating_tables:
        return []
    target_tables = request_f10_tables(client, spec.entry, {"Params": ["jgmbj", context["code"], "", ""]})
    target_stats = analyst_target_stats(target_tables)

    rows = []
    for source_row in rating_tables[0].rows:
        row = normalize_f10_row(spec, source_row, context)
        row["target_price"] = f10_number(target_stats.get("N005"), integer=False)
        row["target_price_low"] = f10_number(target_stats.get("N007"), integer=False)
        row["target_price_high"] = f10_number(target_stats.get("N008"), integer=False)
        row["current_price"] = f10_number(target_stats.get("N006"), integer=False)
        row["upside_pct"] = f10_number(target_stats.get("N004"), integer=False)
        rows.append(row)
    return rows


def request_f10_tables(client: Any, entry: str, body: Mapping[str, Any]) -> tuple[Any, ...]:
    try:
        payload = client.request(entry, body)
    except (TimeoutError, OSError) as exc:
        raise SourceUnavailableError(f"TDX F10 source is unavailable: {exc}") from exc
    return _parse_tqlex_tables(payload)


def normalize_institution_holding_rows(
    spec: F10InterfaceSpec,
    tables: Sequence[Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not tables:
        return []
    trend_rows = list(tables[0].rows)
    period_rows = list(tables[1].rows) if len(tables) > 1 else []
    rows: list[dict[str, Any]] = []
    for index, source_row in enumerate(trend_rows):
        meta_row = period_rows[index] if index < len(period_rows) else {}
        row = normalize_f10_row(spec, source_row, context)
        row["report_period"] = f10_first_text(meta_row, ("N004",))
        rows.append(row)
    return rows


def normalize_control_ranking_rows(
    spec: F10InterfaceSpec,
    tables: Sequence[Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    table_index = min(max(spec.main_table_index, 0), len(tables) - 1)
    rows: list[dict[str, Any]] = []
    for source_row in tables[table_index].rows:
        date_text = f10_date_text(source_row.get("N001"))
        ranking_items = source_row.get("N002")
        if not isinstance(ranking_items, list):
            ranking_items = [source_row]
        for ranking_item in ranking_items:
            parsed = control_ranking_item(ranking_item)
            if not parsed:
                continue
            market = f10_market_from_market_code(parsed.get("market_code"))
            symbol = str(parsed.get("symbol") or "").strip()
            rows.append(
                {
                    "date": date_text,
                    "instrument_id": tdx_code_to_instrument_id(market + symbol)
                    if market and len(symbol) == 6 and symbol.isdigit()
                    else None,
                    "exchange": MARKET_TO_EXCHANGE.get(market) if market else None,
                    "rank": f10_number(parsed.get("rank"), integer=True),
                    "market_code": f10_number(parsed.get("market_code"), integer=True),
                    "symbol": symbol,
                    "name": parsed.get("name"),
                    "control_ratio_pct": f10_number(parsed.get("control_ratio_pct"), integer=False),
                }
            )
    return rows


def request_f10_interface_once(client: Any, spec: F10InterfaceSpec, params: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Request one concrete F10 body and normalize rows."""

    context = f10_context(spec, params)
    body = render_f10_body(spec.body_template, context, spec.body_kind)
    tables = request_f10_tables(client, spec.entry, body)
    if not tables:
        return []
    if spec.name == "stock_dividend_metrics_tdx" and context.get("function") == "pxmz":
        rows = normalize_dividend_metrics_summary_rows(spec, tables, context)
        rows = filter_f10_rows(spec, rows, params)
        return rows
    if spec.name == "stock_equity_financing_events_tdx":
        rows = normalize_equity_financing_rows(spec, tables, context)
        rows = filter_f10_rows(spec, rows, params)
        return rows
    if spec.name == "stock_institution_holding_tdx":
        rows = normalize_institution_holding_rows(spec, tables, context)
        rows = filter_f10_rows(spec, rows, params)
        return rows
    if spec.name == "concept_control_ranking_tdx":
        rows = normalize_control_ranking_rows(spec, tables, context)
        rows = filter_f10_rows(spec, rows, params)
        count = int_param(params, "count", 20, minimum=1, maximum=500)
        return rows[:count]
    table_index = min(max(spec.main_table_index, 0), len(tables) - 1)
    main_rows = list(tables[table_index].rows)
    meta_rows = list(tables[0].rows) if table_index != 0 and tables else []
    if spec.name == "stock_valuation_band_tdx" and len(tables) > 1:
        meta_rows = list(tables[1].rows)
    if spec.name == "stock_forecast_consensus_tdx":
        meta_row: dict[str, Any] = {}
        if tables:
            meta_row.update(tables[0].rows[0] if tables[0].rows else {})
        if len(tables) > 4 and tables[4].rows:
            meta_row.update(tables[4].rows[0])
        meta_rows = [meta_row] if meta_row else []
    if spec.name == "stock_private_placement_allocations_tdx" and len(tables) > 1:
        meta_rows = list(tables[1].rows)
    rows = [normalize_f10_row(spec, row, context, meta_rows=meta_rows) for row in main_rows]
    rows = postprocess_f10_rows(spec, rows)
    rows = filter_f10_rows(spec, rows, params)
    count = int_param(params, "count", 20, minimum=1, maximum=500) if "count" in {p.name for p in spec.params} else None
    if count is not None:
        rows = rows[:count]
    if spec.name == "stock_event_drivers_tdx" and bool_param(params.get("include_detail", False), name="include_detail"):
        rows = attach_event_driver_details(client, rows)
    return rows


def attach_event_driver_details(client: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rows:
        detail_id = str(row.get("detail_id") or "").strip()
        if not detail_id or detail_id in details:
            continue
        details[detail_id] = request_event_driver_detail(client, detail_id)

    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        detail_id = str(item.get("detail_id") or "").strip()
        detail = details.get(detail_id, {})
        item["detail_title"] = detail.get("detail_title")
        item["detail_text"] = detail.get("detail_text")
        enriched.append(item)
    return enriched


def request_event_driver_detail(client: Any, detail_id: str) -> dict[str, Any]:
    tables = request_f10_tables(client, "CWServ.tdxf10_gg_idreq", {"Params": ["sjqd", detail_id]})
    if not tables:
        return {"detail_title": None, "detail_text": None}
    for table in tables:
        for row in table.rows:
            title = normalize_f10_plain_text(row.get("Title"))
            text = normalize_f10_plain_text(row.get("Txt"))
            if title is not None or text is not None:
                return {"detail_title": title, "detail_text": text}
    return {"detail_title": None, "detail_text": None}


def request_f10_all_pages(
    client: Any,
    spec: F10InterfaceSpec,
    params: Mapping[str, Any],
    *,
    key_fields: Sequence[str],
) -> list[dict[str, Any]]:
    page_size = 100
    max_pages = 50
    rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[Any, ...]] = set()
    for page in range(1, max_pages + 1):
        page_params = f10_unfiltered_page_params(spec, params)
        page_params["count"] = page_size
        page_params["cursor"] = str(page)
        page_rows = request_f10_interface_once(client, spec, page_params)
        new_count = 0
        for row in page_rows:
            key = tuple(row.get(field) for field in key_fields)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rows.append(row)
            new_count += 1
        if len(page_rows) < page_size or new_count == 0:
            break
    return rows


def prepare_f10_params(client: Any, spec: F10InterfaceSpec, params: Mapping[str, Any]) -> Mapping[str, Any]:
    if spec.name != "stock_governance_guarantees_tdx" or params.get("period") not in (None, ""):
        return params
    period = latest_f10_guarantee_period(client, params)
    if not period:
        return params
    prepared = dict(params)
    prepared["period"] = period
    return prepared


def latest_f10_guarantee_period(client: Any, params: Mapping[str, Any]) -> str | None:
    context = f10_context(f10_interface_specs()["stock_governance_guarantees_tdx"], params)
    body = {"Params": ["dbmxbgq", context.get("code") or "", ""]}
    try:
        payload = client.request("CWServ.tdxf10_gg_zbyz", body)
        tables = _parse_tqlex_tables(payload)
    except (TimeoutError, OSError) as exc:
        raise SourceUnavailableError(f"TDX F10 source is unavailable: {exc}") from exc
    if not tables:
        return None
    periods = [f10_date_text(row.get("bgq")) for row in tables[0].rows]
    return next((period for period in periods if period), None)


def f10_private_placement_dates(client: Any, params: Mapping[str, Any]) -> list[str]:
    context = f10_context(f10_interface_specs()["stock_private_placement_allocations_tdx"], params)
    body = {"Params": ["zfpg_bgq", context.get("code") or "", ""]}
    try:
        payload = client.request("CWServ.tdxf10_gg_fhrz_zfhpmx", body)
        tables = _parse_tqlex_tables(payload)
    except (TimeoutError, OSError) as exc:
        raise SourceUnavailableError(f"TDX F10 source is unavailable: {exc}") from exc
    if not tables:
        return []
    dates: list[str] = []
    seen: set[str] = set()
    for row in tables[0].rows:
        event_date = f10_date_text(row.get("rq") or row.get("mx"))
        if not event_date or event_date in seen:
            continue
        seen.add(event_date)
        dates.append(event_date)
    return dates


def f10_business_composition_periods(client: Any, params: Mapping[str, Any]) -> list[str]:
    context = f10_context(f10_interface_specs()["stock_business_composition_tdx"], params)
    body = {"Params": ["zygcfx", context.get("code") or ""]}
    try:
        payload = client.request("CWServ.tdxf10_gg_comreq", body)
        tables = _parse_tqlex_tables(payload)
    except (TimeoutError, OSError) as exc:
        raise SourceUnavailableError(f"TDX F10 source is unavailable: {exc}") from exc
    periods: list[str] = []
    seen: set[str] = set()
    for table in tables:
        for row in table.rows:
            for period in f10_business_period_candidates(row):
                if period in seen:
                    continue
                seen.add(period)
                periods.append(period)
    return periods
