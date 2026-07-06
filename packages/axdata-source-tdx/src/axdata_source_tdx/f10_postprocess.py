"""TDX F10 table post-processing helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from .codes import MARKET_TO_EXCHANGE, tdx_code_to_instrument_id
from .f10_normalize import (
    f10_date_text,
    f10_field_value,
    f10_first_text,
    f10_identifier_text,
    f10_market_from_market_code,
    f10_number,
    scale_f10_hundred,
)
from axdata_core.source_errors import SourceRequestValidationError
from .tdx_f10_models import F10InterfaceSpec


def normalize_f10_row(
    spec: F10InterfaceSpec,
    row: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    meta_rows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    merged_meta = dict(meta_rows[0]) if meta_rows else {}
    normalized: dict[str, Any] = {}
    for field in spec.fields:
        normalized[field.name] = f10_field_value(field, row, context, merged_meta)
    if "instrument_id" in normalized and normalized.get("instrument_id") is None:
        normalized["instrument_id"] = context.get("instrument_id")
    if "symbol" in normalized and normalized.get("symbol") is None:
        normalized["symbol"] = context.get("code")
    if spec.name == "stock_dividend_metrics_tdx":
        normalized = normalize_dividend_metrics_row(normalized, row, context)
    if spec.name == "stock_equity_financing_events_tdx":
        normalized = normalize_equity_financing_row(normalized, row, context)
    if spec.name == "stock_private_placement_allocations_tdx":
        normalized = normalize_private_placement_allocation_row(normalized, row, context, merged_meta)
    if spec.name == "stock_northbound_holding_tdx":
        normalized = normalize_northbound_holding_row(normalized, context)
    if spec.name == "stock_event_drivers_tdx":
        normalized["has_detail"] = bool(normalized.get("detail_id"))
        normalized["detail_title"] = None
        normalized["detail_text"] = None
    if spec.name == "stock_topic_exposure_tdx":
        normalized["topic_type"] = topic_exposure_type(context.get("function"))
        normalized["topic_id"] = f10_identifier_text(normalized.get("topic_id"))
        normalized["group_code"] = f10_identifier_text(normalized.get("group_code"))
    if spec.name == "stock_valuation_series_tdx":
        normalized["metric"] = valuation_metric_name(context.get("function"), normalized.get("metric"))
    return normalized


def normalize_dividend_metrics_row(
    normalized: dict[str, Any],
    row: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    item = dict(normalized)
    function = str(context.get("function") or "")
    if function == "fhlszs_gxl":
        item["metric_value"] = f10_number(row.get("N002"), integer=False)
        item["benchmark_value"] = f10_number(row.get("N003"), integer=False)
        item["rank"] = None
        item["stock_name"] = None
        item["stock_code"] = None
        item["summary_total"] = None
        item["cash_dividend_total"] = None
    elif function == "fhlszs_glzfl":
        item["metric_value"] = f10_number(row.get("N004"), integer=False)
        item["benchmark_value"] = None
        item["rank"] = None
        item["stock_name"] = None
        item["stock_code"] = None
        item["summary_total"] = None
        item["cash_dividend_total"] = None
    elif function.startswith("fhpm_"):
        item["date"] = None
        item["metric_value"] = f10_number(row.get("N003"), integer=False)
        item["benchmark_value"] = None
        item["rank"] = f10_number(row.get("N001"), integer=True)
        item["stock_name"] = row.get("N002")
        item["stock_code"] = row.get("dm")
        item["summary_total"] = None
        item["cash_dividend_total"] = None
    return item


def normalize_dividend_metrics_summary_rows(
    spec: F10InterfaceSpec,
    tables: Sequence[Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    summary: dict[str, Any] = {}
    if len(tables) > 6 and tables[6].rows:
        summary.update(tables[6].rows[0])
    if len(tables) > 0 and tables[0].rows:
        summary["total"] = tables[0].rows[0].get("total")
    row = normalize_f10_row_for_summary(spec, summary, context)
    row["date"] = None
    row["metric_value"] = f10_number(summary.get("xjfhnl"), integer=False)
    row["benchmark_value"] = None
    row["rank"] = None
    row["stock_name"] = None
    row["stock_code"] = None
    return [row]


def normalize_equity_financing_rows(
    spec: F10InterfaceSpec,
    tables: Sequence[Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    function = str(context.get("function") or "")
    rows: list[dict[str, Any]] = []
    if function == "zf":
        for table_index, table in enumerate(tables[:2]):
            placement_stage = "completed" if table_index == 0 else "plan"
            for source_row in table.rows:
                row = normalize_f10_row(spec, source_row, context)
                row["progress"] = row.get("progress") or ("已发行" if placement_stage == "completed" else None)
                rows.append(row)
        return rows
    if function == "pf":
        for table_index, table in enumerate(tables[:2]):
            for source_row in table.rows:
                row = normalize_f10_row(spec, source_row, context)
                if table_index == 0:
                    row["progress"] = row.get("progress") or "已实施"
                rows.append(row)
        return rows
    table_index = min(max(spec.main_table_index, 0), len(tables) - 1)
    return [normalize_f10_row(spec, row, context) for row in tables[table_index].rows]


def normalize_equity_financing_row(
    normalized: dict[str, Any],
    row: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    item = dict(normalized)
    function = str(context.get("function") or "")
    item["event_type"] = equity_financing_event_type(function)
    if function == "zf":
        item["event_date"] = f10_date_text(row.get("T003") or row.get("T002"))
        item["plan"] = f10_first_text(row, ("T017", "T007"))
        item["amount"] = f10_number(row.get("T025") or row.get("T008"), integer=False)
        item["price"] = f10_number(row.get("T012"), integer=False)
        item["volume"] = f10_number(row.get("T005"), integer=False)
        item["progress"] = f10_first_text(row, ("T016", "T110"))
    elif function == "pf":
        item["event_date"] = f10_date_text(row.get("rq"))
        item["plan"] = equity_rights_issue_plan(row)
        item["amount"] = f10_number(row.get("T017") or row.get("T015"), integer=False)
        item["price"] = f10_number(row.get("T006") or row.get("T011"), integer=False)
        item["volume"] = f10_number(row.get("T015"), integer=False)
        item["progress"] = f10_first_text(row, ("T023",))
    elif function == "gqjl":
        item["event_date"] = f10_date_text(row.get("N001"))
        item["progress"] = f10_first_text(row, ("N002",))
        item["plan"] = f10_first_text(row, ("N003", "N007"))
        item["amount"] = None
        item["price"] = f10_number(row.get("N006"), integer=False)
        item["volume"] = f10_number(row.get("N004"), integer=False)
    elif function == "kzzdfxyss":
        item["event_date"] = f10_date_text(row.get("N004"))
        item["plan"] = f10_first_text(row, ("N015",))
        item["amount"] = f10_number(row.get("N009"), integer=False)
        item["price"] = f10_number(row.get("N013"), integer=False)
        item["volume"] = f10_number(row.get("N007"), integer=False)
        item["progress"] = convertible_bond_status(row.get("N016"))
    return item


def normalize_private_placement_allocation_row(
    normalized: dict[str, Any],
    row: Mapping[str, Any],
    context: Mapping[str, Any],
    meta_row: Mapping[str, Any],
) -> dict[str, Any]:
    item = dict(normalized)
    item["event_date"] = (
        f10_date_text(row.get("rq")) or f10_date_text(meta_row.get("mx")) or f10_date_text(context.get("event_date"))
    )
    return item


def normalize_northbound_holding_row(
    normalized: dict[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    item = dict(normalized)
    if item.get("channel_type") in (None, ""):
        item["channel_type"] = northbound_record_channel_type(context.get("market"))
    return item


def northbound_record_channel_type(market: Any) -> str | None:
    text = str(market or "").lower()
    if text == "sz":
        return "深股通"
    if text == "sh":
        return "沪股通"
    return None


def equity_financing_event_type(function: str) -> str:
    return {
        "zf": "placement",
        "pf": "rights_issue",
        "gqjl": "incentive",
        "kzzdfxyss": "convertible_bond",
    }.get(function, function)


def equity_rights_issue_plan(row: Mapping[str, Any]) -> str | None:
    ratio = row.get("T005") or row.get("T006")
    price = row.get("T006") if "T005" in row else row.get("T011")
    if ratio not in (None, "") and price not in (None, ""):
        return f"每10股配{ratio}股，配股价{price}元"
    return None


def convertible_bond_status(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return {"0": "未退市", "1": "已退市"}.get(text, text)


def normalize_f10_row_for_summary(
    spec: F10InterfaceSpec,
    row: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for field in spec.fields:
        normalized[field.name] = f10_field_value(field, row, context, {})
    if "instrument_id" in normalized and normalized.get("instrument_id") is None:
        normalized["instrument_id"] = context.get("instrument_id")
    if "symbol" in normalized and normalized.get("symbol") is None:
        normalized["symbol"] = context.get("code")
    return normalized


def postprocess_f10_rows(spec: F10InterfaceSpec, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if spec.name == "concept_constituents_tdx":
        return [postprocess_concept_constituent_row(row) for row in rows]
    if spec.name == "stock_market_rankings_tdx":
        return [postprocess_market_ranking_row(row) for row in rows]
    if spec.name == "stock_valuation_series_tdx":
        processed: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["value"] = scale_f10_hundred(item.get("value"))
            item["percentile"] = scale_f10_hundred(item.get("percentile"))
            processed.append(item)
        return processed
    return rows


def postprocess_concept_constituent_row(row: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(row)
    market = f10_market_from_market_code(item.get("market_code"))
    symbol = str(item.get("symbol") or "").strip()
    if market:
        item["exchange"] = MARKET_TO_EXCHANGE.get(market)
    if market and len(symbol) == 6 and symbol.isdigit():
        item["instrument_id"] = tdx_code_to_instrument_id(market + symbol)
    return item


def postprocess_market_ranking_row(row: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(row)
    market = f10_market_from_market_code(item.get("market_code"))
    symbol = str(item.get("symbol") or "").strip()
    if market:
        item["exchange"] = MARKET_TO_EXCHANGE.get(market)
    if market and len(symbol) == 6 and symbol.isdigit():
        item["instrument_id"] = tdx_code_to_instrument_id(market + symbol)
    return item


def topic_exposure_type(function: Any) -> str | None:
    text = str(function or "").strip()
    if text == "zttzbkz":
        return "sector"
    if text == "zttzztk":
        return "theme"
    return None


def valuation_metric_name(function: Any, fallback: Any) -> str | None:
    text = str(function or "").strip()
    if text in {"0", "1", "2", "3"}:
        return {"0": "pe", "1": "pb", "2": "pcf", "3": "ps"}[text]
    if fallback in (None, ""):
        return None
    return str(fallback)


def filter_f10_rows(spec: F10InterfaceSpec, rows: list[dict[str, Any]], params: Mapping[str, Any]) -> list[dict[str, Any]]:
    if spec.name == "stock_dividend_history_tdx":
        start_year = str(params.get("start_year") or "").strip()
        end_year = str(params.get("end_year") or "").strip()
        if start_year or end_year:
            return [
                row
                for row in rows
                if year_in_range(str(row.get("report_period") or ""), start_year=start_year, end_year=end_year)
            ]
    if spec.name == "stock_shareholder_change_plans_tdx":
        rows = filter_shareholder_change_direction(rows, params)
    if spec.name in {"stock_valuation_metrics_tdx", "stock_valuation_series_tdx", "stock_valuation_band_tdx"}:
        return filter_date_range(rows, "date", params)
    if spec.name in {
        "concept_capital_flow_tdx",
        "concept_control_series_tdx",
        "concept_control_ranking_tdx",
        "stock_northbound_holding_tdx",
        "stock_margin_trading_tdx",
        "stock_chip_distribution_tdx",
        "stock_analyst_rating_tdx",
        "stock_institution_holding_tdx",
        "stock_regulatory_actions_tdx",
        "stock_violation_cases_tdx",
        "stock_event_drivers_tdx",
        "stock_index_constituent_changes_tdx",
    }:
        date_key = "date"
        if spec.name == "stock_regulatory_actions_tdx":
            date_key = "publish_date"
        if spec.name == "stock_violation_cases_tdx":
            date_key = "case_date"
        if spec.name == "stock_event_drivers_tdx":
            date_key = "event_date"
        if spec.name == "stock_index_constituent_changes_tdx":
            date_key = "publish_date"
        return filter_date_range(rows, date_key, params)
    if spec.name == "stock_return_calendar_tdx" and params.get("year") not in (None, ""):
        year = str(params.get("year"))
        return [row for row in rows if str(row.get("year") or "") == year]
    return rows


def filter_shareholder_change_direction(
    rows: list[dict[str, Any]],
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    direction = str(params.get("direction") or "").strip().lower()
    if not direction:
        return rows
    if direction in {"increase", "inc", "增持", "拟增持"}:
        keywords = ("增持",)
    elif direction in {"decrease", "dec", "减持", "拟减持"}:
        keywords = ("减持",)
    else:
        raise SourceRequestValidationError("direction must be one of: increase, decrease")
    return [row for row in rows if any(keyword in str(row.get("direction") or "") for keyword in keywords)]


def filter_date_range(rows: list[dict[str, Any]], key: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
    start = _normalize_optional_date_text(params.get("start_date"))
    end = _normalize_optional_date_text(params.get("end_date"))
    if not start and not end:
        return rows
    filtered = []
    for row in rows:
        value = f10_date_text(row.get(key))
        if not value:
            filtered.append(row)
            continue
        if start and value < start:
            continue
        if end and value > end:
            continue
        filtered.append(row)
    return filtered


def year_in_range(value: str, *, start_year: str, end_year: str) -> bool:
    year = value[:4]
    if start_year and year < start_year:
        return False
    if end_year and year > end_year:
        return False
    return True


def _normalize_optional_date_text(value: Any, *, name: str = "anchor_date") -> str | None:
    if value in (None, "", 0, "0"):
        return None
    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise SourceRequestValidationError(f"{name} must be YYYYMMDD or YYYY-MM-DD")
    try:
        datetime.strptime(text, "%Y%m%d")
    except ValueError as exc:
        raise SourceRequestValidationError(f"{name} must be a valid date") from exc
    return text
