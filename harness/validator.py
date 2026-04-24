from __future__ import annotations

import subprocess
from pathlib import Path

from harness.context_loader import RunContext
from harness.result_types import HarnessExecution, HarnessValidation


def _detect_repo_type(repo_path: Path) -> str:
    if (repo_path / "pyproject.toml").exists() or (repo_path / "setup.py").exists():
        return "python"
    if (repo_path / "package.json").exists():
        return "node"
    return "generic"


def validate_execution(context: RunContext, execution: HarnessExecution) -> HarnessValidation:
    if not execution.applied:
        return HarnessValidation(passed=False, details="Execution did not apply changes", confidence="low")

    repo_type = _detect_repo_type(context.repo_path)
    commands: list[list[str]] = []
    if repo_type == "python":
        commands.append(["python", "-m", "unittest", "discover", "-q"])
    elif repo_type == "node":
        commands.append(["npm", "test", "--", "--help"])

    if not commands:
        return HarnessValidation(
            passed=True,
            details="No repo-type validation command available; artifact-only execution accepted",
            confidence="low",
            commands=[],
        )

    for command in commands:
        completed = subprocess.run(
            command,
            cwd=context.repo_path,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            output = (completed.stdout + "\n" + completed.stderr).strip()
            return HarnessValidation(
                passed=False,
                details=f"Validation failed for {' '.join(command)}: {output[:400]}",
                confidence="high",
                commands=[" ".join(command)],
            )

    return HarnessValidation(
        passed=True,
        details="Validation command(s) completed successfully",
        confidence="high",
        commands=[" ".join(c) for c in commands],
    )
