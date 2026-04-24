from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

_TRANSITIONABLE_STATUSES = {"open", "in_progress", "todo", "ready", "queued", "blocked", "failed"}
_TERMINAL_STATUSES = {"done", "failed", "blocked", "open"}


def _normalize_status(status: str) -> str:
    value = status.strip().lower()
    aliases = {
        "todo": "open",
        "ready": "open",
        "queued": "open",
        "in-progress": "in_progress",
        "completed": "done",
        "complete": "done",
        "closed": "done",
    }
    return aliases.get(value, value)


def _read_rows(queue_csv: Path) -> tuple[list[str], list[dict[str, str]]]:
    with queue_csv.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = [{str(k): "" if v is None else str(v) for k, v in row.items()} for row in reader]
    return fieldnames, rows


def _write_rows_atomic(queue_csv: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    queue_csv.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="", dir=queue_csv.parent, delete=False) as temp:
        writer = csv.DictWriter(temp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
        temp_path = Path(temp.name)
    temp_path.replace(queue_csv)


def _ensure_columns(fieldnames: list[str]) -> list[str]:
    required = [
        "id",
        "summary",
        "status",
        "depends_on",
        "run_id",
        "started_at",
        "updated_at",
        "attempt_count",
        "last_error",
    ]
    merged = list(fieldnames)
    for column in required:
        if column not in merged:
            merged.append(column)
    return merged


def mark_item_in_progress(queue_csv: Path, queue_id: str, run_id: str, started_at: datetime | None = None) -> bool:
    started = started_at or datetime.now(timezone.utc)
    fieldnames, rows = _read_rows(queue_csv)
    fieldnames = _ensure_columns(fieldnames)

    updated = False
    for row in rows:
        if row.get("id", "").strip() != queue_id:
            continue
        status = _normalize_status(row.get("status", ""))
        if status not in _TRANSITIONABLE_STATUSES:
            return False
        previous_attempts = int(row.get("attempt_count", "0") or "0")
        row["status"] = "in_progress"
        row["run_id"] = run_id
        row["started_at"] = started.isoformat()
        row["updated_at"] = started.isoformat()
        row["attempt_count"] = str(previous_attempts + 1)
        row["last_error"] = ""
        updated = True
        break

    if updated:
        _write_rows_atomic(queue_csv, fieldnames, rows)
    return updated


def mark_item_terminal(
    queue_csv: Path,
    queue_id: str,
    terminal_status: str,
    run_id: str,
    *,
    finished_at: datetime | None = None,
    last_error: str = "",
) -> bool:
    normalized_terminal = _normalize_status(terminal_status)
    if normalized_terminal not in _TERMINAL_STATUSES:
        raise ValueError(f"Unsupported terminal status: {terminal_status}")

    ended = finished_at or datetime.now(timezone.utc)
    fieldnames, rows = _read_rows(queue_csv)
    fieldnames = _ensure_columns(fieldnames)

    updated = False
    for row in rows:
        if row.get("id", "").strip() != queue_id:
            continue
        row["status"] = normalized_terminal
        row["run_id"] = run_id
        row["updated_at"] = ended.isoformat()
        if last_error:
            row["last_error"] = last_error
        updated = True
        break

    if updated:
        _write_rows_atomic(queue_csv, fieldnames, rows)
    return updated
