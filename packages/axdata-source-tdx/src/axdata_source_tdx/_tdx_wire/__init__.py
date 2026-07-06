"""Private minimal TDX 7709 wire implementation for AxData code tables."""

from __future__ import annotations


__all__ = [
    "Client",
    "TdxClient",
    "__version__",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    if name in {"Client", "TdxClient"}:
        from .client import Client, TdxClient

        globals()["Client"] = Client
        globals()["TdxClient"] = TdxClient
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
