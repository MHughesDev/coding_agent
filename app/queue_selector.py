from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

REQUIRED_COLUMNS = {"id", "summary", "status"}
KNOWN_OPTIONAL_COLUMNS = {"depends_on", "notes", "related_files"}

ACTIONABLE_STATUSES = {"open"}
DONE_STATUSES = {"done"}
BLOCKING_STATUSES = {"blocked", "failed", "in_progress"}

STATUS_ALIASES = {
    "open": "open",
    "todo": "open",
    "ready": "open",
    "queued": "open",
    "done": "done",
    "closed": "done",
    "complete": "done",
    "completed": "done",
    "in_progress": "in_progress",
    "in-progress": "in_progress",
    "blocked": "blocked",
    "failed": "failed",
}

_DEP_SPLIT_PATTERN = re.compile(r"[;,\s]+")


@dataclass(frozen=True)
class QueueItem:
    queue_id: str
    summary: str
    status: str
    raw: dict[str, str]


@dataclass(frozen=True)
class QueueContractFinding:
    severity: str  # fatal | warning | info
    message: str
    row_number: int | None = None
    column: str | None = None


@dataclass(frozen=True)
class QueueSelectionResult:
    item: QueueItem | None
    findings: list[QueueContractFinding]


def _parse_dependencies(raw_value: str) -> list[str]:
    if not raw_value.strip():
        return []
    return [part.strip() for part in _DEP_SPLIT_PATTERN.split(raw_value) if part.strip()]


def _canonical_status(raw_status: str) -> str:
    normalized = raw_status.strip().lower()
    return STATUS_ALIASES.get(normalized, normalized)


def select_next_item(queue_csv: Path) -> QueueItem | None:
    return select_next_item_with_report(queue_csv).item


def select_next_item_with_report(queue_csv: Path) -> QueueSelectionResult:
    findings: list[QueueContractFinding] = []

    with queue_csv.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = [field.strip() for field in (reader.fieldnames or []) if field is not None]

        missing_columns = sorted(REQUIRED_COLUMNS.difference(fieldnames))
        if missing_columns:
            for column in missing_columns:
                findings.append(
                    QueueContractFinding(
                        severity="fatal",
                        message="queue.csv is missing required column",
                        column=column,
                    )
                )
            return QueueSelectionResult(item=None, findings=findings)

        unknown_columns = sorted(
            set(fieldnames).difference(REQUIRED_COLUMNS).difference(KNOWN_OPTIONAL_COLUMNS)
        )
        for column in unknown_columns:
            findings.append(
                QueueContractFinding(
                    severity="info",
                    message="Unknown queue column retained for forward compatibility",
                    column=column,
                )
            )

        rows = list(reader)

    row_meta: list[tuple[int, dict[str, str], str, str, list[str]]] = []
    first_seen_by_id: dict[str, int] = {}
    all_rows_by_id: dict[str, list[int]] = {}

    for index, row in enumerate(rows, start=2):
        normalized_row = {str(k): "" if v is None else str(v) for k, v in row.items()}
        queue_id = normalized_row.get("id", "").strip()
        status = _canonical_status(normalized_row.get("status", ""))
        dependencies = _parse_dependencies(normalized_row.get("depends_on", ""))

        if not queue_id:
            findings.append(
                QueueContractFinding(
                    severity="warning",
                    message="Row ignored because id is blank",
                    row_number=index,
                    column="id",
                )
            )
            continue

        if status not in ACTIONABLE_STATUSES and status not in DONE_STATUSES and status not in BLOCKING_STATUSES:
            findings.append(
                QueueContractFinding(
                    severity="warning",
                    message="Row ignored because status is not recognized",
                    row_number=index,
                    column="status",
                )
            )
            continue

        all_rows_by_id.setdefault(queue_id, []).append(index)
        if queue_id in first_seen_by_id:
            findings.append(
                QueueContractFinding(
                    severity="warning",
                    message=f"Duplicate id encountered; first occurrence at row {first_seen_by_id[queue_id]} wins",
                    row_number=index,
                    column="id",
                )
            )
        else:
            first_seen_by_id[queue_id] = index

        row_meta.append((index, normalized_row, queue_id, status, dependencies))

    id_set = set(all_rows_by_id.keys())

    for row_number, _row, queue_id, _status, dependencies in row_meta:
        if queue_id in dependencies:
            findings.append(
                QueueContractFinding(
                    severity="warning",
                    message="Item depends on itself",
                    row_number=row_number,
                    column="depends_on",
                )
            )
        for dependency in dependencies:
            if dependency not in id_set:
                findings.append(
                    QueueContractFinding(
                        severity="warning",
                        message=f"Dependency '{dependency}' cannot be resolved",
                        row_number=row_number,
                        column="depends_on",
                    )
                )

    first_rows_only = [meta for meta in row_meta if first_seen_by_id[meta[2]] == meta[0]]

    adjacency: dict[str, list[str]] = {
        queue_id: [dep for dep in dependencies if dep in id_set and dep != queue_id]
        for _row_num, _row, queue_id, _status, dependencies in first_rows_only
    }

    cycle_nodes: set[str] = set()
    visited: set[str] = set()
    active_stack: list[str] = []

    def walk(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        active_stack.append(node)
        for dep in adjacency.get(node, []):
            if dep in active_stack:
                cycle_nodes.update(active_stack[active_stack.index(dep) :])
                continue
            walk(dep)
        active_stack.pop()

    for node in adjacency:
        walk(node)

    for row_number, _row, queue_id, _status, _dependencies in first_rows_only:
        if queue_id in cycle_nodes:
            findings.append(
                QueueContractFinding(
                    severity="warning",
                    message="Dependency cycle detected; item will not be actionable",
                    row_number=row_number,
                    column="depends_on",
                )
            )

    completed = {queue_id for _row_num, _row, queue_id, status, _deps in first_rows_only if status in DONE_STATUSES}

    for row_number, row, queue_id, status, dependencies in first_rows_only:
        if status not in ACTIONABLE_STATUSES:
            continue
        if queue_id in cycle_nodes:
            continue
        unresolved = [dep for dep in dependencies if dep not in completed]
        if unresolved:
            continue
        return QueueSelectionResult(
            item=QueueItem(
                queue_id=queue_id,
                summary=row.get("summary", "").strip(),
                status=status,
                raw=row,
            ),
            findings=findings,
        )

    return QueueSelectionResult(item=None, findings=findings)
