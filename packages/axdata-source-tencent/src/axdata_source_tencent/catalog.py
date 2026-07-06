"""Tencent Finance Provider interface catalog."""

from __future__ import annotations

from axdata_core.plugins import FieldSpec, InterfaceSpec, ParameterSpec, RequestExample

from .metadata import SOURCE_CODE, SOURCE_NAME_ZH

INTERFACE_NAME = "tencent_realtime_snapshot"


INTERFACES: tuple[InterfaceSpec, ...] = (
    InterfaceSpec(
        name=INTERFACE_NAME,
        display_name_zh="实时快照",
        source_code=SOURCE_CODE,
        source_name_zh=SOURCE_NAME_ZH,
        category="行情数据",
        menu_path=(SOURCE_NAME_ZH, "行情数据"),
        asset_class="stock",
        parameters=(
            ParameterSpec(
                name="code",
                display_name_zh="证券代码",
                type="string",
                required=True,
                multiple=True,
                placeholder="000001.SZ,600000.SH",
                description=(
                    "证券代码，支持 000001.SZ、600000.SH、920000.BJ、"
                    "000001.SH、510050.SH 或列表。"
                ),
            ),
        ),
        fields=(
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
            FieldSpec(
                name="asset_type",
                display_name_zh="资产类型",
                type="string",
                description="资产类型：stock、index、etf。",
            ),
            FieldSpec(name="name", display_name_zh="证券简称", type="string"),
            FieldSpec(
                name="quote_time",
                display_name_zh="源端行情时间",
                type="datetime",
                description="源端行情时间，格式 YYYYMMDDHHMMSS。",
            ),
            FieldSpec(
                name="last_price",
                display_name_zh="最新价",
                type="number",
                unit="元或指数点",
            ),
            FieldSpec(
                name="pre_close",
                display_name_zh="昨收价",
                type="number",
                unit="元或指数点",
            ),
            FieldSpec(
                name="open",
                display_name_zh="开盘价",
                type="number",
                unit="元或指数点",
            ),
            FieldSpec(
                name="high",
                display_name_zh="最高价",
                type="number",
                unit="元或指数点",
            ),
            FieldSpec(
                name="low",
                display_name_zh="最低价",
                type="number",
                unit="元或指数点",
            ),
            FieldSpec(
                name="change",
                display_name_zh="涨跌额",
                type="number",
                unit="元或指数点",
            ),
            FieldSpec(
                name="change_pct",
                display_name_zh="涨跌幅",
                type="number",
                unit="%",
                description="百分比数值，例如 1.23 表示 1.23%。",
            ),
            FieldSpec(name="volume", display_name_zh="成交量", type="number"),
            FieldSpec(name="amount", display_name_zh="成交额", type="number", unit="元"),
            FieldSpec(
                name="turnover_rate",
                display_name_zh="换手率",
                type="number",
                unit="%",
                description="百分比数值；指数可能为空。",
            ),
            FieldSpec(
                name="pe_dynamic",
                display_name_zh="动态市盈率",
                type="number",
                description="不适用时为空。",
            ),
            FieldSpec(
                name="pb",
                display_name_zh="市净率",
                type="number",
                description="不适用时为空。",
            ),
            FieldSpec(
                name="total_market_value",
                display_name_zh="总市值",
                type="number",
                unit="亿元",
            ),
            FieldSpec(
                name="float_market_value",
                display_name_zh="流通市值",
                type="number",
                unit="亿元",
            ),
            FieldSpec(
                name="limit_up_price",
                display_name_zh="涨停价",
                type="number",
                unit="元",
                description="不适用时为空。",
            ),
            FieldSpec(
                name="limit_down_price",
                display_name_zh="跌停价",
                type="number",
                unit="元",
                description="不适用时为空。",
            ),
            FieldSpec(name="currency", display_name_zh="币种", type="string"),
        ),
        examples=(
            RequestExample(
                title="批量实时快照",
                request_time="2026-06-22T14:46:33+08:00",
                request={
                    "interface_name": INTERFACE_NAME,
                    "params": {"code": ["000001.SZ", "600000.SH"]},
                    "fields": ["instrument_id", "name", "last_price", "quote_time"],
                },
                response={
                    "data": [
                        {
                            "instrument_id": "000001.SZ",
                            "name": "平安银行",
                            "quote_time": "20260622144633",
                            "last_price": 10.64,
                        }
                    ],
                    "schema": [
                        {"name": "instrument_id", "type": "string"},
                        {"name": "name", "type": "string"},
                        {"name": "quote_time", "type": "datetime"},
                        {"name": "last_price", "type": "number"},
                    ],
                    "meta": {"source": SOURCE_CODE},
                },
            ),
        ),
        notes=(
            "通过腾讯财经公开行情接口临时请求实时快照，默认不入库。"
            "quote_time 是源端行情时间。"
        ),
    ),
)

DOWNLOADER_PROFILES = ()
