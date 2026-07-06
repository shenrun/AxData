from __future__ import annotations

from io import BytesIO
import zipfile

from axdata_core import core_table_path, get_schema, read_core_table, write_core_table
import pandas as pd
import requests

from services.collector import STOCK_BASIC, OfficialExchangeStockBasicAdapter
from services.worker.cli import build_parser
from services.worker.jobs import create_adapter, run_update_job


REMOVED_SOURCE_FIELDS = {
    "source",
    "source_batch_id",
    "source_listing_status",
    "source_product_status",
    "source_updated_at",
    "created_at",
    "updated_at",
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.text = payload if isinstance(payload, str) else ""
        self.content = payload if isinstance(payload, bytes) else b""

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.requests = []

    def get(self, url, *, headers, params, timeout):
        self.requests.append(
            {
                "method": "GET",
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
            }
        )
        if not self.payloads:
            raise AssertionError("No fake payload left for request.")
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(payload)

    def post(self, url, *, headers, data, timeout):
        self.requests.append(
            {
                "method": "POST",
                "url": url,
                "headers": headers,
                "data": data,
                "timeout": timeout,
            }
        )
        if not self.payloads:
            raise AssertionError("No fake payload left for request.")
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(payload)


def make_xlsx(rows: list[list[str]]) -> bytes:
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row):
            column = chr(ord("A") + column_index)
            cells.append(
                f'<c r="{column}{row_index}" t="inlineStr"><is><t>{value}</t></is></c>'
            )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet_xml = (
        f'<worksheet xmlns="{ns}"><sheetData>{"".join(row_xml)}</sheetData></worksheet>'
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def make_stock_basic_rows(exchange: str, count: int, *, start: int = 0) -> list[dict[str, str]]:
    suffixes = {"SSE": ".SH", "SZSE": ".SZ", "BSE": ".BJ"}
    bases = {"SSE": 600000, "SZSE": 1, "BSE": 920000}
    rows = []
    for offset in range(count):
        symbol = f"{bases[exchange] + start + offset:06d}"
        rows.append(
            {
                "instrument_id": f"{symbol}{suffixes[exchange]}",
                "symbol": symbol,
                "exchange": exchange,
                "asset_type": "stock",
                "name": f"{exchange}{offset}",
                "listing_status": "listed",
            }
        )
    return rows


def assert_clean_stock_basic_rows(rows: list[dict[str, object]]) -> None:
    assert rows
    assert get_schema(STOCK_BASIC).name == "stock_basic_exchange"
    for row in rows:
        assert not REMOVED_SOURCE_FIELDS.intersection(row)


def test_official_adapter_maps_sse_stock_basic_fields():
    session = FakeSession(
        [
            {
                "pageHelp": {
                    "pageCount": 1,
                    "data": [
                        {
                            "A_STOCK_CODE": "600000",
                            "SEC_NAME_CN": "浦发银行",
                            "SEC_NAME_FULL": "浦发银行",
                            "COMPANY_ABBR": "浦发银行",
                            "FULL_NAME": "上海浦东发展银行股份有限公司",
                            "COMPANY_ABBR_EN": "SPD BANK",
                            "FULL_NAME_IN_ENGLISH": "Shanghai Pudong Development Bank Co.,Ltd.",
                            "LIST_BOARD": "1",
                            "CSRC_CODE": "J",
                            "CSRC_CODE_DESC": "金融业",
                            "AREA_NAME": "310000",
                            "AREA_NAME_DESC": "上海市",
                            "COMPANY_CODE": "600000",
                            "STATE_CODE": "2",
                            "STATE_CODE_STOCK": "4",
                            "PRODUCT_STATUS": "   D  F  N          ",
                            "LIST_DATE": "19991110",
                            "DELIST_DATE": "-",
                        }
                    ],
                }
            }
        ]
    )
    adapter = OfficialExchangeStockBasicAdapter(session=session)

    rows = adapter.fetch(STOCK_BASIC, {"exchanges": "SSE", "batch_id": "batch_sse"})

    assert_clean_stock_basic_rows(rows)
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
        }
    ]
    assert session.requests[0]["params"]["sqlId"] == "COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L"


