from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoScanResult:
    repo_path: Path
    looks_like_repo: bool
    queue_dir: Path | None
    queue_csv: Path | None

    @property
    def has_queue(self) -> bool:
        return self.queue_dir is not None and self.queue_csv is not None


def looks_like_project_root(repo_path: Path) -> bool:
    if (repo_path / ".git").exists():
        return True
    markers = ["pyproject.toml", "README.md", "README.MD", "package.json", "setup.py"]
    return any((repo_path / marker).exists() for marker in markers)


def scan_repo(repo_path: Path) -> RepoScanResult:
    if not repo_path.exists() or not repo_path.is_dir():
        return RepoScanResult(repo_path=repo_path, looks_like_repo=False, queue_dir=None, queue_csv=None)
    if not looks_like_project_root(repo_path):
        return RepoScanResult(repo_path=repo_path, looks_like_repo=False, queue_dir=None, queue_csv=None)

    queue_dir = repo_path / "queue"
    queue_csv = queue_dir / "queue.csv"
    if not queue_dir.is_dir() or not queue_csv.exists():
        return RepoScanResult(repo_path=repo_path, looks_like_repo=True, queue_dir=None, queue_csv=None)

    return RepoScanResult(repo_path=repo_path, looks_like_repo=True, queue_dir=queue_dir, queue_csv=queue_csv)
