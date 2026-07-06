"""Compatibility exports for the legacy TDX request module."""

from __future__ import annotations

from typing import Any

from axdata_core.adapters.tdx.request_compat import resolve_request_compat_export


def __getattr__(name: str) -> Any:
    return resolve_request_compat_export(name, globals(), __name__)
