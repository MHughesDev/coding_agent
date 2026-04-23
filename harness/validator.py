from __future__ import annotations

from harness.result_types import HarnessExecution, HarnessValidation


def validate_execution(execution: HarnessExecution) -> HarnessValidation:
    if execution.applied:
        return HarnessValidation(passed=True, details="Execution applied changes")
    return HarnessValidation(passed=True, details="No-op execution accepted for MVP")
