# axdata_core

`axdata_core` provides the shared Python primitives for AxData datasets:

- Table schemas and field metadata for `stock_basic_exchange`, `trade_cal`, `daily`, and `adj_factor`.
- A fixed data directory layout: `raw/`, `staging/`, `core/`, and `factor/`.
- Parquet helpers for reading and writing core tables.
- DuckDB helpers for filtered table queries returning `pandas.DataFrame`.
- Basic quality checks for duplicate primary keys and missing required fields.

Parquet files are the durable source of truth. DuckDB is the query engine and
can be rebuilt from Parquet plus metadata/manifest files.

## Quick Example

```python
from axdata_core import AxDataPaths, query_table, read_core_table, validate_table

paths = AxDataPaths("/data/axdata")
df = query_table(
    "daily",
    root=paths.root,
    fields=["ts_code", "trade_date", "close"],
    start_date="20240101",
    end_date="20241231",
)

issues = validate_table("daily", df)
```

Install `pyarrow` to use Parquet helpers:

```bash
pip install axdata-core[parquet]
```
