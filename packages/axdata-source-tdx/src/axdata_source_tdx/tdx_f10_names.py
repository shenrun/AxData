"""TDX F10 interface name constants.

This module intentionally contains only plain constants so ordinary TDX request
dispatch can recognize F10 interface names without importing F10 dataclass
models or full protocol specs.
"""

from __future__ import annotations


F10_INTERFACE_NAMES: tuple[str, ...] = (
    "stock_ipo_listing_profile_tdx",
    "stock_index_constituent_changes_tdx",
    "stock_company_profile_tdx",
    "stock_business_composition_tdx",
    "stock_financial_statement_tdx",
    "stock_financial_diagnosis_tdx",
    "stock_forecast_consensus_tdx",
    "stock_dividend_history_tdx",
    "stock_dividend_metrics_tdx",
    "stock_equity_financing_events_tdx",
    "stock_private_placement_allocations_tdx",
    "stock_shareholder_change_plans_tdx",
    "stock_northbound_holding_tdx",
    "stock_margin_trading_tdx",
    "stock_chip_distribution_tdx",
    "stock_research_reports_tdx",
    "stock_analyst_rating_tdx",
    "stock_institution_holding_tdx",
    "stock_governance_guarantees_tdx",
    "stock_violation_cases_tdx",
    "stock_regulatory_actions_tdx",
    "stock_score_summary_tdx",
    "stock_disclosure_feed_tdx",
    "stock_event_drivers_tdx",
    "stock_topic_exposure_tdx",
    "concept_related_boards_tdx",
    "concept_constituents_tdx",
    "concept_capital_flow_tdx",
    "concept_control_series_tdx",
    "concept_control_ranking_tdx",
    "concept_constituent_comparison_tdx",
    "stock_valuation_metrics_tdx",
    "stock_valuation_series_tdx",
    "stock_valuation_band_tdx",
    "stock_return_calendar_tdx",
    "stock_market_rankings_tdx",
)
