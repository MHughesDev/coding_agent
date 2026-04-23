from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.queue_selector import QueueItem, select_next_item
from app.repo_scanner import RepoScanResult, scan_repo


@dataclass(frozen=True)
class RepoWork:
    scan: RepoScanResult
    item: QueueItem | None


@dataclass(frozen=True)
class FullPassResult:
    works: list[RepoWork]

    @property
    def had_actionable_work(self) -> bool:
        return any(work.item is not None for work in self.works)


def perform_full_pass(repos: list[Path]) -> FullPassResult:
    works: list[RepoWork] = []
    for repo in repos:
        scan = scan_repo(repo)
        item = select_next_item(scan.queue_csv) if scan.has_queue and scan.queue_csv else None
        works.append(RepoWork(scan=scan, item=item))
    return FullPassResult(works=works)
