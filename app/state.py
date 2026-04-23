from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SupervisorState:
    active_repo: Path | None = None
    active_queue_id: str | None = None
    active_started_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.active_repo is not None

    def activate(self, repo: Path, queue_id: str, started_at: datetime) -> None:
        if self.is_active:
            raise RuntimeError("Supervisor already has an active run")
        self.active_repo = repo
        self.active_queue_id = queue_id
        self.active_started_at = started_at

    def clear(self) -> None:
        self.active_repo = None
        self.active_queue_id = None
        self.active_started_at = None
