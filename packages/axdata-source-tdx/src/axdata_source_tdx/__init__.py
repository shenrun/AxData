"""TDX Provider package for AxData."""

from __future__ import annotations

from typing import Any

__all__ = ["TdxProvider", "provider"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .provider import TdxProvider, provider

        return {"TdxProvider": TdxProvider, "provider": provider}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
