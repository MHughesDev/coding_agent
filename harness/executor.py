from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from harness.context_loader import RunContext
from harness.result_types import HarnessExecution, HarnessPlan


def execute_plan(context: RunContext, plan: HarnessPlan) -> HarnessExecution:
    queue_id = str(context.queue_item.get("id", "unknown")).strip() or "unknown"
    run_dir = context.repo_path / "queue" / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_path = run_dir / f"{queue_id}-{stamp}.md"

    lines = [
        f"# Harness Run Artifact: {queue_id}",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Queue summary: {context.queue_item.get('summary', '')}",
        "",
        "## Plan Steps",
    ]
    for step in plan.steps:
        targets = ", ".join(step.targets) if step.targets else "(none)"
        lines.append(f"- [{step.step_id}] intent: {step.intent}")
        lines.append(f"  - acceptance: {step.acceptance}")
        lines.append(f"  - targets: {targets}")

    artifact_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return HarnessExecution(
        applied=True,
        notes=f"Wrote harness artifact {artifact_path.relative_to(context.repo_path)}",
        touched_files=[str(artifact_path.relative_to(context.repo_path))],
    )
