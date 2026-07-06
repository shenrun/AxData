from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from .config import data_root
from .serialization import response_payload


router = APIRouter()


@router.get("/v1/data/datasets")
def list_local_datasets() -> dict[str, Any]:
    from axdata_core import list_datasets

    datasets = [item.to_dict() for item in list_datasets(data_root=data_root())]
    return response_payload(
        datasets,
        count=len(datasets),
        empty_state=(
            "No local datasets found. Run a Collector/Downloader first."
            if not datasets
            else None
        ),
    )


@router.get("/v1/data/datasets/{dataset}")
def inspect_local_dataset(dataset: str) -> dict[str, Any]:
    from axdata_core import DataBrowserError, get_dataset

    try:
        summary = get_dataset(dataset, data_root=data_root())
    except DataBrowserError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return response_payload(summary.to_dict())


@router.get("/v1/data/datasets/{dataset}/preview")
def preview_local_dataset(
    dataset: str,
    fields: str | None = Query(default=None, description="Comma-separated selected fields."),
    symbol: str | None = Query(default=None, description="Symbol filter when the dataset has a symbol column."),
    start: str | None = Query(default=None, description="Start date, YYYYMMDD or YYYY-MM-DD."),
    end: str | None = Query(default=None, description="End date, YYYYMMDD or YYYY-MM-DD."),
    limit: int = Query(default=20, ge=1, description="Maximum rows, capped at 100."),
    filter: list[str] = Query(default_factory=list, description="Exact filter key=value; repeatable."),
) -> dict[str, Any]:
    from axdata_core import DataBrowserError, preview_dataset

    try:
        preview = preview_dataset(
            dataset,
            data_root=data_root(),
            fields=fields,
            filters=_parse_filter_query(filter),
            symbol=symbol,
            start=start,
            end=end,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DataBrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response_payload(
        preview.rows,
        dataset=preview.dataset.to_dict(),
        count=len(preview.rows),
        limit=preview.limit,
        filters=preview.filters,
        columns=preview.columns,
        preview_format=preview.preview_format,
        preview_paths=preview.preview_paths,
    )


@router.delete("/v1/data/datasets/{dataset}")
def delete_local_dataset(dataset: str) -> dict[str, Any]:
    from axdata_core import DataBrowserError, delete_dataset

    try:
        result = delete_dataset(dataset, data_root=data_root())
    except DataBrowserError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "was not found" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return response_payload(result)


def _parse_filter_query(values: list[str]) -> dict[str, Any]:
    from axdata_core import DataBrowserError

    filters: dict[str, Any] = {}
    for item in values:
        if not item:
            continue
        if item.lstrip().startswith("{"):
            try:
                payload = json.loads(item)
            except json.JSONDecodeError as exc:
                raise DataBrowserError("filter JSON must be a valid object.") from exc
            if not isinstance(payload, dict):
                raise DataBrowserError("filter JSON must be an object.")
            filters.update({str(key): value for key, value in payload.items()})
            continue
        if "=" not in item:
            raise DataBrowserError("filter must use key=value or a JSON object.")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise DataBrowserError("filter key cannot be empty.")
        filters[key] = value.strip()
    return filters
