from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import pytest

from axdata_core import request_interface
from axdata_core.adapters.exchange import ExchangeRequestAdapter
from axdata_core.source_errors import SourceRequestValidationError


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class FakeOpener:
    def __init__(self, months):
        self.months = months
        self.requested_months = []

    def __call__(self, request, timeout):
        query = parse_qs(urlparse(request.full_url).query)
        month = query["month"][0]
        self.requested_months.append(month)
        return FakeResponse(self.months.get(month, []))


class FlakyCalendarOpener:
    def __init__(self):
        self.calls_by_month = {}

    def __call__(self, request, timeout):
        query = parse_qs(urlparse(request.full_url).query)
        month = query["month"][0]
        self.calls_by_month[month] = self.calls_by_month.get(month, 0) + 1
        if month == "2026-10" and self.calls_by_month[month] == 1:
            raise URLError("timed out")
        if month == "2026-10":
            return FakeResponse([{"jyrq": "2026-10-08", "jybz": "1"}])
        return FakeResponse([])


class FakeTextResponse:
    def __init__(self, text: str):
        self._text = text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def read(self):
        return self._text.encode("utf-8")


class FakeLifecycleOpener:
    def __init__(self):
        self.requests = []

    def __call__(self, request, timeout):
        parsed = urlparse(request.full_url)
        query = parse_qs(parsed.query)
        self.requests.append(
            {
                "url": request.full_url,
                "host": parsed.netloc,
                "query": query,
                "data": getattr(request, "data", None),
            }
        )

        if parsed.netloc == "query.sse.com.cn":
            stock_type = query.get("STOCK_TYPE", [""])[0]
            page_rows = []
            if stock_type == "1":
                page_rows = [
                    {
                        "A_STOCK_CODE": "600000",
                        "SEC_NAME_CN": "浦发银行",
                        "SEC_NAME_FULL": "浦发银行",
                        "LIST_BOARD": "1",
                        "CSRC_CODE": "J",
                        "CSRC_CODE_DESC": "金融业",
                        "AREA_NAME": "310000",
                        "AREA_NAME_DESC": "上海市",
                        "COMPANY_CODE": "600000",
                        "COMPANY_ABBR": "浦发银行",
                        "FULL_NAME": "上海浦东发展银行股份有限公司",
                        "COMPANY_ABBR_EN": "SPD BANK",
                        "FULL_NAME_IN_ENGLISH": "Shanghai Pudong Development Bank Co.,Ltd.",
                        "LIST_DATE": "19991110",
                        "DELIST_DATE": "-",
                    },
                    {
                        "A_STOCK_CODE": "600001",
                        "SEC_NAME_CN": "邯郸钢铁",
                        "LIST_BOARD": "1",
                        "LIST_DATE": "19980210",
                        "DELIST_DATE": "20091229",
                    },
                ]
            elif stock_type == "8":
                page_rows = [
                    {
                        "A_STOCK_CODE": "688001",
                        "SEC_NAME_CN": "华兴源创",
                        "LIST_BOARD": "2",
                        "LIST_DATE": "20190722",
                        "DELIST_DATE": "-",
                    }
                ]
            return FakeTextResponse(json.dumps({"pageHelp": {"pageCount": 1, "data": page_rows}}))

        if parsed.netloc == "www.szse.cn" and parsed.path.endswith("/ShowReport/data"):
            catalog_id = query.get("CATALOGID", [""])[0]
            tab_key = query.get("TABKEY", [""])[0]
            if catalog_id == "1110":
                payload = [
                    {
                        "metadata": {"pagecount": 1},
                        "data": [
                            {
                                "bk": "主板",
                                "agdm": "000001",
                                "agjc": '<a href="/foo"><u>平安银行</u></a>',
                                "agssrq": "1991-04-03",
                                "agzgb": "194.05",
                                "agltgb": "194.05",
                                "sshymc": "J 金融业",
                                "ylbz": "-",
                                "gskzjglx": "-",
                                "sfjybjqcy": "-",
                            },
                            {
                                "bk": "创业板",
                                "agdm": "300999",
                                "agjc": "未来股份",
                                "agssrq": "2026-01-01",
                            },
                        ],
                    }
                ]
                return FakeTextResponse(json.dumps(payload))
            if catalog_id == "1793_ssgs" and tab_key == "tab2":
                payload = [
                    {"metadata": {"name": "暂停上市", "pagecount": 0}, "data": []},
                    {
                        "metadata": {"name": "终止上市", "pagecount": 1},
                        "data": [
                            {
                                "zqdm": "000005",
                                "zqjc": "ST星源",
                                "ssrq": "1990-12-10",
                                "zzrq": "2024-04-26",
                            },
                            {
                                "zqdm": "000003",
                                "zqjc": "PT金田A",
                                "ssrq": "1991-01-14",
                                "zzrq": "2002-06-14",
                            },
                        ],
                    },
                ]
                return FakeTextResponse(json.dumps(payload))

        if parsed.netloc == "www.bse.cn":
            payload = [
                {
                    "totalPages": 1,
                    "content": [
                        {
                            "xxzqdm": "920000",
                            "xxzqjc": "安徽凤凰",
                            "xxhyzl": "汽车制造业",
                            "xxssdq": "安徽省",
                            "xxzgb": "91680000",
                            "xxfxsgb": "57593925",
                            "xxzbqs": "国元证券股份有限公司",
                            "xxjsrq": "2024-12-31",
                            "xxgprq": "20201223",
                        }
                    ],
                }
            ]
            return FakeTextResponse(f"null({json.dumps(payload, ensure_ascii=False)})")

        raise AssertionError(f"Unexpected request: {request.full_url}")


