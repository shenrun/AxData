"""TDX extended-market Provider package for AxData."""

from __future__ import annotations

from typing import Any

__all__ = ["TdxExtProvider", "provider"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .provider import TdxExtProvider, provider

        return {"TdxExtProvider": TdxExtProvider, "provider": provider}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
