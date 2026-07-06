"""Execution helpers for TDX F10 batch requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .tdx_f10_models import F10InterfaceSpec


@dataclass(frozen=True)
class F10DispatchResult:
    rows: list[dict[str, Any]]
    requested_code_count: int
    worker_count: int
    meta: dict[str, Any]


@dataclass(frozen=True)
class TopicRowsLookupResult:
    rows: dict[str, list[dict[str, Any]]]
    meta: dict[str, Any]


def __getattr__(name: str) -> Any:
    if name == "request_f10_interface":
        from .f10_request import request_f10_interface as value

        globals()[name] = value
        return value
    if name == "TdxTqlexClient":
        from .tqlex import TdxTqlexClient as value

        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _request_f10_interface(client: Any, spec: Any, params: Mapping[str, Any]) -> list[dict[str, Any]]:
    request_func = globals().get("request_f10_interface")
    if request_func is None:
        request_func = __getattr__("request_f10_interface")
    return request_func(client, spec, params)


def _create_default_tqlex_client() -> Any:
    client_class = globals().get("TdxTqlexClient")
    if client_class is None:
        client_class = __getattr__("TdxTqlexClient")
    return client_class()


def request_f10_dispatch_result(
    params: Mapping[str, Any],
    *,
    interface_name: str,
    spec: Any,
    requested_codes: Sequence[str],
    configured_worker_count: int,
    request_one: Callable[[Mapping[str, Any]], list[dict[str, Any]]],
) -> F10DispatchResult:
    result = request_f10_rows(
        params,
        requested_codes,
        configured_worker_count=configured_worker_count,
        request_one=request_one,
    )
    return F10DispatchResult(
        rows=result.rows,
        requested_code_count=result.requested_code_count,
        worker_count=result.worker_count,
        meta={
            "tdx_protocol_family": "7615",
            "tdx_requested_interface": interface_name,
            "tdx_returned_count": len(result.rows),
            "tdx_requested_code_count": result.requested_code_count,
            "tdx_f10_workers": result.worker_count,
            "tdx_f10_category": spec.category,
            "tdx_source_evaluation": spec.evaluation,
        },
    )


def stock_f10_request_result(
    interface_name: str,
    params: Mapping[str, Any],
    *,
    specs: Mapping[str, Any],
    existing_client: Any | None,
    create_client: Callable[[], Any],
    requested_codes: Callable[[Any], Sequence[str]],
    option_workers: Callable[[Mapping[str, Any], int], int],
    options: Mapping[str, Any],
    request_interface: Callable[[Any, Any, Mapping[str, Any]], list[dict[str, Any]]],
) -> F10DispatchResult:
    spec = specs[interface_name]
    client = existing_client if existing_client is not None and hasattr(existing_client, "request") else create_client()
    requested = requested_codes(params.get("code")) if any(param.name == "code" for param in spec.params) else []
    configured_worker_count = option_workers(options, max(1, len(requested))) if "f10_workers" in options else 1
    return request_f10_dispatch_result(
        params,
        interface_name=interface_name,
        spec=spec,
        requested_codes=requested,
        configured_worker_count=configured_worker_count,
        request_one=lambda per_code_params: request_interface(client, spec, per_code_params),
    )


def default_stock_f10_request_result(
    interface_name: str,
    params: Mapping[str, Any],
    *,
    specs: Mapping[str, Any],
    existing_client: Any | None,
    requested_codes: Callable[[Any], Sequence[str]],
    option_workers: Callable[[Mapping[str, Any], int], int],
    options: Mapping[str, Any],
) -> F10DispatchResult:
    return stock_f10_request_result(
        interface_name,
        params,
        specs=specs,
        existing_client=existing_client,
        create_client=_create_default_tqlex_client,
        requested_codes=requested_codes,
        option_workers=option_workers,
        options=options,
        request_interface=_request_f10_interface,
    )


def request_f10_many_with_default_interface(
    client: Any,
    spec: F10InterfaceSpec,
    params: Mapping[str, Any],
    requested_codes: Sequence[str],
    *,
    worker_count: int,
) -> list[dict[str, Any]]:
    return request_f10_many_by_code(
        params,
        requested_codes,
        worker_count=worker_count,
        request_one=lambda per_code_params: _request_f10_interface(client, spec, per_code_params),
    )


def request_f10_rows(
    params: Mapping[str, Any],
    requested_codes: Sequence[str],
    *,
    configured_worker_count: int,
    request_one: Callable[[Mapping[str, Any]], list[dict[str, Any]]],
) -> F10DispatchResult:
    if len(requested_codes) > 1:
        rows = request_f10_many_by_code(
            params,
            requested_codes,
            worker_count=configured_worker_count,
            request_one=request_one,
        )
        return F10DispatchResult(
            rows=rows,
            requested_code_count=len(requested_codes),
            worker_count=min(configured_worker_count, len(requested_codes)),
            meta={},
        )

    rows = request_one(params)
    return F10DispatchResult(
        rows=rows,
        requested_code_count=len(requested_codes) or 1,
        worker_count=1,
        meta={},
    )


def request_f10_many_by_code(
    params: Mapping[str, Any],
    requested_codes: Sequence[str],
    *,
    worker_count: int,
    request_one: Callable[[Mapping[str, Any]], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    indexed_codes = list(enumerate(requested_codes))
    if worker_count <= 1:
        rows: list[dict[str, Any]] = []
        for _index, code in indexed_codes:
            per_code_params = dict(params)
            per_code_params["code"] = code
            rows.extend(request_one(per_code_params))
        return rows

    def request_indexed(index: int, code: str) -> tuple[int, list[dict[str, Any]]]:
        per_code_params = dict(params)
        per_code_params["code"] = code
        return index, request_one(per_code_params)

    rows_by_index: dict[int, list[dict[str, Any]]] = {}
    resolved_worker_count = max(1, min(worker_count, len(indexed_codes)))
    with ThreadPoolExecutor(
        max_workers=resolved_worker_count,
        thread_name_prefix="axdata-tdx-f10",
    ) as executor:
        futures = [executor.submit(request_indexed, index, code) for index, code in indexed_codes]
        for future in as_completed(futures):
            index, code_rows = future.result()
            rows_by_index[index] = code_rows
    rows = []
    for index, _code in indexed_codes:
        rows.extend(rows_by_index.get(index, []))
    return rows


def request_topic_rows_with_refill(
    instrument_ids: Sequence[str],
    *,
    request_one: Callable[[str], list[dict[str, Any]]],
    topic_worker_count: int,
    refill_rounds: int,
    refill_worker_count: int,
    progress_callback: Callable[..., None] | None = None,
    progress_start: int | None = None,
    progress_span: int | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    topic_rows: dict[str, list[dict[str, Any]]] = {}
    unique_instrument_ids = [
        instrument_id
        for instrument_id in dict.fromkeys(str(value or "") for value in instrument_ids)
        if instrument_id
    ]
    total = len(unique_instrument_ids)
    progress_started_at = monotonic()

    def mark_done(instrument_id: str, rows: list[dict[str, Any]], completed: int) -> None:
        topic_rows[instrument_id] = rows
        if progress_start is not None and progress_span is not None:
            _emit_topic_progress(
                progress_callback,
                completed=completed,
                total=total,
                started_at=progress_started_at,
                percent_start=progress_start,
                percent_span=progress_span,
            )

    def fetch_many(
        requested_instrument_ids: Sequence[str],
        *,
        worker_count: int,
        completed_offset: int,
    ) -> int:
        requested = list(requested_instrument_ids)
        if not requested:
            return completed_offset
        completed = completed_offset
        resolved_worker_count = max(1, min(worker_count, len(requested)))
        if resolved_worker_count <= 1:
            for instrument_id in requested:
                rows = request_one(instrument_id)
                completed += 1
                mark_done(instrument_id, rows, completed)
            return completed
        with ThreadPoolExecutor(
            max_workers=resolved_worker_count,
            thread_name_prefix="axdata-tdx-topic",
        ) as executor:
            futures = {executor.submit(request_one, instrument_id): instrument_id for instrument_id in requested}
            for future in as_completed(futures):
                instrument_id = futures[future]
                rows = future.result()
                completed += 1
                mark_done(instrument_id, rows, completed)
        return completed

    completed = fetch_many(
        unique_instrument_ids,
        worker_count=topic_worker_count,
        completed_offset=0,
    )
    refill_requested_count = 0
    refill_round_count = 0
    for _round in range(refill_rounds):
        missing_instrument_ids = [
            instrument_id
            for instrument_id in unique_instrument_ids
            if not topic_rows.get(instrument_id)
        ]
        if not missing_instrument_ids:
            break
        refill_round_count += 1
        refill_requested_count += len(missing_instrument_ids)
        completed = fetch_many(
            missing_instrument_ids,
            worker_count=refill_worker_count,
            completed_offset=completed,
        )

    meta = {
        "tdx_f10_topic_workers": topic_worker_count,
        "tdx_f10_topic_refill_workers": max(1, min(refill_worker_count, int(total or 1))),
        "tdx_f10_topic_refill_rounds": refill_round_count,
        "tdx_f10_topic_refill_configured_rounds": refill_rounds,
        "tdx_f10_topic_refill_requested_count": refill_requested_count,
        "tdx_f10_topic_missing_stock_count": sum(
            1 for instrument_id in unique_instrument_ids if not topic_rows.get(instrument_id)
        ),
    }
    return topic_rows, meta


def request_topic_rows_by_instrument_id(
    instrument_ids: Sequence[str],
    *,
    topic_type: str,
    request_f10: Callable[[str, Mapping[str, Any]], list[dict[str, Any]]],
    topic_worker_count: int,
    refill_rounds: int,
    refill_worker_count: int,
    request_error: type[BaseException],
    progress_callback: Callable[..., None] | None = None,
    progress_start: int | None = None,
    progress_span: int | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    unique_instrument_ids = [
        instrument_id
        for instrument_id in dict.fromkeys(str(value or "") for value in instrument_ids)
        if instrument_id
    ]

    def request_one(instrument_id: str) -> list[dict[str, Any]]:
        try:
            return request_f10(
                "stock_topic_exposure_tdx",
                {"code": instrument_id, "topic_type": topic_type},
            )
        except request_error:
            return []

    return request_topic_rows_with_refill(
        unique_instrument_ids,
        request_one=request_one,
        topic_worker_count=topic_worker_count,
        refill_rounds=refill_rounds,
        refill_worker_count=refill_worker_count,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )


def request_topic_rows_lookup_result(
    instrument_ids: Sequence[str],
    *,
    topic_type: str,
    request_f10: Callable[[str, Mapping[str, Any]], list[dict[str, Any]]],
    topic_worker_count: Callable[[int], int],
    refill_rounds: int,
    refill_worker_count: int,
    request_error: type[BaseException],
    progress_callback: Callable[..., None] | None = None,
    progress_start: int | None = None,
    progress_span: int | None = None,
) -> TopicRowsLookupResult:
    total = len([value for value in dict.fromkeys(str(value or "") for value in instrument_ids) if value])
    rows, meta = request_topic_rows_by_instrument_id(
        instrument_ids,
        topic_type=topic_type,
        request_f10=request_f10,
        topic_worker_count=topic_worker_count(total),
        refill_rounds=refill_rounds,
        refill_worker_count=refill_worker_count,
        request_error=request_error,
        progress_callback=progress_callback,
        progress_start=progress_start,
        progress_span=progress_span,
    )
    return TopicRowsLookupResult(rows=rows, meta=meta)


def _emit_topic_progress(
    progress_callback: Callable[..., None] | None,
    *,
    completed: int,
    total: int,
    started_at: float,
    percent_start: int,
    percent_span: int,
) -> None:
    if progress_callback is None or total <= 0:
        return
    safe_completed = min(total, max(0, completed))
    fraction = min(1.0, max(0.0, safe_completed / total))
    percent = percent_start + int(fraction * percent_span)
    elapsed_ms = max(0.0, (monotonic() - started_at) * 1000)
    eta_ms = None
    if safe_completed > 0 and safe_completed < total:
        eta_ms = int((elapsed_ms / safe_completed) * (total - safe_completed))
    try:
        progress_callback(
            percent,
            f"查询题材 {safe_completed}/{total} 只",
            progress_current=safe_completed,
            progress_total=total,
            progress_unit="只",
            eta_ms=eta_ms,
        )
    except TypeError:
        progress_callback(percent, f"查询题材 {safe_completed}/{total} 只")
