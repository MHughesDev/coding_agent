from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def lock_path(repo_path: Path) -> Path:
    return repo_path / "queue" / "queue.lock"


def write_lock(repo_path: Path, queue_id: str, status: str = "running") -> None:
    path = lock_path(repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "repo_path": str(repo_path),
        "queue_id": queue_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_lock(repo_path: Path) -> None:
    path = lock_path(repo_path)
    if path.exists():
        path.unlink()
