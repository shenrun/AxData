"""Compatibility shim for axdata_core._tdx_wire.client.

The provider-owned TDX wire implementation lives in ``axdata_source_tdx._tdx_wire``.
This module keeps old imports working by loading the TDX plugin on demand.
If the plugin is unavailable, attribute access raises a clear install/enable error.
"""

from __future__ import annotations

from ._shim import install_lazy_provider_first


_PROVIDER_MODULE = "axdata_source_tdx._tdx_wire.client"


install_lazy_provider_first(
    globals(),
    provider_module=_PROVIDER_MODULE,
        exports=[
        "Client",
        "DEFAULT_CODE_PAGE_SIZE",
        "DEFAULT_FILE_CHUNK_SIZE",
        "DEFAULT_PROBE_TIMEOUT",
        "DEFAULT_PROBE_WORKERS",
        "DEFAULT_QUOTE_BATCH_SIZE",
        "Sequence",
        "TYPE_CHECKING",
        "TdxClient",
        "annotations",
        "dataclass",
        "field",
    ],
)
