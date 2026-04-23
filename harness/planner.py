from __future__ import annotations

from harness.context_loader import RunContext
from harness.result_types import HarnessPlan


def build_plan(context: RunContext, model_response: str) -> HarnessPlan:
    summary = context.queue_item.get("summary", "").strip()
    if model_response:
        steps = [f"Queue summary: {summary}", "Review model guidance", "Apply minimal implementation"]
    else:
        steps = [f"Queue summary: {summary}", "Model unavailable fallback", "Prepare manual run output"]
    return HarnessPlan(steps=steps)