def _calendar_payload(start_day: str, days: list[tuple[str, bool]]):
    return [{"jyrq": day, "jybz": "1" if is_open else "0", "zrxh": "0"} for day, is_open in days]


def test_exchange_adapter_requests_trade_calendar_range_and_normalizes_rows():
    opener = FakeOpener(
        {
            "2026-05": _calendar_payload("2026-05-29", [("2026-05-29", True)]),
            "2026-06": _calendar_payload(
                "2026-06-01",
                [
                    ("2026-06-16", True),
                    ("2026-06-17", True),
                    ("2026-06-18", True),
                    ("2026-06-19", False),
                    ("2026-06-20", False),
                    ("2026-06-21", False),
                    ("2026-06-22", True),
                    ("2026-06-23", True),
                ],
            ),
            "2026-07": _calendar_payload("2026-07-01", [("2026-07-01", True)]),
        }
    )
    adapter = ExchangeRequestAdapter(opener=opener)

    rows = adapter.request(
        "stock_trade_calendar_exchange",
        {"start_date": "20260617", "end_date": "20260622"},
    )

    assert rows == [
        {
            "cal_date": "20260617",
            "is_open": True,
            "pretrade_date": "20260616",
            "next_trade_date": "20260618",
        },
        {
            "cal_date": "20260618",
            "is_open": True,
            "pretrade_date": "20260617",
            "next_trade_date": "20260622",
        },
        {
            "cal_date": "20260619",
            "is_open": False,
            "pretrade_date": "20260618",
            "next_trade_date": "20260622",
        },
        {
            "cal_date": "20260620",
            "is_open": False,
            "pretrade_date": "20260618",
            "next_trade_date": "20260622",
        },
        {
            "cal_date": "20260621",
            "is_open": False,
            "pretrade_date": "20260618",
            "next_trade_date": "20260622",
        },
        {
            "cal_date": "20260622",
            "is_open": True,
            "pretrade_date": "20260618",
            "next_trade_date": "20260623",
        },
    ]
    assert opener.requested_months == ["2026-05", "2026-06", "2026-07"]
    assert adapter.last_meta["requested_start_date"] == "20260617"
    assert adapter.last_meta["requested_end_date"] == "20260622"
    assert adapter.last_meta["source_exchange"] == "SZSE"


def test_exchange_adapter_year_param_uses_full_natural_year():
    opener = FakeOpener({f"2026-{month:02d}": [] for month in range(1, 13)})
    opener.months["2026-06"] = _calendar_payload("2026-06-17", [("2026-06-17", True)])
    adapter = ExchangeRequestAdapter(opener=opener)

    rows = adapter.request("stock_trade_calendar_exchange", {"year": "2026"})

    assert rows == [
        {
            "cal_date": "20260617",
            "is_open": True,
            "pretrade_date": None,
            "next_trade_date": None,
        }
    ]
    assert opener.requested_months[0] == "2025-12"
    assert opener.requested_months[-1] == "2027-01"
    assert adapter.last_meta["date_mode"] == "year"


def test_exchange_adapter_retries_trade_calendar_month_timeout(monkeypatch):
    monkeypatch.setattr("axdata_core.adapters.exchange.request.time.sleep", lambda seconds: None)
    opener = FlakyCalendarOpener()
    adapter = ExchangeRequestAdapter(opener=opener)

    rows = adapter.request(
        "stock_trade_calendar_exchange",
        {"start_date": "20261008", "end_date": "20261008"},
    )

    assert opener.calls_by_month["2026-10"] == 2
    assert rows == [
        {
            "cal_date": "20261008",
            "is_open": True,
            "pretrade_date": None,
            "next_trade_date": None,
        }
    ]