def test_official_adapter_maps_szse_stock_basic_fields():
    session = FakeSession(
        [
            [
                {
                    "metadata": {
                        "pagecount": 1,
                        "subname": "2026-06-08 ",
                    },
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
                            "sfjybjqcy": "-",
                            "gskzjglx": "-",
                        }
                    ],
                }
            ]
        ]
    )
    adapter = OfficialExchangeStockBasicAdapter(session=session)

    rows = adapter.fetch(STOCK_BASIC, {"exchanges": "SZSE", "batch_id": "batch_szse"})

    assert_clean_stock_basic_rows(rows)
    assert rows[0]["instrument_id"] == "000001.SZ"
    assert rows[0]["symbol"] == "000001"
    assert rows[0]["exchange"] == "SZSE"
    assert rows[0]["asset_type"] == "stock"
    assert rows[0]["name"] == "平安银行"
    assert rows[0]["market"] == "主板"
    assert rows[0]["industry"] == "J 金融业"
    assert rows[0]["list_date"] == "19910403"
    assert rows[0]["total_share"] == 194.05
    assert rows[0]["float_share"] == 194.05
    assert session.requests[0]["params"]["CATALOGID"] == "1110"


def test_official_adapter_falls_back_to_szse_xlsx_stock_basic_fields():
    session = FakeSession(
        [
            requests.ConnectionError("json endpoint disconnected"),
            make_xlsx(
                [
                    [
                        "板块",
                        "A股代码",
                        "A股简称",
                        "A股上市日期",
                        "A股总股本",
                        "A股流通股本",
                        "所属行业",
                    ],
                    ["主板", "000001", "平安银行", "1991-04-03", "194.05", "194.05", "J 金融业"],
                ]
            ),
        ]
    )
    adapter = OfficialExchangeStockBasicAdapter(session=session, retries=0)

    rows = adapter.fetch(STOCK_BASIC, {"exchanges": "SZSE", "batch_id": "batch_szse_xlsx"})

    assert_clean_stock_basic_rows(rows)
    assert rows[0]["instrument_id"] == "000001.SZ"
    assert rows[0]["symbol"] == "000001"
    assert rows[0]["exchange"] == "SZSE"
    assert rows[0]["name"] == "平安银行"
    assert rows[0]["market"] == "主板"
    assert rows[0]["industry"] == "J 金融业"
    assert rows[0]["list_date"] == "19910403"
    assert rows[0]["total_share"] == 194.05
    assert rows[0]["float_share"] == 194.05
    assert session.requests[0]["params"]["SHOWTYPE"] == "JSON"
    assert session.requests[1]["params"]["SHOWTYPE"] == "xlsx"


def test_official_adapter_maps_bse_stock_basic_fields():
    session = FakeSession(
        [
            (
                'null([{"totalPages":1,"content":[{'
                '"xxzqdm":"920000",'
                '"xxzqjc":"安徽凤凰",'
                '"xxfcbj":"2",'
                '"xxhyzl":"汽车制造业",'
                '"xxssdq":"安徽省",'
                '"xxywjc":"ANHUI PHOENIX",'
                '"xxzqjb":"T",'
                '"xxqtyw":"FF  ",'
                '"xxgprq":"20201223",'
                '"fxssrq":"20201223",'
                '"xxzgb":91680000,'
                '"xxfxsgb":57593925,'
                '"xxzbqs":"国元证券股份有限公司",'
                '"xxjsrq":"20260608"'
                '}]}])'
            )
        ]
    )
    adapter = OfficialExchangeStockBasicAdapter(session=session)

    rows = adapter.fetch(STOCK_BASIC, {"exchanges": "BSE", "batch_id": "batch_bse"})

    assert_clean_stock_basic_rows(rows)
    assert rows[0]["instrument_id"] == "920000.BJ"
    assert rows[0]["symbol"] == "920000"
    assert rows[0]["exchange"] == "BSE"
    assert rows[0]["asset_type"] == "stock"
    assert rows[0]["name"] == "安徽凤凰"
    assert rows[0]["market_code"] == "2"
    assert rows[0]["market"] == "北交所"
    assert rows[0]["industry"] == "汽车制造业"
    assert rows[0]["region"] == "安徽省"
    assert rows[0]["company_short_name_en"] == "ANHUI PHOENIX"
    assert rows[0]["list_date"] == "20201223"
    assert rows[0]["total_share"] == 0.9168
    assert rows[0]["float_share"] == 0.57593925
    assert rows[0]["sponsor"] == "国元证券股份有限公司"
    assert rows[0]["share_report_date"] == "20260608"
    assert session.requests[0]["method"] == "POST"
    assert session.requests[0]["data"]["xxfcbj[]"] == "2"


