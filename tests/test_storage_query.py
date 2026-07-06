import pandas as pd

from axdata_core import query_table, read_core_table, validate_table, write_core_table


def test_core_parquet_round_trip_and_query(tmp_path):
    root = tmp_path / "data"
    df = pd.DataFrame(
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
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "20240102",
                "open": 20.0,
                "high": 21.0,
                "low": 19.5,
                "close": 20.5,
                "pre_close": 20.0,
                "change": 0.5,
                "pct_chg": 2.5,
                "vol": 2000.0,
                "amount": 41000.0,
            },
        ]
    )

    path = write_core_table("daily", df, root=root)
    assert path.exists()

    saved = read_core_table("daily", root=root)
    assert len(saved) == 2
    assert not validate_table("daily", saved)

    result = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=["ts_code", "trade_date", "close"],
        start_date="20240101",
        end_date="20240131",
    )

    assert list(result.columns) == ["ts_code", "trade_date", "close"]
    assert result.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2}
    ]

    limited = query_table(
        "daily",
        root=root,
        fields=["ts_code", "trade_date"],
        limit=1,
    )

    assert list(limited.columns) == ["ts_code", "trade_date"]
    assert len(limited) == 1


def test_partitioned_core_table_read_and_query(tmp_path):
    root = tmp_path / "data"
    first_partition = root / "core" / "table=daily" / "trade_date=20240102"
    second_partition = root / "core" / "table=daily" / "trade_date=2024-01-03"
    first_partition.mkdir(parents=True)
    second_partition.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240102",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
            }
        ]
    ).to_parquet(first_partition / "part-0.parquet", engine="pyarrow", index=False)
    pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "open": 10.2,
                "high": 10.8,
                "low": 10.1,
                "close": 10.6,
            }
        ]
    ).to_parquet(second_partition / "part-0.parquet", engine="pyarrow", index=False)

    saved = read_core_table("daily", root=root)
    saved_records = saved.sort_values(["trade_date", "ts_code"]).to_dict(orient="records")

    assert saved_records == [
        {
            "ts_code": "000001.SZ",
            "trade_date": "20240102",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
        },
        {
            "ts_code": "000001.SZ",
            "trade_date": "20240103",
            "open": 10.2,
            "high": 10.8,
            "low": 10.1,
            "close": 10.6,
        },
    ]
    assert not validate_table("daily", saved)

    result = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=["ts_code", "trade_date", "close"],
        start_date="20240102",
        end_date="20240103",
    )

    assert result.sort_values("trade_date").to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2},
        {"ts_code": "000001.SZ", "trade_date": "20240103", "close": 10.6},
    ]


def test_query_partitioned_core_table_prunes_date_partitions(tmp_path):
    root = tmp_path / "data"
    first_partition = root / "core" / "table=daily" / "trade_date=20240102"
    second_partition = root / "core" / "table=daily" / "trade_date=20240103"
    first_partition.mkdir(parents=True)
    second_partition.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
            }
        ]
    ).to_parquet(first_partition / "part-0.parquet", engine="pyarrow", index=False)
    (second_partition / "bad.parquet").write_text("not parquet", encoding="utf-8")

    result = query_table(
        "daily",
        root=root,
        filters={"ts_code": "000001.SZ"},
        fields=["ts_code", "trade_date", "close"],
        start_date="20240102",
        end_date="20240102",
    )

    assert result.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2},
    ]

    end_only = query_table(
        "daily",
        root=root,
        fields=["ts_code", "trade_date", "close"],
        start_date=None,
        end_date="20240102",
    )

    assert end_only.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20240102", "close": 10.2},
    ]


def test_query_partitioned_core_table_under_format_subdirectory(tmp_path):
    root = tmp_path / "data"
    partition_root = root / "core" / "table=adj_factor" / "parquet"
    first_partition = partition_root / "trade_date=20260617"
    second_partition = partition_root / "trade_date=20260618"
    first_partition.mkdir(parents=True)
    second_partition.mkdir(parents=True)
    pd.DataFrame(
        [{"ts_code": "000001.SZ", "adj_factor": 0.98}]
    ).to_parquet(first_partition / "part-0.parquet", engine="pyarrow", index=False)
    pd.DataFrame(
        [{"ts_code": "000001.SZ", "adj_factor": 1.0}]
    ).to_parquet(second_partition / "part-0.parquet", engine="pyarrow", index=False)

    saved = read_core_table("adj_factor", root=root)
    assert saved.sort_values("trade_date").to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20260617", "adj_factor": 0.98},
        {"ts_code": "000001.SZ", "trade_date": "20260618", "adj_factor": 1.0},
    ]

    result = query_table(
        "adj_factor",
        root=root,
        fields=["ts_code", "trade_date", "adj_factor"],
        filters={"ts_code": "000001.SZ"},
        start_date="20260618",
        end_date="20260618",
    )

    assert result.to_dict(orient="records") == [
        {"ts_code": "000001.SZ", "trade_date": "20260618", "adj_factor": 1.0},
    ]


def test_query_partitioned_core_table_returns_empty_for_missing_date_partition(tmp_path):
    root = tmp_path / "data"
    partition = root / "core" / "table=daily" / "trade_date=20240102"
    partition.mkdir(parents=True)
    pd.DataFrame(
        [{"ts_code": "000001.SZ", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2}]
    ).to_parquet(partition / "part-0.parquet", engine="pyarrow", index=False)

    result = query_table(
        "daily",
        root=root,
        fields=["ts_code", "trade_date", "close"],
        start_date="20240104",
        end_date="20240104",
    )

    assert list(result.columns) == ["ts_code", "trade_date", "close"]
    assert result.empty


def test_quality_detects_duplicate_primary_key():
    df = pd.DataFrame(
        [
            {"exchange": "SSE", "cal_date": "20240101", "is_open": 0},
            {"exchange": "SSE", "cal_date": "20240101", "is_open": 0},
        ]
    )

    issues = validate_table("trade_cal", df)

    assert any(issue.check == "primary_key_duplicates" for issue in issues)
