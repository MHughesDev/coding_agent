from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ACTIONABLE_STATUSES = {"open", "todo", "ready", "queued"}
DONE_STATUSES = {"done", "closed", "complete", "completed"}


@dataclass(frozen=True)
class QueueItem:
    queue_id: str
    summary: str
    status: str
    raw: dict[str, str]


def _parse_dependencies(raw_value: str) -> list[str]:
    if not raw_value.strip():
        return []
    return [part.strip() for part in raw_value.replace(";", ",").split(",") if part.strip()]


def select_next_item(queue_csv: Path) -> QueueItem | None:
    with queue_csv.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    completed = {
        str(row.get("id", "")).strip()
        for row in rows
        if str(row.get("status", "")).strip().lower() in DONE_STATUSES
    }

    for row in rows:
        status = str(row.get("status", "")).strip().lower()
        if status not in ACTIONABLE_STATUSES:
            continue
        queue_id = str(row.get("id", "")).strip()
        if not queue_id:
            continue
        deps = _parse_dependencies(str(row.get("depends_on", "")))
        if deps and not all(dep in completed for dep in deps):
            continue
        return QueueItem(
            queue_id=queue_id,
            summary=str(row.get("summary", "")).strip(),
            status=status,
            raw={k: str(v) for k, v in row.items()},
        )

    return None