def test_worker_creates_official_exchange_adapter():
    adapter = create_adapter("official_exchange")

    assert isinstance(adapter, OfficialExchangeStockBasicAdapter)


def test_worker_cli_accepts_stock_basic_dataset_choices():
    parser = build_parser()

    for dataset in (
        "stock_basic",
        "stock-basic",
        "stock_basic_exchange",
        "stock-basic-exchange",
    ):
        args = parser.parse_args(["update", dataset, "--source", "official_exchange"])

        assert args.dataset == dataset

    adapter_args = parser.parse_args(
        ["update", "stock_basic_exchange", "--adapter", "official_exchange"]
    )
    assert adapter_args.source == "official_exchange"


def test_run_update_job_keeps_batch_id_in_task_state_and_adapter_params():
    class EchoAdapter(OfficialExchangeStockBasicAdapter):
        def __init__(self):
            self.params = None

        def fetch(self, dataset, params=None):
            self.params = params
            return [
                {
                    "instrument_id": "600000.SH",
                    "symbol": "600000",
                    "exchange": "SSE",
                    "asset_type": "stock",
                    "name": "浦发银行",
                    "listing_status": "listed",
                }
            ]

    adapter = EchoAdapter()
    result = run_update_job(
        STOCK_BASIC,
        source="official_exchange",
        batch_id="batch_worker",
        adapter=adapter,
    )

    assert result.state.status == "dry_run"
    assert result.state.batch_id == "batch_worker"
    assert result.state.source == "official_exchange"
    assert adapter.params["batch_id"] == "batch_worker"
    assert_clean_stock_basic_rows(result.rows)


def test_official_stock_basic_persist_rejects_limited_preview(tmp_path):
    class LimitedAdapter(OfficialExchangeStockBasicAdapter):
        def __init__(self):
            pass

        def fetch(self, dataset, params=None):
            return make_stock_basic_rows("BSE", 1)

    result = run_update_job(
        STOCK_BASIC,
        source="official_exchange",
        data_root=tmp_path / "data",
        dry_run=False,
        params={"exchanges": "BSE", "limit": 1},
        adapter=LimitedAdapter(),
    )

    assert result.state.status == "failed"
    assert "limited official stock_basic_exchange" in result.state.error


def test_official_stock_basic_short_snapshot_does_not_overwrite_existing(tmp_path):
    root = tmp_path / "data"
    existing_rows = make_stock_basic_rows("BSE", 300)
    write_core_table(STOCK_BASIC, pd.DataFrame(existing_rows), root=root)

    class ShortAdapter(OfficialExchangeStockBasicAdapter):
        def __init__(self):
            pass

        def fetch(self, dataset, params=None):
            return make_stock_basic_rows("BSE", 210, start=1000)

    result = run_update_job(
        STOCK_BASIC,
        source="official_exchange",
        data_root=root,
        dry_run=False,
        params={"exchanges": "BSE"},
        adapter=ShortAdapter(),
    )

    saved = read_core_table(STOCK_BASIC, root=root)

    assert result.state.status == "failed"
    assert "dropped from 300 to 210" in result.state.error
    assert len(saved) == 300
    assert saved["instrument_id"].tolist() == [row["instrument_id"] for row in existing_rows]


def test_official_stock_basic_single_exchange_refresh_preserves_other_exchanges(tmp_path):
    root = tmp_path / "data"
    existing_sse_rows = make_stock_basic_rows("SSE", 3)
    write_core_table(STOCK_BASIC, pd.DataFrame(existing_sse_rows), root=root)

    class BseAdapter(OfficialExchangeStockBasicAdapter):
        def __init__(self):
            pass

        def fetch(self, dataset, params=None):
            return make_stock_basic_rows("BSE", 200)

    result = run_update_job(
        STOCK_BASIC,
        source="official_exchange",
        data_root=root,
        dry_run=False,
        params={"exchanges": "BSE"},
        adapter=BseAdapter(),
    )

    saved = read_core_table(STOCK_BASIC, root=root)

    assert result.state.status == "success"
    assert core_table_path(STOCK_BASIC, root).name == "stock_basic_exchange.parquet"
    assert core_table_path(STOCK_BASIC, root).exists()
    assert not REMOVED_SOURCE_FIELDS.intersection(saved.columns)
    assert len(saved) == 203
    assert int((saved["exchange"] == "SSE").sum()) == 3
    assert int((saved["exchange"] == "BSE").sum()) == 200
