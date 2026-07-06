"""Data directory conventions for AxData."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

DATA_LAYERS = ("raw", "staging", "core", "factor")


@dataclass(frozen=True)
class AxDataPaths:
    """Resolved paths for the standard AxData data lake layout."""

    root: Path

    def __init__(self, root: str | Path) -> None:
        object.__setattr__(self, "root", Path(root).expanduser().resolve())

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def staging(self) -> Path:
        return self.root / "staging"

    @property
    def core(self) -> Path:
        return self.root / "core"

    @property
    def factor(self) -> Path:
        return self.root / "factor"

    def table_path(self, layer: str, table: str) -> Path:
        if layer not in DATA_LAYERS:
            layers = ", ".join(DATA_LAYERS)
            raise ValueError(f"Unknown data layer {layer!r}. Expected one of: {layers}.")
        return getattr(self, layer) / f"{table}.parquet"

    def as_dict(self) -> Dict[str, Path]:
        return {layer: getattr(self, layer) for layer in DATA_LAYERS}

    def ensure(self, layers: Iterable[str] = DATA_LAYERS) -> None:
        for layer in layers:
            if layer not in DATA_LAYERS:
                known = ", ".join(DATA_LAYERS)
                raise ValueError(f"Unknown data layer {layer!r}. Expected one of: {known}.")
            getattr(self, layer).mkdir(parents=True, exist_ok=True)
