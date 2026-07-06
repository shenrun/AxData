"""Local source sessions for high-frequency in-process requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .plugins import SourceResult
from .source_errors import SourceAdapterError, SourceAdapterNotFound, SourceUnavailableError
from .source_execution_options import execution_options_for_source
from .source_request import SourceRequestResult, request_interface

SUPPORTED_SESSION_SOURCES = frozenset({"tdx", "tdx_ext"})


@dataclass
class LocalSourceSession:
    """Keep a local source adapter and its long-connection resources alive."""

    source: str
    data_root: str | Path | None = None
    options: Mapping[str, Any] | None = None
    _source_code: str = field(init=False, default="")
    _provider_id: str | None = field(init=False, default=None)
    _provider_adapter: Any | None = field(init=False, default=None)
    _request_adapter: Any | None = field(init=False, default=None)
    _client: Any | None = field(init=False, default=None)
    _client_pool: Any | None = field(init=False, default=None)
    _owns_client: bool = field(init=False, default=False)
    _owns_client_pool: bool = field(init=False, default=False)
    _opened: bool = field(init=False, default=False)

    def __enter__(self) -> "LocalSourceSession":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def tdx_client(self) -> Any | None:
        """Return the ordinary TDX client used by this session, if any."""

        return self._client

    @property
    def tdx_ext_client_pool(self) -> Any | None:
        """Return the TDX Ext client pool used by this session, if any."""

        return self._client_pool

    def open(self) -> None:
        if self._opened:
            return
        source_code = _normalize_source(self.source)
        _validate_supported_source(source_code)
        base_options = dict(self.options or {})
        provider_id, provider_adapter_factory = _resolve_provider_adapter_factory(
            source_code,
            data_root=self.data_root,
        )
        execution_options = execution_options_for_source(
            base_options,
            data_root=self.data_root,
            provider_id=provider_id,
            source_code=source_code,
        )
        session_options = dict(execution_options)
        if source_code == "tdx":
            client = session_options.pop("client", None)
            if client is None:
                client = _create_tdx_session_client(session_options)
                self._owns_client = True
            self._client = client
            session_options["client"] = client
        elif source_code == "tdx_ext":
            client_pool = session_options.pop("client_pool", None)
            client_pool_config = session_options.pop("client_pool_config", None)
            if client_pool is None:
                client_pool, client_pool_config = _create_tdx_ext_session_pool(session_options)
                self._owns_client_pool = True
            self._client_pool = client_pool
            session_options["client_pool"] = client_pool
            if client_pool_config is not None:
                session_options["client_pool_config"] = client_pool_config

        provider_adapter = provider_adapter_factory(session_options)
        self._source_code = source_code
        self._provider_id = provider_id
        self._provider_adapter = provider_adapter
        self._request_adapter = SessionSourceRequestAdapter(
            source=source_code,
            provider_adapter=provider_adapter,
        )
        self._opened = True

    def close(self) -> None:
        if self._request_adapter is not None:
            _close_if_possible(self._request_adapter)
        if self._provider_adapter is not None:
            _close_if_possible(self._provider_adapter)
        if self._owns_client_pool and self._client_pool is not None:
            _close_if_possible(self._client_pool)
        if self._owns_client and self._client is not None:
            _close_if_possible(self._client)
        self._request_adapter = None
        self._provider_adapter = None
        self._client_pool = None
        self._client = None
        self._owns_client_pool = False
        self._owns_client = False
        self._opened = False

    def call(
        self,
        interface: str,
        *,
        params: Mapping[str, Any] | None = None,
        fields: str | Sequence[str] | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> SourceRequestResult:
        """Call a source interface through the session-owned adapter."""

        if options:
            raise SourceAdapterError(
                "Per-call request options are not supported inside a local source session; "
                "pass TDX connection options to client.session(...)."
            )
        if not self._opened:
            self.open()
        assert self._request_adapter is not None
        return request_interface(
            interface,
            params=params,
            fields=fields,
            persist=False,
            adapter=self._request_adapter,
            data_root=self.data_root,
        )


@dataclass
class SessionSourceRequestAdapter:
    """SourceRequestAdapter wrapper around a reusable Provider adapter."""

    source: str
    provider_adapter: Any
    last_meta: dict[str, Any] = field(default_factory=dict)

    def supports(self, interface_name: str) -> bool:
        supports = getattr(self.provider_adapter, "supports", None)
        if callable(supports):
            return bool(supports(interface_name))
        adapter_for_call = getattr(self.provider_adapter, "_adapter_for_call", None)
        if callable(adapter_for_call):
            adapter = adapter_for_call(None)
            adapter_supports = getattr(adapter, "supports", None)
            if callable(adapter_supports):
                return bool(adapter_supports(interface_name))
        return True

    def request(self, interface_name: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        if hasattr(self.provider_adapter, "call"):
            result = self.provider_adapter.call(interface_name, params=params)
            return self._records_from_provider_result(result)
        if hasattr(self.provider_adapter, "request"):
            rows = self.provider_adapter.request(interface_name, params)
            adapter_meta = getattr(self.provider_adapter, "last_meta", None)
            self.last_meta = dict(adapter_meta) if isinstance(adapter_meta, Mapping) else {}
            return [dict(row) for row in rows]
        raise SourceAdapterError(
            f"Source adapter for {self.source!r} does not expose call(...) or request(...)."
        )

    def _records_from_provider_result(self, result: Any) -> list[dict[str, Any]]:
        if isinstance(result, SourceResult):
            self.last_meta = dict(result.meta)
            return [dict(row) for row in result.data]
        if isinstance(result, Mapping):
            meta = result.get("meta")
            self.last_meta = dict(meta) if isinstance(meta, Mapping) else {}
            data = result.get("data", [])
            if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
                return [dict(row) for row in data]
            return [dict(result)]
        self.last_meta = {}
        return [dict(row) for row in result]


def create_source_session(
    *,
    source: str,
    data_root: str | Path | None = None,
    options: Mapping[str, Any] | None = None,
) -> LocalSourceSession:
    """Create a local high-frequency source session."""

    return LocalSourceSession(source=source, data_root=data_root, options=options)


def _normalize_source(source: str) -> str:
    return str(source or "").strip().lower()


def _validate_supported_source(source_code: str) -> None:
    if source_code not in SUPPORTED_SESSION_SOURCES:
        supported = ", ".join(sorted(SUPPORTED_SESSION_SOURCES))
        raise SourceAdapterNotFound(
            f"Local source sessions currently support only {supported}; got {source_code!r}."
        )


def _resolve_provider_adapter_factory(
    source_code: str,
    *,
    data_root: str | Path | None,
):
    try:
        from .provider_catalog import build_builtin_provider_registry

        registry = build_builtin_provider_registry(data_root=data_root)
        snapshot = registry.snapshot()
    except Exception:
        snapshot = None

    if snapshot is not None:
        source_providers = [
            provider
            for provider in snapshot.providers.values()
            if provider.source_code == source_code
        ]
        enabled = [
            provider
            for provider in source_providers
            if provider.status == "enabled" and provider.enabled
        ]
        if enabled:
            provider = sorted(enabled, key=lambda item: item.provider_id)[0]

            def create_adapter(options: Mapping[str, Any]) -> Any:
                provider_object = _load_provider_object(provider)
                try:
                    return provider_object.create_adapter(options=options)
                except TypeError:
                    return provider_object.create_adapter(options)

            return provider.provider_id, create_adapter
        if source_providers:
            status = ", ".join(
                f"{provider.provider_id}:{provider.status}" for provider in source_providers
            )
            raise SourceUnavailableError(
                f"Source provider for {source_code!r} is not enabled or unavailable ({status})."
            )

    def create_legacy_adapter(options: Mapping[str, Any]) -> Any:
        from .source_adapter_factory import adapter_for_source_code

        try:
            return adapter_for_source_code(source_code, options=options)
        except KeyError as exc:
            raise SourceUnavailableError(
                f"Source provider for {source_code!r} is not installed or enabled."
            ) from exc

    return None, create_legacy_adapter


def _load_provider_object(provider: Any) -> Any:
    try:
        provider_object = provider.load_provider()
    except Exception as exc:
        raise SourceAdapterError(
            f"Failed to load source provider {provider.provider_id!r}: {exc}"
        ) from exc
    if provider_object is None:
        raise SourceAdapterError(
            f"Source provider {provider.provider_id!r} could not be loaded."
        )
    return provider_object


def _create_tdx_session_client(options: Mapping[str, Any]) -> Any:
    try:
        from axdata_source_tdx.options import (
            tdx_request_option_hosts,
            tdx_request_option_pool_size,
        )
        from axdata_source_tdx.request_adapter import (
            configured_tdx_hosts_from_options,
            create_tdx_client,
        )
    except ModuleNotFoundError as exc:
        from .tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE

        raise SourceUnavailableError(TDX_PLUGIN_REQUIRED_MESSAGE) from exc

    hosts = (
        tdx_request_option_hosts(options, configured_hosts=configured_tdx_hosts_from_options)
        or configured_tdx_hosts_from_options(options)
    )
    return create_tdx_client(
        hosts=hosts,
        pool_size=tdx_request_option_pool_size(options),
    )


def _create_tdx_ext_session_pool(options: Mapping[str, Any]) -> tuple[Any, Any]:
    from .adapters.tdx_ext.options import positive_tdx_ext_option_int
    from .adapters.tdx_ext.pool import TdxExtClientPool, TdxExtPoolConfig
    from .adapters.tdx_ext.pool import _configured_extended_servers

    server_cache_root = options.get("server_cache_root")
    servers = _configured_extended_servers(
        cache_root=str(server_cache_root) if server_cache_root not in (None, "") else None
    )
    source_server_count = positive_tdx_ext_option_int(
        options.get("source_server_count", 1),
        "source_server_count",
        maximum=64,
    )
    requested_connections_per_server = positive_tdx_ext_option_int(
        options.get("connections_per_server", 1),
        "connections_per_server",
        maximum=64,
    )
    selected_servers = tuple(servers[: min(source_server_count, len(servers))])
    if not selected_servers:
        raise SourceUnavailableError("No TDX extended market server is configured.")
    connection_count = min(len(selected_servers) * requested_connections_per_server, 128)
    connections_per_server = max(
        1,
        (connection_count + len(selected_servers) - 1) // len(selected_servers),
    )
    config = TdxExtPoolConfig(
        source_server_count=len(selected_servers),
        connections_per_server=connections_per_server,
        connection_count=connection_count,
        requested_connections_per_server=requested_connections_per_server,
        servers=selected_servers,
    )
    pool = TdxExtClientPool(
        servers=selected_servers,
        connections_per_server=connections_per_server,
        connection_count=connection_count,
    )
    return pool, config


def _close_if_possible(value: Any) -> None:
    close = getattr(value, "close", None)
    if callable(close):
        close()
