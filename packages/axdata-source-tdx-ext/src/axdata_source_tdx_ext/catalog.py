"""TDX extended-market Provider interface catalog projection."""

from __future__ import annotations

import json
from importlib import resources
from functools import lru_cache
from typing import TYPE_CHECKING

from axdata_core.plugins import ProviderManifest

if TYPE_CHECKING:
    from axdata_core.plugins import DownloaderProfile, InterfaceSpec

from .metadata import SOURCE_CODE, SOURCE_NAME_ZH


def tdx_ext_external_interfaces() -> tuple[InterfaceSpec, ...]:
    """Return TDX extended-market interfaces with stable Provider metadata."""

    return tuple(_manifest().interfaces)


def tdx_ext_external_downloader_profiles() -> tuple[DownloaderProfile, ...]:
    """Return TDX extended-market downloader profiles for the external Provider shape."""

    return tuple(_manifest().downloaders)


@lru_cache(maxsize=1)
def _manifest() -> ProviderManifest:
    payload = resources.files("axdata_source_tdx_ext").joinpath("axdata-provider.json").read_text(encoding="utf-8")
    return ProviderManifest.from_dict(json.loads(payload))
