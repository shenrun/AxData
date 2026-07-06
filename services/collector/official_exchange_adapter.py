"""Official exchange collectors for AxData stock master data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import unescape
from io import BytesIO
import json
import re
import time
from typing import Any
import zipfile
import xml.etree.ElementTree as ET

import requests

from axdata_core import get_schema
from services.collector.base import STOCK_BASIC, CollectorAdapter, FetchParams, Row, normalize_dataset


SSE_STOCK_LIST_URL = "https://query.sse.com.cn/sseQuery/commonQuery.do"
SZSE_STOCK_LIST_URL = "https://www.szse.cn/api/report/ShowReport/data"
SZSE_STOCK_LIST_XLSX_URL = "https://www.szse.cn/api/report/ShowReport"
BSE_STOCK_LIST_URL = "https://www.bse.cn/nqxxController/nqxxCnzq.do"

SSE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.sse.com.cn/assortment/stock/list/share/",
    "User-Agent": "Mozilla/5.0",
}

SZSE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.szse.cn/market/product/stock/list/index.html",
    "User-Agent": "Mozilla/5.0",
}

SZSE_XLSX_HEADERS = {
    "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.8",
    "Referer": "https://www.szse.cn/market/product/stock/list/index.html",
    "User-Agent": "Mozilla/5.0",
}

BSE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.bse.cn/nq/listedcompany.html",
    "User-Agent": "Mozilla/5.0",
}

SSE_BOARD_NAMES = {
    "1": "主板",
    "8": "科创板",
}

EXCHANGE_ALIASES = {
    "SH": "SSE",
    "SSE": "SSE",
    "上海": "SSE",
    "上交所": "SSE",
    "SZ": "SZSE",
    "SZSE": "SZSE",
    "深圳": "SZSE",
    "深交所": "SZSE",
    "BJ": "BSE",
    "BSE": "BSE",
    "北京": "BSE",
    "北交所": "BSE",
}


class OfficialExchangeStockBasicAdapter(CollectorAdapter):
    """Fetch and normalize official SSE/SZSE/BSE stock lists.

    This adapter performs source-side requests only in the collection path. SDK
    and HTTP query paths should continue to read already-ingested core data.
    """

    source = "official_exchange"

    def __init__(
        self,
        session: requests.Session | None = None,
        *,
        timeout: float = 15.0,
        retries: int = 2,
        retry_delay: float = 0.5,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def fetch(self, dataset: str, params: FetchParams | None = None) -> list[Row]:
        dataset_name = normalize_dataset(dataset)
        if dataset_name != STOCK_BASIC:
            raise ValueError("official_exchange currently supports only stock_basic_exchange.")

        params_dict = dict(params or {})
        exchanges = _parse_exchanges(params_dict.get("exchanges", params_dict.get("exchange")))
        limit = _parse_limit(params_dict.get("limit"))

        rows: list[Row] = []
        for exchange in exchanges:
            remaining = None if limit is None else max(limit - len(rows), 0)
            if remaining == 0:
                break

            if exchange == "SSE":
                rows.extend(self._fetch_sse(params_dict, limit=remaining))
            elif exchange == "SZSE":
                rows.extend(self._fetch_szse(params_dict, limit=remaining))
            elif exchange == "BSE":
                rows.extend(self._fetch_bse(params_dict, limit=remaining))

        return _limit_rows(_dedupe_by_instrument_id(rows), limit)

    def _fetch_sse(
        self,
        params: Mapping[str, Any],
        *,
        limit: int | None,
    ) -> list[Row]:
        page_size = _parse_positive_int(params.get("sse_page_size", params.get("page_size")), default=500)
        if limit is not None:
            page_size = max(1, min(page_size, limit))

        rows: list[Row] = []
        page_no = 1
        page_count = 1

        while page_no <= page_count:
            payload = self._get_json(
                SSE_STOCK_LIST_URL,
                headers=SSE_HEADERS,
                params={
                    "isPagination": "true",
                    "pageHelp.cacheSize": "1",
                    "pageHelp.beginPage": str(page_no),
                    "pageHelp.pageSize": str(page_size),
                    "pageHelp.pageNo": str(page_no),
                    "sqlId": "COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L",
                    "STOCK_TYPE": "1",
                    "REG_PROVINCE": "",
                    "CSRC_CODE": "",
                    "STOCK_CODE": "",
                    "COMPANY_STATUS": "2,4,5,7,8",
                    "type": "inParams",
                },
            )
            page_help = payload.get("pageHelp", {}) if isinstance(payload, dict) else {}
            page_count = _parse_positive_int(page_help.get("pageCount"), default=1)
            page_rows = page_help.get("data") or payload.get("result") or []

            if not isinstance(page_rows, list) or not page_rows:
                break

            for source_row in page_rows:
                if isinstance(source_row, dict):
                    rows.append(_normalize_sse_row(source_row))
                    if limit is not None and len(rows) >= limit:
                        return rows

            page_no += 1

        return rows

    def _fetch_bse(
        self,
        params: Mapping[str, Any],
        *,
        limit: int | None,
    ) -> list[Row]:
        rows: list[Row] = []
        page_no = 0
        total_pages = 1

        while page_no < total_pages:
            payload = self._post_jsonp(
                BSE_STOCK_LIST_URL,
                headers=BSE_HEADERS,
                data={
                    "page": str(page_no),
                    "typejb": "T",
                    "xxfcbj[]": "2",
                    "xxzqdm": "",
                    "sortfield": "xxzqdm",
                    "sorttype": "asc",
                },
            )
            table_payload = _first_bse_table(payload)
            total_pages = _parse_positive_int(table_payload.get("totalPages"), default=1)
            page_rows = table_payload.get("content") or []

            if not isinstance(page_rows, list) or not page_rows:
                break

            for source_row in page_rows:
                if isinstance(source_row, dict):
                    rows.append(_normalize_bse_row(source_row))
                    if limit is not None and len(rows) >= limit:
                        return rows

            page_no += 1

        return rows

    def _fetch_szse(
        self,
        params: Mapping[str, Any],
        *,
        limit: int | None,
    ) -> list[Row]:
        try:
            return self._fetch_szse_json(
                params,
                limit=limit,
            )
        except (requests.RequestException, ValueError, zipfile.BadZipFile):
            return self._fetch_szse_xlsx(
                limit=limit,
            )

    def _fetch_szse_json(
        self,
        params: Mapping[str, Any],
        *,
        limit: int | None,
    ) -> list[Row]:
        page_size = _parse_positive_int(params.get("szse_page_size", params.get("page_size")), default=20)
        rows: list[Row] = []
        page_no = 1
        page_count = 1

        while page_no <= page_count:
            payload = self._get_json(
                SZSE_STOCK_LIST_URL,
                headers=SZSE_HEADERS,
                params={
                    "SHOWTYPE": "JSON",
                    "CATALOGID": "1110",
                    "TABKEY": "tab1",
                    "PAGENO": str(page_no),
                    "PAGESIZE": str(page_size),
                    "random": f"{time.time():.6f}",
                },
            )
            table_payload = _first_szse_table(payload)
            metadata = table_payload.get("metadata", {})
            page_count = _parse_positive_int(metadata.get("pagecount"), default=1)
            page_rows = table_payload.get("data") or []

            if not isinstance(page_rows, list) or not page_rows:
                break

            for source_row in page_rows:
                if isinstance(source_row, dict):
                    rows.append(_normalize_szse_row(source_row))
                    if limit is not None and len(rows) >= limit:
                        return rows

            page_no += 1

        return rows

    def _fetch_szse_xlsx(
        self,
        *,
        limit: int | None,
    ) -> list[Row]:
        content = self._get_content(
            SZSE_STOCK_LIST_XLSX_URL,
            headers=SZSE_XLSX_HEADERS,
            params={
                "SHOWTYPE": "xlsx",
                "CATALOGID": "1110",
                "TABKEY": "tab1",
                "random": f"{time.time():.6f}",
            },
        )
        source_rows = _parse_szse_xlsx_rows(content)
        rows: list[Row] = []
        for source_row in source_rows:
            rows.append(_normalize_szse_row(source_row))
            if limit is not None and len(rows) >= limit:
                return rows
        return rows

    def _get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str],
    ) -> Any:
        attempts = max(1, self.retries + 1)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self.session.get(
                    url,
                    headers=dict(headers),
                    params=dict(params),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                time.sleep(self.retry_delay * (attempt + 1))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Request failed without an exception.")

    def _post_jsonp(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        data: Mapping[str, str],
    ) -> Any:
        attempts = max(1, self.retries + 1)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self.session.post(
                    url,
                    headers=dict(headers),
                    data=dict(data),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return _parse_jsonp_array(response.text)
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                time.sleep(self.retry_delay * (attempt + 1))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Request failed without an exception.")

    def _get_content(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str],
    ) -> bytes:
        attempts = max(1, self.retries + 1)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self.session.get(
                    url,
                    headers=dict(headers),
                    params=dict(params),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.content
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                time.sleep(self.retry_delay * (attempt + 1))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Request failed without an exception.")


def _normalize_sse_row(row: Mapping[str, Any]) -> Row:
    symbol = _none_if_blank(row.get("A_STOCK_CODE"))
    delist_date = _normalize_date(row.get("DELIST_DATE"))
    market_code = _none_if_blank_or_dash(row.get("LIST_BOARD"))

    return _ordered_row(
        {
            "instrument_id": f"{symbol}.SH" if symbol else None,
            "symbol": symbol,
            "exchange": "SSE",
            "asset_type": "stock",
            "name": _none_if_blank(row.get("SEC_NAME_CN")),
            "security_full_name": _none_if_blank(row.get("SEC_NAME_FULL")),
            "market_code": market_code,
            "market": SSE_BOARD_NAMES.get(str(market_code), market_code),
            "industry_code": _none_if_blank_or_dash(row.get("CSRC_CODE")),
            "industry": _none_if_blank_or_dash(row.get("CSRC_CODE_DESC")),
            "region_code": _none_if_blank_or_dash(row.get("AREA_NAME")),
            "region": _none_if_blank_or_dash(row.get("AREA_NAME_DESC")),
            "company_code": _none_if_blank_or_dash(row.get("COMPANY_CODE")),
            "company_short_name": _none_if_blank_or_dash(row.get("COMPANY_ABBR")),
            "company_full_name": _none_if_blank_or_dash(row.get("FULL_NAME")),
            "company_short_name_en": _none_if_blank_or_dash(row.get("COMPANY_ABBR_EN")),
            "company_full_name_en": _none_if_blank_or_dash(row.get("FULL_NAME_IN_ENGLISH")),
            "listing_status": "delisted" if delist_date else "listed",
            "list_date": _normalize_date(row.get("LIST_DATE")),
            "delist_date": delist_date,
            "total_share": None,
            "float_share": None,
            "is_profit": None,
            "is_vie": None,
            "has_weighted_voting_rights": None,
            "sponsor": None,
            "share_report_date": None,
        }
    )


def _normalize_szse_row(row: Mapping[str, Any]) -> Row:
    symbol = _none_if_blank(row.get("agdm"))

    return _ordered_row(
        {
            "instrument_id": f"{symbol}.SZ" if symbol else None,
            "symbol": symbol,
            "exchange": "SZSE",
            "asset_type": "stock",
            "name": _none_if_blank(_strip_html(row.get("agjc"))),
            "security_full_name": None,
            "market_code": None,
            "market": _none_if_blank_or_dash(row.get("bk")),
            "industry_code": None,
            "industry": _none_if_blank_or_dash(row.get("sshymc")),
            "region_code": None,
            "region": None,
            "company_code": None,
            "company_short_name": None,
            "company_full_name": None,
            "company_short_name_en": None,
            "company_full_name_en": None,
            "listing_status": "listed",
            "list_date": _normalize_date(row.get("agssrq")),
            "delist_date": None,
            "total_share": _parse_float(row.get("agzgb")),
            "float_share": _parse_float(row.get("agltgb")),
            "is_profit": _none_if_blank(row.get("ylbz")),
            "is_vie": _none_if_blank(row.get("gskzjglx")),
            "has_weighted_voting_rights": _none_if_blank(row.get("sfjybjqcy")),
            "sponsor": None,
            "share_report_date": None,
        }
    )


def _normalize_bse_row(row: Mapping[str, Any]) -> Row:
    symbol = _none_if_blank(row.get("xxzqdm"))

    return _ordered_row(
        {
            "instrument_id": f"{symbol}.BJ" if symbol else None,
            "symbol": symbol,
            "exchange": "BSE",
            "asset_type": "stock",
            "name": _none_if_blank(row.get("xxzqjc")),
            "security_full_name": None,
            "market_code": _none_if_blank_or_dash(row.get("xxfcbj")),
            "market": "北交所",
            "industry_code": None,
            "industry": _none_if_blank_or_dash(row.get("xxhyzl")),
            "region_code": None,
            "region": _none_if_blank_or_dash(row.get("xxssdq")),
            "company_code": None,
            "company_short_name": None,
            "company_full_name": None,
            "company_short_name_en": _none_if_blank_or_dash(row.get("xxywjc")),
            "company_full_name_en": None,
            "listing_status": "listed",
            "list_date": _normalize_date(row.get("xxgprq") or row.get("fxssrq")),
            "delist_date": None,
            "total_share": _parse_share_count_to_100m(row.get("xxzgb")),
            "float_share": _parse_share_count_to_100m(row.get("xxfxsgb")),
            "is_profit": None,
            "is_vie": None,
            "has_weighted_voting_rights": None,
            "sponsor": _none_if_blank_or_dash(row.get("xxzbqs")),
            "share_report_date": _normalize_date(row.get("xxjsrq")),
        }
    )


def _ordered_row(values: Mapping[str, Any]) -> Row:
    schema = get_schema(STOCK_BASIC)
    return {field_name: values.get(field_name) for field_name in schema.field_names}


def _parse_exchanges(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        parts: Iterable[Any] = ("SSE", "SZSE", "BSE")
    elif isinstance(value, str):
        parts = re.split(r"[,，\s]+", value)
    elif isinstance(value, Iterable):
        parts = value
    else:
        parts = (value,)

    exchanges: list[str] = []
    for part in parts:
        text = str(part).strip()
        if not text:
            continue
        normalized = EXCHANGE_ALIASES.get(text.upper(), EXCHANGE_ALIASES.get(text))
        if normalized is None:
            allowed = ", ".join(("SSE", "SZSE", "BSE"))
            raise ValueError(f"Unsupported exchange '{text}'. Expected one of: {allowed}")
        if normalized not in exchanges:
            exchanges.append(normalized)

    return tuple(exchanges or ("SSE", "SZSE", "BSE"))


def _parse_limit(value: Any) -> int | None:
    if value in (None, ""):
        return None
    limit = int(value)
    if limit < 0:
        raise ValueError("limit must be greater than or equal to 0")
    return limit


def _parse_positive_int(value: Any, *, default: int) -> int:
    if value in (None, ""):
        return default
    result = int(value)
    if result <= 0:
        raise ValueError("integer value must be greater than 0")
    return result


def _limit_rows(rows: list[Row], limit: int | None) -> list[Row]:
    if limit is None:
        return rows
    return rows[:limit]


def _dedupe_by_instrument_id(rows: list[Row]) -> list[Row]:
    seen: set[str] = set()
    result: list[Row] = []
    for row in rows:
        instrument_id = row.get("instrument_id")
        if not instrument_id:
            result.append(row)
            continue
        key = str(instrument_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


SZSE_XLSX_HEADER_MAP = {
    "板块": "bk",
    "证券类别": "bk",
    "A股代码": "agdm",
    "A股证券代码": "agdm",
    "证券代码": "agdm",
    "A股简称": "agjc",
    "A股证券简称": "agjc",
    "证券简称": "agjc",
    "A股上市日期": "agssrq",
    "上市日期": "agssrq",
    "A股总股本": "agzgb",
    "总股本": "agzgb",
    "A股流通股本": "agltgb",
    "流通股本": "agltgb",
    "所属行业": "sshymc",
    "行业": "sshymc",
    "是否尚未盈利": "ylbz",
    "盈利标识": "ylbz",
    "是否具有表决权差异安排": "sfjybjqcy",
    "表决权差异安排": "sfjybjqcy",
    "公司控制架构类型": "gskzjglx",
    "协议控制架构": "gskzjglx",
}

XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XLSX_PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _parse_szse_xlsx_rows(content: bytes) -> list[dict[str, str]]:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        shared_strings = _read_xlsx_shared_strings(archive)
        sheet_xml = archive.read(_first_xlsx_sheet_path(archive))
        sheet_root = ET.fromstring(sheet_xml)

    rows = _read_xlsx_rows(sheet_root, shared_strings)
    header_map: dict[int, str] = {}
    data_rows: list[dict[str, str]] = []

    for values in rows:
        if not values:
            continue
        if not header_map:
            header_map = {
                index: field_name
                for index, value in enumerate(values)
                if (field_name := SZSE_XLSX_HEADER_MAP.get(_normalize_header_label(value)))
            }
            if {"agdm", "agjc"}.issubset(set(header_map.values())):
                continue
            header_map = {}
            continue

        row = {
            field_name: values[index]
            for index, field_name in header_map.items()
            if index < len(values) and values[index] != ""
        }
        symbol = _none_if_blank(row.get("agdm"))
        if symbol and symbol.isdigit():
            data_rows.append(row)

    if not data_rows:
        raise ValueError("Unexpected SZSE xlsx stock list response format.")
    return data_rows


def _read_xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall(f"{{{XLSX_MAIN_NS}}}si"):
        parts = [
            text_node.text or ""
            for text_node in item.findall(f".//{{{XLSX_MAIN_NS}}}t")
        ]
        strings.append("".join(parts))
    return strings


def _first_xlsx_sheet_path(archive: zipfile.ZipFile) -> str:
    fallback = "xl/worksheets/sheet1.xml"
    if "xl/workbook.xml" not in archive.namelist():
        return fallback

    workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
    first_sheet = workbook_root.find(f".//{{{XLSX_MAIN_NS}}}sheet")
    relationship_id = None if first_sheet is None else first_sheet.get(f"{{{XLSX_REL_NS}}}id")
    if not relationship_id or "xl/_rels/workbook.xml.rels" not in archive.namelist():
        return fallback

    rel_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relationship in rel_root.findall(f"{{{XLSX_PACKAGE_REL_NS}}}Relationship"):
        if relationship.get("Id") != relationship_id:
            continue
        target = relationship.get("Target", "")
        if target.startswith("/"):
            return target.lstrip("/")
        return f"xl/{target}"
    return fallback


def _read_xlsx_rows(root: ET.Element, shared_strings: list[str]) -> list[list[str]]:
    sheet_data = root.find(f".//{{{XLSX_MAIN_NS}}}sheetData")
    if sheet_data is None:
        return []

    rows: list[list[str]] = []
    for row_node in sheet_data.findall(f"{{{XLSX_MAIN_NS}}}row"):
        row_values: list[str] = []
        next_index = 0
        for cell in row_node.findall(f"{{{XLSX_MAIN_NS}}}c"):
            column_index = _xlsx_column_index(cell.get("r")) or next_index
            while len(row_values) < column_index:
                row_values.append("")
            row_values.append(_xlsx_cell_text(cell, shared_strings))
            next_index = column_index + 1
        while row_values and row_values[-1] == "":
            row_values.pop()
        rows.append(row_values)
    return rows


def _xlsx_cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        parts = [
            text_node.text or ""
            for text_node in cell.findall(f".//{{{XLSX_MAIN_NS}}}t")
        ]
        return _collapse_spaces("".join(parts)) or ""

    value_node = cell.find(f"{{{XLSX_MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return ""

    value = value_node.text
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (IndexError, ValueError):
            return ""
    return _collapse_spaces(value) or ""


def _xlsx_column_index(reference: str | None) -> int | None:
    if not reference:
        return None
    match = re.match(r"([A-Z]+)", reference)
    if match is None:
        return None
    index = 0
    for char in match.group(1):
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def _normalize_header_label(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _first_szse_table(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return first
    if isinstance(payload, dict):
        return payload
    raise ValueError("Unexpected SZSE stock list response format.")


def _first_bse_table(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return first
    raise ValueError("Unexpected BSE stock list response format.")


def _parse_jsonp_array(text: str) -> Any:
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < start:
        raise ValueError("Unexpected JSONP response format.")
    return json.loads(text[start : end + 1])


def _normalize_date(value: Any) -> str | None:
    text = _none_if_blank_or_dash(value)
    if text is None:
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) < 8:
        return None
    return digits[:8]


def _parse_float(value: Any) -> float | None:
    text = _none_if_blank_or_dash(value)
    if text is None:
        return None
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def _parse_share_count_to_100m(value: Any) -> float | None:
    parsed = _parse_float(value)
    if parsed is None:
        return None
    return parsed / 100_000_000


def _strip_html(value: Any) -> str | None:
    text = _none_if_blank(value)
    if text is None:
        return None
    without_tags = re.sub(r"<[^>]+>", "", unescape(text))
    return _collapse_spaces(without_tags)


def _collapse_spaces(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip() or None


def _none_if_blank(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _none_if_blank_or_dash(value: Any) -> str | None:
    text = _none_if_blank(value)
    if text is None or text in {"-", "--", "N/A", "n/a", "null", "None"}:
        return None
    return text
