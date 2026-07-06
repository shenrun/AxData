"""Canonical AxData interface schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Tuple


@dataclass(frozen=True)
class Field:
    """Field metadata used by storage, query, docs, and quality checks."""

    name: str
    dtype: str
    nullable: bool = True
    description: str = ""
    description_zh: str = ""
    unit: str | None = None
    aliases: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TableSchema:
    """Table-level schema metadata."""

    name: str
    fields: Tuple[Field, ...]
    primary_key: Tuple[str, ...]
    date_field: str | None = None
    datetime_field: str | None = None
    description: str = ""
    display_name_zh: str = ""
    interface_group: str = ""
    status: str = "ready"
    provider_field_mappings: Mapping[str, str] = field(default_factory=dict)

    @property
    def field_names(self) -> Tuple[str, ...]:
        return tuple(field.name for field in self.fields)

    @property
    def required_fields(self) -> Tuple[str, ...]:
        required = {field.name for field in self.fields if not field.nullable}
        required.update(self.primary_key)
        return tuple(name for name in self.field_names if name in required)

    def has_field(self, name: str) -> bool:
        return name in self.field_names


STOCK_BASIC_FIELDS: Tuple[Field, ...] = (
    Field(
        "instrument_id",
        "string",
        nullable=False,
        description="AxData stock identifier, e.g. 000001.SZ.",
        description_zh="AxData 统一证券代码，例如 000001.SZ、600000.SH、430047.BJ。",
    ),
    Field(
        "symbol",
        "string",
        nullable=False,
        description="Exchange-local stock code without suffix.",
        description_zh="证券代码，不带交易所后缀，例如 000001。",
    ),
    Field(
        "exchange",
        "string",
        nullable=False,
        description="Exchange code: SSE, SZSE, or BSE.",
        description_zh="交易所代码，建议值为 SSE、SZSE、BSE。",
    ),
    Field(
        "asset_type",
        "string",
        nullable=False,
        description="Asset type, fixed to stock for stock basic interfaces.",
        description_zh="资产类型，本接口固定为 stock。",
    ),
    Field(
        "name",
        "string",
        nullable=False,
        description="Security short name.",
        description_zh="证券简称。",
    ),
    Field(
        "security_full_name",
        "string",
        description="Security full name when available.",
        description_zh="证券全称；没有时为空。",
    ),
    Field(
        "market_code",
        "string",
        description="Market board code when available.",
        description_zh="市场板块代码；没有时为空。",
    ),
    Field(
        "market",
        "string",
        description="Market board name.",
        description_zh="市场板块名称，例如主板、创业板、科创板、北交所。",
    ),
    Field(
        "industry_code",
        "string",
        description="Industry code when available.",
        description_zh="行业代码；没有时为空。",
    ),
    Field(
        "industry",
        "string",
        description="Industry name when available.",
        description_zh="行业名称；没有时为空。",
    ),
    Field(
        "region_code",
        "string",
        description="Region code when available.",
        description_zh="地区代码；没有时为空。",
    ),
    Field(
        "region",
        "string",
        description="Company region when available.",
        description_zh="地区名称；没有时为空。",
    ),
    Field(
        "company_code",
        "string",
        description="Company code when available.",
        description_zh="公司代码；没有时为空。",
    ),
    Field(
        "company_short_name",
        "string",
        description="Company short name when available.",
        description_zh="公司简称；没有时为空。",
    ),
    Field(
        "company_full_name",
        "string",
        description="Company full legal name when available.",
        description_zh="公司法定全称；没有时为空。",
    ),
    Field(
        "company_short_name_en",
        "string",
        description="Company English short name when available.",
        description_zh="公司英文简称；没有时为空。",
    ),
    Field(
        "company_full_name_en",
        "string",
        description="Company English full name when available.",
        description_zh="公司英文全称；没有时为空。",
    ),
    Field(
        "listing_status",
        "string",
        nullable=False,
        description="AxData listing status: listed, delisted, suspended, or unknown.",
        description_zh="AxData 上市状态，建议值 listed、delisted、suspended、unknown。",
    ),
    Field(
        "list_date",
        "string",
        description="Listing date in YYYYMMDD format.",
        description_zh="上市日期，格式为 YYYYMMDD。",
    ),
    Field(
        "delist_date",
        "string",
        description="Delisting date in YYYYMMDD format.",
        description_zh="退市日期，格式为 YYYYMMDD；未退市为空。",
    ),
    Field(
        "total_share",
        "float64",
        description="Total shares, unit: 100 million shares.",
        description_zh="总股本，单位：亿股；没有时为空。",
    ),
    Field(
        "float_share",
        "float64",
        description="Tradable shares, unit: 100 million shares.",
        description_zh="流通股本，单位：亿股；没有时为空。",
    ),
    Field(
        "is_profit",
        "string",
        description="Profitability marker when available.",
        description_zh="是否尚未盈利；没有时为空。",
    ),
    Field(
        "is_vie",
        "string",
        description="VIE/control-structure marker when available.",
        description_zh="是否具有协议控制架构；没有时为空。",
    ),
    Field(
        "has_weighted_voting_rights",
        "string",
        description="Weighted voting rights marker when available.",
        description_zh="是否具有表决权差异安排；没有时为空。",
    ),
    Field(
        "sponsor",
        "string",
        description="Sponsoring broker or listing sponsor when available.",
        description_zh="保荐机构或主办券商；没有时为空。",
    ),
    Field(
        "share_report_date",
        "string",
        description="Share capital report date in YYYYMMDD format when available.",
        description_zh="股本数据报告日期，格式为 YYYYMMDD；没有时为空。",
    ),
)


SCHEMAS: Dict[str, TableSchema] = {
    "stock_basic_exchange": TableSchema(
        name="stock_basic_exchange",
        primary_key=("instrument_id",),
        date_field="list_date",
        description="Stock list in official exchange interface口径.",
        display_name_zh="股票列表（交易所）",
        interface_group="本地数据/股票/基础资料",
        fields=STOCK_BASIC_FIELDS,
    ),
    "trade_cal": TableSchema(
        name="trade_cal",
        primary_key=("exchange", "cal_date"),
        date_field="cal_date",
        description="Trading calendar by exchange.",
        display_name_zh="交易日历",
        interface_group="本地数据/股票/基础资料",
        fields=(
            Field(
                "exchange",
                "string",
                nullable=False,
                description="Exchange code.",
                description_zh="交易所代码。",
            ),
            Field(
                "cal_date",
                "string",
                nullable=False,
                description="Calendar date in YYYYMMDD format.",
                description_zh="自然日期，格式为 YYYYMMDD。",
            ),
            Field(
                "is_open",
                "int64",
                nullable=False,
                description="1 for trading day, 0 otherwise.",
                description_zh="是否交易日，1 表示交易日，0 表示非交易日。",
            ),
            Field(
                "pretrade_date",
                "string",
                description="Previous trading date in YYYYMMDD format.",
                description_zh="上一个交易日，格式为 YYYYMMDD。",
            ),
        ),
    ),
    "daily": TableSchema(
        name="daily",
        primary_key=("ts_code", "trade_date"),
        date_field="trade_date",
        description="Daily OHLCV market data.",
        display_name_zh="日线行情",
        interface_group="本地数据/股票/行情数据",
        provider_field_mappings={
            "instrument_id": "ts_code",
            "volume": "vol",
            "trade_time": "trade_date",
        },
        fields=(
            Field(
                "ts_code",
                "string",
                nullable=False,
                description="AxData stock identifier.",
                description_zh="AxData 统一证券代码，例如 000001.SZ。",
                aliases=("instrument_id",),
            ),
            Field(
                "trade_date",
                "string",
                nullable=False,
                description="Trading date in YYYYMMDD format.",
                description_zh="交易日期，格式为 YYYYMMDD。",
                aliases=("trade_time",),
            ),
            Field("open", "float64", description="Open price.", description_zh="开盘价。", unit="CNY"),
            Field("high", "float64", description="High price.", description_zh="最高价。", unit="CNY"),
            Field("low", "float64", description="Low price.", description_zh="最低价。", unit="CNY"),
            Field("close", "float64", description="Close price.", description_zh="收盘价。", unit="CNY"),
            Field("pre_close", "float64", description="Previous close price.", description_zh="昨收价。", unit="CNY"),
            Field("change", "float64", description="Absolute price change.", description_zh="涨跌额。", unit="CNY"),
            Field("pct_chg", "float64", description="Percentage price change.", description_zh="涨跌幅。", unit="percent"),
            Field(
                "vol",
                "float64",
                description="Trading volume.",
                description_zh="成交量，单位：手。",
                unit="lot",
                aliases=("volume",),
            ),
            Field("amount", "float64", description="Trading amount.", description_zh="成交额，单位：千元。", unit="thousand CNY"),
        ),
    ),
    "adj_factor": TableSchema(
        name="adj_factor",
        primary_key=("ts_code", "trade_date"),
        date_field="trade_date",
        description="Daily adjustment factors.",
        display_name_zh="复权因子",
        interface_group="本地数据/股票/复权与股本",
        fields=(
            Field(
                "ts_code",
                "string",
                nullable=False,
                description="AxData stock identifier.",
                description_zh="AxData 统一证券代码，例如 000001.SZ。",
                aliases=("instrument_id",),
            ),
            Field(
                "trade_date",
                "string",
                nullable=False,
                description="Trading date in YYYYMMDD format.",
                description_zh="交易日期，格式为 YYYYMMDD。",
            ),
            Field(
                "adj_factor",
                "float64",
                nullable=False,
                description="Adjustment factor.",
                description_zh="复权因子。",
            ),
        ),
    ),
}

TABLE_ALIASES: Dict[str, str] = {
    "stock_basic": "stock_basic_exchange",
    "stock-basic": "stock_basic_exchange",
    "stock-basic-exchange": "stock_basic_exchange",
    "stock_basic_exchange": "stock_basic_exchange",
}


def normalize_table_name(table: str) -> str:
    normalized = table.strip().lower()
    return TABLE_ALIASES.get(normalized, normalized)


def list_tables(*, include_aliases: bool = False) -> Tuple[str, ...]:
    tables = tuple(SCHEMAS)
    if include_aliases:
        return tuple(dict.fromkeys((*tables, *TABLE_ALIASES)))
    return tables


def get_schema(table: str) -> TableSchema:
    table_name = normalize_table_name(table)
    try:
        return SCHEMAS[table_name]
    except KeyError as exc:
        known = ", ".join(list_tables())
        raise KeyError(f"Unknown AxData table {table!r}. Known tables: {known}.") from exc


def require_fields(table: str, fields: Iterable[str]) -> None:
    schema = get_schema(table)
    missing = [field for field in fields if not schema.has_field(field)]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Unknown field(s) for {table!r}: {missing_text}.")
