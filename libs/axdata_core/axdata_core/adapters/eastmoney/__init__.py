"""Eastmoney source request adapter."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["EastmoneyRequestAdapter"]


def __getattr__(name: str) -> Any:
    if name != "EastmoneyRequestAdapter":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    request_module = import_module(".request", __name__)
    value = getattr(request_module, name)
    globals()[name] = value
    return value
