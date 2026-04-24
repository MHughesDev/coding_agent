from __future__ import annotations

from pathlib import Path

from harness.context_loader import load_context
from harness.executor import execute_plan
from harness.model_client import OpenAICompatibleClient
from harness.planner import build_plan
from harness.result_types import HarnessRunRequest, HarnessRunResult
from harness.validator import validate_execution


class HarnessRunner:
    def __init__(self, model_client: OpenAICompatibleClient) -> None:
        self._model_client = model_client

    def _load_prompt(self, prompt_file: str, fallback: str) -> str:
        path = Path(__file__).parent / "prompts" / prompt_file
        if path.exists():
            return path.read_text(encoding="utf-8")
        return fallback

    def run(self, request: HarnessRunRequest) -> HarnessRunResult:
        context = load_context(request.repo_path, request.queue_item)
        system_prompt = self._load_prompt("system_prompt.md", "You are a coding harness assistant.")
        completion_prompt = self._load_prompt("completion_prompt.md", "Plan and execute the queue item.")
        user_prompt = (
            f"Queue item: {request.queue_item}\n\n"
            f"Completion guidance:\n{completion_prompt}\n\n"
            f"Repo path: {request.repo_path}"
        )

        try:
            model_response = self._model_client.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        except RuntimeError as exc:
            model_response = f"MODEL_UNAVAILABLE: {exc}"

        plan = build_plan(context, model_response)
        execution = execute_plan(context, plan)
        validation = validate_execution(execution)

        status = "success" if validation.passed else "failed"
        return HarnessRunResult(
            status=status,
            message=validation.details,
            metadata={
                "plan_steps": plan.steps,
                "execution_notes": execution.notes,
                "model_response_excerpt": model_response[:300],
            },
        )
