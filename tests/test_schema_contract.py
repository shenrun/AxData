import csv
from pathlib import Path

from axdata_core import get_schema, list_tables


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_initial_tables_are_registered():
    assert set(list_tables()) >= {
        "stock_basic_exchange",
        "trade_cal",
        "daily",
        "adj_factor",
    }
    assert "stock_basic" not in set(list_tables())
    assert "stock_basic" in set(list_tables(include_aliases=True))


def test_stock_basic_alias_points_to_exchange_interface():
    assert get_schema("stock_basic").name == "stock_basic_exchange"


def test_schema_contract_has_primary_keys_and_required_metadata():
    for table in ("stock_basic_exchange", "trade_cal", "daily", "adj_factor"):
        schema = get_schema(table)

        assert schema.name == table
        assert schema.primary_key
        assert schema.fields
        assert schema.field_names

        for key in schema.primary_key:
            assert key in schema.field_names

        for field in schema.fields:
            assert field.name
            assert field.dtype
            assert isinstance(field.nullable, bool)


def test_daily_schema_matches_quant_baseline():
    schema = get_schema("daily")

    for field in ("ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"):
        assert field in schema.field_names

    assert schema.primary_key == ("ts_code", "trade_date")
    assert schema.date_field == "trade_date"


def test_daily_schema_documents_canonical_aliases_and_units():
    schema = get_schema("daily")
    fields = {field.name: field for field in schema.fields}

    assert schema.provider_field_mappings == {
        "instrument_id": "ts_code",
        "volume": "vol",
        "trade_time": "trade_date",
    }
    assert fields["ts_code"].aliases == ("instrument_id",)
    assert fields["trade_date"].aliases == ("trade_time",)
    assert fields["vol"].aliases == ("volume",)
    assert fields["open"].unit == "CNY"
    assert fields["vol"].unit == "lot"
    assert fields["amount"].unit == "thousand CNY"


def test_adj_factor_schema_accepts_instrument_id_as_source_alias():
    schema = get_schema("adj_factor")
    fields = {field.name: field for field in schema.fields}

    assert fields["ts_code"].aliases == ("instrument_id",)


def test_stock_basic_schema_uses_axdata_canonical_fields():
    schema = get_schema("stock_basic_exchange")

    expected_fields = [
        "instrument_id",
        "symbol",
        "exchange",
        "asset_type",
        "name",
        "security_full_name",
        "market_code",
        "market",
        "industry_code",
        "industry",
        "region_code",
        "region",
        "company_code",
        "company_short_name",
        "company_full_name",
        "company_short_name_en",
        "company_full_name_en",
        "listing_status",
        "list_date",
        "delist_date",
        "total_share",
        "float_share",
        "is_profit",
        "is_vie",
        "has_weighted_voting_rights",
        "sponsor",
        "share_report_date",
    ]

    assert list(schema.field_names) == expected_fields
    assert "ts_code" not in schema.field_names
    assert "list_status" not in schema.field_names
    assert "upstream_source" not in schema.field_names
    assert "source" not in schema.field_names
    assert "source_batch_id" not in schema.field_names
    assert schema.primary_key == ("instrument_id",)
    assert schema.date_field == "list_date"


def test_stock_basic_schema_has_chinese_descriptions():
    exchange_schema = get_schema("stock_basic_exchange")

    assert exchange_schema.display_name_zh == "股票列表（交易所）"

    for field in exchange_schema.fields:
        assert field.description_zh

    instrument_id = next(field for field in exchange_schema.fields if field.name == "instrument_id")
    assert "统一证券代码" in instrument_id.description_zh

    exchange = next(field for field in exchange_schema.fields if field.name == "exchange")
    assert "SSE" in exchange.description_zh
    assert "SZSE" in exchange.description_zh
    assert "BSE" in exchange.description_zh


def test_stock_basic_csv_sample_matches_schema_contract():
    schema = get_schema("stock_basic_exchange")
    csv_path = PROJECT_ROOT / "examples" / "csv" / "stock_basic.csv"

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        rows = list(reader)

    assert reader.fieldnames == list(schema.field_names)
    assert rows
    assert {row["exchange"] for row in rows} == {"SSE", "SZSE", "BSE"}
    assert {row["asset_type"] for row in rows} == {"stock"}
    assert {row["instrument_id"].split(".")[-1] for row in rows} == {"SH", "SZ", "BJ"}
    assert all(row["listing_status"] == "listed" for row in rows)
