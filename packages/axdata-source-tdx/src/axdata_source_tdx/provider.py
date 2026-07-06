"""TDX Provider entry point."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from axdata_core.plugins import CollectorSpec, DownloaderProfile, InterfaceSpec, PLUGIN_API_VERSION

from .catalog import tdx_external_collectors, tdx_external_downloader_profiles, tdx_external_interfaces
from .metadata import PROVIDER_ID, SOURCE_CODE, SOURCE_NAME_ZH, VERSION

if TYPE_CHECKING:
    from .adapter import TdxProviderAdapter


class TdxProvider:
    """Provider for ordinary TDX quote interfaces."""

    provider_id = PROVIDER_ID
    source_code = SOURCE_CODE
    source_name_zh = SOURCE_NAME_ZH
    version = VERSION
    plugin_api_version = PLUGIN_API_VERSION

    def interfaces(self) -> Sequence[InterfaceSpec]:
        return tdx_external_interfaces()

    def create_adapter(
        self,
        options: Mapping[str, object] | None = None,
    ) -> TdxProviderAdapter:
        from .adapter import TdxProviderAdapter

        return TdxProviderAdapter(options=options)

    def downloader_profiles(self) -> Sequence[DownloaderProfile]:
        return tdx_external_downloader_profiles()

    def collectors(self) -> Sequence[CollectorSpec]:
        return tdx_external_collectors()


provider = TdxProvider()
