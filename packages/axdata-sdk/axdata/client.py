"""Python client for AxData local and remote data access."""

from __future__ import annotations

import os
import json
import time
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse
from uuid import uuid4

import requests


DEFAULT_API_BASE = "http://127.0.0.1:8666"
BackendMode = str
DEFAULT_LIMIT = 1000
LOCAL_STREAM_NAME = "stock_quote_refresh_tdx"
LOCAL_STREAM_DEFAULT_INTERVAL_MS = 3000
LOCAL_STREAM_MIN_INTERVAL_MS = 500
LOCAL_STREAM_MAX_CODES = 100


class AxDataError(RuntimeError):
    """Raised when AxData returns an invalid or failed response."""


class AxDataClient:
    """User-facing AxData client.

    The default backend is local: it reads the current machine's AxData data
    directory through axdata_core and does not require an API service. Pass
    api_base, set AXDATA_API_BASE, or use mode="api" to read a LAN/server AxData
    service through HTTP.
    """

    def __init__(
        self,
        token: str | None = None,
        api_base: str | None = None,
        data_root: str | Path | None = None,
        data_dir: str | Path | None = None,
        data_home: str | Path | None = None,
        mode: BackendMode = "auto",
        backend: BackendMode | None = None,
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> None:
        if backend is not None and mode != "auto":
            raise ValueError("Use either mode or backend, not both.")
        if backend is None and mode == "auto" and api_base is None:
            backend = os.getenv("AXDATA_BACKEND")
        if backend is not None:
            mode = backend
        if mode not in {"auto", "local", "api"}:
            raise ValueError("backend/mode must be one of: auto, local, api")

        self.token = token if token is not None else os.getenv("AXDATA_TOKEN")
        env_api_base = os.getenv("AXDATA_API_BASE")
        resolved_api_base = api_base or env_api_base
        if mode == "api" and not resolved_api_base:
            resolved_api_base = DEFAULT_API_BASE

        if mode == "auto":
            self.mode = "api" if resolved_api_base else "local"
        else:
            self.mode = mode
        self.backend = self.mode

        self.api_base = resolved_api_base.rstrip("/") if resolved_api_base else None
        self.data_root = self._resolve_data_root(
            data_root=data_root,
            data_dir=data_dir,
            data_home=data_home,
        )
        self._http_session = session or requests.Session()
        self.timeout = timeout

    @classmethod
    def local(
        cls,
        *,
        data_root: str | Path | None = None,
        data_dir: str | Path | None = None,
        data_home: str | Path | None = None,
    ) -> "AxDataClient":
        """Create a client that reads the current machine's AxData data directory."""

        return cls(mode="local", data_root=data_root, data_dir=data_dir, data_home=data_home)

    @classmethod
    def api(
        cls,
        api_base: str = DEFAULT_API_BASE,
        *,
        token: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> "AxDataClient":
        """Create a client that reads a local/LAN/server AxData API service."""

        return cls(
            token=token,
            api_base=api_base,
            mode="api",
            session=session,
            timeout=timeout,
        )

    def query(
        self,
        api_name: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        """Query an AxData table and return records as a pandas.DataFrame."""

        if not api_name:
            raise ValueError("api_name is required")

        if self.mode == "local":
            return self._query_local(api_name, fields=fields, **params)
        return self._query_api(api_name, fields=fields, **params)

    def call(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        options: Mapping[str, Any] | None = None,
        **params: Any,
    ):
        """Call a provider-style source interface and return a pandas.DataFrame."""

        if not interface:
            raise ValueError("interface is required")

        if self.mode == "local":
            return self._call_local(interface, fields=fields, options=options, **params)
        return self._call_api(interface, fields=fields, options=options, **params)

    def download(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        output_root: str | Path | None = None,
        output_dir: str | Path | None = None,
        formats: str | list[str] | tuple[str, ...] | None = None,
        collect_mode: str | None = None,
        connection_mode: str | None = None,
        connection_count: int | None = None,
        source_server_count: int | None = None,
        connections_per_server: int | None = None,
        max_concurrent_tasks: int | None = None,
        batch_size: int | None = None,
        request_interval_ms: int | None = None,
        retry_count: int | None = None,
        timeout_ms: int | None = None,
        **params: Any,
    ) -> SimpleNamespace:
        """Run a configured downloader and return job metadata."""

        if not interface:
            raise ValueError("interface is required")

        if self.mode == "local":
            return self._download_local(
                interface,
                fields=fields,
                output_root=output_root,
                output_dir=output_dir,
                formats=formats,
                collect_mode=collect_mode,
                connection_mode=connection_mode,
                connection_count=connection_count,
                source_server_count=source_server_count,
                connections_per_server=connections_per_server,
                max_concurrent_tasks=max_concurrent_tasks,
                batch_size=batch_size,
                request_interval_ms=request_interval_ms,
                retry_count=retry_count,
                timeout_ms=timeout_ms,
                **params,
            )
        return self._download_api(
            interface,
            fields=fields,
            output_root=output_root,
            output_dir=output_dir,
            formats=formats,
            collect_mode=collect_mode,
            connection_mode=connection_mode,
            connection_count=connection_count,
            source_server_count=source_server_count,
            connections_per_server=connections_per_server,
            max_concurrent_tasks=max_concurrent_tasks,
            batch_size=batch_size,
            request_interval_ms=request_interval_ms,
            retry_count=retry_count,
            timeout_ms=timeout_ms,
            **params,
        )

    def stream(
        self,
        stream: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ) -> "AxDataStream | LocalAxDataStream":
        """Open an AxData realtime stream.

        Local clients run supported streams in-process without requiring the
        AxData API service. API clients keep using the `/v1/stream/{stream}`
        WebSocket route.
        """

        if not stream:
            raise ValueError("stream is required")
        stream_params = {
            str(key): self._normalize_param_value(value)
            for key, value in params.items()
            if value is not None
        }
        selected_fields = self._normalize_fields(fields) if fields is not None else None
        if selected_fields is not None:
            stream_params["fields"] = selected_fields
        if self.mode == "local":
            return LocalAxDataStream(
                stream=stream,
                params=stream_params,
                data_root=self.data_root,
                timeout=self.timeout,
            )
        return AxDataStream(
            api_base=self.api_base or DEFAULT_API_BASE,
            stream=stream,
            params=stream_params,
            token=self.token,
            timeout=self.timeout,
        )

    def session(
        self,
        source: str,
        options: Mapping[str, Any] | None = None,
        **source_options: Any,
    ) -> "AxDataLocalSession":
        """Open a local high-frequency source session for TDX/TDX_EXT."""

        if not source:
            raise ValueError("source is required")
        if self.mode != "local":
            raise AxDataError(
                "client.session(...) is local-only. Create AxDataClient() without api_base "
                "to reuse local TDX/TDX_EXT connections; API clients should use call(...) or stream(...)."
            )
        resolved_options = self._normalize_options(options or {})
        resolved_options.update(
            {
                str(key): self._normalize_param_value(value)
                for key, value in source_options.items()
                if value is not None
            }
        )
        return AxDataLocalSession(
            client=self,
            source=source,
            options=resolved_options,
        )

    def stock_quote_refresh_tdx(
        self,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ) -> "AxDataStream":
        """Subscribe to TDX stock quote refresh events."""

        return self.stream("stock_quote_refresh_tdx", fields=fields, **params)

    def request_interface(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        options: Mapping[str, Any] | None = None,
        **params: Any,
    ):
        """Compatibility helper for :meth:`call`."""

        return self.call(interface, fields=fields, options=options, **params)

    def _query_api(
        self,
        api_name: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        if not self.api_base:
            raise AxDataError("api_base is required for API mode")

        query_parts = self._split_query_params(params)
        payload: dict[str, Any] = {
            "table": api_name,
            "params": query_parts["params"],
        }
        if fields is not None:
            payload["fields"] = self._normalize_fields(fields)
        if query_parts["filters"]:
            payload["filters"] = query_parts["filters"]
        if query_parts["start_date"] is not None:
            payload["start_date"] = query_parts["start_date"]
        if query_parts["end_date"] is not None:
            payload["end_date"] = query_parts["end_date"]
        if query_parts["limit"] is not None:
            payload["limit"] = query_parts["limit"]

        response = self._http_session.post(
            f"{self.api_base}/v1/query",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        self._raise_for_status(response)
        data = response.json()
        records = self._extract_records(data)
        return self._to_dataframe(records)

    def _call_api(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        options: Mapping[str, Any] | None = None,
        **params: Any,
    ):
        if not self.api_base:
            raise AxDataError("api_base is required for API mode")

        payload: dict[str, Any] = {
            "params": {
                str(key): self._normalize_param_value(value)
                for key, value in params.items()
                if value is not None
            },
        }
        if fields is not None:
            payload["fields"] = self._normalize_fields(fields)
        if options:
            payload["options"] = self._normalize_options(options)

        response = self._http_session.post(
            f"{self.api_base}/v1/request/{interface}",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        self._raise_for_status(response)
        data = response.json()
        records = self._extract_records(data)
        return self._to_dataframe(records)

    def _download_api(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        output_root: str | Path | None = None,
        output_dir: str | Path | None = None,
        formats: str | list[str] | tuple[str, ...] | None = None,
        collect_mode: str | None = None,
        connection_mode: str | None = None,
        connection_count: int | None = None,
        source_server_count: int | None = None,
        connections_per_server: int | None = None,
        max_concurrent_tasks: int | None = None,
        batch_size: int | None = None,
        request_interval_ms: int | None = None,
        retry_count: int | None = None,
        timeout_ms: int | None = None,
        **params: Any,
    ) -> SimpleNamespace:
        if not self.api_base:
            raise AxDataError("api_base is required for API mode")

        payload: dict[str, Any] = {
            "params": {
                str(key): self._normalize_param_value(value)
                for key, value in params.items()
                if value is not None
            },
        }
        if fields is not None:
            payload["fields"] = self._normalize_fields(fields)
        if output_root is not None:
            payload["output_root"] = str(output_root)
        if output_dir is not None:
            payload["output_dir"] = str(output_dir)
        if formats is not None:
            payload["formats"] = self._normalize_fields(formats)
        if collect_mode is not None:
            payload["collect_mode"] = collect_mode
        if connection_mode is not None:
            payload["connection_mode"] = connection_mode
        if connection_count is not None:
            payload["connection_count"] = int(connection_count)
        if source_server_count is not None:
            payload["source_server_count"] = int(source_server_count)
        if connections_per_server is not None:
            payload["connections_per_server"] = int(connections_per_server)
        if max_concurrent_tasks is not None:
            payload["max_concurrent_tasks"] = int(max_concurrent_tasks)
        if batch_size is not None:
            payload["batch_size"] = int(batch_size)
        if request_interval_ms is not None:
            payload["request_interval_ms"] = int(request_interval_ms)
        if retry_count is not None:
            payload["retry_count"] = int(retry_count)
        if timeout_ms is not None:
            payload["timeout_ms"] = int(timeout_ms)

        response = self._http_session.post(
            f"{self.api_base}/v1/download/{interface}",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        self._raise_for_status(response)
        data = response.json()
        result = self._extract_data_object(data)
        return SimpleNamespace(**result)

    def _query_local(
        self,
        table: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        try:
            from axdata_core import query_table
        except ImportError as exc:
            raise ImportError(
                "AxData local mode requires axdata_core and DuckDB. Install the workspace "
                "or use `pip install axdata[local]`."
            ) from exc

        query_parts = self._split_query_params(params)
        filters = dict(query_parts["filters"])
        filters.update(query_parts["params"])
        selected_fields = self._normalize_fields(fields) if fields is not None else None
        return query_table(
            table,
            root=self.data_root,
            filters=filters,
            fields=selected_fields,
            start_date=query_parts["start_date"],
            end_date=query_parts["end_date"],
            limit=query_parts["limit"],
        )

    def _call_local(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        options: Mapping[str, Any] | None = None,
        **params: Any,
    ):
        try:
            from axdata_core import request_interface
        except ImportError as exc:
            raise ImportError(
                "AxData local source requests require axdata_core. Install the workspace "
                "or use API mode with api_base."
            ) from exc

        request_params = {
            str(key): self._normalize_param_value(value)
            for key, value in params.items()
            if value is not None
        }
        selected_fields = self._normalize_fields(fields) if fields is not None else None
        request_kwargs = {
            "params": request_params,
            "fields": selected_fields,
            "persist": False,
            "data_root": self.data_root,
        }
        if options:
            request_kwargs["options"] = self._normalize_options(options)
        result = request_interface(interface, **request_kwargs)
        return self._to_dataframe(result.records)

    def _download_local(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        output_root: str | Path | None = None,
        output_dir: str | Path | None = None,
        formats: str | list[str] | tuple[str, ...] | None = None,
        collect_mode: str | None = None,
        connection_mode: str | None = None,
        connection_count: int | None = None,
        source_server_count: int | None = None,
        connections_per_server: int | None = None,
        max_concurrent_tasks: int | None = None,
        batch_size: int | None = None,
        request_interval_ms: int | None = None,
        retry_count: int | None = None,
        timeout_ms: int | None = None,
        **params: Any,
    ) -> SimpleNamespace:
        try:
            from axdata_core import run_downloader
        except ImportError as exc:
            raise ImportError(
                "AxData local downloads require axdata_core. Install the workspace "
                "or use API mode with api_base."
            ) from exc

        request_params = {
            str(key): self._normalize_param_value(value)
            for key, value in params.items()
            if value is not None
        }
        selected_fields = self._normalize_fields(fields) if fields is not None else None
        result = run_downloader(
            interface,
            params=request_params,
            fields=selected_fields,
            data_root=self.data_root,
            output_root=output_root,
            output_dir=output_dir,
            formats=self._normalize_fields(formats) if formats is not None else None,
            collect_mode=collect_mode,
            connection_mode=connection_mode,
            connection_count=connection_count,
            source_server_count=source_server_count,
            connections_per_server=connections_per_server,
            max_concurrent_tasks=max_concurrent_tasks,
            batch_size=batch_size,
            request_interval_ms=request_interval_ms,
            retry_count=retry_count,
            timeout_ms=timeout_ms,
        )
        return SimpleNamespace(**result)

    def daily(
        self,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        """Query daily market data."""

        return self.query("daily", fields=fields, **params)

    def adj_factor(
        self,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        """Query daily adjustment factors."""

        return self.query("adj_factor", fields=fields, **params)

    def trade_cal(
        self,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        """Query the trading calendar."""

        return self.query("trade_cal", fields=fields, **params)

    def stock_basic(
        self,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        """Query stock basic information.

        Compatibility alias for :meth:`stock_basic_exchange`.
        """

        return self.stock_basic_exchange(fields=fields, **params)

    def stock_basic_exchange(
        self,
        fields: str | list[str] | tuple[str, ...] | None = None,
        **params: Any,
    ):
        """Query stock list using the official exchange interface口径."""

        return self.query("stock_basic_exchange", fields=fields, **params)

    @staticmethod
    def _resolve_data_root(
        *,
        data_root: str | Path | None = None,
        data_dir: str | Path | None = None,
        data_home: str | Path | None = None,
    ) -> Path:
        if data_root is not None and data_dir is not None:
            raise ValueError("Use either data_root or data_dir, not both.")
        if data_root is not None:
            return Path(data_root).expanduser().resolve()
        if data_dir is not None:
            return Path(data_dir).expanduser().resolve()

        env_data_root = os.getenv("AXDATA_DATA_DIR")
        if env_data_root:
            return Path(env_data_root).expanduser().resolve()

        resolved_data_home = data_home or os.getenv("AXDATA_DATA_HOME")
        if resolved_data_home:
            return (Path(resolved_data_home).expanduser().resolve() / "data")

        return (Path.cwd() / "data").resolve()

    @staticmethod
    def _normalize_date_text(value: Any) -> Any:
        if isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-":
            return value.replace("-", "")
        return value

    @classmethod
    def _split_query_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        query_params = dict(params)
        explicit_filters = query_params.pop("filters", None)
        start_date = cls._normalize_date_text(
            query_params.pop("start_date", None) or query_params.pop("start", None)
        )
        end_date = cls._normalize_date_text(
            query_params.pop("end_date", None) or query_params.pop("end", None)
        )
        limit = cls._normalize_limit(query_params.pop("limit", DEFAULT_LIMIT))
        filters = {
            str(key): cls._normalize_param_value(value)
            for key, value in dict(explicit_filters or {}).items()
            if value is not None
        }
        params = {
            str(key): cls._normalize_param_value(value)
            for key, value in query_params.items()
            if value is not None
        }
        return {
            "params": params,
            "filters": filters,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        }

    @classmethod
    def _normalize_param_value(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls._normalize_date_text(value)
        if isinstance(value, tuple):
            return tuple(cls._normalize_param_value(item) for item in value)
        if isinstance(value, list):
            return [cls._normalize_param_value(item) for item in value]
        if isinstance(value, set):
            return [cls._normalize_param_value(item) for item in value]
        if isinstance(value, frozenset):
            return [cls._normalize_param_value(item) for item in value]
        return value

    @classmethod
    def _normalize_options(cls, options: Mapping[str, Any]) -> dict[str, Any]:
        return {
            str(key): cls._normalize_param_value(value)
            for key, value in dict(options or {}).items()
            if value is not None
        }

    @staticmethod
    def _normalize_limit(value: Any) -> int | None:
        if value is None:
            return None
        return int(value)

    def _headers(self) -> dict[str, str] | None:
        if not self.token:
            return None
        return {"Authorization": f"Bearer {self.token}"}

    @staticmethod
    def _raise_for_status(response: Any) -> None:
        status_code = getattr(response, "status_code", 200)
        if status_code is not None and int(status_code) >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = None
            if isinstance(payload, Mapping):
                error = payload.get("error")
                if isinstance(error, Mapping) and error.get("message"):
                    raise AxDataError(str(error["message"]))
                if payload.get("message") or payload.get("msg"):
                    raise AxDataError(str(payload.get("message") or payload.get("msg")))
        response.raise_for_status()

    @staticmethod
    def _normalize_fields(fields: str | list[str] | tuple[str, ...]) -> list[str]:
        if isinstance(fields, str):
            return [field.strip() for field in fields.split(",") if field.strip()]
        return [str(field).strip() for field in fields if str(field).strip()]

    @staticmethod
    def _extract_records(data: Any) -> list[Mapping[str, Any]]:
        if not isinstance(data, Mapping):
            raise AxDataError("AxData response must be a JSON object")

        if data.get("success") is False:
            error = data.get("error")
            if isinstance(error, Mapping):
                message = error.get("message") or error.get("code")
            else:
                message = data.get("message") or data.get("msg")
            message = message or "AxData query failed"
            raise AxDataError(str(message))

        if isinstance(data.get("data"), list):
            records = data["data"]
        elif "records" in data:
            records = data["records"]
        elif isinstance(data.get("data"), Mapping) and "records" in data["data"]:
            records = data["data"]["records"]
        else:
            raise AxDataError("AxData response is missing a data record list")

        if records is None:
            return []
        if not isinstance(records, list):
            raise AxDataError("AxData response 'records' must be a list")

        return records

    @staticmethod
    def _extract_data_object(data: Any) -> dict[str, Any]:
        if not isinstance(data, Mapping):
            raise AxDataError("AxData response must be a JSON object")

        if data.get("success") is False:
            error = data.get("error")
            if isinstance(error, Mapping):
                message = error.get("message") or error.get("code")
            else:
                message = data.get("message") or data.get("msg")
            raise AxDataError(str(message or "AxData request failed"))

        payload = data.get("data")
        if not isinstance(payload, Mapping):
            raise AxDataError("AxData response is missing a data object")
        return dict(payload)

    @staticmethod
    def _to_dataframe(records: list[Mapping[str, Any]]):
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "AxData SDK requires pandas to convert API records to a DataFrame. "
                "Install it with `pip install pandas` or `pip install axdata[pandas]`."
            ) from exc

        return pd.DataFrame.from_records(records)


class AxDataStream:
    """Synchronous iterator wrapper for AxData WebSocket streams."""

    def __init__(
        self,
        *,
        api_base: str,
        stream: str,
        params: Mapping[str, Any],
        token: str | None,
        timeout: float,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.stream = stream
        self.params = dict(params)
        self.token = token
        self.timeout = timeout
        self._ws = None

    def __enter__(self) -> "AxDataStream":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __iter__(self) -> Iterator[SimpleNamespace]:
        return self

    def __next__(self) -> SimpleNamespace:
        if self._ws is None:
            self.open()
        assert self._ws is not None
        raw = self._ws.recv()
        if raw in (None, ""):
            raise StopIteration
        payload = json.loads(raw)
        if isinstance(payload, Mapping) and payload.get("type") == "error":
            error = payload.get("error")
            if isinstance(error, Mapping) and error.get("message"):
                raise AxDataError(str(error["message"]))
        return SimpleNamespace(**payload)

    @property
    def url(self) -> str:
        parsed = urlparse(self.api_base)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        query = parsed.query
        if self.token:
            token_query = urlencode({"token": self.token})
            query = f"{query}&{token_query}" if query else token_query
        return urlunparse((scheme, parsed.netloc, f"/v1/stream/{self.stream}", "", query, ""))

    def open(self) -> None:
        if self._ws is not None:
            return
        try:
            import websocket
        except ImportError as exc:
            raise ImportError(
                "AxData realtime streams require websocket-client. Install axdata with "
                "`pip install axdata` from this workspace or install `websocket-client`."
            ) from exc

        headers = []
        if self.token:
            headers.append(f"Authorization: Bearer {self.token}")
        self._ws = websocket.create_connection(
            self.url,
            timeout=self.timeout,
            header=headers or None,
        )
        self._ws.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "stream": self.stream,
                    "params": self.params,
                }
            )
        )

    def close(self) -> None:
        if self._ws is None:
            return
        try:
            self._ws.close()
        finally:
            self._ws = None


class AxDataLocalSession:
    """SDK wrapper around an in-process local source session."""

    def __init__(
        self,
        *,
        client: AxDataClient,
        source: str,
        options: Mapping[str, Any],
    ) -> None:
        self._client = client
        self.source = source
        self.options = dict(options)
        self._session = None

    def __enter__(self) -> "AxDataLocalSession":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        if self._session is not None:
            return
        try:
            from axdata_core import create_source_session
        except ImportError as exc:
            raise ImportError(
                "AxData local source sessions require axdata_core. Install the workspace "
                "or use API mode with api_base."
            ) from exc
        try:
            session = create_source_session(
                source=self.source,
                data_root=self._client.data_root,
                options=self.options,
            )
            session.open()
        except Exception as exc:
            raise AxDataError(f"Failed to open local source session for {self.source!r}: {exc}") from exc
        self._session = session

    def close(self) -> None:
        if self._session is None:
            return
        try:
            self._session.close()
        finally:
            self._session = None

    def call(
        self,
        interface: str,
        fields: str | list[str] | tuple[str, ...] | None = None,
        options: Mapping[str, Any] | None = None,
        **params: Any,
    ):
        """Call a source request interface through the session-owned adapter."""

        if not interface:
            raise ValueError("interface is required")
        if self._session is None:
            self.open()
        assert self._session is not None
        request_params = {
            str(key): self._client._normalize_param_value(value)
            for key, value in params.items()
            if value is not None
        }
        selected_fields = self._client._normalize_fields(fields) if fields is not None else None
        request_options = self._client._normalize_options(options) if options else None
        try:
            result = self._session.call(
                interface,
                params=request_params,
                fields=selected_fields,
                options=request_options,
            )
        except AxDataError:
            raise
        except Exception as exc:
            raise AxDataError(f"Local source session call {interface!r} failed: {exc}") from exc
        return self._client._to_dataframe(result.records)


class LocalAxDataStream:
    """Synchronous iterator for local in-process TDX streams."""

    def __init__(
        self,
        *,
        stream: str,
        params: Mapping[str, Any],
        data_root: Path,
        timeout: float,
    ) -> None:
        self.stream = stream
        self.params = dict(params)
        self.data_root = data_root
        self.timeout = timeout
        self._source_session = None
        self._subscription_id: str | None = None
        self._code: list[str] = []
        self._fields: list[str] | None = None
        self._interval_ms = LOCAL_STREAM_DEFAULT_INTERVAL_MS
        self._initial_snapshot = True
        self._pending: list[SimpleNamespace] = []
        self._next_step = "closed"
        self._refresh_cursors: dict[str, int] = {}

    def __enter__(self) -> "LocalAxDataStream":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __iter__(self) -> Iterator[SimpleNamespace]:
        return self

    def __next__(self) -> SimpleNamespace:
        if self._source_session is None:
            self.open()
        if self._pending:
            return self._pending.pop(0)
        if self._next_step == "snapshot":
            self._next_step = "update"
            return self._snapshot_event()
        if self._next_step == "update":
            time.sleep(self._interval_ms / 1000.0)
            return self._update_event()
        raise StopIteration

    def open(self) -> None:
        if self._source_session is not None:
            return
        if self.stream != LOCAL_STREAM_NAME:
            raise AxDataError(
                f"Local streams currently support only {LOCAL_STREAM_NAME!r}; got {self.stream!r}. "
                "Pass api_base to AxDataClient for remote WebSocket streams."
            )
        code = _normalize_stream_codes(self.params.get("code"))
        if not code:
            raise AxDataError("code must include at least one security code for local TDX stream.")
        if len(code) > LOCAL_STREAM_MAX_CODES:
            raise AxDataError(f"Local TDX stream supports at most {LOCAL_STREAM_MAX_CODES} codes per subscription.")
        fields = self.params.get("fields")
        selected_fields = AxDataClient._normalize_fields(fields) if fields is not None else None
        interval_ms = _normalize_stream_interval_ms(self.params.get("interval_ms"))
        initial_snapshot = _normalize_stream_bool(
            self.params.get("initial_snapshot", self.params.get("snapshot")),
            True,
        )
        try:
            from axdata_core import create_source_session
        except ImportError as exc:
            raise ImportError(
                "AxData local streams require axdata_core and the TDX source plugin. "
                "Install the workspace or create AxDataClient(api_base=...) for remote streams."
            ) from exc

        session_options = _local_stream_session_options(self.params)
        try:
            source_session = create_source_session(
                source="tdx",
                data_root=self.data_root,
                options=session_options,
            )
            source_session.open()
        except Exception as exc:
            raise AxDataError(f"Failed to open local TDX stream session: {exc}") from exc

        self._source_session = source_session
        self._subscription_id = f"sub_{uuid4().hex[:12]}"
        self._code = code
        self._fields = selected_fields
        self._interval_ms = interval_ms
        self._initial_snapshot = initial_snapshot
        self._next_step = "snapshot" if initial_snapshot else "update"
        self._pending.append(
            self._event(
                "subscribed",
                {
                    "code": code,
                    "fields": selected_fields,
                    "interval_ms": interval_ms,
                    "initial_snapshot": initial_snapshot,
                },
            )
        )

    def close(self) -> None:
        if self._source_session is None:
            return
        try:
            self._source_session.close()
        finally:
            self._source_session = None
            self._subscription_id = None
            self._pending.clear()
            self._refresh_cursors.clear()
            self._next_step = "closed"

    def _snapshot_event(self) -> SimpleNamespace:
        assert self._source_session is not None
        try:
            result = self._source_session.call(
                "stock_realtime_snapshot_tdx",
                params={"code": self._code},
                fields=self._fields,
            )
        except Exception as exc:
            raise AxDataError(f"Local TDX stream snapshot failed: {exc}") from exc
        return self._event("snapshot", list(result.records))

    def _update_event(self) -> SimpleNamespace:
        assert self._source_session is not None
        try:
            from axdata_core.adapters.tdx.realtime_refresh import request_realtime_refresh_rows

            rows = request_realtime_refresh_rows(
                code=self._code,
                fields=self._fields,
                cursors=self._refresh_cursors,
                include_internal=True,
                client=getattr(self._source_session, "tdx_client", None),
            )
        except Exception as exc:
            raise AxDataError(f"Local TDX stream update failed: {exc}") from exc
        _update_refresh_cursors(self._refresh_cursors, rows)
        return self._event("update", _strip_internal_fields(rows))

    def _event(self, event_type: str, data: Any) -> SimpleNamespace:
        return SimpleNamespace(
            type=event_type,
            stream=self.stream,
            subscription_id=self._subscription_id,
            server_time=_stream_time(),
            data=data,
        )


def _stream_time() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _normalize_stream_codes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set, frozenset)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _normalize_stream_interval_ms(value: Any) -> int:
    if value is None:
        return LOCAL_STREAM_DEFAULT_INTERVAL_MS
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return LOCAL_STREAM_DEFAULT_INTERVAL_MS
    return max(LOCAL_STREAM_MIN_INTERVAL_MS, parsed)


def _normalize_stream_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _local_stream_session_options(params: Mapping[str, Any]) -> dict[str, Any]:
    option_keys = {
        "connections_per_server",
        "hosts",
        "pool_size",
        "source_server_count",
    }
    return {
        key: value
        for key, value in params.items()
        if key in option_keys and value is not None
    }


def _update_refresh_cursors(cursors: dict[str, int], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        instrument_id = row.get("_tdx_instrument_id") or row.get("instrument_id")
        update_time_raw = row.get("_tdx_update_time_raw")
        if not instrument_id or update_time_raw in (None, ""):
            continue
        try:
            cursors[str(instrument_id).upper()] = int(update_time_raw)
        except (TypeError, ValueError):
            continue


def _strip_internal_fields(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in dict(row).items() if not str(key).startswith("_tdx_")}
        for row in rows
    ]


def pro_api(
    token: str | None = None,
    api_base: str | None = None,
    data_root: str | Path | None = None,
    data_dir: str | Path | None = None,
    data_home: str | Path | None = None,
    mode: BackendMode = "auto",
    backend: BackendMode | None = None,
) -> AxDataClient:
    """Create an AxData client.

    If api_base or AXDATA_API_BASE is set, the client reads that AxData API
    service. Otherwise it reads the local AxData data directory directly.
    """

    return AxDataClient(
        token=token,
        api_base=api_base,
        data_root=data_root,
        data_dir=data_dir,
        data_home=data_home,
        mode=mode,
        backend=backend,
    )


def connect(
    *,
    api_base: str | None = None,
    data_root: str | Path | None = None,
    data_dir: str | Path | None = None,
    data_home: str | Path | None = None,
    token: str | None = None,
    mode: BackendMode = "auto",
    backend: BackendMode | None = None,
) -> AxDataClient:
    """Connect to local AxData data or a remote AxData API service."""

    return AxDataClient(
        token=token,
        api_base=api_base,
        data_root=data_root,
        data_dir=data_dir,
        data_home=data_home,
        mode=mode,
        backend=backend,
    )


Client = AxDataClient
