"""Tencent Finance Provider entry point."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from axdata_core.plugins import DownloaderProfile, InterfaceSpec, PLUGIN_API_VERSION

from .catalog import DOWNLOADER_PROFILES, INTERFACES
from .metadata import PROVIDER_ID, SOURCE_CODE, SOURCE_NAME_ZH, VERSION

if TYPE_CHECKING:
    from .adapter import TencentProviderAdapter


class TencentProvider:
    """Provider for Tencent Finance public quote snapshots."""

    provider_id = PROVIDER_ID
    source_code = SOURCE_CODE
    source_name_zh = SOURCE_NAME_ZH
    version = VERSION
    plugin_api_version = PLUGIN_API_VERSION

    def interfaces(self) -> Sequence[InterfaceSpec]:
        return INTERFACES

    def create_adapter(
        self,
        options: Mapping[str, object] | None = None,
    ) -> TencentProviderAdapter:
        from .adapter import TencentProviderAdapter

        return TencentProviderAdapter(options=options)

    def downloader_profiles(self) -> Sequence[DownloaderProfile]:
        return DOWNLOADER_PROFILES


provider = TencentProvider()
