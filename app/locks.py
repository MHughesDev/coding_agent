from __future__ import annotations

import json
import logging
import os
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import queue_state

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LockInspection:
    status: str  # missing | active | stale | uncertain | invalid
    payload: dict[str, Any] | None
    reason: str


@dataclass(frozen=True)
class RecoveryAction:
    should_skip_repo: bool
    lock_cleared: bool
    queue_updated: bool
    reason: str


def lock_path(repo_path: Path) -> Path:
    return repo_path / "queue" / "queue.lock"


def write_lock(
    repo_path: Path,
    queue_id: str,
    status: str = "running",
    *,
    run_id: str | None = None,
    pass_index: int | None = None,
) -> None:
    path = lock_path(repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "status": status,
        "repo_path": str(repo_path),
        "queue_id": queue_id,
        "run_id": run_id or "",
        "pass_index": pass_index,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "start_time": now,
        "updated_time": now,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_lock(repo_path: Path) -> dict[str, Any] | None:
    path = lock_path(repo_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_lock(repo_path: Path) -> None:
    path = lock_path(repo_path)
    if path.exists():
        path.unlink()


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def inspect_lock(repo_path: Path, stale_after_seconds: int) -> LockInspection:
    path = lock_path(repo_path)
    if not path.exists():
        return LockInspection(status="missing", payload=None, reason="no-lock-file")

    try:
        payload = read_lock(repo_path)
    except (json.JSONDecodeError, OSError, ValueError):
        return LockInspection(status="invalid", payload=None, reason="unreadable-lock-payload")

    if payload is None:
        return LockInspection(status="missing", payload=None, reason="no-lock-file")

    pid = payload.get("pid")
    if isinstance(pid, int) and _is_pid_running(pid):
        return LockInspection(status="active", payload=payload, reason="lock-pid-is-alive")

    start_time_raw = str(payload.get("start_time", "")).strip()
    if not start_time_raw:
        return LockInspection(status="uncertain", payload=payload, reason="missing-start-time")

    try:
        started = datetime.fromisoformat(start_time_raw)
    except ValueError:
        return LockInspection(status="uncertain", payload=payload, reason="invalid-start-time")

    now = datetime.now(timezone.utc)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)

    age_seconds = (now - started).total_seconds()
    if age_seconds >= stale_after_seconds:
        return LockInspection(status="stale", payload=payload, reason=f"age-seconds={int(age_seconds)}")

    return LockInspection(status="uncertain", payload=payload, reason=f"age-seconds={int(age_seconds)}")


def recover_lock_if_needed(repo_path: Path, queue_csv: Path | None, stale_after_seconds: int) -> RecoveryAction:
    inspection = inspect_lock(repo_path, stale_after_seconds=stale_after_seconds)
    if inspection.status == "missing":
        return RecoveryAction(False, False, False, inspection.reason)

    if inspection.status == "active":
        logger.warning("Repo %s has active lock; skipping repo for this pass", repo_path)
        return RecoveryAction(True, False, False, inspection.reason)

    if inspection.status == "uncertain":
        logger.warning("Repo %s has uncertain lock state; skipping repo for this pass", repo_path)
        return RecoveryAction(True, False, False, inspection.reason)

    payload = inspection.payload or {}
    queue_id = str(payload.get("queue_id", "")).strip()
    run_id = str(payload.get("run_id", "")).strip() or "recovery-run"
    queue_updated = False

    if queue_csv is not None and queue_csv.exists() and queue_id:
        queue_updated = queue_state.mark_item_terminal(
            queue_csv=queue_csv,
            queue_id=queue_id,
            terminal_status="failed",
            run_id=run_id,
            finished_at=datetime.now(timezone.utc),
            last_error=f"Recovered {inspection.status} lock ({inspection.reason})",
        )

    clear_lock(repo_path)
    logger.info("Recovered %s lock for repo %s and cleared queue.lock", inspection.status, repo_path)
    return RecoveryAction(False, True, queue_updated, inspection.reason)
