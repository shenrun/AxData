from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from .config import data_root
from .models import QueryRequest
from .serialization import (
    normalize_date_text,
    normalize_filters,
    parse_fields,
    pop_date_params,
    response_payload,
)


router = APIRouter()


def query_core_table(
    table: str,
    *,
    fields: str | list[str] | tuple[str, ...] | None = None,
    filters: dict[str, Any] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = 1000,
) -> Any:
    """Read already-ingested AxData data through the core query engine."""

    try:
        from axdata_core import query_table
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="axdata_core is not available. Install the core package before querying data.",
        ) from exc

    try:
        df = query_table(
            table,
            root=data_root(),
            filters=filters,
            fields=parse_fields(fields),
            start_date=normalize_date_text(start_date),
            end_date=normalize_date_text(end_date),
            limit=limit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return df


@router.get("/v1/tables")
def list_tables() -> dict[str, Any]:
    from axdata_core import list_tables as core_list_tables

    return response_payload(list(core_list_tables()))


@router.get("/v1/tables/{table}")
def get_table(table: str) -> dict[str, Any]:
    from axdata_core import get_schema

    try:
        return response_payload(get_schema(table))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/v1/query")
def run_query(request: QueryRequest) -> dict[str, Any]:
    params = dict(request.params)
    params_start_date, params_end_date = pop_date_params(params)
    fields = request.fields if request.fields is not None else request.columns
    start_date = request.start_date or request.start or params_start_date
    end_date = request.end_date or request.end or params_end_date
    filters = normalize_filters(params, request.filters)
    data = query_core_table(
        request.table,
        fields=fields,
        filters=filters,
        start_date=start_date,
        end_date=end_date,
        limit=request.limit,
    )
    return response_payload(data, table=request.table, count=len(data))
