"""TDX Provider interface catalog projection."""

from __future__ import annotations

import json
from importlib import resources
from functools import lru_cache
from typing import TYPE_CHECKING

from axdata_core.plugins import ProviderManifest

if TYPE_CHECKING:
    from axdata_core.plugins import CollectorSpec, DownloaderProfile, InterfaceSpec

from .metadata import SOURCE_CODE, SOURCE_NAME_ZH


def tdx_external_interfaces() -> tuple[InterfaceSpec, ...]:
    """Return TDX interfaces with stable external Provider metadata."""

    return tuple(_manifest().interfaces)


def tdx_external_downloader_profiles() -> tuple[DownloaderProfile, ...]:
    """Return ordinary TDX downloader profiles for the external Provider shape."""

    return tuple(_manifest().downloaders)


def tdx_external_collectors() -> tuple[CollectorSpec, ...]:
    """Return ordinary TDX collector specs for the external Provider shape."""

    return tuple(_manifest().collectors)


@lru_cache(maxsize=1)
def _manifest() -> ProviderManifest:
    payload = resources.files("axdata_source_tdx").joinpath("axdata-provider.json").read_text(encoding="utf-8")
    return ProviderManifest.from_dict(json.loads(payload))
