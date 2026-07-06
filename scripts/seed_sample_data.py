"""Seed tiny AxData core tables for local API and web smoke tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from axdata_core import get_schema, write_core_table


def main() -> None:
    data_root = Path("data")

    write_core_table(
        "stock_basic_exchange",
        pd.DataFrame(
            [
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "exchange": "SZSE",
                    "asset_type": "stock",
                    "name": "平安银行",
                    "security_full_name": None,
                    "market_code": None,
                    "market": "主板",
                    "industry_code": None,
                    "industry": "J 金融业",
                    "region_code": None,
                    "region": None,
                    "company_code": None,
                    "company_short_name": None,
                    "company_full_name": None,
                    "company_short_name_en": None,
                    "company_full_name_en": None,
                    "listing_status": "listed",
                    "list_date": "19910403",
                    "delist_date": None,
                    "total_share": 194.05,
                    "float_share": 194.05,
                    "is_profit": "-",
                    "is_vie": "-",
                    "has_weighted_voting_rights": "-",
                    "sponsor": None,
                    "share_report_date": None,
                },
                {
                    "instrument_id": "600000.SH",
                    "symbol": "600000",
                    "exchange": "SSE",
                    "asset_type": "stock",
                    "name": "浦发银行",
                    "security_full_name": "浦发银行",
                    "market_code": "1",
                    "market": "主板",
                    "industry_code": "J",
                    "industry": "金融业",
                    "region_code": "310000",
                    "region": "上海市",
                    "company_code": "600000",
                    "company_short_name": "浦发银行",
                    "company_full_name": "上海浦东发展银行股份有限公司",
                    "company_short_name_en": "SPD BANK",
                    "company_full_name_en": "Shanghai Pudong Development Bank Co.,Ltd.",
                    "listing_status": "listed",
                    "list_date": "19991110",
                    "delist_date": None,
                    "total_share": None,
                    "float_share": None,
                    "is_profit": None,
                    "is_vie": None,
                    "has_weighted_voting_rights": None,
                    "sponsor": None,
                    "share_report_date": None,
                },
                {
                    "instrument_id": "430047.BJ",
                    "symbol": "430047",
                    "exchange": "BSE",
                    "asset_type": "stock",
                    "name": "诺思兰德",
                    "security_full_name": None,
                    "market_code": None,
                    "market": "北交所",
                    "industry_code": None,
                    "industry": "医药制造业",
                    "region_code": None,
                    "region": "北京市",
                    "company_code": None,
                    "company_short_name": None,
                    "company_full_name": None,
                    "company_short_name_en": None,
                    "company_full_name_en": None,
                    "listing_status": "listed",
                    "list_date": "20201124",
                    "delist_date": None,
                    "total_share": 2.75,
                    "float_share": 1.85,
                    "is_profit": None,
                    "is_vie": None,
                    "has_weighted_voting_rights": None,
                    "sponsor": "中泰证券",
                    "share_report_date": "20240102",
                },
            ],
            columns=get_schema("stock_basic_exchange").field_names,
        ),
        root=data_root,
    )

    write_core_table(
        "trade_cal",
        pd.DataFrame(
            [
                {"exchange": "SSE", "cal_date": "20240101", "is_open": 0, "pretrade_date": "20231229"},
                {"exchange": "SSE", "cal_date": "20240102", "is_open": 1, "pretrade_date": "20231229"},
            ]
        ),
        root=data_root,
    )

    write_core_table(
        "daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20240102",
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "pre_close": 10.0,
                    "change": 0.2,
                    "pct_chg": 2.0,
                    "vol": 1000.0,
                    "amount": 10200.0,
                }
            ]
        ),
        root=data_root,
    )

    write_core_table(
        "adj_factor",
        pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240102", "adj_factor": 1.0},
            ]
        ),
        root=data_root,
    )

    print(f"Seeded sample AxData tables under {data_root.resolve() / 'core'}")


if __name__ == "__main__":
    main()
