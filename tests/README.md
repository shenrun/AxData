# AxData Tests

These tests are the first integration contract for AxData:

- Schema metadata must exist for the first four tables.
- Core Parquet storage must round-trip with DuckDB queries.
- The SDK must translate API responses into pandas DataFrames.
- The FastAPI app must expose the local query and metadata routes.

Run them from the repository root:

```bash
pytest
```

