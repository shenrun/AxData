"""Lightweight security code classification helpers for TDX wire responses."""

from __future__ import annotations

from axdata_source_tdx._tdx_wire._command_layouts import (
    ETF_PREFIXES,
    FUND_PREFIXES,
    INDEX_PREFIXES,
    SSE_A_SHARE_PREFIXES,
    SZSE_A_SHARE_PREFIXES,
)


def classify_security(full_code: str) -> tuple[str, str]:
    code = full_code.lower()
    if code.startswith(INDEX_PREFIXES):
        return "index", "index code prefix"
    if code.startswith(ETF_PREFIXES):
        return "etf", "ETF code prefix"
    if code.startswith(FUND_PREFIXES):
        return "fund", "fund code prefix"
    if code.startswith(SSE_A_SHARE_PREFIXES):
        return "a_share", "SSE A-share code prefix"
    if code.startswith("sh689"):
        return "cdr", "SSE CDR code prefix"
    if code.startswith(SZSE_A_SHARE_PREFIXES):
        return "a_share", "SZSE A-share code prefix"
    if code.startswith("bj92"):
        return "a_share", "BSE listed stock code prefix"
    if code.startswith("sh900") or any(code.startswith(f"sz20{digit}") for digit in range(10)):
        return "b_share", "B-share code prefix"
    if code.startswith("bj810"):
        return "private_convertible_bond", "BSE private convertible bond prefix"
    if code.startswith("bj821"):
        return "bond", "BSE bond sample prefix"
    return "unknown", "no matched code prefix"


def classify_board(full_code: str, category: str | None = None) -> tuple[str, str]:
    code = full_code.lower()
    if category not in {None, "a_share", "cdr"}:
        return "none", "not an A-share stock or CDR"
    if code.startswith(("sh600", "sh601", "sh603", "sh605")):
        return "sse_main_board", "SSE main-board prefix"
    if code.startswith("sh688"):
        return "sse_star_market", "SSE STAR Market prefix"
    if code.startswith("sh689"):
        return "sse_cdr", "SSE CDR prefix"
    if code.startswith(("sz000", "sz001", "sz002", "sz003", "sz004")):
        return "szse_main_board", "SZSE main-board prefix"
    if code.startswith(("sz300", "sz301")):
        return "szse_chinext", "SZSE ChiNext prefix"
    if code.startswith("bj92"):
        return "bse_listed_stock", "BSE listed stock prefix"
    return "none", "no stock board matched"


__all__ = [
    "classify_board",
    "classify_security",
]
