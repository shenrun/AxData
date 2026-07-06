"""TDX extended market server model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TdxExtServer:
    """One configured extended market server."""

    index: int
    name: str
    host: str
    port: int
    is_primary: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "is_primary": self.is_primary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TdxExtServer":
        return cls(
            index=int(data["index"]),
            name=str(data.get("name") or ""),
            host=str(data["host"]),
            port=int(data["port"]),
            is_primary=bool(data.get("is_primary", False)),
        )
