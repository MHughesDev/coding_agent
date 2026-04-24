from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarnessRunRequest:
    repo_path: Path
    queue_item: dict[str, str]


@dataclass(frozen=True)
class HarnessPlan:
    steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HarnessExecution:
    applied: bool
    notes: str


@dataclass(frozen=True)
class HarnessValidation:
    passed: bool
    details: str


@dataclass(frozen=True)
class HarnessRunResult:
    status: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
