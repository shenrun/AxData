"""Worker task state models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskState:
    batch_id: str
    source: str
    dataset: str
    status: str = "pending"
    started_at: str | None = None
    finished_at: str | None = None
    rows: int = 0
    error: str | None = None

    def mark_running(self) -> None:
        self.status = "running"
        self.started_at = utc_now_iso()
        self.finished_at = None
        self.error = None

    def mark_finished(self, rows: int, status: str = "success") -> None:
        self.status = status
        self.finished_at = utc_now_iso()
        self.rows = rows
        self.error = None

    def mark_failed(self, error: BaseException | str) -> None:
        self.status = "failed"
        self.finished_at = utc_now_iso()
        self.error = str(error)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
