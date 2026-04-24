from __future__ import annotations

import json
from typing import Any

from harness.context_loader import RunContext
from harness.result_types import HarnessPlan, HarnessPlanStep


def _coerce_steps(payload: Any) -> list[HarnessPlanStep]:
    raw_steps = payload.get("steps", []) if isinstance(payload, dict) else []
    steps: list[HarnessPlanStep] = []
    for index, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, dict):
            continue
        intent = str(raw_step.get("intent", "")).strip()
        acceptance = str(raw_step.get("acceptance", "")).strip()
        targets_raw = raw_step.get("targets", [])
        targets = [str(item).strip() for item in targets_raw if str(item).strip()] if isinstance(targets_raw, list) else []
        if not intent:
            continue
        steps.append(
            HarnessPlanStep(
                step_id=f"S{index}",
                intent=intent,
                acceptance=acceptance or "Acceptance not provided",
                targets=targets,
            )
        )
    return steps


def build_plan(context: RunContext, model_response: str) -> HarnessPlan:
    malformed = False
    steps: list[HarnessPlanStep] = []

    if model_response.strip():
        try:
            parsed = json.loads(model_response)
        except json.JSONDecodeError:
            malformed = True
        else:
            steps = _coerce_steps(parsed)

    if not steps:
        summary = context.queue_item.get("summary", "").strip() or "No queue summary provided"
        hints = ", ".join(context.related_files.keys()) or "queue/runs artifact"
        steps = [
            HarnessPlanStep(
                step_id="S1",
                intent=f"Address queue item: {summary}",
                acceptance="Implementation intent is clearly documented",
                targets=list(context.related_files.keys()),
            ),
            HarnessPlanStep(
                step_id="S2",
                intent="Capture execution artifact for operator traceability",
                acceptance="A run artifact is written under queue/runs",
                targets=["queue/runs"],
            ),
            HarnessPlanStep(
                step_id="S3",
                intent=f"Identify likely touch points ({hints})",
                acceptance="Potential file targets are listed",
                targets=list(context.related_files.keys()),
            ),
        ]

    return HarnessPlan(steps=steps, malformed_output=malformed)