def test_exchange_gateway_routes_trade_calendar_exchange_adapter():
    opener = FakeOpener(
        {
            "2026-05": [],
            "2026-06": _calendar_payload("2026-06-17", [("2026-06-17", True)]),
            "2026-07": [],
        }
    )
    adapter = ExchangeRequestAdapter(opener=opener)

    result = request_interface(
        "stock_trade_calendar_exchange",
        params={"start_date": "20260617", "end_date": "20260617"},
        fields=["cal_date", "is_open"],
        adapter=adapter,
    )

    assert result.records == [{"cal_date": "20260617", "is_open": True}]
    assert result.meta["source"] == "exchange"
    assert result.meta["requested_fields"] == ["cal_date", "is_open"]


def test_exchange_adapter_rejects_invalid_params():
    adapter = ExchangeRequestAdapter(opener=FakeOpener({}))

    with pytest.raises(SourceRequestValidationError, match="start_date must be before"):
        adapter.request(
            "stock_trade_calendar_exchange",
            {"start_date": "20260622", "end_date": "20260617"},
        )


def test_exchange_gateway_rejects_exchange_param():
    adapter = ExchangeRequestAdapter(opener=FakeOpener({}))

    with pytest.raises(SourceRequestValidationError, match="Unknown param"):
        request_interface(
            "stock_trade_calendar_exchange",
            params={"exchange": "SZSE", "start_date": "20260617", "end_date": "20260617"},
            adapter=adapter,
        )


def test_exchange_adapter_builds_historical_stock_list_from_lifecycle_dates():
    opener = FakeLifecycleOpener()
    adapter = ExchangeRequestAdapter(opener=opener)

    rows = adapter.request("stock_historical_list_exchange", {"trade_date": "20240102"})

    assert rows == [
        {
            "trade_date": "20240102",
            "instrument_id": "600000.SH",
            "symbol": "600000",
            "exchange": "SSE",
            "name": "浦发银行",
            "market": "主板",
            "list_date": "19991110",
            "delist_date": None,
            "listing_status": "listed",
        },
        {
            "trade_date": "20240102",
            "instrument_id": "688001.SH",
            "symbol": "688001",
            "exchange": "SSE",
            "name": "华兴源创",
            "market": "科创板",
            "list_date": "20190722",
            "delist_date": None,
            "listing_status": "listed",
        },
        {
            "trade_date": "20240102",
            "instrument_id": "000001.SZ",
            "symbol": "000001",
            "exchange": "SZSE",
            "name": "平安银行",
            "market": "主板",
            "list_date": "19910403",
            "delist_date": None,
            "listing_status": "listed",
        },
        {
            "trade_date": "20240102",
            "instrument_id": "000005.SZ",
            "symbol": "000005",
            "exchange": "SZSE",
            "name": "ST星源",
            "market": None,
            "list_date": "19901210",
            "delist_date": "20240426",
            "listing_status": "delisted",
        },
        {
            "trade_date": "20240102",
            "instrument_id": "920000.BJ",
            "symbol": "920000",
            "exchange": "BSE",
            "name": "安徽凤凰",
            "market": "北交所",
            "list_date": "20201223",
            "delist_date": None,
            "listing_status": "listed",
        },
    ]
    assert "600001.SH" not in {row["instrument_id"] for row in rows}
    assert "300999.SZ" not in {row["instrument_id"] for row in rows}
    assert adapter.last_meta["trade_date"] == "20240102"
    assert adapter.last_meta["trade_dates"] == ["20240102"]
    assert adapter.last_meta["source_exchange"] == "SSE,SZSE,BSE"
    assert adapter.last_meta["filtered_count"] == 5


def test_exchange_adapter_historical_stock_list_accepts_date_list():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    rows = adapter.request(
        "stock_historical_list_exchange",
        {"trade_date": ["20091229", "20091230"], "exchange": "SSE"},
    )

    assert [row["instrument_id"] for row in rows] == [
        "600000.SH",
        "600001.SH",
        "600000.SH",
    ]
    assert [row["trade_date"] for row in rows] == ["20091229", "20091229", "20091230"]
    assert adapter.last_meta["date_mode"] == "trade_date_list"
    assert adapter.last_meta["trade_date"] is None
    assert adapter.last_meta["trade_dates"] == ["20091229", "20091230"]


def test_exchange_adapter_historical_stock_list_accepts_date_range():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    rows = adapter.request(
        "stock_historical_list_exchange",
        {"start_date": "2024-01-02", "end_date": "2024-01-03", "exchange": "SZSE"},
    )

    assert [row["trade_date"] for row in rows] == [
        "20240102",
        "20240102",
        "20240103",
        "20240103",
    ]
    assert [row["instrument_id"] for row in rows] == [
        "000001.SZ",
        "000005.SZ",
        "000001.SZ",
        "000005.SZ",
    ]
    assert adapter.last_meta["date_mode"] == "range"
    assert adapter.last_meta["requested_start_date"] == "20240102"
    assert adapter.last_meta["requested_end_date"] == "20240103"


