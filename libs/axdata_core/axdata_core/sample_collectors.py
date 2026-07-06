"""Small local collector runners used to exercise the independent path."""

from __future__ import annotations

from typing import Any


def sample_stock_snapshot(
    *,
    params: dict[str, Any] | None = None,
    fields: list[str] | None = None,
    collector: dict[str, Any] | None = None,
    data_root: Any = None,
    output_root: Any = None,
    output_dir: Any = None,
    formats: list[str] | None = None,
    progress_callback: Any = None,
) -> dict[str, Any]:
    """Return a deterministic local stock snapshot without source plugins."""

    del collector, data_root, output_root, output_dir, formats
    if progress_callback is not None:
        progress_callback(40, "生成本地样例数据")
    options = dict(params or {})
    instrument_id = str(options.get("instrument_id") or options.get("code") or "000001.SZ")
    trade_date = str(options.get("trade_date") or "20260701")
    record = {
        "instrument_id": instrument_id,
        "trade_date": trade_date,
        "name": "AxData Sample",
        "last_price": 12.34,
    }
    if fields is not None:
        selected = {field: record.get(field) for field in fields if field in record}
        record = selected
    return {
        "records": [record],
        "meta": {
            "data_date": trade_date,
            "source": "local_sample",
        },
    }
