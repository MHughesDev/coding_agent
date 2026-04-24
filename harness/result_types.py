from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarnessRunRequest:
    repo_path: Path
    queue_item: dict[str, str]


@dataclass(frozen=True)
class HarnessPlanStep:
    step_id: str
    intent: str
    acceptance: str
    targets: list[str] = field(default_factory=list)
    status: str = "pending"


@dataclass(frozen=True)
class HarnessPlan:
    steps: list[HarnessPlanStep] = field(default_factory=list)
    malformed_output: bool = False


@dataclass(frozen=True)
class HarnessExecution:
    applied: bool
    notes: str
    touched_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HarnessValidation:
    passed: bool
    details: str
    confidence: str = "low"
    commands: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HarnessRunResult:
    status: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
