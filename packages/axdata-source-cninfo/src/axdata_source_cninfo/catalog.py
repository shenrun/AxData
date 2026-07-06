"""Cninfo Provider interface catalog."""

from __future__ import annotations

from axdata_core.plugins import FieldSpec, InterfaceSpec, ParameterSpec, RequestExample

from .metadata import SOURCE_CODE, SOURCE_NAME_ZH

ANNOUNCEMENTS_INTERFACE_NAME = "cninfo_announcements"
DETAIL_INTERFACE_NAME = "cninfo_announcement_detail"


ANNOUNCEMENT_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="instrument_id",
        display_name_zh="AxData 统一证券代码",
        type="string",
        required=True,
        description="AxData 统一证券代码。",
    ),
    FieldSpec(name="symbol", display_name_zh="六位证券代码", type="string"),
    FieldSpec(
        name="exchange",
        display_name_zh="交易所",
        type="string",
        description="交易所代码：SSE、SZSE、BSE。",
    ),
    FieldSpec(name="name", display_name_zh="证券简称", type="string"),
    FieldSpec(name="announcement_id", display_name_zh="公告 ID", type="string"),
    FieldSpec(name="title", display_name_zh="公告标题", type="string"),
    FieldSpec(
        name="publish_date",
        display_name_zh="公告发布日期",
        type="date",
        description="公告发布日期，格式 YYYYMMDD。",
    ),
    FieldSpec(name="file_type", display_name_zh="附件类型", type="string"),
    FieldSpec(
        name="file_size_kb",
        display_name_zh="附件大小",
        type="number",
        unit="KB",
    ),
    FieldSpec(name="download_url", display_name_zh="PDF 下载地址", type="string"),
)


INTERFACES: tuple[InterfaceSpec, ...] = (
    InterfaceSpec(
        name=ANNOUNCEMENTS_INTERFACE_NAME,
        display_name_zh="公告列表",
        source_code=SOURCE_CODE,
        source_name_zh=SOURCE_NAME_ZH,
        category="公告数据",
        menu_path=(SOURCE_NAME_ZH, "公告数据"),
        asset_class="stock",
        parameters=(
            ParameterSpec(
                name="code",
                display_name_zh="股票代码",
                type="string",
                required=True,
                multiple=True,
                placeholder="000001.SZ,600000.SH",
                description="股票代码，支持 000001、000001.SZ、sh600000 或列表。",
            ),
            ParameterSpec(
                name="start_date",
                display_name_zh="开始日期",
                type="date",
                placeholder="20240101",
                description="开始日期，YYYYMMDD 或 YYYY-MM-DD。",
            ),
            ParameterSpec(
                name="end_date",
                display_name_zh="结束日期",
                type="date",
                placeholder="20240131",
                description="结束日期，YYYYMMDD 或 YYYY-MM-DD。",
            ),
            ParameterSpec(
                name="page",
                display_name_zh="页码",
                type="integer",
                default=1,
                description="页码，默认 1。",
            ),
            ParameterSpec(
                name="limit",
                display_name_zh="每页条数",
                type="integer",
                default=30,
                description="每页条数，默认 30，最大 100。",
            ),
        ),
        fields=ANNOUNCEMENT_FIELDS,
        examples=(
            RequestExample(
                title="查询单只股票公告",
                request_time="2026-06-22T14:46:33+08:00",
                request={
                    "interface_name": ANNOUNCEMENTS_INTERFACE_NAME,
                    "params": {
                        "code": "000001.SZ",
                        "start_date": "20240101",
                        "end_date": "20240131",
                        "limit": 3,
                    },
                    "fields": ["instrument_id", "title", "publish_date", "download_url"],
                },
                response={
                    "data": [
                        {
                            "instrument_id": "000001.SZ",
                            "title": "关联交易公告",
                            "publish_date": "20240123",
                            "download_url": "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF",
                        }
                    ],
                    "schema": [
                        {"name": "instrument_id", "type": "string"},
                        {"name": "title", "type": "string"},
                        {"name": "publish_date", "type": "date"},
                        {"name": "download_url", "type": "string"},
                    ],
                    "meta": {"source": SOURCE_CODE},
                },
            ),
        ),
        notes="临时请求巨潮公告列表，返回公告元信息，默认不入库。",
    ),
    InterfaceSpec(
        name=DETAIL_INTERFACE_NAME,
        display_name_zh="公告PDF元信息",
        source_code=SOURCE_CODE,
        source_name_zh=SOURCE_NAME_ZH,
        category="公告数据",
        menu_path=(SOURCE_NAME_ZH, "公告数据"),
        asset_class="stock",
        parameters=(
            ParameterSpec(
                name="announcement_id",
                display_name_zh="公告 ID",
                type="string",
                description="公告 ID；可选。",
            ),
            ParameterSpec(
                name="url",
                display_name_zh="公告 PDF 路径",
                type="string",
                required=True,
                placeholder="https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF",
                description="公告 PDF 路径或完整 URL。",
            ),
            ParameterSpec(
                name="title",
                display_name_zh="公告标题",
                type="string",
                description="可选公告标题，用于透传。",
            ),
        ),
        fields=(
            FieldSpec(name="announcement_id", display_name_zh="公告 ID", type="string"),
            FieldSpec(name="title", display_name_zh="公告标题", type="string"),
            FieldSpec(name="content_type", display_name_zh="文件类型", type="string"),
            FieldSpec(
                name="file_size_bytes",
                display_name_zh="文件大小",
                type="integer",
                unit="字节",
            ),
            FieldSpec(name="download_url", display_name_zh="PDF 下载地址", type="string"),
        ),
        examples=(
            RequestExample(
                title="查询公告 PDF 元信息",
                request_time="2026-06-22T14:46:33+08:00",
                request={
                    "interface_name": DETAIL_INTERFACE_NAME,
                    "params": {
                        "announcement_id": "1218968511",
                        "url": "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF",
                    },
                    "fields": ["announcement_id", "content_type", "file_size_bytes", "download_url"],
                },
                response={
                    "data": [
                        {
                            "announcement_id": "1218968511",
                            "content_type": "application/pdf",
                            "file_size_bytes": 158287,
                            "download_url": "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF",
                        }
                    ],
                    "schema": [
                        {"name": "announcement_id", "type": "string"},
                        {"name": "content_type", "type": "string"},
                        {"name": "file_size_bytes", "type": "integer"},
                        {"name": "download_url", "type": "string"},
                    ],
                    "meta": {"source": SOURCE_CODE},
                },
            ),
        ),
        notes="只确认公告 PDF 的类型、大小和下载地址，不解析 PDF 正文。",
    ),
)

DOWNLOADER_PROFILES = ()
