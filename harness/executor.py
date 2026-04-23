from __future__ import annotations

from harness.context_loader import RunContext
from harness.result_types import HarnessExecution, HarnessPlan


def execute_plan(context: RunContext, plan: HarnessPlan) -> HarnessExecution:
    _ = context
    _ = plan
    return HarnessExecution(applied=False, notes="MVP harness: planning-only execution placeholder")
