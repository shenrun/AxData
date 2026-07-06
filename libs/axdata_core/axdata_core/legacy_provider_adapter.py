"""Helpers for exposing legacy request adapters through Provider adapters."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from axdata_core.source_adapter_options import timeout_seconds

LegacyAdapterFactory = Callable[[Mapping[str, object]], Any]


class LegacyProviderAdapter:
    """Bridge a legacy request adapter into the Provider ``call`` contract."""

    def __init__(
        self,
        *,
        source: str,
        provider_id: str,
        create_adapter: LegacyAdapterFactory,
        options: Mapping[str, object] | None = None,
    ) -> None:
        self.source = source
        self.provider_id = provider_id
        self.options = dict(options or {})
        self._create_adapter = create_adapter
        self._adapter: Any | None = None

    def call(
        self,
        interface_name: str,
        params: Mapping[str, object] | None = None,
        fields: Sequence[str] | None = None,
        options: Mapping[str, object] | None = None,
    ) -> SourceResult:
        adapter = self._adapter_for_call(options)
        records = adapter.request(interface_name, dict(params or {}))
        if fields:
            records = _select_fields(records, fields)
        meta: dict[str, Any] = {
            "source": self.source,
            "provider_id": self.provider_id,
            "interface_name": interface_name,
        }
        adapter_meta = getattr(adapter, "last_meta", None)
        if isinstance(adapter_meta, Mapping):
            meta.update(adapter_meta)
        from axdata_core.plugins import SourceResult

        return SourceResult(data=tuple(records), meta=meta)

    def _adapter_for_call(self, options: Mapping[str, object] | None) -> Any:
        if options:
            call_options = {**self.options, **dict(options)}
            return self._create_adapter(call_options)
        if self._adapter is None:
            self._adapter = self._create_adapter(self.options)
        return self._adapter


def _select_fields(
    records: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> list[dict[str, Any]]:
    from axdata_core.source_projection import select_fields

    return select_fields(records, fields)
