from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_FILE_CHARS = 8_000


@dataclass(frozen=True)
class RunContext:
    repo_path: Path
    queue_item: dict[str, str]
    documents: dict[str, str]
    related_files: dict[str, str]


def _safe_read(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")[:MAX_FILE_CHARS]


def _parse_related_files(raw_value: str) -> list[str]:
    if not raw_value.strip():
        return []
    normalized = raw_value.replace(";", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def load_context(repo_path: Path, queue_item: dict[str, str]) -> RunContext:
    docs = {
        "README.md": _safe_read(repo_path / "README.md"),
        "docs/README.MD": _safe_read(repo_path / "docs" / "README.MD"),
        "docs/AGENTS.MD": _safe_read(repo_path / "docs" / "AGENTS.MD"),
        "queue/QUEUE_INSTRUCTIONS.md": _safe_read(repo_path / "queue" / "QUEUE_INSTRUCTIONS.md"),
        "queue/QUEUE_AGENT_PROMPT.md": _safe_read(repo_path / "queue" / "QUEUE_AGENT_PROMPT.md"),
    }

    related_files: dict[str, str] = {}
    for rel_path in _parse_related_files(str(queue_item.get("related_files", ""))):
        candidate = repo_path / rel_path
        if candidate.exists() and candidate.is_file():
            related_files[rel_path] = _safe_read(candidate)

    return RunContext(
        repo_path=repo_path,
        queue_item=queue_item,
        documents=docs,
        related_files=related_files,
    )
