"""Tencent Finance Provider package for AxData."""

from __future__ import annotations

from typing import Any

__all__ = ["TencentProvider", "provider"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .provider import TencentProvider, provider

        return {"TencentProvider": TencentProvider, "provider": provider}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