def test_exchange_adapter_historical_stock_list_can_filter_exchange():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    rows = adapter.request(
        "stock_historical_list_exchange",
        {"trade_date": "2024-01-02", "exchange": "SZSE"},
    )

    assert [row["instrument_id"] for row in rows] == ["000001.SZ", "000005.SZ"]
    assert {row["trade_date"] for row in rows} == {"20240102"}
    assert {row["exchange"] for row in rows} == {"SZSE"}
    assert adapter.last_meta["source_exchange"] == "SZSE"


def test_exchange_gateway_routes_historical_stock_list_exchange_adapter():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    result = request_interface(
        "stock_historical_list_exchange",
        params={"trade_date": "20240102", "exchange": "SZSE"},
        fields=["trade_date", "instrument_id", "name", "delist_date"],
        adapter=adapter,
    )

    assert result.records == [
        {"trade_date": "20240102", "instrument_id": "000001.SZ", "name": "平安银行", "delist_date": None},
        {"trade_date": "20240102", "instrument_id": "000005.SZ", "name": "ST星源", "delist_date": "20240426"},
    ]
    assert result.meta["source"] == "exchange"
    assert result.meta["requested_fields"] == ["trade_date", "instrument_id", "name", "delist_date"]


def test_exchange_adapter_returns_current_stock_basic_info():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    rows = adapter.request("stock_basic_info_exchange", {"code": ["000001.SZ", "600000.SH", "920000.BJ"]})

    assert rows == [
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
            "instrument_id": "920000.BJ",
            "symbol": "920000",
            "exchange": "BSE",
            "asset_type": "stock",
            "name": "安徽凤凰",
            "security_full_name": None,
            "market_code": None,
            "market": "北交所",
            "industry_code": None,
            "industry": "汽车制造业",
            "region_code": None,
            "region": "安徽省",
            "company_code": None,
            "company_short_name": None,
            "company_full_name": None,
            "company_short_name_en": None,
            "company_full_name_en": None,
            "listing_status": "listed",
            "list_date": "20201223",
            "delist_date": None,
            "total_share": 0.9168,
            "float_share": 0.57593925,
            "is_profit": None,
            "is_vie": None,
            "has_weighted_voting_rights": None,
            "sponsor": "国元证券股份有限公司",
            "share_report_date": "20241231",
        },
    ]
    assert adapter.last_meta["source_exchange"] == "SSE,SZSE,BSE"
    assert adapter.last_meta["filtered_count"] == 3


def test_exchange_adapter_stock_basic_info_accepts_name_and_exchange_filters():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    rows = adapter.request(
        "stock_basic_info_exchange",
        {"exchange": "SZSE", "name": "平安银行"},
    )

    assert [row["instrument_id"] for row in rows] == ["000001.SZ"]
    assert rows[0]["industry"] == "J 金融业"
    assert adapter.last_meta["source_exchange"] == "SZSE"


def test_exchange_gateway_routes_stock_basic_info_exchange_adapter():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    result = request_interface(
        "stock_basic_info_exchange",
        params={"code": "sz000001"},
        fields=["instrument_id", "name", "industry", "total_share"],
        adapter=adapter,
    )

    assert result.records == [
        {
            "instrument_id": "000001.SZ",
            "name": "平安银行",
            "industry": "J 金融业",
            "total_share": 194.05,
        }
    ]
    assert result.meta["source"] == "exchange"
    assert result.meta["requested_fields"] == ["instrument_id", "name", "industry", "total_share"]


def test_exchange_adapter_rejects_invalid_historical_stock_list_params():
    adapter = ExchangeRequestAdapter(opener=FakeLifecycleOpener())

    with pytest.raises(SourceRequestValidationError, match="trade_date must be"):
        adapter.request("stock_historical_list_exchange", {"trade_date": "202401"})

    with pytest.raises(SourceRequestValidationError, match="Use either trade_date"):
        adapter.request(
            "stock_historical_list_exchange",
            {"trade_date": "20240102", "start_date": "20240102"},
        )

    with pytest.raises(SourceRequestValidationError, match="start_date must be before"):
        adapter.request(
            "stock_historical_list_exchange",
            {"start_date": "20240103", "end_date": "20240102"},
        )

    with pytest.raises(SourceRequestValidationError, match="exchange must be"):
        adapter.request(
            "stock_historical_list_exchange",
            {"trade_date": "20240102", "exchange": "NYSE"},
        )
