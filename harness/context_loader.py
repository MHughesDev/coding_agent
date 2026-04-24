from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    repo_path: Path
    queue_item: dict[str, str]
    documents: dict[str, str]


def _safe_read(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def load_context(repo_path: Path, queue_item: dict[str, str]) -> RunContext:
    docs = {
        "README.md": _safe_read(repo_path / "README.md"),
        "docs/README.MD": _safe_read(repo_path / "docs" / "README.MD"),
        "docs/AGENTS.MD": _safe_read(repo_path / "docs" / "AGENTS.MD"),
        "queue/QUEUE_INSTRUCTIONS.md": _safe_read(repo_path / "queue" / "QUEUE_INSTRUCTIONS.md"),
        "queue/QUEUE_AGENT_PROMPT.md": _safe_read(repo_path / "queue" / "QUEUE_AGENT_PROMPT.md"),
    }
    return RunContext(repo_path=repo_path, queue_item=queue_item, documents=docs)
